import uuid
from datetime import date, datetime, time
from io import BytesIO
from typing import List

import httpx
from fastapi.responses import Response
from PIL import Image as PILImage, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image as PDFImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select, func
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.db.schema import DetectedObject, Detection
from app.models.detect import ListObjects, ListDetections, Area
from app.services.detections_service import DetectionService


class ReportService:
    def __init__(
            self,
            session: Session,
            detection_service: DetectionService,
    ):
        self._db = session
        self._detection_service = detection_service

    # Public report entry points

    def generate_interval_detections_report(
            self,
            user_id: uuid.UUID,
            start_date: date,
            end_date: date,
    ) -> Response:

        detections = self._detection_service.get_detections_for_interval(user_id, start_date, end_date)

        pdf = self._create_interval_pdf(detections, start_date, end_date)

        filename = f"detections-report-{start_date}-{end_date}.pdf"

        return self._create_pdf_response(pdf, filename)

    def generate_single_detection_report(
            self,
            detection_id: uuid.UUID,

            bbox_enable: bool,
            bbox_label_enable: bool,
            dot_enable: bool,
            dot_label_enable: bool,

            area_color: str,

            bbox_color: str,
            dot_color: str,
            text_color: str,
            text_background_color: str,
    ) -> Response:

        detection = self._detection_service.get_detection(detection_id)

        objects = self._detection_service.get_objects_from_detection(detection_id)

        pdf = self._create_detection_pdf(
            detection,
            objects,
            area_color=area_color,
            bbox_color=bbox_color,
            dot_color=dot_color,
            text_color=text_color,
            text_background_color=text_background_color,
            bbox_enable=bbox_enable,
            bbox_label_enable=bbox_label_enable,
            dot_enable=dot_enable,
            dot_label_enable=dot_label_enable,
        )

        return self._create_pdf_response(pdf, f"detection-report-{detection_id}.pdf")

    # Shared PDF configuration
    def _create_pdf_response(self, pdf: bytes, filename: str) -> Response:
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def _create_document(self, buffer: BytesIO) -> SimpleDocTemplate:
        return SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

    def _create_header(
            self,
            title: str,
            styles: StyleSheet1,
            spacing: float,
    ) -> list[Flowable]:
        return [
            Paragraph("ObjectDetection", styles["Title"]),
            Paragraph(title, styles["Heading2"]),
            Spacer(1, spacing),
        ]

    def _get_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])

    def _get_information_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eeeeee")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])

    # Report for a date interval

    def _create_interval_pdf(
            self,
            detections: list[ListDetections],
            start_date: date,
            end_date: date,
    ) -> bytes:
        buffer = BytesIO()
        document = self._create_document(buffer)
        styles = getSampleStyleSheet()

        elements = self._create_header("Detection Report", styles, spacing=8)
        elements.extend([
            Paragraph(
                f"<b>Period:</b> {start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}",
                styles["Normal"],
            ),
            Paragraph(f"<b>Total detections:</b> {len(detections)}", styles["Normal"]),
            Spacer(1, 15),
            self._create_interval_table(detections),
        ])

        document.build(elements)
        return buffer.getvalue()

    def _format_processing_time(self, ms: float) -> str:
        if ms < 1000:
            return f"{ms:.2f} ms"
        elif ms < 60000:
            return f"{ms / 1000:.2f} s"
        else:
            return f"{ms / 60000:.2f} min"

    def _create_interval_table(self, detections: list[ListDetections]) -> Table:
        rows = [[
            "Date", "Model", "Threshold Set", "Processing Time", "Nº Objects", "Type",
        ]]
        for detection in detections:
            rows.append([
                detection.created_at.strftime("%d/%m/%Y %H:%M"),
                detection.model,
                f"{detection.conf_threshold * 100:.0f}%",
                f"{self._format_processing_time(detection.processing_time_ms)}",
                str(detection.count),
                detection.type.value,
            ])

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[32 * mm, 25 * mm, 27 * mm, 28 * mm, 20 * mm, 20 * mm],
        )
        table.setStyle(self._get_table_style())
        return table

    # Report for a single detection

    def _create_detection_pdf(
            self,
            detection: Detection,
            objects: list[ListObjects],

            bbox_enable: bool,
            bbox_label_enable: bool,
            dot_enable: bool,
            dot_label_enable: bool,

            area_color: str,

            bbox_color: str,
            dot_color: str,
            text_color: str,
            text_background_color: str,
    ) -> bytes:
        buffer = BytesIO()
        document = self._create_document(buffer)
        styles = getSampleStyleSheet()

        elements = self._create_header(
            f"Detection Report #{detection.id}", styles, spacing=10,
        )

        elements.append(self._create_information_table(detection, objects, styles))
        elements.append(Spacer(1, 20))

        elements.extend(self._create_image_section(
            detection,
            objects,
            document.width,
            styles,
            area_color=area_color,
            bbox_color=bbox_color,
            dot_color=dot_color,
            text_color=text_color,
            text_background_color=text_background_color,
            bbox_enable=bbox_enable,
            bbox_label_enable=bbox_label_enable,
            dot_enable=dot_enable,
            dot_label_enable=dot_label_enable,
        ))

        if objects:
            elements.extend(self._create_class_summary_section(objects, styles))
        elements.extend(self._create_objects_section(objects, styles))

        document.build(elements)
        return buffer.getvalue()

    def _calculate_object_statistics(self, objects: list[ListObjects]) -> dict[str, float]:
        if not objects:
            return {"average": 0, "highest": 0, "lowest": 0, "unique_classes": 0}

        confidences = [obj.confidence for obj in objects]
        return {
            "average": sum(confidences) / len(confidences),
            "highest": max(confidences),
            "lowest": min(confidences),
            "unique_classes": len({obj.obj_class_id for obj in objects}),
        }

    def _create_area_content(
            self,
            detection: Detection,
            styles: StyleSheet1,
    ) -> Paragraph | str:
        coordinates = (
            detection.area_x1, detection.area_y1,
            detection.area_x2, detection.area_y2,
        )
        if any(value is None for value in coordinates):
            return "Undefined"

        area_style = ParagraphStyle(
            "AreaInfo",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            spaceBefore=0,
            spaceAfter=0,
        )
        return Paragraph(
            f"<b>Start Point:</b> "
            f"x = {detection.area_x1:g}, y = {detection.area_y1:g}<br/>"
            f"<b>Final Point:</b> "
            f"x = {detection.area_x2:g}, y = {detection.area_y2:g}",
            area_style,
        )

    def _create_information_table(
            self,
            detection: Detection,
            objects: list[ListObjects],
            styles: StyleSheet1,
    ) -> Table:
        statistics = self._calculate_object_statistics(objects)
        detection_type = (
            detection.type.value
            if hasattr(detection.type, "value")
            else str(detection.type)
        )
        rows = [
            ["Date", detection.created_at.strftime("%d/%m/%Y %H:%M")],
            ["Model", detection.model],
            ["Threshold Set", f"{detection.conf_threshold * 100:.0f}%"],
            ["Processing Time", f"{self._format_processing_time(detection.processing_time_ms)}"],
            ["Type", detection_type],
            ["Objects Detected", str(len(objects))],
            ["Classes Detected", str(statistics["unique_classes"])],
            ["Average Confidence", f"{statistics['average'] * 100:.2f}%"],
            ["Highest Confidence", f"{statistics['highest'] * 100:.2f}%"],
            ["Lowest Confidence", f"{statistics['lowest'] * 100:.2f}%"],
            ["Area", self._create_area_content(detection, styles)],
        ]
        table = Table(rows, colWidths=[45 * mm, 120 * mm])
        table.setStyle(self._get_information_table_style())
        return table

    def _create_image_section(
            self,
            detection: Detection,
            objects: List[ListObjects],
            max_width: float,
            styles: StyleSheet1,

            bbox_enable: bool,
            bbox_label_enable: bool,
            dot_enable: bool,
            dot_label_enable: bool,

            area_color: str,

            bbox_color: str,
            dot_color: str,
            text_color: str,
            text_background_color: str,
    ) -> list[Flowable]:
        return [
            Paragraph("Processed Result", styles["Heading2"]),
            Spacer(1, 8),
            self._create_pdf_image(
                detection.image_url,
                max_width,
                area=[
                    detection.area_x1,
                    detection.area_y1,
                    detection.area_x2,
                    detection.area_y2
                ],
                objects=objects,
                area_color=area_color,
                bbox_color=bbox_color,
                dot_color=dot_color,
                text_color=text_color,
                text_background_color=text_background_color,
                bbox_enable=bbox_enable,
                bbox_label_enable=bbox_label_enable,
                dot_enable=dot_enable,
                dot_label_enable=dot_label_enable,
            ),
            Spacer(1, 20),
        ]

    def _create_pdf_image(
            self,
            image_url: str,
            max_width: float,
            area: list[float | None],
            objects: list[ListObjects] | None = None,
            max_height: float = 100 * mm,

            bbox_enable: bool = True,
            bbox_label_enable: bool = True,
            dot_enable: bool = False,
            dot_label_enable: bool = False,

            area_color: str = "blue",

            bbox_color: str = "red",
            dot_color: str = "yellow",
            text_color: str = "yellow",
            text_background_color: str = "black",

    ) -> PDFImage:

        response = httpx.get(image_url, timeout=30.0)
        response.raise_for_status()

        with PILImage.open(BytesIO(response.content)) as source:
            annotated_image = source.convert("RGB")

        width, height = source.size
        draw = ImageDraw.Draw(annotated_image)
        line_width = max(2, round(min(width, height) / 250))


        if all(value is not None for value in area):
            # Area coordinates are normalized between 0 and 1.
            draw.rectangle(
                area,
                outline=area_color,
                width=line_width,
            )

        for index, obj in enumerate(objects, start=1):

            # Label
            label = f"{index} - {obj.confidence:.0%}"

            # Center of the object
            x_center = (obj.bbox.x1 + obj.bbox.x2) / 2
            y_center = (obj.bbox.y1 + obj.bbox.y2) / 2

            # Position of the text
            text_position = (
                (x_center if dot_label_enable else obj.bbox.x1) + 3,
                max(0, ((y_center - 12) if dot_label_enable else obj.bbox.y1) - 3),
            )

            # Draw bounding box
            if bbox_enable:
                bbox = (
                    obj.bbox.x1,
                    obj.bbox.y1,
                    obj.bbox.x2,
                    obj.bbox.y2,
                )

                draw.rectangle(
                    bbox,
                    outline=bbox_color,
                    width=line_width,
                )

            # Draw a dot at the center of the object
            if dot_enable:

                draw.ellipse(
                    (
                        x_center - 5,
                        y_center - 5,
                        x_center + 5,
                        y_center + 5
                    ),
                    fill=dot_color
                )

            if dot_label_enable or bbox_label_enable:

                # Area occupied by text
                label_bbox = draw.textbbox(
                    text_position,
                    label,
                    anchor="ms" if dot_label_enable else "ls",
                )

                # Drawing background
                padding = 3
                draw.rectangle(
                    (
                        label_bbox[0] - padding,
                        label_bbox[1] - padding,
                        label_bbox[2] + padding,
                        label_bbox[3] + padding,
                    ),
                    fill=text_background_color,
                )

                # Drawing text above
                draw.text(
                    text_position,
                    label,
                    fill=text_color,
                    anchor="ms" if dot_label_enable else "ls",
                )

        image_buffer = BytesIO()
        annotated_image.save(image_buffer, format="PNG")

        scale = min(max_width / width, max_height / height)
        image_buffer.seek(0)

        image = PDFImage(image_buffer, width=width * scale, height=height * scale)
        image.hAlign = "CENTER"

        return image

    def _summarize_objects_by_class(self, objects: list[ListObjects]) -> dict:
        summary = {}
        for obj in objects:
            if obj.obj_class_id not in summary:
                summary[obj.obj_class_id] = {
                    "name": obj.obj_name,
                    "count": 0,
                    "confidence_sum": 0,
                }
            summary[obj.obj_class_id]["count"] += 1
            summary[obj.obj_class_id]["confidence_sum"] += obj.confidence
        return summary

    def _create_class_summary_section(
            self,
            objects: list[ListObjects],
            styles: StyleSheet1,
    ) -> list[Flowable]:
        rows = [["Class ID", "Class", "Objects", "Avg. Confidence"]]
        for class_id, data in self._summarize_objects_by_class(objects).items():
            average = data["confidence_sum"] / data["count"]
            rows.append([
                str(class_id), data["name"], str(data["count"]), f"{average * 100:.2f}%",
            ])

        table = Table(
            rows, repeatRows=1, colWidths=[25 * mm, 50 * mm, 30 * mm, 40 * mm],
        )
        table.setStyle(self._get_table_style())
        return [
            Paragraph("Summary by Class", styles["Heading2"]),
            Spacer(1, 8),
            table,
            Spacer(1, 20),
        ]

    def _create_objects_section(
            self,
            objects: list[ListObjects],
            styles: StyleSheet1,
    ) -> list[Flowable]:
        elements = [
            Paragraph("Detected Objects", styles["Heading2"]),
            Spacer(1, 8),
        ]
        if not objects:
            elements.append(Paragraph("No objects were detected.", styles["Normal"]))
            return elements

        rows = [["#", "ID", "Class ID", "Object", "Confidence"]]
        for index, obj in enumerate(objects, start=1):
            rows.append([
                str(index), str(obj.id), str(obj.obj_class_id), obj.obj_name,
                f"{obj.confidence * 100:.2f}%",
            ])

        table = Table(
            rows, repeatRows=1, colWidths=[10 * mm, 60 * mm, 18 * mm, 35 * mm, 25 * mm],
        )
        table.setStyle(self._get_table_style())
        elements.append(table)
        return elements
