# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

import pytest

from rte_sonar_reports import app
from rte_sonar_reports.app import DEPENDENCY_VULNERABILITY_RULE


def test_module_should_have_a_name():
    my_module = app.Module("My module")
    assert my_module.name == "My module"


@pytest.mark.parametrize(
    "module_type",
    [
        app.Module.Type.BACKEND,
        app.Module.Type.FRONTEND,
        app.Module.Type.OTHER
    ]
)
def test_module_should_have_provided_type(module_type):
    my_module = app.Module("My module", module_type=module_type)
    assert my_module.module_type == module_type


def test_module_without_type_have_type_other():
    my_module = app.Module("My module")
    assert my_module.module_type == app.Module.Type.OTHER


@pytest.mark.parametrize(
    "returned_non_dependency_security_rating, vulnerabilities",
    [
        (app.Rating.A, [{"rule": "any", "severity": "INFO"}]),
        (app.Rating.A, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "BLOCKER"}]),
        (app.Rating.A, []),
        (app.Rating.B, [{"rule": "any", "severity": "MINOR"}]),
        (app.Rating.C, [{"rule": "any", "severity": "MAJOR"}]),
        (app.Rating.D, [{"rule": "any", "severity": "CRITICAL"}]),
        (app.Rating.D, [{"rule": "any", "severity": "INFO"},{"rule": "any", "severity": "CRITICAL"}]),
        (app.Rating.D, [{"rule": "any", "severity": "CRITICAL"},{"rule": "any", "severity": "INFO"}]),
        (app.Rating.E, [{"rule": "any", "severity": "BLOCKER"}]),
    ]
)
def test_module_should_provide_non_dependency_security_rating(returned_non_dependency_security_rating, vulnerabilities):
    my_module = app.Module("My module", vulnerabilities=vulnerabilities)
    assert my_module.non_dependency_security_rating() == returned_non_dependency_security_rating


@pytest.mark.parametrize(
    "returned_dependency_security_rating, vulnerabilities",
    [
        (app.Rating.A, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"}]),
        (app.Rating.A, [{"rule": "any", "severity": "BLOCKER"}]),
        (app.Rating.A, []),
        (app.Rating.B, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "MINOR"}]),
        (app.Rating.C, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "MAJOR"}]),
        (app.Rating.D, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "CRITICAL"}]),
        (app.Rating.D, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"},{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "CRITICAL"}]),
        (app.Rating.D, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "CRITICAL"},{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"}]),
        (app.Rating.E, [{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "BLOCKER"}]),
    ]
)
def test_module_should_provide_dependency_security_rating(returned_dependency_security_rating, vulnerabilities):
    my_module = app.Module("My module", vulnerabilities=vulnerabilities)
    assert my_module.dependency_security_rating() == returned_dependency_security_rating


def test_module_with_no_vulnerabilities_have_security_rating_not_calculated():
    my_module = app.Module("My module")
    assert my_module.non_dependency_security_rating() == app.Rating.NOT_CALCULATED
    assert my_module.dependency_security_rating() == app.Rating.NOT_CALCULATED


@pytest.mark.parametrize(
    "coverage",
    [
        0.0,
        18.2,
        95.4,
    ]
)
def test_module_should_have_provided_coverage(coverage):
    my_module = app.Module("My module", coverage=coverage)
    assert my_module.coverage == coverage


def test_module_with_no_coverage_have_a_coverage_of_zero():
    my_module = app.Module("My module")
    assert math.isclose(my_module.coverage, 0.0)


@pytest.mark.parametrize(
    "maintainability_rating",
    [
        app.Rating.A,
        app.Rating.B,
        app.Rating.C,
        app.Rating.D,
        app.Rating.E,
        app.Rating.NOT_CALCULATED
    ]
)
def test_module_should_have_provided_maintainability_rating(maintainability_rating):
    my_module = app.Module("My module", maintainability_rating=maintainability_rating)
    assert my_module.maintainability_rating == maintainability_rating


def test_module_with_no_maintainability_rating_have_a_maintainability_rating_not_calculated():
    my_module = app.Module("My module")
    assert my_module.maintainability_rating == app.Rating.NOT_CALCULATED
