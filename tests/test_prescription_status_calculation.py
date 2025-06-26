# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import timedelta

import pytest

from rte_sonar_reports.app import Application, Rating
from rte_sonar_reports.prescription_validator import compute_prescription_status, PrescriptionStatus, \
    datetime_in_paris_timezone, SECURITY_CRITERIA_START_DATE, TEST_COVERAGE_CRITERIA_START_DATE, \
    MAINTAINABILITY_CRITERIA_START_DATE

app = Application("TEST_APP", "0.0.0")


def test_all_criterias_validated():
    app.worst_non_dependency_security_rating = lambda: Rating.A
    app.aggregated_backend_coverage = lambda: 60.0
    app.worst_maintainability_rating = lambda: Rating.A
    assert compute_prescription_status(app, datetime_in_paris_timezone(2020, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED
    assert compute_prescription_status(app, datetime_in_paris_timezone(2024, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED
    assert compute_prescription_status(app, datetime_in_paris_timezone(2026, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED

def test_coverage_criteria_on_backend_when_only_frontend_modules():
    app.worst_non_dependency_security_rating = lambda: Rating.A
    app.aggregated_backend_coverage = lambda: None
    app.worst_maintainability_rating = lambda: Rating.A
    assert compute_prescription_status(app, datetime_in_paris_timezone(2020, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED
    assert compute_prescription_status(app, datetime_in_paris_timezone(2024, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED
    assert compute_prescription_status(app, datetime_in_paris_timezone(2026, 1, 1)) == PrescriptionStatus.ALL_FUTURE_CRITERIA_VALIDATED

@pytest.mark.parametrize(
    "worst_security_rating, aggregated_backend_coverage, worst_maintainability_rating, limit_date",
    [
        (Rating.B, 60.0, Rating.A, SECURITY_CRITERIA_START_DATE),
        (Rating.A, 59.9, Rating.A, TEST_COVERAGE_CRITERIA_START_DATE),
        (Rating.A, 60.0, Rating.B, MAINTAINABILITY_CRITERIA_START_DATE),
    ]
)
def test_any_criteria_not_validated(worst_security_rating, aggregated_backend_coverage, worst_maintainability_rating, limit_date):
    app.worst_non_dependency_security_rating = lambda: worst_security_rating
    app.aggregated_backend_coverage = lambda: aggregated_backend_coverage
    app.worst_maintainability_rating = lambda: worst_maintainability_rating
    assert compute_prescription_status(app, datetime_in_paris_timezone(2020, 1, 1)) == PrescriptionStatus.ONLY_CURRENT_CRITERIA_VALIDATED
    assert compute_prescription_status(app, limit_date - timedelta(seconds=1)) == PrescriptionStatus.ONLY_CURRENT_CRITERIA_VALIDATED
    assert compute_prescription_status(app, limit_date) == PrescriptionStatus.CURRENT_CRITERIA_NOT_VALIDATED
    assert compute_prescription_status(app, datetime_in_paris_timezone(2026, 1, 1)) == PrescriptionStatus.CURRENT_CRITERIA_NOT_VALIDATED
