import uuid
from datetime import date, datetime, time
from io import BytesIO
from typing import List
from xml.sax.saxutils import escape

import httpx
from fastapi.responses import Response
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image as PDFImage,
    Paragraph,
    PageBreak,
    KeepTogether,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select, func
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.db.schema import DetectedObject, Detection, DetectionType
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
            model: str | None = None,
            detection_type: DetectionType | None = None,
            team_id: uuid.UUID | None = None,
            unassigned: bool = False,
    ) -> Response:

        # Fetch only the detections matching the requested period and filters.
        detections = self._detection_service.get_detections_for_interval(
            user_id,
            start_date,
            end_date,
            model=model,
            detection_type=detection_type,
            team_id=team_id,
            unassigned=unassigned,
        )

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

        # Render the report using the selected image annotation options.
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
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title="Individual detection report",
            author="ObjectDetection",
        )

    def _create_header(
            self,
            title: str,
            styles: StyleSheet1,
            spacing: float,
    ) -> list[Flowable]:
        return [
            Paragraph(
                "OBJECTDETECTION",
                ParagraphStyle(
                    "ReportBrand",
                    fontName="Helvetica-Bold",
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor("#475467"),
                ),
            ),
            Paragraph(title, styles["Title"]),
            Spacer(1, spacing),
        ]

    def _report_styles(self) -> StyleSheet1:
        styles = getSampleStyleSheet()

        # Use a clear hierarchy for the report title, section headings and body.
        styles["Title"].fontName = "Helvetica-Bold"
        styles["Title"].fontSize = 22
        styles["Title"].leading = 28
        styles["Title"].alignment = 0
        styles["Title"].spaceBefore = 6
        styles["Title"].textColor = colors.HexColor("#182230")

        styles["Heading2"].fontSize = 12
        styles["Heading2"].leading = 16
        styles["Heading2"].textColor = colors.HexColor("#182230")

        styles["Normal"].fontSize = 9
        styles["Normal"].leading = 13
        styles["Normal"].textColor = colors.HexColor("#475467")

        return styles

    def _draw_report_page(self, canvas, doc, subtitle: str):
        canvas.saveState()

        # Align page decorations with the padded content frame.
        left, right = doc.leftMargin + 6, A4[0] - doc.rightMargin - 6

        # Draw the footer separator, report context and page number.
        canvas.setStrokeColor(colors.HexColor("#D0D5DD"))
        canvas.setLineWidth(0.5)
        canvas.line(left, 16 * mm, right, 16 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#475467"))
        canvas.drawString(left, 11 * mm, f"ObjectDetection | {subtitle}")
        canvas.drawRightString(right, 11 * mm, f"Page {doc.page}")

        # Repeat a compact header on continuation pages.
        if doc.page > 1:
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(left, A4[1] - 12 * mm, "Detection report")
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(right, A4[1] - 12 * mm, subtitle)

        canvas.restoreState()

    def _styled_report_table(self, rows, ratios, width, numeric_columns=()) -> Table:
        cell = ParagraphStyle(
            "ReportCell",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#344054"),
            splitLongWords=True,
        )

        header = ParagraphStyle(
            "ReportTableHeader",
            parent=cell,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.white,
        )

        # Escape user text before ReportLab interprets paragraph markup.
        cells = [
            [
                Paragraph(escape(str(value)), header if index == 0 else cell)
                for value in row
            ]
            for index, row in enumerate(rows)
        ]

        # Keep column proportions consistent and repeat headers after page breaks.
        table = Table(
            cells,
            repeatRows=1,
            colWidths=[width * ratio / sum(ratios) for ratio in ratios],
            hAlign="LEFT",
        )

        commands = list(self._get_table_style().getCommands())

        # Paragraph alignment controls numeric cells independently of table placement.
        for column in numeric_columns:
            for row in cells[1:]:
                row[column].style = ParagraphStyle("ReportNumeric", parent=cell, alignment=2)

        table.setStyle(TableStyle(commands))

        return table

    def _get_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#344054")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#EAECF0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])

    def _get_information_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F4F7")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#344054")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#EAECF0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])

    # Report for a date interval

    def _create_interval_pdf(
            self,
            detections: list[ListDetections],
            start_date: date,
            end_date: date,
    ) -> bytes:
        buffer = BytesIO()

        # Reserve space above and below the content for page decorations.
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title="Detection report by date interval",
            author="ObjectDetection",
        )

        width = document.width - 12  # Account for the document frame's padding.

        # Define the interval report's typography and color palette.
        ink = colors.HexColor("#182230")
        muted = colors.HexColor("#475467")
        styles = getSampleStyleSheet()

        brand = ParagraphStyle(
            "IntervalBrand",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=muted,
        )

        title = ParagraphStyle(
            "IntervalTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=ink,
            spaceBefore=6,
            spaceAfter=8,
        )

        body = ParagraphStyle(
            "IntervalBody",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=muted,
        )

        metric = ParagraphStyle(
            "IntervalMetric",
            parent=body,
            fontSize=9,
            leading=18,
        )

        heading = ParagraphStyle(
            "IntervalHeading",
            parent=styles["Heading2"],
            textColor=ink,
            fontSize=12,
            leading=16,
            spaceAfter=8,
        )

        # Start with the report identity and the selected date range.
        period = f"{start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}"

        elements = [
            Paragraph("OBJECTDETECTION", brand),
            Paragraph("Detection report", title),
            Paragraph(f"Period: {period}", body),
            Spacer(1, 16),
        ]
        # Summarize the filtered results before listing individual detections.
        total_objects = sum(detection.count for detection in detections)

        summary = Table([[
            Paragraph(f"Detections<br/><font size='16' color='#182230'><b>{len(detections):,}</b></font>", metric),
            Paragraph(f"Objects detected<br/><font size='16' color='#182230'><b>{total_objects:,}</b></font>", metric),
        ]], colWidths=[width / 2] * 2, hAlign="LEFT")

        summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))

        elements.extend([summary, Spacer(1, 20), Paragraph("Detections in this period", heading)])

        # An empty result still produces a useful report with a clear message.
        if detections:
            elements.append(self._create_interval_table(detections, width=width))
        else:
            elements.append(Paragraph("No detections match this period and the selected filters.", body))

        def draw_page(canvas, doc):
            self._draw_report_page(canvas, doc, period)

        document.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)

        return buffer.getvalue()

    def _format_processing_time(self, ms: float) -> str:
        if ms < 1000:
            return f"{ms:.2f} ms"
        elif ms < 60000:
            return f"{ms / 1000:.2f} s"
        else:
            return f"{ms / 60000:.2f} min"

    def _create_interval_table(
            self,
            detections: list[ListDetections],
            width: float = 176 * mm,
    ) -> Table:
        # Allow long model names to wrap instead of overflowing their column.
        cell_style = ParagraphStyle(
            "IntervalCell",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#344054"),
            splitLongWords=True,
        )

        header_style = ParagraphStyle(
            "IntervalTableHeader",
            parent=cell_style,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.white,
        )

        rows = [[Paragraph(label, header_style) for label in (
            "Date",
            "Model",
            "Threshold",
            "Processing<br/>time",
            "Objects",
            "Type",
        )]]

        # Keep dates compact and format numeric values for quick comparison.
        for detection in detections:
            rows.append([
                Paragraph(detection.created_at.strftime("%d/%m/%Y<br/>%H:%M"), cell_style),
                Paragraph(escape(detection.model), cell_style),
                f"{detection.conf_threshold * 100:.0f}%",
                f"{self._format_processing_time(detection.processing_time_ms)}",
                str(detection.count),
                Paragraph(escape(detection.type.value.title()), cell_style),
            ])

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[width * ratio / 176 for ratio in (30, 60, 22, 25, 20, 19)],
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#344054")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#344054")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#344054")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#EAECF0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 1), (4, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

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
        styles = self._report_styles()
        width = document.width - 12

        # Present the report title separately from the full detection identifier.
        elements = self._create_header(
            "Detection report",
            styles,
            spacing=0,
        )

        elements.extend([
            Paragraph(f"Detection ID: {detection.id}", styles["Normal"]),
            Spacer(1, 16),
        ])

        # Show detection metadata before the annotated image.
        elements.append(self._create_information_table(detection, objects, styles))
        elements.append(Spacer(1, 20))

        annotation_options = dict(
            area_color=area_color, bbox_color=bbox_color, dot_color=dot_color,
            text_color=text_color, text_background_color=text_background_color,
            bbox_enable=bbox_enable, bbox_label_enable=bbox_label_enable,
            dot_enable=dot_enable, dot_label_enable=dot_label_enable,
        )
        if detection.type in (DetectionType.Video, DetectionType.Stream):
            if objects:
                elements.extend(self._create_class_summary_section(objects, styles, width))
            elements.extend(self._create_frames_section(
                detection, objects, width, styles, **annotation_options,
            ))
            if detection.line_x1 is not None:
                elements.extend(self._create_crossings_section(detection, width, styles, **annotation_options))
        else:
            elements.extend(self._create_image_section(
                detection, objects, width, styles, **annotation_options,
            ))
            # Follow the photo with class totals and the complete object list.
            if objects:
                elements.extend(self._create_class_summary_section(objects, styles, width))
            elements.extend(self._create_objects_section(objects, styles, width))

        def draw_page(canvas, doc):
            self._draw_report_page(canvas, doc, detection.created_at.strftime("%d/%m/%Y %H:%M"))

        document.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)

        return buffer.getvalue()

    def _create_frames_section(self, detection, objects, width, styles, **annotation_options):
        frames = sorted(
            (image for image in detection.images if image.frame_number is not None and image.objects),
            key=lambda image: image.frame_number,
        )
        elements = [Paragraph("Saved Detection Frames", styles["Heading2"])]
        if not frames:
            elements.append(Paragraph(
                "No saved frames are available for this detection.", styles["Normal"],
            ))
            # Older detections may have objects without an associated image.
            elements.extend(self._create_objects_section(objects, styles, width))
            return elements

        elements.append(Paragraph(
            f"{len(frames)} saved frames. Each frame shows only the objects first detected "
            "in that frame. Annotation numbers match the object table below each image.",
            styles["Normal"],
        ))
        objects_by_image = {}
        for obj in objects:
            frame_object = obj.model_copy(update={
                "confidence": obj.frame_confidence if obj.frame_confidence is not None else obj.confidence,
            })
            objects_by_image.setdefault(obj.image_id, []).append(frame_object)
        area = [detection.area_x1, detection.area_y1, detection.area_x2, detection.area_y2]
        gap = 12
        card_width = (width - gap) / 2
        card_height = 100 * mm
        cards = []
        for frame in frames:
            frame_objects = objects_by_image.get(frame.id, [])
            if frame.timestamp_ms is None:
                timestamp = "Unavailable"
            else:
                milliseconds = max(0, round(frame.timestamp_ms))
                seconds, milliseconds = divmod(milliseconds, 1000)
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                timestamp = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
            prefix = [
                Paragraph(f"Frame {frame.frame_number}", styles["Heading2"]),
                Paragraph(
                    f"{timestamp} | New objects: {len(frame_objects)}", styles["Normal"],
                ),
                Spacer(1, 6),
                self._create_pdf_image(
                    frame.image_url, card_width, area=area, objects=frame_objects,
                    line=[detection.line_x1, detection.line_y1, detection.line_x2, detection.line_y2],
                    max_height=50 * mm, label_font_size=7, **annotation_options,
                ),
                Spacer(1, 8),
            ]
            if not frame_objects:
                cards.append(prefix + [Paragraph("No objects were detected.", styles["Normal"])])
                continue
            table = self._create_frame_objects_table(frame_objects, card_width)
            # Split crowded frames into bounded cards so a grid row always fits a page.
            while table is not None:
                prefix_height = sum(item.wrap(card_width, card_height)[1] for item in prefix)
                available = card_height - prefix_height - 12
                if table.wrap(card_width, available)[1] <= available:
                    cards.append(prefix + [table])
                    break
                parts = table.split(card_width, available)
                if len(parts) < 2:
                    raise ValueError("A frame object row is too large for the compact report layout")
                cards.append(prefix + [parts[0]])
                table = parts[1]
                prefix = [
                    Paragraph(f"Frame {frame.frame_number} (continued)", styles["Heading2"]),
                    Paragraph(timestamp, styles["Normal"]),
                    Spacer(1, 6),
                ]
        rows = [[elements, "", ""]]
        rows.extend([[cards[index], "", cards[index + 1] if index + 1 < len(cards) else ""]
                     for index in range(0, len(cards), 2)])
        grid = Table(rows, colWidths=[card_width, gap, card_width], hAlign="LEFT")
        grid.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("NOSPLIT", (0, 0), (-1, 1)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ]))
        elements = [Spacer(1, 12), grid]
        frame_ids = {frame.id for frame in frames}
        unassociated = [obj for obj in objects if obj.image_id not in frame_ids]
        if unassociated:
            elements.extend([
                PageBreak(),
                Paragraph("Objects Without a Saved Frame", styles["Heading2"]),
                Paragraph(
                    "These older records have no associated frame image.", styles["Normal"],
                ),
            ])
            elements.extend(self._create_objects_section(unassociated, styles, width))
        return elements

    def _create_crossings_section(self, detection, width, styles, **annotation_options):
        events = sorted(detection.crossings, key=lambda event: (event.frame_number, event.track_id))
        forward = sum(event.direction == "A_to_B" for event in events)
        elements = [Paragraph("Line Crossings", styles["Heading2"]), Paragraph(
            f"Total passages: {len(events)} | A to B: {forward} | B to A: {len(events) - forward}", styles["Normal"]),
            Paragraph("Crossings use the bounding-box center. A and B are the sides of the oriented line.", styles["Normal"]),
            Spacer(1, 10)]
        by_image = {}
        for event in events:
            by_image.setdefault(event.image_id, []).append(event)
        cards, gap = [], 12
        card_width = (width - gap) / 2
        # Keep each two-column card small enough to fit on a report page.
        chunks = (group[start:start + 6] for group in by_image.values() for start in range(0, len(group), 6))
        for frame_events in chunks:
            frame = frame_events[0].image
            frame_objects = [ListObjects(
                id=event.object_id, obj_name=event.object.object_name,
                obj_class_id=event.object.object_class_id, confidence=event.confidence,
                bbox=Area(x1=event.bbox_x1, y1=event.bbox_y1, x2=event.bbox_x2, y2=event.bbox_y2),
            ) for event in frame_events]
            cards.append([
                Paragraph(f"Frame {frame.frame_number} | {frame.timestamp_ms / 1000:.2f} s", styles["Heading2"]),
                self._create_pdf_image(frame.image_url, card_width,
                    area=[detection.area_x1, detection.area_y1, detection.area_x2, detection.area_y2],
                    line=[detection.line_x1, detection.line_y1, detection.line_x2, detection.line_y2],
                    objects=frame_objects, max_height=50 * mm, label_font_size=7,
                    **{**annotation_options, "bbox_enable": True}),
                Spacer(1, 6),
                self._styled_report_table(
                    [["#", "Object", "Direction"]] + [[str(index), event.object.object_name,
                        "A to B" if event.direction == "A_to_B" else "B to A"]
                        for index, event in enumerate(frame_events, 1)], (9, 48, 29), card_width, (0,)),
            ])
        if cards:
            grid = Table([[cards[index], "", cards[index + 1] if index + 1 < len(cards) else ""]
                          for index in range(0, len(cards), 2)], colWidths=[card_width, gap, card_width])
            grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
            elements.append(grid)
        return elements

    def _create_frame_objects_table(self, objects, width):
        rows = [["#", "Object", "Conf."]]
        for index, obj in enumerate(objects, start=1):
            rows.append([
                str(index), obj.obj_name, f"{obj.confidence * 100:.1f}%",
            ])
        table = self._styled_report_table(rows, (9, 58, 19), width, (0, 2))
        table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

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
            detection.area_x1,
            detection.area_y1,
            detection.area_x2,
            detection.area_y2,
        )

        # Missing area coordinates mean the full image was processed.
        if any(value is None for value in coordinates):
            return "Full Frame"

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
        label_style = ParagraphStyle(
            "InformationLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
        )

        # Preserve formatted area content while escaping plain metadata values.
        rows = [
            [
                Paragraph(escape(label), label_style),
                value
                if isinstance(value, Paragraph)
                else Paragraph(escape(value), styles["Normal"]),
            ]
            for label, value in rows
        ]

        width = A4[0] - 30 * mm - 12

        table = Table(rows, colWidths=[width * 0.29, width * 0.71], hAlign="LEFT")
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
        if not detection.images:
            return []
        return [
            Paragraph("Processed Result", styles["Heading2"]),
            self._create_pdf_image(
                detection.images[0].image_url,
                max_width,
                area=[
                    detection.area_x1,
                    detection.area_y1,
                    detection.area_x2,
                    detection.area_y2
                ],
                objects=objects,
                max_height=75 * mm,
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
            label_font_size: float | None = None,
            line: list[float | None] | None = None,

    ) -> PDFImage:

        # Download the source image before applying the requested annotations.
        response = httpx.get(image_url, timeout=30.0)
        response.raise_for_status()

        with PILImage.open(BytesIO(response.content)) as source:
            annotated_image = source.convert("RGB")

        width, height = source.size
        scale = min(max_width / width, max_height / height)
        font = ImageFont.load_default(size=max(10, round(label_font_size / scale))) if label_font_size else None
        draw = ImageDraw.Draw(annotated_image)
        line_width = max(2, round(min(width, height) / 250))
        if line is not None and all(value is not None for value in line):
            draw.line(line, fill="#a78bfa", width=line_width)
            dx, dy = line[2] - line[0], line[3] - line[1]
            length = (dx * dx + dy * dy) ** 0.5
            if length:
                side_font = ImageFont.load_default(size=max(14, round(width / 50)))
                offset = max(22, width / 30)
                for label, sign in (("A", -1), ("B", 1)):
                    point = ((line[0] + line[2]) / 2 - sign * dy / length * offset,
                             (line[1] + line[3]) / 2 + sign * dx / length * offset)
                    draw.text(point, label, font=side_font, anchor="mm", fill="#a78bfa",
                              stroke_width=2, stroke_fill="black")
        if all(value is not None for value in area):
            # Outline the configured detection area.
            draw.rectangle(
                [min(area[0], area[2]), min(area[1], area[3]),
                 max(area[0], area[2]), max(area[1], area[3])],
                outline=area_color,
                width=line_width,
            )

        for index, obj in enumerate(objects or [], start=1):

            # Match object labels to the numbered rows in the details table.
            label = f"{index} - {obj.confidence:.0%}"

            # Calculate the object center for optional dot annotations.
            x_center = (obj.bbox.x1 + obj.bbox.x2) / 2
            y_center = (obj.bbox.y1 + obj.bbox.y2) / 2

            # Place labels near the selected marker and keep them below the top edge.
            text_position = (
                (x_center if dot_label_enable else obj.bbox.x1) + 3,
                max(0, ((y_center - 12) if dot_label_enable else obj.bbox.y1) - 3),
            )
            if label_font_size:
                text_position = (text_position[0], max(font.size + 3, text_position[1]))

            # Draw the bounding box when enabled.
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

            # Draw an optional dot at the object center.
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

                # Measure the label before drawing its background.
                label_bbox = draw.textbbox(
                    text_position,
                    label,
                    font=font,
                    anchor="ms" if dot_label_enable else "ls",
                )

                # Add padding around the label for contrast against the image.
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

                # Draw the label over its background.
                draw.text(
                    text_position,
                    label,
                    font=font,
                    fill=text_color,
                    anchor="ms" if dot_label_enable else "ls",
                )

        # Scale the annotated image to fit while preserving its aspect ratio.
        image_buffer = BytesIO()
        annotated_image.save(image_buffer, format="PNG")

        image_buffer.seek(0)

        image = PDFImage(image_buffer, width=width * scale, height=height * scale)
        image.hAlign = "CENTER"

        return image

    def _summarize_objects_by_class(self, objects: list[ListObjects]) -> dict:
        summary = {}

        # Aggregate object counts and confidence totals by class identifier.
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
            width: float = 176 * mm,
    ) -> list[Flowable]:
        rows = [["Class ID", "Class", "Objects", "Avg. Confidence"]]

        for class_id, data in self._summarize_objects_by_class(objects).items():
            average = data["confidence_sum"] / data["count"]
            rows.append([
                str(class_id),
                data["name"],
                str(data["count"]),
                f"{average * 100:.2f}%",
            ])

        table = self._styled_report_table(rows, (25, 70, 30, 40), width, (0, 2, 3))

        # Keep the class summary heading with its table whenever it fits on a page.
        return [
            KeepTogether([Paragraph("Summary by Class", styles["Heading2"]), table]),
            Spacer(1, 20),
        ]

    def _create_objects_section(
            self,
            objects: list[ListObjects],
            styles: StyleSheet1,
            width: float = 176 * mm,
    ) -> list[Flowable]:
        elements = [
            Paragraph("Detected Objects", styles["Heading2"]),
        ]

        if not objects:
            elements.append(Paragraph("No objects were detected.", styles["Normal"]))
            return elements

        rows = [["#", "ID", "Class ID", "Object", "Confidence"]]

        # Preserve the annotation numbering and full object identifiers.
        for index, obj in enumerate(objects, start=1):
            rows.append([
                str(index),
                str(obj.id),
                str(obj.obj_class_id),
                obj.obj_name,
                f"{obj.confidence * 100:.2f}%",
            ])

        table = self._styled_report_table(rows, (10, 65, 20, 55, 26), width, (0, 2, 4))
        elements.append(table)

        return elements
