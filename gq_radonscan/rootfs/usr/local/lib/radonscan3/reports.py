from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import __version__
from .analysis import parse_dt
from .config import Settings
from .report_utils import peak_preserving_downsample
from .storage import Storage, StorageError, iso, utc_now

ORANGE = colors.HexColor("#F47B20")
DARK = colors.HexColor("#172033")
MUTED = colors.HexColor("#667085")
LIGHT = colors.HexColor("#F3F6FA")
GRID = colors.HexColor("#DDE3EA")
GREEN = colors.HexColor("#16835F")
WARNING = colors.HexColor("#C17600")
DANGER = colors.HexColor("#C83A3A")
BLUE = colors.HexColor("#1769AA")

TEXT = {
    "de": {
        "report": "Wissenschaftlicher Radon-Messbericht",
        "compact": "Radon-Kurzbericht",
        "measurement_site": "Messort",
        "period": "Messzeitraum",
        "created": "Erstellt",
        "summary": "Ergebnisübersicht",
        "last": "Letzter Wert im Zeitraum",
        "mean": "Mittelwert",
        "median": "Median",
        "maximum": "Maximum",
        "minimum": "Minimum",
        "coverage": "Datenabdeckung",
        "quality": "Datenqualität",
        "samples": "Messwerte",
        "stddev": "Standardabweichung",
        "p95": "95. Perzentil",
        "trend": "Trend pro Tag",
        "warning_hours": "Zeit über Warnschwelle",
        "danger_hours": "Zeit über Gefahrenschwelle",
        "time_series": "Zeitreihe",
        "distribution": "Messwertverteilung",
        "daily": "Tagesstatistik",
        "patterns": "Zeitmuster",
        "weekday": "Wochentagsprofil",
        "hourly": "Tageszeitprofil",
        "heatmap": "Wochen-Heatmap",
        "events": "Ereignisse und Maßnahmen",
        "traceability": "Messort, Gerät und Nachvollziehbarkeit",
        "method": "Methode und Einschränkungen",
        "method_text": "Ausgewertet wurden ausschließlich abgeschlossene, lokal gespeicherte Stundenwerte des GQ RadonScan. Die Zeitstempel der rückwirkend ausgelesenen Gerätehistorie werden aus dem erkannten Stundenindex rekonstruiert. Statistische Zusammenhänge beweisen keine Ursache-Wirkungs-Beziehung.",
        "disclaimer": "Orientierungshilfe; keine medizinische, behördliche oder fachliche Gebäudebewertung.",
        "insufficient": "Der ausgewählte Zeitraum ist wegen unzureichender Datenabdeckung nur eingeschränkt auswertbar.",
        "no_events": "Im Berichtszeitraum sind keine Ereignisse dokumentiert.",
        "source": "Datenquelle",
        "factor": "Umrechnungsfaktor",
        "device": "Gerät",
        "firmware": "Firmware",
        "serial": "Seriennummer",
        "app_version": "App-Version",
        "report_id": "Bericht-ID",
        "sha": "PDF-SHA-256",
        "data_sha": "Daten-SHA-256",
        "page": "Seite",
        "of": "von",
        "unit": "Bq/m³",
        "date": "Datum",
        "time": "Zeit",
        "type": "Typ",
        "title": "Titel",
        "notes": "Notizen",
        "building_floor": "Gebäude / Etage",
        "map": "Karte / Grundriss",
        "author": "Autor",
        "organisation": "Organisation",
        "quality_high": "Hoch",
        "quality_good": "Gut",
        "quality_limited": "Eingeschränkt",
        "quality_insufficient": "Nicht ausreichend",
        "chart_downsampled": "Die Zeitreihengrafik wurde für eine lesbare und schnelle PDF-Darstellung auf {points} repräsentative Punkte reduziert. Alle statistischen Berechnungen und Prüfsummen verwenden weiterhin sämtliche {samples} Messwerte.",
    },
    "en": {
        "report": "Scientific radon measurement report",
        "compact": "Radon summary report",
        "measurement_site": "Measurement site",
        "period": "Measurement period",
        "created": "Created",
        "summary": "Results overview",
        "last": "Latest value in period",
        "mean": "Mean",
        "median": "Median",
        "maximum": "Maximum",
        "minimum": "Minimum",
        "coverage": "Data coverage",
        "quality": "Data quality",
        "samples": "Measurements",
        "stddev": "Standard deviation",
        "p95": "95th percentile",
        "trend": "Trend per day",
        "warning_hours": "Time above warning threshold",
        "danger_hours": "Time above danger threshold",
        "time_series": "Time series",
        "distribution": "Measurement distribution",
        "daily": "Daily statistics",
        "patterns": "Temporal patterns",
        "weekday": "Weekday profile",
        "hourly": "Time-of-day profile",
        "heatmap": "Weekly heatmap",
        "events": "Events and interventions",
        "traceability": "Site, device and traceability",
        "method": "Method and limitations",
        "method_text": "The analysis uses only completed hourly values stored locally by the GQ RadonScan. Timestamps of retrospectively read device history are reconstructed from the detected hour index. Statistical associations do not prove cause and effect.",
        "disclaimer": "Guidance only; not medical, regulatory or professional building advice.",
        "insufficient": "The selected period has insufficient data coverage and can only be interpreted with caution.",
        "no_events": "No events were documented during the report period.",
        "source": "Data source",
        "factor": "Conversion factor",
        "device": "Device",
        "firmware": "Firmware",
        "serial": "Serial number",
        "app_version": "App version",
        "report_id": "Report ID",
        "sha": "PDF SHA-256",
        "data_sha": "Data SHA-256",
        "page": "Page",
        "of": "of",
        "unit": "Bq/m³",
        "date": "Date",
        "time": "Time",
        "type": "Type",
        "title": "Title",
        "notes": "Notes",
        "building_floor": "Building / floor",
        "map": "Map / floor plan",
        "author": "Author",
        "organisation": "Organisation",
        "quality_high": "High",
        "quality_good": "Good",
        "quality_limited": "Limited",
        "quality_insufficient": "Insufficient",
        "chart_downsampled": "For a readable and efficient PDF, the time-series chart was reduced to {points} representative points. All statistical calculations and checksums still use all {samples} measurements.",
    },
}


def _fmt(value: object, digits: int = 1) -> str:
    if value is None:
        return "–"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _paragraph_text(value: object) -> str:
    return xml_escape(str(value or "")).replace("\n", "<br/>")


def _dt(value: object, locale: str) -> str:
    parsed = parse_dt(value)
    if not parsed:
        return "–"
    return parsed.strftime("%d.%m.%Y %H:%M UTC") if locale == "de" else parsed.strftime("%Y-%m-%d %H:%M UTC")


def _status_color(mean: float | None, settings: Settings):
    if mean is None:
        return MUTED
    if mean >= settings.danger_threshold_bq_m3:
        return DANGER
    if mean >= settings.warning_threshold_bq_m3:
        return WARNING
    return GREEN


def _timeseries(records: list[dict[str, object]], settings: Settings, width: float = 170 * mm, height: float = 58 * mm) -> Drawing:
    drawing = Drawing(width, height)
    left, right, top, bottom = 12 * mm, 4 * mm, 5 * mm, 10 * mm
    plot_w, plot_h = width - left - right, height - top - bottom
    values = [float(row["bq_m3"]) for row in records if row.get("bq_m3") is not None]
    if len(values) < 2:
        drawing.add(String(width / 2, height / 2, "No data", textAnchor="middle", fillColor=MUTED))
        return drawing
    max_value = max(max(values) * 1.12, settings.warning_threshold_bq_m3 * 1.05, 10.0)
    for fraction in (0, .25, .5, .75, 1):
        y = bottom + plot_h * fraction
        drawing.add(Line(left, y, width - right, y, strokeColor=GRID, strokeWidth=.5))
        label = max_value * fraction
        drawing.add(String(1 * mm, y - 1.5 * mm, f"{label:.0f}", fontSize=7, fillColor=MUTED))
    for threshold, color in ((settings.warning_threshold_bq_m3, WARNING), (settings.danger_threshold_bq_m3, DANGER)):
        if threshold <= max_value:
            y = bottom + plot_h * threshold / max_value
            drawing.add(Line(left, y, width - right, y, strokeColor=color, strokeWidth=.8, strokeDashArray=[3, 2]))
    points = []
    for index, value in enumerate(values):
        x = left + plot_w * index / (len(values) - 1)
        y = bottom + plot_h * value / max_value
        points.extend((x, y))
    drawing.add(PolyLine(points, strokeColor=ORANGE, strokeWidth=1.4))
    drawing.add(String(left, 1.5 * mm, _dt(records[0].get("completed_at"), "en")[:10], fontSize=7, fillColor=MUTED))
    drawing.add(String(width - right, 1.5 * mm, _dt(records[-1].get("completed_at"), "en")[:10], fontSize=7, fillColor=MUTED, textAnchor="end"))
    return drawing


def _histogram(histogram: list[dict[str, object]], width: float = 170 * mm, height: float = 52 * mm) -> Drawing:
    drawing = Drawing(width, height)
    left, right, top, bottom = 12 * mm, 4 * mm, 4 * mm, 10 * mm
    plot_w, plot_h = width - left - right, height - top - bottom
    max_count = max((int(item["count"]) for item in histogram), default=1)
    if not histogram:
        drawing.add(String(width / 2, height / 2, "No data", textAnchor="middle", fillColor=MUTED))
        return drawing
    bar_w = plot_w / len(histogram)
    for index, item in enumerate(histogram):
        count = int(item["count"])
        h = plot_h * count / max_count if max_count else 0
        drawing.add(Rect(left + index * bar_w + 1, bottom, max(1, bar_w - 2), h, fillColor=BLUE, strokeColor=None))
        if index % max(1, len(histogram) // 6) == 0:
            drawing.add(String(left + index * bar_w, 2 * mm, f"{float(item['from']):.0f}", fontSize=7, fillColor=MUTED))
    drawing.add(Line(left, bottom, width - right, bottom, strokeColor=MUTED, strokeWidth=.6))
    return drawing


def _heatmap(cells: list[list[dict[str, object]]], settings: Settings, width: float = 170 * mm, height: float = 48 * mm) -> Drawing:
    drawing = Drawing(width, height)
    left, right, top, bottom = 12 * mm, 3 * mm, 3 * mm, 7 * mm
    cell_w = (width - left - right) / 24
    cell_h = (height - top - bottom) / 7
    for day in range(7):
        drawing.add(String(1 * mm, bottom + (6 - day) * cell_h + cell_h / 2 - 2, str(day + 1), fontSize=7, fillColor=MUTED))
        for hour in range(24):
            item = cells[day][hour]
            value = item.get("mean_bq_m3")
            samples = int(item.get("samples") or 0)
            if value is None or samples < 1:
                color = colors.HexColor("#E8ECF1")
            elif float(value) >= settings.danger_threshold_bq_m3:
                color = DANGER
            elif float(value) >= settings.warning_threshold_bq_m3:
                color = WARNING
            elif float(value) >= settings.warning_threshold_bq_m3 * .6:
                color = ORANGE
            else:
                color = GREEN
            drawing.add(Rect(left + hour * cell_w, bottom + (6 - day) * cell_h, cell_w - .4, cell_h - .4, fillColor=color, strokeColor=None))
    for hour in (0, 3, 6, 9, 12, 15, 18, 21):
        drawing.add(String(left + hour * cell_w, 1 * mm, f"{hour:02d}", fontSize=7, fillColor=MUTED))
    return drawing


class ScientificReport:
    def __init__(self, storage: Storage, settings: Settings) -> None:
        self.storage = storage
        self.settings = settings

    def create(self, payload: dict[str, object]) -> dict[str, object]:
        locale = str(payload.get("locale") or "de")
        locale = locale if locale in TEXT else "en"
        tx = TEXT[locale]
        profile = str(payload.get("profile") or "detailed")
        profile = profile if profile in {"compact", "detailed"} else "detailed"
        location_id = int(payload["location_id"]) if payload.get("location_id") not in (None, "") else None
        device_id = str(payload.get("device_id") or "").strip() or None
        if device_id is None:
            latest_device = self.storage.device()
            device_id = str(latest_device.get("device_id")) if latest_device else None
        if device_id is None or self.storage.device(device_id) is None:
            raise StorageError("A valid measurement device is required for a scientific report")
        days = int(payload.get("days") or 30)
        start = str(payload.get("start") or "") or None
        end = str(payload.get("end") or "") or None
        analysis = self.storage.analysis(
            start=start,
            end=end,
            days=days,
            location_id=location_id,
            device_id=device_id,
            warning_threshold=self.settings.warning_threshold_bq_m3,
            danger_threshold=self.settings.danger_threshold_bq_m3,
            minimum_coverage_percent=self.settings.minimum_data_coverage_percent,
            timezone_name=(self.settings.analysis_timezone if self.settings.analysis_timezone != "auto" else "UTC"),
        )
        stats = analysis["statistics"]
        digest_records = [
            {
                "completed_at": row.get("completed_at"),
                "device_id": row.get("device_id"),
                "campaign_id": row.get("campaign_id"),
                "hour_index": row.get("hour_index"),
                "raw_cph": row.get("raw_cph"),
                "bq_m3": row.get("bq_m3"),
                "factor": row.get("factor"),
                "location_id": row.get("location_id"),
                "session_id": row.get("session_id"),
            }
            for row in analysis.get("records", [])
        ]
        data_digest = hashlib.sha256(
            json.dumps(digest_records, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        location = self.storage.location(location_id) if location_id else None
        device = self.storage.device(device_id) or {}
        report_id = "RM-" + utc_now().strftime("%Y%m%d-%H%M%S-%f")[:20]
        title = str(payload.get("title") or (tx["compact"] if profile == "compact" else tx["report"]))
        filename = f"radon-monitoring-{report_id.lower()}.pdf"
        path = self.storage.reports_dir / filename
        created_at = iso(utc_now())

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="RMTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=DARK, spaceAfter=7 * mm))
        styles.add(ParagraphStyle(name="RMH1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=DARK, spaceBefore=4 * mm, spaceAfter=3 * mm))
        styles.add(ParagraphStyle(name="RMH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=DARK, spaceBefore=3 * mm, spaceAfter=2 * mm))
        styles.add(ParagraphStyle(name="RMBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=DARK))
        styles.add(ParagraphStyle(name="RMSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED))
        styles.add(ParagraphStyle(name="RMNotice", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=DANGER, borderColor=DANGER, borderWidth=.6, borderPadding=6, backColor=colors.HexColor("#FFF5F5")))

        def footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(GRID)
            canvas.line(20 * mm, 13 * mm, 190 * mm, 13 * mm)
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(MUTED)
            canvas.drawString(20 * mm, 8 * mm, f"Radon Monitoring {__version__} · {report_id}")
            canvas.drawRightString(190 * mm, 8 * mm, f"{tx['page']} {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=title,
            author=self.settings.report_author or "Radon Monitoring",
            subject=tx["report"],
        )
        story: list[Any] = []
        story.append(Table([[Paragraph("Radon Monitoring", styles["RMH2"]), Paragraph(f"v{__version__}", styles["RMSmall"])]], colWidths=[140 * mm, 30 * mm], style=TableStyle([("BACKGROUND", (0,0), (-1,-1), LIGHT), ("BOX", (0,0), (-1,-1), .6, GRID), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)])))
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(_paragraph_text(title), styles["RMTitle"]))
        site_name = (location or {}).get("name") or "–"
        metadata_rows = [
            [tx["measurement_site"], site_name],
            [tx["period"], f"{_dt(stats.get('period_start'), locale)} – {_dt(stats.get('period_end'), locale)}"],
            [tx["created"], _dt(created_at, locale)],
            [tx["report_id"], report_id],
            [tx["data_sha"], Paragraph(data_digest, styles["RMSmall"])],
        ]
        story.append(Table(metadata_rows, colWidths=[43 * mm, 127 * mm], style=TableStyle([("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (1,0), (1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 9), ("TEXTCOLOR", (0,0), (0,-1), MUTED), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LINEBELOW", (0,0), (-1,-1), .4, GRID), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)])))
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph(tx["disclaimer"], styles["RMNotice"]))
        if not stats.get("sufficient"):
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(tx["insufficient"], styles["RMNotice"]))

        story.append(Paragraph(tx["summary"], styles["RMH1"]))
        summary_data = [
            [tx["last"], tx["mean"], tx["maximum"], tx["coverage"]],
            [
                f"{_fmt(stats.get('last_bq_m3'))} {tx['unit']}",
                f"{_fmt(stats.get('mean_bq_m3'))} {tx['unit']}",
                f"{_fmt(stats.get('maximum_bq_m3'))} {tx['unit']}",
                f"{_fmt(stats.get('coverage_percent'), 0)} %",
            ],
        ]
        summary_table = Table(summary_data, colWidths=[42.5 * mm] * 4)
        summary_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), LIGHT), ("TEXTCOLOR", (0,0), (-1,0), MUTED), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,1), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,0), 8), ("FONTSIZE", (0,1), (-1,1), 12), ("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("BOX", (0,0), (-1,-1), .6, GRID), ("INNERGRID", (0,0), (-1,-1), .4, GRID), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7), ("TEXTCOLOR", (1,1), (1,1), _status_color(stats.get("mean_bq_m3"), self.settings))]))
        story.append(summary_table)
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(tx["time_series"], styles["RMH2"]))
        plot_records = peak_preserving_downsample(analysis["records"], 1800)
        story.append(_timeseries(plot_records, self.settings))
        if len(plot_records) < len(analysis["records"]):
            story.append(Spacer(1, 1.5 * mm))
            story.append(Paragraph(
                tx["chart_downsampled"].format(points=len(plot_records), samples=len(analysis["records"])),
                styles["RMSmall"],
            ))

        details = [
            [tx["samples"], str(stats.get("samples") or 0), tx["quality"], tx.get(f"quality_{stats.get('quality')}", str(stats.get("quality") or "–"))],
            [tx["minimum"], f"{_fmt(stats.get('minimum_bq_m3'))} {tx['unit']}", tx["maximum"], f"{_fmt(stats.get('maximum_bq_m3'))} {tx['unit']}"],
            [tx["median"], f"{_fmt(stats.get('median_bq_m3'))} {tx['unit']}", tx["stddev"], f"{_fmt(stats.get('standard_deviation_bq_m3'))} {tx['unit']}"],
            [tx["p95"], f"{_fmt(stats.get('p95_bq_m3'))} {tx['unit']}", tx["trend"], f"{_fmt(stats.get('slope_bq_m3_per_day'), 2)} {tx['unit']}/d"],
            [tx["warning_hours"], f"{analysis['thresholds']['warning']['hours']} h ({_fmt(analysis['thresholds']['warning']['percent'], 1)} %)", tx["danger_hours"], f"{analysis['thresholds']['danger']['hours']} h ({_fmt(analysis['thresholds']['danger']['percent'], 1)} %)"]
        ]
        story.append(Table(details, colWidths=[39 * mm, 46 * mm, 39 * mm, 46 * mm], style=TableStyle([("FONTNAME", (0,0), (-1,-1), "Helvetica"), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 8), ("TEXTCOLOR", (0,0), (-1,-1), DARK), ("BACKGROUND", (0,0), (0,-1), LIGHT), ("BACKGROUND", (2,0), (2,-1), LIGHT), ("GRID", (0,0), (-1,-1), .4, GRID), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)])))

        if profile == "detailed":
            story.append(PageBreak())
            story.append(Paragraph(tx["distribution"], styles["RMH1"]))
            story.append(_histogram(analysis["histogram"]))
            story.append(Paragraph(tx["daily"], styles["RMH2"]))
            daily_rows = [[tx["date"], tx["samples"], tx["coverage"], tx["minimum"], tx["median"], tx["maximum"], tx["mean"]]]
            for item in analysis["daily"][-31:]:
                daily_rows.append([
                    item["date"], item["samples"], f"{_fmt(item['coverage_percent'],0)} %",
                    _fmt(item["minimum_bq_m3"]), _fmt(item["median_bq_m3"]), _fmt(item["maximum_bq_m3"]), _fmt(item["mean_bq_m3"]),
                ])
            story.append(Table(daily_rows, repeatRows=1, colWidths=[25 * mm, 18 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm], style=TableStyle([("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 7), ("GRID", (0,0), (-1,-1), .35, GRID), ("ALIGN", (1,1), (-1,-1), "RIGHT"), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]), ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)])))

            story.append(PageBreak())
            story.append(Paragraph(tx["patterns"], styles["RMH1"]))
            story.append(Paragraph(tx["heatmap"], styles["RMH2"]))
            story.append(_heatmap(analysis["weekly_heatmap"], self.settings))
            profile_rows = [[tx["weekday"], f"{tx['mean']} Bq/m³", tx["samples"]]]
            weekday_names_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
            weekday_names_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            names = weekday_names_de if locale == "de" else weekday_names_en
            for item in analysis["weekday_profile"]:
                profile_rows.append([names[int(item["weekday"])], _fmt(item["mean_bq_m3"]), item["samples"]])
            story.append(Table(profile_rows, colWidths=[70 * mm, 50 * mm, 50 * mm], style=TableStyle([("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 8), ("GRID", (0,0), (-1,-1), .4, GRID), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]), ("ALIGN", (1,1), (-1,-1), "RIGHT"), ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)])))

            story.append(Paragraph(tx["events"], styles["RMH1"]))
            if analysis["events"]:
                event_rows = [[tx["time"], tx["type"], tx["title"], tx["notes"]]]
                for event in analysis["events"]:
                    event_rows.append([_dt(event.get("occurred_at"), locale), event.get("event_type"), event.get("title"), event.get("notes") or ""])
                story.append(Table(event_rows, repeatRows=1, colWidths=[38 * mm, 28 * mm, 45 * mm, 59 * mm], style=TableStyle([("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 7), ("GRID", (0,0), (-1,-1), .35, GRID), ("VALIGN", (0,0), (-1,-1), "TOP"), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT])])))
            else:
                story.append(Paragraph(tx["no_events"], styles["RMBody"]))

        story.append(PageBreak())
        story.append(Paragraph(tx["traceability"], styles["RMH1"]))
        trace = [
            [tx["measurement_site"], site_name],
            [tx["building_floor"], f"{(location or {}).get('building') or '–'} / {(location or {}).get('floor') or '–'}"],
            [tx["device"], device.get("model") or "GQ RadonScan"],
            [tx["firmware"], device.get("firmware") or "–"],
            [tx["serial"], device.get("serial_number") or "–"],
            [tx["source"], "Read-only SPIR hourly history → SQLite"],
            [tx["factor"], f"{self.settings.factor_bq_m3_per_cph:.6f} Bq/m³ per count/h"],
            [tx["app_version"], __version__],
            [tx["author"], self.settings.report_author or "–"],
            [tx["organisation"], self.settings.report_organisation or "–"],
            [tx["report_id"], report_id],
        ]
        story.append(Table(trace, colWidths=[45 * mm, 125 * mm], style=TableStyle([("BACKGROUND", (0,0), (0,-1), LIGHT), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (1,0), (1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 8.5), ("GRID", (0,0), (-1,-1), .4, GRID), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)])))

        if location and location.get("map_filename"):
            map_path = self.storage.maps_dir / str(location["map_filename"])
            if map_path.is_file():
                story.append(Paragraph(tx["map"], styles["RMH2"]))
                try:
                    image = Image(str(map_path))
                    image._restrictSize(165 * mm, 85 * mm)
                    story.append(image)
                except Exception:
                    pass

        story.append(Paragraph(tx["method"], styles["RMH1"]))
        story.append(Paragraph(tx["method_text"], styles["RMBody"]))
        custom_disclaimer = self.settings.report_disclaimer.strip()
        if custom_disclaimer:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(_paragraph_text(custom_disclaimer), styles["RMBody"]))

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        metadata = {
            "report_id": report_id,
            "profile": profile,
            "locale": locale,
            "title": title,
            "period_start": stats.get("period_start"),
            "period_end": stats.get("period_end"),
            "location_id": location_id,
            "location_name": site_name,
            "device_id": device_id,
            "device_model": device.get("model"),
            "device_serial_number": device.get("serial_number"),
            "filename": filename,
            "sha256": digest,
            "data_sha256": data_digest,
            "created_at": created_at,
            "samples": stats.get("samples"),
            "coverage_percent": stats.get("coverage_percent"),
            "mean_bq_m3": stats.get("mean_bq_m3"),
            "minimum_bq_m3": stats.get("minimum_bq_m3"),
            "maximum_bq_m3": stats.get("maximum_bq_m3"),
            "app_version": __version__,
            "analysis_model": "5.2.0",
            "chart_points": len(plot_records),
            "chart_downsampled": len(plot_records) < len(analysis["records"]),
            "scientific_quality_class": stats.get("scientific_quality_class"),
            "quality_reasons": stats.get("quality_reasons"),
            "uncertainty": analysis.get("uncertainty"),
            "quality_control": analysis.get("quality_control"),
            "change_point": analysis.get("change_point"),
            "methodology": analysis.get("methodology"),
            "report_author": self.settings.report_author,
            "report_organisation": self.settings.report_organisation,
        }
        return self.storage.add_report(metadata)
