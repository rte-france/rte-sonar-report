# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import datetime
import logging

import pytz

import importlib_resources
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph, Table
from svglib.svglib import svg2rlg

from rte_sonar_reports.app import Rating, Module
from rte_sonar_reports.prescription_validator import PrescriptionStatus, compute_prescription_status

STYLES = getSampleStyleSheet()
RATING_COLORS = {
    Rating.A: "#6cd46c",
    Rating.B: "#c6e056",
    Rating.C: "#f4d348",
    Rating.D: "#f69d53",
    Rating.E: "#f0878e",
    Rating.NOT_CALCULATED: "#d3d3d3"
}
RATING_MESSAGE = {
    Rating.A: "A",
    Rating.B: "B",
    Rating.C: "C",
    Rating.D: "D",
    Rating.E: "E",
    Rating.NOT_CALCULATED: "N/A"
}
TRAFFIC_LIGHT_IMAGE = {
    PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED: "traffic_green.svg",
    PrescriptionStatus.ONLY_CURRENT_CRITERIA_VALIDATED: "traffic_orange.svg",
    PrescriptionStatus.CURRENT_CRITERIA_NOT_VALIDATED: "traffic_red.svg"
}
LOGGER = logging.getLogger(__name__)


def add_rte_logo(report):
    with importlib_resources.path(__package__, "RTE_logo.svg") as rte_logo_path:
        rte_logo = svg2rlg(rte_logo_path)
        report.append(Image(rte_logo, width=2.5*cm, height=2.5*cm, hAlign="RIGHT", kind="proportional"))


def add_space(report):
    report.append(Spacer(1, 1 * cm))


def add_title(report, app):
    report.append(Paragraph(f"Rapport d'analyse Sonar de l'application \"{app.name}\" version {app.version}",
                            style=STYLES["Title"]))


def add_traffic_light(report, app, generation_date):
    prescription_status = compute_prescription_status(app, generation_date)
    with importlib_resources.path(__package__, TRAFFIC_LIGHT_IMAGE.get(prescription_status)) as traffic_light_img_path:
        traffic_light_img = svg2rlg(traffic_light_img_path)
        report.append(Image(traffic_light_img, width=2.5*cm, height=2.5*cm, kind="proportional"))


def add_abstract(report, app, generation_date):
    report.append(Paragraph("Récapitulatif", style=STYLES["Heading1"]))
    add_traffic_light(report, app, generation_date)
    add_space(report)
    data = [["Sécurité", "Couverture du backend", "Maintenabilité"],
            [convert_rating(app.worst_non_dependency_security_rating(), 'Title'),
             convert_coverage(app.aggregated_backend_coverage(), 'Title'),
             convert_rating(app.worst_maintainability_rating(), 'Title')
             ]]
    report.append(Table(data))


def convert_module_type(module_type):
    if module_type == Module.Type.FRONTEND:
        return "Frontend"
    elif module_type == Module.Type.BACKEND:
        return "Backend"
    else:
        return "Autre"


def convert_rating(rating, parent):
    color = RATING_COLORS.get(rating) if rating in RATING_COLORS else RATING_COLORS[Rating.NOT_CALCULATED]
    message = RATING_MESSAGE.get(rating) if rating in RATING_MESSAGE else RATING_MESSAGE[Rating.NOT_CALCULATED]

    local_style = ParagraphStyle(name='local_style',
                                 parent=STYLES[parent],
                                 backColor=color,
                                 borderPadding=0,
                                 borderRadius=0.1 * cm,
                                 borderColor=color,
                                 borderWidth=1,
                                 alignment=TA_CENTER)
    return Paragraph(message, style=local_style)


def convert_percentage_to_rating(percentage):
    saturated_integer = max(min(int(percentage / 20), 4), 0)
    return Rating(5-saturated_integer)


def convert_coverage(coverage, parent):
    if coverage is None:
        color = RATING_COLORS[Rating.NOT_CALCULATED]
        message = "N/A"
    else:
        color = RATING_COLORS[convert_percentage_to_rating(coverage)]
        message = f"{coverage}%"

    local_style = ParagraphStyle(name='local_style',
                                 parent=STYLES[parent],
                                 backColor=color,
                                 borderPadding=0,
                                 borderRadius=0.1 * cm,
                                 borderColor=color,
                                 borderWidth=1,
                                 alignment=TA_CENTER)
    return Paragraph(message, style=local_style)


def convert_text(text):
    return Paragraph(text, style=STYLES["Normal"])


def add_detail(report, app):
    report.append(Paragraph("Détail par module", style=STYLES["Heading1"]))
    columns_headers = ["Nom", "Branche", "Type", "Sécurité", "Dépendances", "Couverture", "Maintenabilité"]
    data = [columns_headers]
    number_of_modules = len(app.modules)
    number_of_columns = len(columns_headers)
    for module in app.modules:
        data.append([convert_text(module.name),
                     convert_text(module.branch_name),
                     convert_module_type(module.module_type),
                     convert_rating(module.non_dependency_security_rating(), 'Normal'),
                     convert_rating(module.dependency_security_rating(), 'Normal'),
                     convert_coverage(module.calculated_coverage(), 'Normal'),
                     convert_rating(module.maintainability_rating, 'Normal'), ])

    local_style = [('FONTSIZE', (0, 0), (number_of_columns-1, number_of_modules), 8),
                   ("LINEABOVE", (0, 0), (number_of_columns-1, 1), 1, "black"),
                   ("LINEBEFORE", (1, 1), (number_of_columns-1, number_of_modules), 1, "black"),
                   ("VALIGN", (0, 0), (number_of_columns-1, number_of_modules), "MIDDLE"),]
    report.append(Table(data, style=local_style, colWidths=[4*cm, 4*cm, 2*cm, 2*cm, 2*cm, 2*cm,2*cm]))


def add_generation_date(report, generation_date):
    generation_date_rendered = generation_date.strftime("%d/%m/%Y à %H:%M")
    local_style = ParagraphStyle(name='local_style',
                                 parent=STYLES['Normal'],
                                 alignment=TA_CENTER)
    report.append(Paragraph(f"Généré le {generation_date_rendered}", style=local_style))


def export(output_path, app):
    LOGGER.info(f"""Generating Sonar indicators report for application {app.name} version {app.version}""")
    generation_date = datetime.datetime.now(pytz.timezone('Europe/Paris'))
    doc = SimpleDocTemplate(output_path)
    report = []
    add_rte_logo(report)
    add_space(report)
    add_title(report, app)
    add_generation_date(report, generation_date)
    add_space(report)
    add_abstract(report, app, generation_date)
    add_space(report)
    add_detail(report, app)
    doc.build(report)
