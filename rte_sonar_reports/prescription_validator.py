# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime
from enum import Enum

import pytz

from rte_sonar_reports.app import Rating


def datetime_in_paris_timezone(year, month, day):
    return pytz.timezone('Europe/Paris').localize(datetime(year, month, day))


class Criteria:
    def __init__(self, criteria_start_date, criteria_validation_method):
        self.criteria_start_date = criteria_start_date
        self.criteria_validation_method = criteria_validation_method

    def criteria_start_date(self):
        return self.criteria_start_date

    def is_validated(self, app):
        return self.criteria_validation_method(app)


SECURITY_CRITERIA_START_DATE = datetime_in_paris_timezone(2024, 11, 1)
SECURITY_CRITERIA = Criteria(SECURITY_CRITERIA_START_DATE, lambda app : app.worst_non_dependency_security_rating() <= Rating.A)

TEST_COVERAGE_CRITERIA_START_DATE = datetime_in_paris_timezone(2025, 3, 1)
TEST_COVERAGE_CRITERIA = Criteria(TEST_COVERAGE_CRITERIA_START_DATE, lambda app : app.aggregated_backend_coverage() is None or app.aggregated_backend_coverage() >= 60)

MAINTAINABILITY_CRITERIA_START_DATE = datetime_in_paris_timezone(2025, 9, 1)
MAINTAINABILITY_CRITERIA = Criteria(MAINTAINABILITY_CRITERIA_START_DATE, lambda app : app.worst_maintainability_rating() <= Rating.A)

ALL_CRITERIAS = [SECURITY_CRITERIA, TEST_COVERAGE_CRITERIA, MAINTAINABILITY_CRITERIA]


class PrescriptionStatus(Enum):
    ALL_FUTURE_CRITERIA_VALIDATED = 0
    ONLY_CURRENT_CRITERIA_VALIDATED = 1
    CURRENT_CRITERIA_NOT_VALIDATED = 2


def compute_prescription_status(app, date):
    worst_criteria = PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED
    for criteria in ALL_CRITERIAS:
        if not criteria.is_validated(app):
            if date >= criteria.criteria_start_date:
                return PrescriptionStatus.CURRENT_CRITERIA_NOT_VALIDATED
            else:
                worst_criteria = PrescriptionStatus.ONLY_CURRENT_CRITERIA_VALIDATED
    return worst_criteria
