# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import math

import requests

from rte_sonar_reports.app import Rating

LOGGER = logging.getLogger(__name__)
MAINTAINABILITY_RATING_METRIC_KEY = "sqale_rating"
LINES_TO_COVER_METRIC_KEY = "lines_to_cover"
UNCOVERED_LINES_METRIC_KEY = "uncovered_lines"
CONDITIONS_TO_COVER_METRIC_KEY = "conditions_to_cover"
UNCOVERED_CONDITIONS_METRIC_KEY = "uncovered_conditions"

ALL_METRIC_KEYS = [MAINTAINABILITY_RATING_METRIC_KEY,
                   LINES_TO_COVER_METRIC_KEY,
                   UNCOVERED_LINES_METRIC_KEY,
                   CONDITIONS_TO_COVER_METRIC_KEY,
                   UNCOVERED_CONDITIONS_METRIC_KEY]

class SonarClient:

    EMPTY_PASSWORD_FIELD = ""

    def __init__(self, sonar_config):
        self.base_url = sonar_config["base_url"]
        self.auth = (sonar_config["token"], SonarClient.EMPTY_PASSWORD_FIELD) if "token" in sonar_config else None

    @staticmethod
    def get_rating_from_sonar_api_string_value(value):
        return Rating(int(float(value)))

    def get_all_indicators(self, project_key, branch_name):
        request_params = {"component": project_key, "metricKeys": ",".join(ALL_METRIC_KEYS)}
        request_params["branch"] = branch_name if branch_name else self.find_default_branch(project_key)

        response = requests.get(self.base_url + "/api/measures/component",
                                params=request_params,
                                auth=self.auth)
        LOGGER.debug(f"Response {response}")
        LOGGER.debug(f"{response.json()}")
        component = response.json()["component"]
        values = {}
        for metric_key in ALL_METRIC_KEYS:
            associated_measures = [measure for measure in component["measures"] if measure["metric"] == metric_key]
            values[metric_key] = associated_measures[0]["value"] if associated_measures else 0
        return {
            MAINTAINABILITY_RATING_METRIC_KEY: self.get_rating_from_sonar_api_string_value(values[MAINTAINABILITY_RATING_METRIC_KEY]),
            LINES_TO_COVER_METRIC_KEY: int(values[LINES_TO_COVER_METRIC_KEY]),
            UNCOVERED_LINES_METRIC_KEY: int(values[UNCOVERED_LINES_METRIC_KEY]),
            CONDITIONS_TO_COVER_METRIC_KEY: int(values[CONDITIONS_TO_COVER_METRIC_KEY]),
            UNCOVERED_CONDITIONS_METRIC_KEY: int(values[UNCOVERED_CONDITIONS_METRIC_KEY])
        }

    def get_all_vulnerabilities_sorted(self, project_key, branch_name):
        request_params = {"componentKeys": project_key, "resolved": "false", "types": "VULNERABILITY"}
        request_params["branch"] = branch_name if branch_name else self.find_default_branch(project_key)

        response = requests.get(self.base_url + "/api/issues/search",
                                params=request_params,
                                auth=self.auth)
        LOGGER.debug(f"Response {response}")
        LOGGER.debug(f"{response.json()}")
        response_obj = response.json()
        number_of_vulnerabilities = response_obj["total"]
        number_of_vulnerabilities_per_page = response_obj["ps"]
        vulnerabilities = []
        vulnerabilities += response_obj["issues"]
        for page_num in range(2, math.ceil(number_of_vulnerabilities / number_of_vulnerabilities_per_page) + 1):
            request_params["p"] = page_num
            response = requests.get(self.base_url + "/api/issues/search",
                                    params=request_params,
                                    auth=self.auth)
            LOGGER.debug(f"Response {response}")
            LOGGER.debug(f"{response.json()}")
            response_obj = response.json()
            vulnerabilities += response_obj["issues"]
        return vulnerabilities

    def find_default_branch(self, project_key):
        request_params = {"project": project_key}
        response = requests.get(self.base_url + "/api/project_branches/list",
                                params=request_params,
                                auth=self.auth)
        LOGGER.debug(f"Response {response}")
        LOGGER.debug(f"{response.json()}")
        main_branches = [branch for branch in response.json()["branches"] if branch["isMain"]]
        if len(main_branches) == 0:
            LOGGER.error(f"No main branches found for project {project_key}")
            return None
        elif len(main_branches) > 1:
            first_main_branch = main_branches[0]["name"]
            LOGGER.warning(f"Multiple main branches found for project {project_key}, using first one {first_main_branch}")
            return first_main_branch
        else:
            main_branch = main_branches[0]["name"]
            LOGGER.info(f"Main branch for project {project_key} is {main_branch}")
            return main_branch

