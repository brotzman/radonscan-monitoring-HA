from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

VERSION = "5.1.0"
ORANGE = colors.HexColor("#F47B20")
DARK = colors.HexColor("#172033")
MUTED = colors.HexColor("#667085")
LIGHT = colors.HexColor("#F4F6F9")
BORDER = colors.HexColor("#D9DEE7")
GREEN = colors.HexColor("#167A5A")

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "rootfs/usr/local/share/radonscan3/docs"
ICON = ROOT / "icon.png"

CONTENT = {
"de": {
"title": "Radon Monitoring",
"subtitle": "Benutzerhandbuch",
"tagline": "Lokale Überwachung für GQ RadonScan Geräte",
"date": "Stand 26.07.2026",
"contents": "Inhalt",
"sections": [
("1. Zweck, Messprinzip und Grenzen", [
"Radon Monitoring liest abgeschlossene Stundenwerte kompatibler GQ RadonScan Geräte ausschließlich mit lesenden SPIR-Befehlen aus. Die App speichert Rohzählwerte (CPH), den jeweils verwendeten Umrechnungsfaktor und die daraus berechnete Aktivitätskonzentration lokal in SQLite.",
"Die App dient der kontinuierlichen Beobachtung, statistischen Auswertung und nachvollziehbaren Dokumentation. Sie ersetzt keine rückführbare Kalibrierung, keine behördlich anerkannte Messung und keine medizinische, bauliche oder rechtliche Fachberatung.",
"Ein hoher einzelner Stundenwert ist nicht automatisch eine Überschreitung eines Jahresreferenzwerts. Oberfläche und Berichte trennen aktuellen Wert, Zeitraumstatistik, Zählunsicherheit, Kalibrierinformation und fachliche Einordnung."
]),
("2. Installation, Upgrade und erster Start", [
"Verbinden Sie das RadonScan Gerät per USB, stellen Sie MQTT für Home Assistant bereit und starten Sie die App. Für die automatische Erkennung kann serial_port leer beziehungsweise auf auto bleiben. Für eine feste Zuordnung ist ein Pfad unter /dev/serial/by-id/ vorzuziehen.",
"Vor Upgrades und destruktiven Aktionen sollte ein Home-Assistant-Backup erstellt werden. Nach dem Upgrade muss in Seitenleiste oder Hilfe Version 5.1.0 erscheinen. Bleibt eine alte Ingress-Ansicht geöffnet, schließen Sie das Panel und öffnen Sie es erneut.",
"Nur abgeschlossene Stunden werden übernommen. Nach dem ersten Anschließen kann deshalb zunächst noch kein aktueller Messwert verfügbar sein."
]),
("3. Übersicht", [
"Die Übersicht zeigt den letzten abgeschlossenen Stundenwert, Datenalter, Rohwert, Messort, gespeicherte Stunden, Geräteverbindung und MQTT-Status. Zusätzlich werden 24-Stunden-, 7-Tage- und 30-Tage-Kennwerte angezeigt.",
"Ein Zeitraumwert erscheint erst, wenn die geforderte Messdauer und Mindestabdeckung erreicht sind. Andernfalls steht in der Kachel eine konkrete Begründung wie Zeitraum noch nicht vollständig oder Datenabdeckung zu gering.",
"Der Home-Assistant-Standort zeigt den in den allgemeinen Home-Assistant-Einstellungen hinterlegten Standortnamen oder eine dort bereitgestellte Adresse sowie Koordinaten, Höhe, Land und Zeitzone. Radon Monitoring führt keine externe Rückwärts-Geokodierung durch und sendet die Standortdaten nicht an einen Geokodierungsdienst. Die Radonampel ordnet den aktuellen Stundenwert anhand der konfigurierten Warn- und Gefahrenschwellen als grün, gelb oder rot ein.",
"Der Aktualisieren-Schalter lädt zuerst den kompakten Systemzustand. Verlauf, Katalog und Analyse folgen getrennt, damit neue USB-Daten nicht durch langsamere Abfragen verdeckt werden."
]),
("4. Analyse und Statistik", [
"Die Grundauswertung enthält Mittelwert, Median, Minimum, Maximum, Quantile, Datenabdeckung, Qualitätsklasse, Schwellenzeiten und robuste Streuungsmaße. Die erweiterte Statistik ergänzt effektive Stichprobengröße, Moving-Block-Bootstrap-Konfidenzintervalle, Mann-Kendall-Diagnostik, Sen-Steigung, Autokorrelation, Verteilungskennwerte, gleitenden Median, Interquartilsband und zusammenhängende Schwellenereignisse.",
"Fehlende Messwerte werden nicht imputiert. Auffällige Werte werden nicht automatisch gelöscht. Qualitätsflags kennzeichnen unter anderem nicht dokumentierte Faktoren, nicht primäre Datenquellen, unplausible Werte und doppelte Zeitstempel.",
"Die Strukturbruchanalyse ist explorativ. Bei sehr langen Reihen wird ausschließlich diese Diagnose auf eine gleichmäßig verteilte, zeitlich geordnete Stichprobe begrenzt. Deskriptive Kennwerte, Schwellenberechnungen und Datenprüfsummen verwenden weiterhin alle ausgewählten Datensätze.",
"Eine statistische Signifikanz beweist weder eine Ursache noch eine praktisch relevante Wirkung. Ereignisse und Maßnahmen müssen zusätzlich fachlich interpretiert werden."
]),
("5. Geräte & System, Faktor und Kalibrierung", [
"Die frühere Expertenansicht wurde in Version 5.1.0 vollständig aus Oberfläche und Seitenleiste entfernt. Geräte-, Protokoll-, Dienst- und Datenbankstatus finden Sie gebündelt unter Geräte & System; konfigurierbare Schwellen und weitere Betriebsparameter stehen unter Einstellungen.",
"Der aktuell konfigurierte Faktor wird getrennt vom Faktor des ausgewählten historischen Messwerts dargestellt. Dadurch bleiben ältere Werte reproduzierbar, auch wenn die Konfiguration später geändert wird.",
"Kalibrierungen können mit Datum, Labor, Zertifikatsreferenz, Faktor, Unsicherheit, Folgetermin und Notizen dokumentiert werden. Ein Eintrag verändert vorhandene Messwerte nicht automatisch."
]),
("6. Messorte, Sitzungen und Ereignisse", [
"Messorte, Messsitzungen und Ereignisse sind lokale Metadaten. Sie dokumentieren Gebäude, Raum, Aufstellung, Messhöhe, Lüftung, Maßnahmen, Gerätewechsel oder Ausfälle, ohne die Originalmesswerte zu verändern.",
"Für wissenschaftliche Vergleiche sollten Beginn, Ende, Fragestellung und relevante Randbedingungen einer Kampagne vollständig eingetragen werden."
]),
("7. GQ Radiation World Map", [
"Der Upload ist optional und standardmäßig deaktiviert. Account-ID und Geräte-ID werden in den App-Optionen hinterlegt. Die Oberfläche zeigt diese Kennungen nur maskiert.",
"Eine persistente Warteschlange verhindert Doppelübertragungen, wiederholt temporäre Fehler mit zunehmendem Abstand und kann zu alte Werte nach einer konfigurierbaren Grenze verwerfen. Der manuelle Upload ist eine geschützte POST-Aktion.",
"Die öffentliche Position wird im GQ-Konto verwaltet. Radon Monitoring übermittelt keine eigenen GPS-Koordinaten."
]),
("8. Wissenschaftliche PDF-Berichte", [
"Kompakte und detaillierte Berichte enthalten Zeitraum, Messort, Gerät, Faktor, Datenabdeckung, Kennwerte, Zeitreihe, Methodik, Qualitätsinformationen, Softwareversion und SHA-256-Prüfsummen.",
"Bei mehrjährigen Reihen wird nur die Zeitreihengrafik auf eine begrenzte, spitzenerhaltende Punktzahl reduziert. Statistische Kennwerte, Schwellenereignisse und Datenprüfsumme beruhen weiterhin auf allen ausgewählten Messwerten.",
"Berichte sind Dokumentationshilfen und keine amtlichen Zertifikate."
]),
("9. Datenverwaltung und Sicherheit", [
"Die Datenverwaltung kann mit data_management_enabled vollständig aus Navigation und API ausgeblendet werden.",
"Der vollständige lokale Reset erstellt automatisch eine Sicherheitskopie, löscht App-Daten transaktional, prüft anschließend die SQLite-Integrität und zeigt Vorgangs-ID, gelöschte Datensätze, Dateianzahl, Größen und Dauer an. Die App unterdrückt danach den sofortigen erneuten Import der zuvor gelöschten Gerätehistorie.",
"Der Home-Assistant-Recorder-Purge übermittelt erkannte RadonScan-Entitäten und stabile Namensmuster an recorder.purge_entities. Ein langlebiger Administrator-Token ist optional erforderlich. Er wird nicht angezeigt, nicht in Diagnoseexporte übernommen und zentral aus Fehlermeldungen entfernt.",
"Die Verifikation prüft anschließend den jüngeren Home-Assistant-Verlauf. Sie bestätigt nicht die sofortige physische Komprimierung jeder Recorder-Datenbank und erfasst nicht automatisch separat gespeicherte Langzeitstatistiken."
]),
("10. Bedienung, Mobilansicht und Barrierefreiheit", [
"Die Seitenleiste wird auf kleinen Bildschirmen als Menü eingeblendet. Tabellen und Wochen-Heatmap bleiben innerhalb ihrer Kachel horizontal scrollbar; die restliche Seite darf keinen horizontalen Überstand erzeugen.",
"Die Oberfläche unterstützt Tastaturbedienung, sichtbare Fokusmarkierungen, einen Sprunglink zum Hauptinhalt, Escape zum Schließen des Menüs, reduzierte Animationen und Schriftvergrößerung bis 200 Prozent.",
"Version 5.1.0 wurde in Chromium bei 320, 390, 768 und 1440 Pixeln, in allen acht Sprachen und mit langen Testbezeichnungen geprüft."
]),
("11. Fehlerbehebung", [
"Kein Gerät: USB-Zuordnung, Berechtigungen, konfigurierten Port und konkurrierende Prozesse prüfen.",
"Keine neuen Werte: Nur abgeschlossene Stunden werden importiert. Aktualisieren betätigen und den Zeitpunkt des letzten Scans unter Geräte & System prüfen.",
"Alte Oberfläche: App neu starten, Ingress-Panel schließen und neu öffnen.",
"Recorder-Purge schlägt fehl: Administrator-Token, Recorder-Integration und Home-Assistant-Administratorrechte prüfen.",
"Verifikation zeigt verbleibende Daten: Warten und erneut prüfen; Recorder-Arbeiten können asynchron laufen. Langzeitstatistiken sind separat zu behandeln.",
"Wiederherstellung abgelehnt: Nur lesbare SQLite-Sicherungen mit kompatiblem Schema werden übernommen. Die aktive Datenbank bleibt bei Fehlern unverändert."
]),
("12. Datenschutz und verantwortungsvolle Nutzung", [
"Messwerte und Metadaten bleiben standardmäßig lokal. Nur aktivierte externe Funktionen übertragen Daten. Die Standortkachel liest ihre Angaben ausschließlich über die lokale Home-Assistant-Core-API und verwendet keinen externen Geokodierungsdienst. Prüfen Sie vor World-Map-Uploads, ob Veröffentlichung und Standortangaben Ihren Datenschutzanforderungen entsprechen.",
"Bewahren Sie Backups und Berichte geschützt auf. Sie können Gerätekennungen, Messorte, Zeiträume und Gebäudedaten enthalten."
]),
("13. Neu in Version 5.1.0", [
"Die Übersicht enthält jetzt eine responsive Kachel für den Home-Assistant-Standort und eine Radonampel, die den aktuellen Stundenwert anhand der konfigurierten Schwellen einordnet. Die frühere Expertenansicht wurde vollständig aus Oberfläche und Seitenleiste entfernt, weil die benötigten Betriebsdaten bereits unter Geräte & System und Einstellungen verfügbar sind. Es findet keine externe Geokodierung statt. Versionsangaben, Tests sowie das deutsche und englische Benutzerhandbuch wurden auf Version 5.1.0 aktualisiert."
])
],
"options": [
("serial_port", "Automatische Erkennung oder stabiler USB-Pfad"),
("factor_bq_m3_per_cph", "Aktuell verwendeter Umrechnungsfaktor"),
("minimum_data_coverage_percent", "Mindestabdeckung für Zeitfenster und Qualitätsstatus"),
("analysis_timezone", "Zeitzone für Tages- und Wochenprofile"),
("data_management_enabled", "Datenverwaltung in Navigation und API aktivieren"),
("homeassistant_access_token", "Optionaler Administrator-Token für Recorder-Aktionen"),
("gmcmap_enabled", "GQ Radiation World Map aktivieren"),
("gmcmap_auto_upload", "Automatische Upload-Warteschlange aktivieren")
]
},
"en": {
"title": "Radon Monitoring",
"subtitle": "User manual",
"tagline": "Local monitoring for GQ RadonScan devices",
"date": "Updated 26 July 2026",
"contents": "Contents",
"sections": [
("1. Purpose, measurement principle and limitations", [
"Radon Monitoring reads completed hourly records from compatible GQ RadonScan devices using read-only SPIR commands. It stores raw counts (CPH), the conversion factor used for each record and the calculated activity concentration locally in SQLite.",
"The app supports continuous observation, statistical analysis and traceable documentation. It does not replace traceable calibration, a recognised regulatory measurement or professional medical, building or legal advice.",
"A high individual hourly value is not automatically an exceedance of an annual reference value. The interface and reports distinguish the current value, period statistics, counting uncertainty, calibration information and professional interpretation."
]),
("2. Installation, upgrade and first start", [
"Connect the RadonScan by USB, make MQTT available to Home Assistant and start the app. Leave serial_port empty or set to auto for discovery. For a stable fixed assignment, prefer a path under /dev/serial/by-id/.",
"Create a Home Assistant backup before upgrades and destructive actions. After upgrading, the sidebar or Help view must show version 5.1.0. If an old Ingress view remains open, close the panel and reopen it.",
"Only completed hours are imported. A newly connected device can therefore remain without a current value until a complete record is available."
]),
("3. Overview", [
"Overview shows the latest completed hourly value, data age, raw value, measurement site, stored hours, device connection and MQTT state. It also shows 24-hour, 7-day and 30-day summaries.",
"A period result is displayed only after the required duration and minimum coverage have been reached. Otherwise the card explains why the value is not yet meaningful.",
"The Home Assistant location card shows the location name or an address supplied in the general Home Assistant settings together with coordinates, elevation, country and time zone. Radon Monitoring performs no external reverse geocoding and does not send the location data to a geocoding service. The Radon traffic light classifies the current hourly value as green, amber or red using the configured warning and danger thresholds.",
"Refresh loads the compact system state first. History, catalogue and analysis follow separately so that slower requests do not hide newly imported USB data."
]),
("4. Analysis and statistics", [
"Basic analysis includes mean, median, minimum, maximum, quantiles, coverage, quality class, threshold time and robust dispersion measures. Advanced analysis adds effective sample size, moving-block-bootstrap confidence intervals, Mann-Kendall diagnostics, Sen slope, autocorrelation, distribution diagnostics, rolling median, interquartile band and continuous threshold events.",
"Missing measurements are not imputed. Unusual observations are not deleted automatically. Quality flags identify undocumented factors, non-primary sources, implausible values and duplicate timestamps.",
"Change-point analysis is exploratory. For very long series, only this diagnostic is bounded to an evenly distributed, time-ordered sample. Descriptive statistics, threshold calculations and data checksums continue to use every selected record.",
"Statistical significance proves neither causality nor practical importance. Events and interventions still require professional interpretation."
]),
("5. Devices & System, factor and calibration", [
"The former Expert view was removed completely from the interface and sidebar in version 5.1.0. Device, protocol, service and database status is grouped under Devices & System; configured thresholds and other operating parameters are shown under Settings.",
"The currently configured factor is displayed separately from the factor stored with the selected historical measurement. Historical results therefore remain reproducible after later configuration changes.",
"Calibration records can include date, laboratory, certificate reference, factor, uncertainty, next due date and notes. A calibration entry does not silently alter existing measurements."
]),
("6. Sites, sessions and events", [
"Measurement sites, sessions and events are local metadata. They document building, room, placement, height, ventilation, interventions, device changes and outages without changing original measurements.",
"For scientific comparisons, record the campaign question, start, end and relevant environmental conditions."
]),
("7. GQ Radiation World Map", [
"Upload is optional and disabled by default. Account ID and device ID are stored in app options and shown only in masked form in the interface.",
"A persistent queue prevents duplicates, retries temporary failures with increasing delay and can discard measurements older than a configured limit. Manual upload is a protected POST action.",
"The public position is managed in the GQ account. Radon Monitoring does not transmit its own GPS coordinates."
]),
("8. Scientific PDF reports", [
"Compact and detailed reports contain period, site, device, factor, coverage, statistics, time series, method, quality information, software version and SHA-256 checksums.",
"For multi-year series, only the time-series chart is reduced to a bounded peak-preserving point set. Statistics, threshold events and the data checksum continue to use all selected measurements.",
"Reports are documentation aids, not official certificates."
]),
("9. Data management and security", [
"The complete Data management area can be hidden from navigation and blocked at the API using data_management_enabled.",
"Complete local reset automatically creates a safety backup, clears app data transactionally, verifies SQLite integrity and reports operation ID, deleted records, removed files, sizes and duration. Immediate re-import of the deleted device history is suppressed.",
"Home Assistant Recorder purge submits recognised RadonScan entities and stable name patterns to recorder.purge_entities. An optional long-lived administrator token may be required. It is never displayed, excluded from diagnostics and centrally redacted from error messages.",
"Verification subsequently checks recent Home Assistant history. It does not prove immediate physical compaction of every Recorder backend and does not automatically cover separately retained long-term statistics."
]),
("10. Operation, mobile layout and accessibility", [
"On small screens the sidebar opens as a menu. Tables and the weekly heatmap remain horizontally scrollable inside their own cards; the rest of the page must not create horizontal page overflow.",
"The interface supports keyboard operation, visible focus, a skip link, Escape to close the menu, reduced motion and text scaling to 200 percent.",
"Version 5.1.0 was checked in Chromium at 320, 390, 768 and 1440 pixels, in all eight languages and with deliberately long labels."
]),
("11. Troubleshooting", [
"No device: check USB mapping, permissions, configured port and competing processes.",
"No new values: only completed hours are imported. Press Refresh and inspect the latest scan time under Devices & System.",
"Old interface: restart the app, close the Ingress panel and reopen it.",
"Recorder purge fails: check administrator token, Recorder integration and Home Assistant administrator rights.",
"Verification reports remaining data: wait and verify again; Recorder maintenance can be asynchronous. Treat long-term statistics separately.",
"Restore rejected: only readable SQLite backups with a compatible schema are accepted. The active database remains unchanged after validation failure."
]),
("12. Privacy and responsible use", [
"Measurements and metadata remain local by default. Only enabled external functions transmit data. The location card reads its values only through the local Home Assistant Core API and uses no external geocoding service. Before World Map publication, confirm that location and publication settings meet your privacy requirements.",
"Protect backups and reports because they may contain device identifiers, sites, periods and building information."
]),
("13. New in version 5.1.0", [
"Overview now contains a responsive Home Assistant location card and a Radon traffic light that classifies the current hourly value using the configured thresholds. The former Expert view was removed completely from the interface and sidebar because the required operating information is already available under Devices & System and Settings. No external geocoding is performed. Version metadata, tests and the German and English user manuals were updated to version 5.1.0."
])
],
"options": [
("serial_port", "Automatic discovery or stable USB path"),
("factor_bq_m3_per_cph", "Currently configured conversion factor"),
("minimum_data_coverage_percent", "Minimum coverage for period results and quality"),
("analysis_timezone", "Time zone for daily and weekly profiles"),
("data_management_enabled", "Enable Data management navigation and API"),
("homeassistant_access_token", "Optional administrator token for Recorder actions"),
("gmcmap_enabled", "Enable GQ Radiation World Map"),
("gmcmap_auto_upload", "Enable the automatic upload queue")
]
}
}


def build(lang: str) -> Path:
    tx = CONTENT[lang]
    out = DOCS / f"Radon_Monitoring_User_Manual_{VERSION}_{lang}.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=32, textColor=DARK, alignment=TA_CENTER, spaceAfter=5*mm))
    styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=16, leading=21, textColor=ORANGE, alignment=TA_CENTER, spaceAfter=4*mm))
    styles.add(ParagraphStyle(name="CoverTag", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=15, textColor=MUTED, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="H1RM", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=DARK, spaceBefore=4*mm, spaceAfter=2.5*mm, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyRM", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13.2, textColor=DARK, spaceAfter=2.4*mm))
    styles.add(ParagraphStyle(name="SmallRM", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.5, textColor=MUTED))
    styles.add(ParagraphStyle(name="TOC", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.3, leading=13, textColor=DARK, leftIndent=4*mm, spaceAfter=1.1*mm))
    styles.add(ParagraphStyle(name="Notice", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.7, leading=12, textColor=DARK, backColor=LIGHT, borderColor=ORANGE, borderWidth=.8, borderPadding=7, spaceBefore=2*mm, spaceAfter=4*mm))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(18*mm, 13*mm, 192*mm, 13*mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(18*mm, 8.5*mm, f"Radon Monitoring {VERSION}")
        canvas.drawRightString(192*mm, 8.5*mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm, title=f"Radon Monitoring {VERSION} - {tx['subtitle']}", author="Radon Monitoring")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))

    story=[]
    story.append(Spacer(1, 24*mm))
    if ICON.exists():
        img=Image(str(ICON), width=30*mm, height=30*mm)
        img.hAlign="CENTER"
        story.append(img)
        story.append(Spacer(1, 8*mm))
    story.append(Paragraph(tx["title"], styles["CoverTitle"]))
    story.append(Paragraph(tx["subtitle"], styles["CoverSub"]))
    story.append(Paragraph(tx["tagline"], styles["CoverTag"]))
    story.append(Spacer(1, 20*mm))
    cover=Table([
        ["Version", VERSION],
        [tx["date"].split(" ",1)[0] if lang=="de" else "Date", tx["date"].split(" ",1)[1] if " " in tx["date"] else tx["date"]],
        ["Home Assistant", "Local app / Ingress"],
        ["Data", "Local SQLite + optional external upload" if lang=="en" else "Lokales SQLite + optionaler externer Upload"],
    ], colWidths=[45*mm, 95*mm], hAlign="CENTER")
    cover.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),LIGHT),("TEXTCOLOR",(0,0),(0,-1),MUTED),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTNAME",(1,0),(1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),9),("BOX",(0,0),(-1,-1),.6,BORDER),
        ("INNERGRID",(0,0),(-1,-1),.3,BORDER),("TOPPADDING",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),("LEFTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(cover)
    story.append(PageBreak())

    story.append(Paragraph(tx["contents"], styles["H1RM"]))
    for title,_ in tx["sections"]:
        story.append(Paragraph(title, styles["TOC"]))
    story.append(Spacer(1, 5*mm))
    notice = "Wichtiger Hinweis: Diese App ist ein Monitoring- und Dokumentationswerkzeug, kein amtliches Messsystem." if lang=="de" else "Important: this app is a monitoring and documentation tool, not an official measurement system."
    story.append(Paragraph(notice, styles["Notice"]))
    story.append(PageBreak())

    # Group sections into balanced pages.
    breaks_after={2,4,6,8,10,12}
    for idx,(title, paragraphs) in enumerate(tx["sections"], start=1):
        block=[Paragraph(title, styles["H1RM"])]
        for paragraph in paragraphs:
            block.append(Paragraph(paragraph, styles["BodyRM"]))
        story.append(KeepTogether(block) if len(paragraphs)<=2 else block[0])
        if len(paragraphs)>2:
            story.extend(block[1:])
        if idx in breaks_after:
            story.append(PageBreak())

    story.append(Paragraph("Konfigurationsübersicht" if lang=="de" else "Configuration overview", styles["H1RM"]))
    rows=[["Option", "Bedeutung" if lang=="de" else "Purpose"]]
    rows += [[Paragraph(k, styles["SmallRM"]), Paragraph(v, styles["BodyRM"])] for k,v in tx["options"]]
    table=Table(rows, colWidths=[61*mm, 113*mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),ORANGE),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),8.5),
        ("GRID",(0,0),(-1,-1),.4,BORDER),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,LIGHT]),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(table)
    story.append(Spacer(1,4*mm))
    final = "Weitere technische Einzelheiten stehen in DOCS.md und in der integrierten Hilfe." if lang=="de" else "Further technical details are available in DOCS.md and the built-in Help view."
    story.append(Paragraph(final, styles["Notice"]))

    doc.build(story)
    return out


if __name__ == "__main__":
    DOCS.mkdir(parents=True, exist_ok=True)
    for language in ("de", "en"):
        print(build(language))
