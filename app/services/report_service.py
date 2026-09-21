import uuid
from datetime import date, datetime, time
from io import BytesIO
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.schema import DetectedObject, Detection
from app.models.detect import ListObjects
from app.services.detections_service import DetectionService


class ReportService:

    def __init__(
            self,
            session: Session,
            detection_service: DetectionService,
    ):
        self._db = session
        self._detection_service = detection_service

    def _get_table_style(self) -> TableStyle:
        return TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eeeeee"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )

    def generate_report_interval(
            self,
            user_id: uuid.UUID,
            start_date: date,
            end_date: date,
    ):

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
            .where(
                Detection.user_id == user_id,
                Detection.created_at >= start_datetime,
                Detection.created_at <= end_datetime,
            )
            .group_by(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
            )
            .order_by(Detection.created_at.desc())
        )

        result = self._db.execute(stmt).all()

        pdf = self._create_interval_pdf(
            detections=result,
            start_date=start_date,
            end_date=end_date,
        )

        filename = (
            f"detections-report-{start_date}-{end_date}.pdf"
        )

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    def _create_interval_pdf(
            self,
            detections,
            start_date: date,
            end_date: date,
    ) -> bytes:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()

        elements = []

        # Title
        elements.append(
            Paragraph(
                "ObjectDetection",
                styles["Title"],
            )
        )

        elements.append(
            Paragraph(
                "Detection Report",
                styles["Heading2"],
            )
        )

        elements.append(Spacer(1, 8))

        # Report information
        elements.append(
            Paragraph(
                f"<b>Period:</b> "
                f"{start_date.strftime('%d/%m/%Y')} - "
                f"{end_date.strftime('%d/%m/%Y')}",
                styles["Normal"],
            )
        )

        elements.append(
            Paragraph(
                f"<b>Total detections:</b> {len(detections)}",
                styles["Normal"],
            )
        )

        elements.append(Spacer(1, 15))

        # Table
        table_data = [
            [
                "Date",
                "Model",
                "Threshold Set",
                "Processing Time",
                "Nº Objects",
                "Type",
            ]
        ]

        for detection in detections:
            table_data.append(
                [
                    detection.created_at.strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    detection.model,
                    f"{detection.conf_threshold * 100:.0f}%",
                    f"{detection.processing_time_ms:.3f} ms",
                    str(detection.count_objects),
                    detection.type.value,
                ]
            )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                32 * mm,
                25 * mm,
                27 * mm,
                28 * mm,
                20 * mm,
                20 * mm,
            ],
        )

        table.setStyle(self._get_table_style())

        elements.append(table)

        document.build(elements)

        return buffer.getvalue()

    def generate_detection_report(
            self,
            detection_id: uuid.UUID,
    ):
        detection = self._detection_service.get_detection(
            detection_id
        )

        detection_objects = self._detection_service.get_objects_from_detection(detection_id)

        pdf = self._create_detection_pdf(
            detection=detection,
            objects=detection_objects,
        )

        filename = f"detection-report-{detection_id}.pdf"

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    def _create_detection_pdf(
            self,
            detection: Detection,
            objects: list[ListObjects],
    ) -> bytes:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        elements.append(
            Paragraph(
                "ObjectDetection",
                styles["Title"],
            )
        )

        elements.append(
            Paragraph(
                f"Detection Report #{detection.id}",
                styles["Heading2"],
            )
        )

        elements.append(Spacer(1, 10))

        detection_type = (
            detection.type.value
            if hasattr(detection.type, "value")
            else str(detection.type)
        )

        if objects:
            average_confidence = (
                    sum(obj.confidence for obj in objects) / len(objects)
            )

            highest_confidence = max(
                obj.confidence for obj in objects
            )

            lowest_confidence = min(
                obj.confidence for obj in objects
            )

            unique_classes = len({
                obj.obj_class_id for obj in objects
            })
        else:
            average_confidence = 0
            highest_confidence = 0
            lowest_confidence = 0
            unique_classes = 0

        # Informações gerais da deteção
        information_data = [
            [
                "Date",
                detection.created_at.strftime("%d/%m/%Y %H:%M")
            ],
            [
                "Model",
                detection.model
            ],
            [
                "Threshold Set",
                f"{detection.conf_threshold * 100:.0f}%",
            ],
            [
                "Processing Time",
                f"{detection.processing_time_ms:.3f} ms",
            ],
            [
                "Type",
                detection_type
            ],
            [
                "Objects Detected",
                str(len(objects))
            ],
            [
                "Classes Detected",
                str(unique_classes)
            ],
            [
                "Average Confidence",
                f"{average_confidence * 100:.2f}%"
            ],
            [
                "Highest Confidence",
                f"{highest_confidence * 100:.2f}%"
            ],
            [
                "Lowest Confidence",
                f"{lowest_confidence * 100:.2f}%"
            ],
        ]

        information_table = Table(
            information_data,
            colWidths=[
                45 * mm,
                120 * mm,
            ],
        )

        information_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#eeeeee"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        elements.append(information_table)
        elements.append(Spacer(1, 20))

        class_summary = {}

        for obj in objects:
            if obj.obj_class_id not in class_summary:
                class_summary[obj.obj_class_id] = {
                    "name": obj.obj_name,
                    "count": 0,
                    "confidence_sum": 0,
                }

            class_summary[obj.obj_class_id]["count"] += 1
            class_summary[obj.obj_class_id]["confidence_sum"] += (
                obj.confidence
            )

        class_data = [
            [
                "Class ID",
                "Class",
                "Objects",
                "Avg. Confidence",
            ]
        ]

        for class_id, data in class_summary.items():
            average = (
                    data["confidence_sum"] / data["count"]
            )

            class_data.append(
                [
                    str(class_id),
                    data["name"],
                    str(data["count"]),
                    f"{average * 100:.2f}%",
                ]
            )

        class_table = Table(
            class_data,
            repeatRows=1,
            colWidths=[
                25 * mm,
                50 * mm,
                30 * mm,
                40 * mm,
            ],
        )

        class_table.setStyle(
            self._get_table_style()
        )

        if objects:
            elements.append(
                Paragraph(
                    "Summary by Class",
                    styles["Heading2"],
                )
            )

            elements.append(Spacer(1, 8))
            elements.append(class_table)
            elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                "Detected Objects",
                styles["Heading2"],
            )
        )

        elements.append(Spacer(1, 8))

        if not objects:
            elements.append(
                Paragraph(
                    "No objects were detected.",
                    styles["Normal"],
                )
            )
        else:
            objects_data = [
                [
                    "ID",
                    "Class ID",
                    "Object",
                    "Confidence",
                ]
            ]

            for detected_object in objects:
                objects_data.append(
                    [
                        str(detected_object.id),
                        str(detected_object.obj_class_id),
                        detected_object.obj_name,
                        f"{detected_object.confidence * 100:.2f}%",
                    ]
                )

            objects_table = Table(
                objects_data,
                repeatRows=1,
                colWidths=[
                    60 * mm,
                    20 * mm,
                    30 * mm,
                    30 * mm
                ],
            )

            objects_table.setStyle(self._get_table_style())
            elements.append(objects_table)

        document.build(elements)

        return buffer.getvalue()
