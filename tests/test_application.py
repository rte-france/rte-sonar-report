# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

from rte_sonar_reports.app import Application, Module, Rating, DEPENDENCY_VULNERABILITY_RULE

TEST_APPLICATION_NAME = "My application"
TEST_APPLICATION_VERSION = "Version"


def test_application_should_have_a_name():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    assert my_application.name == TEST_APPLICATION_NAME


def test_application_may_have_only_one_module():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Module 1"))
    assert len(my_application.modules) == 1


def test_application_may_have_multiple_modules():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Module 1"))
    my_application.add_module(Module("Module 2"))
    my_application.add_module(Module("Module 3"))
    assert len(my_application.modules) == 3


def test_application_worst_non_dependency_security_rating_is_the_worse_of_its_modules_first_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1", vulnerabilities=[{"rule": "any", "severity": "MINOR"}]))
    my_application.add_module(Module("Backend 2", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(Module("Backend 4", vulnerabilities=[{"rule": "any", "severity": "CRITICAL"}]))
    assert my_application.worst_non_dependency_security_rating() == Rating.D


def test_application_worst_non_dependency_security_rating_is_the_worse_of_its_modules_second_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1", vulnerabilities=[{"rule": "any", "severity": "MINOR"}]))
    my_application.add_module(Module("Backend 2", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(Module("Backend 4", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    assert my_application.worst_non_dependency_security_rating() == Rating.B


def test_application_worst_dependency_security_rating_is_the_worse_of_its_modules_first_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(
        Module("Backend 1", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "MINOR"}]))
    my_application.add_module(
        Module("Backend 2", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(
        Module("Backend 4", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "CRITICAL"}]))
    assert my_application.worst_dependency_security_rating() == Rating.D


def test_application_worst_dependency_security_rating_is_the_worse_of_its_modules_second_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(
        Module("Backend 1", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "MINOR"}]))
    my_application.add_module(
        Module("Backend 2", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(
        Module("Backend 4", vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"}]))
    assert my_application.worst_dependency_security_rating() == Rating.B


def test_application_worst_non_dependency_security_rating_does_ignore_dependency_security():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1",
                                     vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "BLOCKER"},
                                                      {"rule": "any", "severity": "MINOR"}]))
    my_application.add_module(Module("Backend 2", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(Module("Backend 4", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    assert my_application.worst_non_dependency_security_rating() == Rating.B


def test_application_worst_dependency_security_rating_does_ignore_non_dependency_security():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1",
                                     vulnerabilities=[{"rule": DEPENDENCY_VULNERABILITY_RULE, "severity": "INFO"},
                                                      {"rule": "any", "severity": "MINOR"}]))
    my_application.add_module(Module("Backend 2", vulnerabilities=[{"rule": "any", "severity": "INFO"}]))
    my_application.add_module(Module("Backend 3", vulnerabilities=[]))
    my_application.add_module(Module("Backend 4", vulnerabilities=[{"rule": "any", "severity": "CRITICAL"}]))
    assert my_application.worst_dependency_security_rating() == Rating.A


def test_application_aggregated_backend_coverage_is_calculated_correctly_based_of_coverage_data_from_modules():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(
        Module("Backend 1", module_type=Module.Type.BACKEND, lines_to_cover=50, uncovered_lines=17,
               conditions_to_cover=10, uncovered_conditions=1))
    my_application.add_module(
        Module("Backend 2", module_type=Module.Type.BACKEND, lines_to_cover=150, uncovered_lines=0,
               conditions_to_cover=19, uncovered_conditions=0))
    my_application.add_module(
        Module("Backend 3", module_type=Module.Type.BACKEND, lines_to_cover=0, uncovered_lines=0, conditions_to_cover=0,
               uncovered_conditions=0))
    my_application.add_module(
        Module("Backend 4", module_type=Module.Type.BACKEND, lines_to_cover=2500, uncovered_lines=154,
               conditions_to_cover=1028, uncovered_conditions=542))
    assert math.isclose(my_application.aggregated_backend_coverage(), 81.0)


def test_application_aggregated_backend_coverage_is_only_based_on_backend_modules():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(
        Module("Backend 1", module_type=Module.Type.BACKEND, lines_to_cover=50, uncovered_lines=17,
               conditions_to_cover=10, uncovered_conditions=1))
    my_application.add_module(
        Module("Backend 2", module_type=Module.Type.BACKEND, lines_to_cover=150, uncovered_lines=0,
               conditions_to_cover=19, uncovered_conditions=0))
    my_application.add_module(
        Module("Backend 3", module_type=Module.Type.BACKEND, lines_to_cover=0, uncovered_lines=0, conditions_to_cover=0,
               uncovered_conditions=0))
    my_application.add_module(
        Module("Backend 4", module_type=Module.Type.BACKEND, lines_to_cover=2500, uncovered_lines=154,
               conditions_to_cover=1028, uncovered_conditions=542))
    my_application.add_module(
        Module("Frontend", module_type=Module.Type.FRONTEND, lines_to_cover=125786, uncovered_lines=125786,
               conditions_to_cover=5786, uncovered_conditions=5786))
    my_application.add_module(
        Module("Other", module_type=Module.Type.OTHER, lines_to_cover=0, uncovered_lines=0, conditions_to_cover=0,
               uncovered_conditions=0))
    assert math.isclose(my_application.aggregated_backend_coverage(), 81.0)


def test_application_aggregated_backend_coverage_when_no_backend_modules():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Frontend", module_type=Module.Type.FRONTEND, coverage=0.0))
    my_application.add_module(Module("Other", module_type=Module.Type.OTHER, coverage=10.0))
    assert my_application.aggregated_backend_coverage() == None


def test_application_worst_maintainability_rating_is_the_worse_of_its_modules_first_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1", maintainability_rating=Rating.B))
    my_application.add_module(Module("Backend 2", maintainability_rating=Rating.A))
    my_application.add_module(Module("Backend 3", maintainability_rating=Rating.NOT_CALCULATED))
    my_application.add_module(Module("Backend 4", maintainability_rating=Rating.D))
    assert my_application.worst_maintainability_rating() == Rating.D


def test_application_worst_maintainability_rating_is_the_worse_of_its_modules_second_example():
    my_application = Application(TEST_APPLICATION_NAME, TEST_APPLICATION_VERSION)
    my_application.add_module(Module("Backend 1", maintainability_rating=Rating.B))
    my_application.add_module(Module("Backend 2", maintainability_rating=Rating.A))
    my_application.add_module(Module("Backend 3", maintainability_rating=Rating.NOT_CALCULATED))
    my_application.add_module(Module("Backend 4", maintainability_rating=Rating.A))
    assert my_application.worst_maintainability_rating() == Rating.B
