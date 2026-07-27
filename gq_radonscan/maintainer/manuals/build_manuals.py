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

VERSION = "5.4.0"
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
"Vor Upgrades und destruktiven Aktionen sollte ein Home-Assistant-Backup erstellt werden. Nach dem Upgrade muss in Seitenleiste oder Hilfe Version 5.4.0 erscheinen. Bleibt eine alte Ingress-Ansicht geöffnet, schließen Sie das Panel und öffnen Sie es erneut.",
"Nur abgeschlossene Stunden werden übernommen. Nach dem ersten Anschließen kann deshalb zunächst noch kein aktueller Messwert verfügbar sein."
]),
("3. Übersicht", [
"Die Kontextleiste der Übersicht wählt Gerät und Kampagne. Der zuletzt beziehungsweise aktuell zugeordnete Raum wird automatisch ermittelt. Aktueller Wert, Zeitfenster, Stichprobenzahl, 24-Stunden-Maximum und Diagramm werden aus genau diesem Gerät, dieser Kampagne und diesem Raum gebildet. Gerät und Kampagne bleiben lokal im Browser gespeichert.",
"Die Radonampel bewertet bevorzugt den 24-Stunden-Mittelwert. Reichen Messdauer oder Datenabdeckung noch nicht aus, verwendet sie vorläufig den letzten abgeschlossenen Stundenwert. Bewertungsbasis, Abdeckung sowie Warn- und Gefahrenschwellen stehen direkt unter der Ampel.",
"Die vierte Kennzahl zeigt statt eines schwer interpretierbaren Gesamtmittels das beobachtete Maximum der letzten 24 Stunden mit Zeitpunkt und Datenabdeckung. Dokumentierte Ereignisse erscheinen als Markierungen im Verlauf; Datenlücken werden als Unterbrechungen und nicht als verbindende Linie dargestellt.",
"Der Home-Assistant-Standort zeigt je nach Datenschutzmodus Adresse und genaue Koordinaten, nur Ortsname und gerundete Koordinaten oder gar keine Standortkachel. Koordinaten enthalten Gradzeichen und Himmelsrichtungen, zum Beispiel 51,60176° N, 7,45410° E. Direkt darunter stehen ausschließlich der automatisch zugeordnete Raum und - sofern hinterlegt - die Messhöhe. Die Standortdaten stammen aus der lokalen Home-Assistant-Core-Konfiguration; es findet keine externe Geokodierung statt."
]),
("4. Analyse und Statistik", [
"Die Analyse beginnt mit einer verständlichen Zusammenfassung von Trendrichtung, Warn- und Gefahrenschwellenanteil sowie Datenabdeckung. Die Grundauswertung enthält Mittelwert, Median, Minimum, Maximum, Quantile und Schwellenzeiten. Effektive Stichprobengröße, Moving-Block-Bootstrap-Konfidenzintervalle, Autokorrelation, Verteilungsdiagnostik und Sensitivitätsanalyse sind standardmäßig in einem eingeklappten erweiterten Bereich zusammengefasst.",
"Fehlende Messwerte werden nicht imputiert. Auffällige Werte werden nicht automatisch gelöscht. Qualitätsflags kennzeichnen unter anderem nicht dokumentierte Faktoren, nicht primäre Datenquellen, unplausible Werte und doppelte Zeitstempel.",
"Die Strukturbruchanalyse ist explorativ. Bei sehr langen Reihen wird ausschließlich diese Diagnose auf eine gleichmäßig verteilte, zeitlich geordnete Stichprobe begrenzt. Deskriptive Kennwerte, Schwellenberechnungen und Datenprüfsummen verwenden weiterhin alle ausgewählten Datensätze.",
"Eine statistische Signifikanz beweist weder eine Ursache noch eine praktisch relevante Wirkung. Ereignisse und Maßnahmen müssen zusätzlich fachlich interpretiert werden."
]),
("5. Geräte & System, Faktor und Kalibrierung", [
"Die frühere Expertenansicht wurde in Version 5.1.0 vollständig aus Oberfläche und Seitenleiste entfernt. Geräte-, Protokoll-, Dienst- und Datenbankstatus finden Sie gebündelt unter Geräte & System; konfigurierbare Schwellen und weitere Betriebsparameter stehen unter Einstellungen.",
"Der System-Selbsttest prüft auf Anforderung API-Version, SQLite-Integrität, schreibgeschützten Raum-Rundlauf, Berichtsverzeichnis, Gerätestatus, MQTT und die lokale Home-Assistant-Verbindung. Das Ergebnis wird als verständliche Checkliste angezeigt und verändert keine gespeicherten Räume oder Messwerte.",
"Der aktuell konfigurierte Faktor wird getrennt vom Faktor des ausgewählten historischen Messwerts dargestellt. Dadurch bleiben ältere Werte reproduzierbar, auch wenn die Konfiguration später geändert wird.",
"Kalibrierungen können mit Datum, Labor, Zertifikatsreferenz, Faktor, Unsicherheit, Folgetermin und Notizen dokumentiert werden. Ein Eintrag verändert vorhandene Messwerte nicht automatisch."
]),
("6. Räume, Zuordnungen und Ereignisse", [
"Die Ansicht Lokale Metadaten heißt Räume und Ereignisse. Ort beziehungsweise Adresse und Gebäudename werden direkt aus den allgemeinen Home-Assistant-Einstellungen übernommen und können in der App nicht doppelt oder abweichend eingetragen werden. Manuell ergänzt werden ausschließlich der Raum und die Messhöhe.",
"Der Arbeitsablauf ist in zwei Schritte gegliedert: Zuerst wird ein Raum angelegt oder bearbeitet, danach wird er einem Gerät und Zeitraum zugeordnet. Solange kein Raum gespeichert ist, bleibt die Zuordnung deaktiviert. Fehler werden unmittelbar am betroffenen Eingabefeld angezeigt; gespeicherte Zuordnungen erscheinen als eigene Liste unter den Formularen.",
"Das Speichern von Räumen ist idempotent: Eine erneute Speicherung desselben normalisierten Raumnamens aktualisiert den vorhandenen Datensatz statt ein Duplikat anzulegen. Die App unterstützt Dezimalpunkt und Dezimalkomma bei der Messhöhe und übermittelt unter Home Assistant Ingress zusätzlich eng begrenzte Rückfallinformationen, falls ein Proxy den regulären Anfrageinhalt verändert.",
"Messwerte können einem Raum für einen definierten Zeitraum zugeordnet werden. Messkampagnen, Zweck, Beginn, Ende und Notizen bleiben lokal. Lüftung, Maßnahmen, Gerätewechsel, Baumaßnahmen oder Ausfälle können als Ereignisse dokumentiert werden, ohne Originalmesswerte zu verändern. Passende Ereignisse werden in Übersichts- und Analysediagrammen markiert."
]),
("7. GQ Radiation World Map", [
"Der Upload ist optional und standardmäßig deaktiviert. Ist gmcmap_enabled ausgeschaltet, wird die World-Map-Ansicht vollständig aus der Seitenleiste ausgeblendet. Bei Aktivierung enthält sie ausschließlich externe Upload-, Warteschlangen- und Verlaufsfunktionen; lokale Räume, Zuordnungen und Ereignisse verbleiben in ihrer eigenen Ansicht. Account-ID und Geräte-ID werden nur maskiert angezeigt.",
"Eine persistente Warteschlange verhindert Doppelübertragungen, wiederholt temporäre Fehler mit zunehmendem Abstand und kann zu alte Werte nach einer konfigurierbaren Grenze verwerfen. Der manuelle Upload ist eine geschützte POST-Aktion.",
"Die öffentliche Position wird im GQ-Konto verwaltet. Radon Monitoring übermittelt keine eigenen GPS-Koordinaten."
]),
("8. Wissenschaftliche PDF-Berichte", [
"Kompakte und detaillierte Berichte enthalten Zeitraum, Raum, Messhöhe, Home-Assistant-Standort und -Gebäude, Gerät, Faktor, Datenabdeckung, Kennwerte, Zeitreihe, Methodik, Qualitätsinformationen, Softwareversion und SHA-256-Prüfsummen.",
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
"Version 5.4.0 wurde in Chromium bei 320, 390, 768 und 1440 Pixeln, in allen acht Sprachen und mit langen Testbezeichnungen geprüft."
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
"Messwerte und Metadaten bleiben standardmäßig lokal. Nur aktivierte externe Funktionen übertragen Daten. Die Standortkachel liest ihre Angaben ausschließlich über die lokale Home-Assistant-Core-API und verwendet keinen externen Geokodierungsdienst. Mit location_display_mode kann die Anzeige vollständig, reduziert oder ausgeblendet erfolgen. Prüfen Sie vor Bildschirmfotos, Berichten und World-Map-Uploads, ob die sichtbaren Standortangaben Ihren Datenschutzanforderungen entsprechen.",
"Bewahren Sie Backups und Berichte geschützt auf. Sie können Gerätekennungen, Räume, Zeiträume und Gebäudedaten enthalten."
]),
("13. Neu in Version 5.4.0", [
"Version 5.4.0 ist ein Stabilitäts- und Wartbarkeitsrelease. Der Raum-Workflow wurde mit zentraler Eingabevalidierung, idempotentem Speichern, Unterstützung für Dezimalkommas sowie JSON-, Formular-, Query- und Header-Verarbeitung für Home Assistant Ingress abgesichert. Räume müssen nun vor einer Messzuordnung angelegt werden; Validierungsfehler stehen direkt am Feld, und vorhandene Zuordnungen sind sichtbar. Ein nicht destruktiver System-Selbsttest prüft die wichtigsten lokalen Komponenten. Die neuen Module room_metadata.py, diagnostics.py, rooms-events.js und system-diagnostics.js trennen diese Funktionen aus den zuvor sehr großen Kernmodulen. Eine Kompatibilitätsmatrix unterscheidet automatisiert geprüfte Eigenschaften klar von noch erforderlichen Feldtests. Bestehende Datenbanken und Messwerte bleiben kompatibel."
])
],
"options": [
("serial_port", "Automatische Erkennung oder stabiler USB-Pfad"),
("factor_bq_m3_per_cph", "Aktuell verwendeter Umrechnungsfaktor"),
("minimum_data_coverage_percent", "Mindestabdeckung für Zeitfenster und Qualitätsstatus"),
("analysis_timezone", "Zeitzone für Tages- und Wochenprofile"),
("location_display_mode", "Standort vollständig, reduziert oder ausgeblendet anzeigen"),
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
"Create a Home Assistant backup before upgrades and destructive actions. After upgrading, the sidebar or Help view must show version 5.4.0. If an old Ingress view remains open, close the panel and reopen it.",
"Only completed hours are imported. A newly connected device can therefore remain without a current value until a complete record is available."
]),
("3. Overview", [
"The Overview context bar selects a device and campaign. The most recently or currently assigned room is resolved automatically. Current value, period windows, selected sample count, 24-hour maximum and chart are derived from that device, campaign and room. Device and campaign choices are retained locally in the browser.",
"The Radon traffic light primarily assesses the 24-hour mean. Until duration or coverage is sufficient, it provisionally uses the latest completed hourly value. The assessment basis, coverage and configured warning/danger thresholds are displayed directly below the signal.",
"The fourth metric shows the observed maximum within the latest 24-hour window, including its time and coverage, instead of a potentially mixed overall mean. Documented events appear as chart markers and gaps are shown as breaks rather than connected lines.",
"Depending on the privacy mode, the Home Assistant location card shows an address and precise coordinates, only the location name and rounded coordinates, or no location card. Coordinates include degree units and cardinal directions, for example 51.60176° N, 7.45410° E. Directly below it, the interface shows only the automatically assigned room and, when available, the measurement height. Location values come only from the local Home Assistant Core configuration and no external geocoding is performed."
]),
("4. Analysis and statistics", [
"Analysis starts with a plain-language summary of trend direction, warning/danger threshold share and data coverage. Basic analysis contains mean, median, minimum, maximum, quantiles and threshold time. Effective sample size, moving-block-bootstrap confidence intervals, autocorrelation, distribution diagnostics and sensitivity analysis are grouped in an advanced section that is collapsed by default.",
"Missing measurements are not imputed. Unusual observations are not deleted automatically. Quality flags identify undocumented factors, non-primary sources, implausible values and duplicate timestamps.",
"Change-point analysis is exploratory. For very long series, only this diagnostic is bounded to an evenly distributed, time-ordered sample. Descriptive statistics, threshold calculations and data checksums continue to use every selected record.",
"Statistical significance proves neither causality nor practical importance. Events and interventions still require professional interpretation."
]),
("5. Devices & System, factor and calibration", [
"The former Expert view was removed completely from the interface and sidebar in version 5.1.0. Device, protocol, service and database status is grouped under Devices & System; configured thresholds and other operating parameters are shown under Settings.",
"The on-demand System self-test checks the API version, SQLite integrity, a rolled-back room persistence round trip, the report directory, device runtime, MQTT and the local Home Assistant connection. Results are shown as an actionable checklist and do not alter stored rooms or measurements.",
"The currently configured factor is displayed separately from the factor stored with the selected historical measurement. Historical results therefore remain reproducible after later configuration changes.",
"Calibration records can include date, laboratory, certificate reference, factor, uncertainty, next due date and notes. A calibration entry does not silently alter existing measurements."
]),
("6. Rooms, assignments and events", [
"The Local metadata view is named Rooms and events. Place or address and building name are taken directly from the general Home Assistant settings and cannot be entered again or differently in the app. Only the room and measurement height are added manually.",
"The workflow is divided into two steps: first create or edit a room, then assign it to a device and time period. Assignment remains disabled until at least one room has been stored. Validation messages appear directly beside the affected field, and stored assignments are shown in a dedicated list below the forms.",
"Room storage is idempotent: saving the same normalised room name again updates the existing record instead of creating a duplicate. Both decimal points and decimal commas are accepted for measurement height, and under Home Assistant Ingress the interface sends tightly bounded fallback information if a proxy changes the regular request body.",
"Measurements can be assigned to a room for a defined period. Campaign, purpose, start, end and notes remain local. Ventilation, interventions, device moves, construction work or outages can be documented as events without changing original measurements. Matching events are marked in Overview and Analysis charts."
]),
("7. GQ Radiation World Map", [
"Upload is optional and disabled by default. When gmcmap_enabled is off, the World Map view is omitted from the sidebar. When enabled it contains only external upload, queue and history functions; local rooms, assignments and events remain in their dedicated view. Account ID and device ID are shown only in masked form.",
"A persistent queue prevents duplicates, retries temporary failures with increasing delay and can discard measurements older than a configured limit. Manual upload is a protected POST action.",
"The public position is managed in the GQ account. Radon Monitoring does not transmit its own GPS coordinates."
]),
("8. Scientific PDF reports", [
"Compact and detailed reports contain period, room, measurement height, Home Assistant location and building, device, factor, coverage, statistics, time series, method, quality information, software version and SHA-256 checksums.",
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
"Version 5.4.0 was checked in Chromium at 320, 390, 768 and 1440 pixels, in all eight languages and with deliberately long labels."
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
"Measurements and metadata remain local by default. Only enabled external functions transmit data. Location, address and building name are read only through the local Home Assistant Core API and are not manually duplicated. No external geocoding service is used. location_display_mode can show full, reduced or no location details. Before screenshots, reports and World Map publication, confirm that visible location data meets your privacy requirements.",
"Protect backups and reports because they may contain device identifiers, rooms, periods and building information."
]),
("13. New in version 5.4.0", [
"Version 5.4.0 is a stability and maintainability release. The room workflow now uses central input validation, idempotent storage, decimal-comma support and JSON, form, query and header handling for Home Assistant Ingress. Rooms must be created before a measurement assignment; validation errors appear at the relevant field and existing assignments are visible. A non-destructive System self-test checks the most important local components. New room_metadata.py, diagnostics.py, rooms-events.js and system-diagnostics.js modules separate these functions from the previously large core modules. A compatibility matrix clearly distinguishes automated verification from field testing that is still required. Existing databases and measurements remain compatible."
])
],
"options": [
("serial_port", "Automatic discovery or stable USB path"),
("factor_bq_m3_per_cph", "Currently configured conversion factor"),
("minimum_data_coverage_percent", "Minimum coverage for period results and quality"),
("analysis_timezone", "Time zone for daily and weekly profiles"),
("location_display_mode", "Show full, reduced or no location details"),
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
