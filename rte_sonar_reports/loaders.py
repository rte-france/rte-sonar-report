# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from importlib_resources import read_text
from jsonschema import validate
import yaml

from rte_sonar_reports.app import Application, Module, Rating
from rte_sonar_reports.sonar import SonarClient, \
    MAINTAINABILITY_RATING_METRIC_KEY, LINES_TO_COVER_METRIC_KEY, UNCOVERED_LINES_METRIC_KEY, \
    CONDITIONS_TO_COVER_METRIC_KEY, UNCOVERED_CONDITIONS_METRIC_KEY

APPLICATION_DESCRIPTION_SCHEMA = yaml.safe_load(read_text("rte_sonar_reports", "application_description_schema.yml"))
LOGGER = logging.getLogger(__name__)


class ApplicationLoader:

    def __init__(self, sonar_configs):
        self.sonar_configs = sonar_configs

    @staticmethod
    def get_type(module_description):
        if "type" not in module_description:
            return Module.Type.OTHER
        module_type_str = module_description["type"]
        if module_type_str == "backend":
            return Module.Type.BACKEND
        elif module_type_str == "frontend":
            return Module.Type.FRONTEND
        else:
            return Module.Type.OTHER

    def load_file(self, file):
        with open(file) as f:
            return self.load(f.read())

    def load(self, yaml_content):
        application_description_content = yaml.safe_load(yaml_content)
        validate(application_description_content, APPLICATION_DESCRIPTION_SCHEMA)
        application_description = application_description_content["application"]
        app = Application(application_description["name"], application_description["version"])
        self.add_modules(app, application_description)
        return app

    def add_modules(self, app, application_description):
        if "modules" not in application_description:
            return
        if application_description["modules"] is None:
            return
        for module in application_description["modules"]:
            branch_name, indicators, vulnerabilities = self.get_all_sonar_indicators(module)
            maintainability_rating = indicators[MAINTAINABILITY_RATING_METRIC_KEY] if MAINTAINABILITY_RATING_METRIC_KEY in indicators else Rating.NOT_CALCULATED
            lines_to_cover = indicators[LINES_TO_COVER_METRIC_KEY] if LINES_TO_COVER_METRIC_KEY in indicators else 0
            uncovered_lines = indicators[UNCOVERED_LINES_METRIC_KEY] if UNCOVERED_LINES_METRIC_KEY in indicators else 0
            conditions_to_cover = indicators[CONDITIONS_TO_COVER_METRIC_KEY] if CONDITIONS_TO_COVER_METRIC_KEY in indicators else 0
            uncovered_conditions = indicators[UNCOVERED_CONDITIONS_METRIC_KEY] if UNCOVERED_CONDITIONS_METRIC_KEY in indicators else 0
            app.add_module(Module(module["name"], branch_name=branch_name, module_type=self.get_type(module),
                                  maintainability_rating=maintainability_rating, lines_to_cover=lines_to_cover,
                                  uncovered_lines=uncovered_lines, conditions_to_cover=conditions_to_cover,
                                  uncovered_conditions=uncovered_conditions, vulnerabilities=vulnerabilities))

    def get_all_sonar_indicators(self, module):
        branch_name = module["branch"] if "branch" in module else None
        indicators = dict()
        if "sonar_config" not in module or "project_key" not in module:
            LOGGER.error(f"""Module '{module["name"]}' definition is not complete, its indicators cannot be retrieved.""")
            return branch_name, indicators, None
        if module["sonar_config"] not in self.sonar_configs:
            LOGGER.error(f"""Module '{module["name"]}' is based on Sonar configuration '{module["sonar_config"]}' which has not been defined. Its indicators cannot be retrieved.""")
            return branch_name, indicators, None
        sonar_config = self.sonar_configs[module["sonar_config"]]
        project_key = module["project_key"]
        if not sonar_config:
            LOGGER.error(f"""Module '{module["name"]}' is based on Sonar configuration '{module["sonar_config"]}' which is not well defined. Its indicators cannot be retrieved.""")
            return branch_name, indicators, None
        sonar_client = SonarClient(sonar_config)
        if not branch_name:
            branch_name = sonar_client.find_default_branch(project_key)
        LOGGER.info(
            f"""Retrieving Sonar indicators for module '{module["name"]}' on Sonar configuration '{sonar_config.name}' with project key '{project_key}'""")
        indicators = sonar_client.get_all_indicators(project_key, branch_name)
        vulnerabilities = sonar_client.get_all_vulnerabilities_sorted(project_key, branch_name)
        return branch_name, indicators, vulnerabilities
