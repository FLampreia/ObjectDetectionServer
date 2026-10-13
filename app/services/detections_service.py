import uuid
from datetime import datetime, time, date
from typing import List
from sqlalchemy import select, func, Row
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException

from app.db.schema import DetectedObject, User, Detection, DetectionType, Team, DetectionImage, TeamMember, LineCrossing
from app.exceptions.custom_exceptions import DetectionNotFound, FailedDeletingFromCloud, NotAllowedToDelete
from app.models.detect import ListObjects, ListDetections, Area, Line, ListImages, ListCrossing
from app.models.stats import ModelsUsage, DetectionTypeUsage, TopObject, Stats
from app.services.cloudinary_service import delete_image
from app.services.user_service import UserService


class DetectionService:

    def __init__(
            self,
            session: Session,
    ):
        self._db = session

    def get_detection(
            self,
            detection_id: uuid.UUID,
    ) -> Detection | None:
        stmt = (
            select(Detection)
            .where(Detection.id == detection_id)
        )

        return self._db.scalar(stmt)

    async def delete_detection(
            self,
            current_user: User,
            detection_ids: list[uuid.UUID],
    ):
        # Remove duplicate UUIDs
        detection_ids = list(set(detection_ids))

        # Get all requested detections
        statement = select(Detection).where(
            Detection.id.in_(detection_ids),
        )

        detections = self._db.scalars(statement).all()

        # Check if all detections exist
        if len(detections) != len(detection_ids):
            raise DetectionNotFound()

        # Check if user owns all detections
        if any(
                detection.user_id != current_user.id
                for detection in detections
        ):
            raise NotAllowedToDelete()


        for detection in detections:

            # Delete images from Cloudinary
            for image in detection.images:
                if image.image_public_id is None:
                    continue
                try:
                    await delete_image(image.image_public_id)
                except Exception:
                    raise FailedDeletingFromCloud()

            # Delete detections from database
            self._db.delete(detection)

        self._db.commit()

        return True

    def get_all_detection_from_logged_user(
            self,
            current_user: User
    ) -> list[ListDetections]:
        stmt = (
            select(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
                Detection.team_id,
                Team.name.label("team_name"),
                func.count(DetectedObject.id).label("count_objects"),
            )
            .outerjoin(
                DetectedObject,
                DetectedObject.detection_id == Detection.id
            )
            .where(Detection.user_id == current_user.id)
            .outerjoin(Team, Team.id == Detection.team_id)
            .group_by(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
                Detection.team_id,
                Team.name,
            )
            .order_by(Detection.created_at.desc())
        )

        result = self._db.execute(stmt).all()

        return [
            ListDetections(
                id=r.id,
                username=current_user.username,
                created_at=r.created_at,
                model=r.model,
                conf_threshold=r.conf_threshold,
                processing_time_ms=r.processing_time_ms,
                count=r.count_objects,
                type=r.type,
                team_id=r.team_id,
                team_name=r.team_name,
            )
            for r in result
        ]

    def get_objects_from_detection(
            self,
            detection_id: uuid.UUID,
    ) -> list[ListObjects]:
        stmt = (
            select(
                DetectedObject.id,
                DetectedObject.object_name,
                DetectedObject.object_class_id,
                DetectedObject.confidence,
                DetectedObject.mean_confidence,
                DetectedObject.confidence_samples,
                DetectedObject.bbox_x1,
                DetectedObject.bbox_y1,
                DetectedObject.bbox_x2,
                DetectedObject.bbox_y2,
                DetectedObject.track_id,
                DetectedObject.image_id,
                DetectionImage.frame_number,
            )
            .where(DetectedObject.detection_id == detection_id)
            .outerjoin(DetectionImage, DetectionImage.id == DetectedObject.image_id)
        )

        result = self._db.execute(stmt).all()

        return [
            ListObjects(
                id=r.id,
                obj_name=r.object_name,
                obj_class_id=r.object_class_id,
                confidence=r.mean_confidence if r.mean_confidence is not None else r.confidence,
                frame_confidence=r.confidence,
                mean_confidence=r.mean_confidence,
                confidence_samples=r.confidence_samples,
                track_id=r.track_id,
                image_id=r.image_id,
                frame_number=r.frame_number,
                bbox=Area(
                    x1=r.bbox_x1,
                    y1=r.bbox_y1,
                    x2=r.bbox_x2,
                    y2=r.bbox_y2,
                )
            ) for r in result
        ]

    def get_images_from_detection(self, detection_id, current_user, frames_only=False):

        detection = self.get_detection(detection_id)

        if detection is None:
            raise HTTPException(404, "Detection not found")

        if detection.user_id != current_user.id:
            member = None if detection.team_id is None else self._db.get(
                TeamMember, (current_user.id, detection.team_id),
            )
            if member is None:
                raise HTTPException(403, "Not allowed to access this detection")

        statement = (
            select(DetectionImage)
            .where(DetectionImage.detection_id == detection_id)
            .options(selectinload(DetectionImage.objects),
                     selectinload(DetectionImage.crossings).selectinload(LineCrossing.object))
            .order_by(DetectionImage.frame_number)
        )

        if frames_only:
            statement = statement.where(DetectionImage.frame_number.is_not(None))
        images = self._db.scalars(statement).all()

        area_coordinates = (detection.area_x1, detection.area_y1, detection.area_x2, detection.area_y2)
        area = Area(x1=area_coordinates[0], y1=area_coordinates[1],
                    x2=area_coordinates[2], y2=area_coordinates[3]) if all(
            coordinate is not None for coordinate in area_coordinates
        ) else None
        line_coordinates = (detection.line_x1, detection.line_y1, detection.line_x2, detection.line_y2)
        line = Line(x1=line_coordinates[0], y1=line_coordinates[1],
                    x2=line_coordinates[2], y2=line_coordinates[3]) if all(
            coordinate is not None for coordinate in line_coordinates
        ) else None

        return [ListImages(
            id=frame.id, frame_number=frame.frame_number,
            timestamp_ms=frame.timestamp_ms, image_url=frame.image_url,
            area=area,
            line=line,
            crossings=[self.serialize_crossing(event) for event in frame.crossings],
            objects=[ListObjects(
                id=obj.id, obj_name=obj.object_name, obj_class_id=obj.object_class_id,
                confidence=obj.confidence, track_id=obj.track_id,
                frame_confidence=obj.confidence,
                mean_confidence=obj.mean_confidence, confidence_samples=obj.confidence_samples,
                image_id=frame.id, frame_number=frame.frame_number,
                bbox=Area(x1=obj.bbox_x1, y1=obj.bbox_y1, x2=obj.bbox_x2, y2=obj.bbox_y2),
            ) for obj in frame.objects],
        ) for frame in images]

    def get_frames_from_detection(self, detection_id, current_user):
        return self.get_images_from_detection(detection_id, current_user, frames_only=True)

    @staticmethod
    def serialize_crossing(event):
        return ListCrossing(
            id=event.id, object_id=event.object_id, image_id=event.image_id,
            track_id=event.track_id, obj_name=event.object.object_name,
            obj_class_id=event.object.object_class_id, direction=event.direction,
            confidence=event.confidence, frame_number=event.frame_number,
            timestamp_ms=event.timestamp_ms,
            bbox=Area(x1=event.bbox_x1, y1=event.bbox_y1, x2=event.bbox_x2, y2=event.bbox_y2),
        )

    def get_detections_stats(
            self,
            current_user: User,
    ) -> Stats:
        # Total detections
        total_detections = self._db.scalar(
            select(func.count(Detection.id))
            .where(Detection.user_id == current_user.id)
        ) or 0

        # Total detected objects
        total_objects = self._db.scalar(
            select(func.count(DetectedObject.id))
            .join(
                Detection,
                Detection.id == DetectedObject.detection_id,
            )
            .where(Detection.user_id == current_user.id)
        ) or 0

        # Most frequently detected objects
        top_objects_result = self._db.execute(
            select(
                DetectedObject.object_name,
                func.count(DetectedObject.id).label("count"),
            )
            .join(
                Detection,
                Detection.id == DetectedObject.detection_id,
            )
            .where(Detection.user_id == current_user.id)
            .group_by(DetectedObject.object_name)
            .order_by(func.count(DetectedObject.id).desc())
            .limit(5)
        ).all()

        top_objects = [
            TopObject(
                name=row.object_name,
                count=row.count,
            )
            for row in top_objects_result
        ]

        # Most frequently used models
        top_models_result = self._db.execute(
            select(
                Detection.model,
                func.count(Detection.id).label("count"),
            )
            .where(Detection.user_id == current_user.id)
            .group_by(Detection.model)
            .order_by(func.count(Detection.id).desc())
            .limit(5)
        )

        top_models = [
            ModelsUsage(
                name=row.model,
                count=row.count,
            )
            for row in top_models_result
        ]

        # Detection counts by type
        detection_types = self._db.execute(
            select(
                Detection.type,
                func.count(Detection.id).label("count"),
            )
            .where(Detection.user_id == current_user.id)
            .group_by(Detection.type)
            .order_by(func.count(Detection.id).desc())
            .limit(3)
        )

        detection_types = [
            DetectionTypeUsage(
                type=row.type,
                count=row.count,
            )
            for row in detection_types
        ]

        # Latest detections
        last_detections_result = self._db.execute(
            select(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                func.count(DetectedObject.id).label("count"),
                Detection.type,
            )
            .join(
                User,
                User.id == Detection.user_id,
            )
            .outerjoin(
                DetectedObject,
                DetectedObject.detection_id == Detection.id,
            )
            .where(Detection.user_id == current_user.id)
            .group_by(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
            )
            .order_by(Detection.created_at.desc())
            .limit(5)
        ).all()

        last_detections = [
            ListDetections(
                id=row.id,
                username=row.username,
                created_at=row.created_at,
                model=row.model,
                conf_threshold=row.conf_threshold,
                processing_time_ms=row.processing_time_ms,
                count=row.count,
                type=row.type,
            )
            for row in last_detections_result
        ]

        return Stats(
            total_detections=total_detections,
            total_objects=total_objects,

            top_objects=top_objects,
            top_models=top_models,
            detection_types=detection_types,

            last_detections=last_detections,
        )

    def get_detections_for_interval(
            self,
            user_id: uuid.UUID,
            start_date: date,
            end_date: date,
            model: str | None = None,
            detection_type: DetectionType | None = None,
            team_id: uuid.UUID | None = None,
            unassigned: bool = False,
    ) -> list[ListDetections]:
        start_datetime = datetime.combine(
            start_date,
            time.min,
        )

        end_datetime = datetime.combine(
            end_date,
            time.max,
        )

        stmt = (
            select(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
                func.count(DetectedObject.id).label("count_objects"),
            )
            .outerjoin(
                DetectedObject,
                DetectedObject.detection_id == Detection.id
            )
            .join(User, User.id == Detection.user_id)
            .where(
                Detection.user_id == user_id,
                Detection.created_at >= start_datetime,
                Detection.created_at <= end_datetime,
            )
            .group_by(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
            )
            .order_by(Detection.created_at.desc())
        )

        if model is not None:
            stmt = stmt.where(Detection.model == model)
        if detection_type is not None:
            stmt = stmt.where(Detection.type == detection_type)
        if team_id is not None:
            stmt = stmt.where(Detection.team_id == team_id)
        if unassigned:
            stmt = stmt.where(Detection.team_id.is_(None))

        return [
            ListDetections(
                id=row.id,
                username=row.username,
                created_at=row.created_at,
                model=row.model,
                conf_threshold=row.conf_threshold,
                processing_time_ms=row.processing_time_ms,
                count=row.count_objects,
                type=row.type,
            )
            for row in self._db.execute(stmt).all()
        ]
