# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from enum import Enum
from ordered_enum import OrderedEnum

ISSUES_RULE_KEY = "rule"
ISSUES_SEVERITY_KEY = "severity"
DEPENDENCY_VULNERABILITY_RULE = "OWASP:UsingComponentWithKnownVulnerability"


def calculate_coverage_in_percent(lines_to_cover, uncovered_lines, conditions_to_cover, uncovered_conditions):
    calculated_coverage_in_pu = 1 - (uncovered_lines + uncovered_conditions) / (lines_to_cover + conditions_to_cover)
    return round(100 * calculated_coverage_in_pu, 1)


class Rating(OrderedEnum):
    NOT_CALCULATED = 0
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5


class Application:
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.modules = []

    def add_module(self, module):
        self.modules.append(module)

    def worst_non_dependency_security_rating(self):
        return max([module.non_dependency_security_rating() for module in self.modules])

    def worst_dependency_security_rating(self):
        return max([module.dependency_security_rating() for module in self.modules])

    def worst_maintainability_rating(self):
        return max([module.maintainability_rating for module in self.modules])

    def aggregated_backend_coverage(self):
        backend_modules = [module for module in self.modules if module.module_type == Module.Type.BACKEND]
        lines_to_cover = sum([backend_module.lines_to_cover for backend_module in backend_modules])
        uncovered_lines = sum([backend_module.uncovered_lines for backend_module in backend_modules])
        conditions_to_cover = sum([backend_module.conditions_to_cover for backend_module in backend_modules])
        uncovered_conditions = sum([backend_module.uncovered_conditions for backend_module in backend_modules])
        if lines_to_cover + conditions_to_cover == 0:
            return None
        return calculate_coverage_in_percent(lines_to_cover, uncovered_lines, conditions_to_cover, uncovered_conditions)


def rating_from_vulnerability(vulnerability):
    severity = vulnerability[ISSUES_SEVERITY_KEY]
    if severity == "INFO":
        return Rating.A
    elif severity == "MINOR":
        return Rating.B
    elif severity == "MAJOR":
        return Rating.C
    elif severity == "CRITICAL":
        return Rating.D
    elif severity == "BLOCKER":
        return Rating.E
    else:
        return Rating.A


class Module:

    class Type(Enum):
        BACKEND = 0
        FRONTEND = 1
        OTHER = 2

    def __init__(self, name, branch_name=None, module_type=Type.OTHER,
                 coverage=0,
                 maintainability_rating=Rating.NOT_CALCULATED,
                 lines_to_cover=0,
                 uncovered_lines=0,
                 conditions_to_cover=0,
                 uncovered_conditions=0,
                 vulnerabilities=None):
        self.module_type = module_type
        self.name = name
        self.branch_name = branch_name
        self.coverage = coverage
        self.maintainability_rating = maintainability_rating
        self.lines_to_cover = lines_to_cover
        self.uncovered_lines = uncovered_lines
        self.conditions_to_cover = conditions_to_cover
        self.uncovered_conditions = uncovered_conditions
        self.vulnerabilities = vulnerabilities

    def non_dependency_security_rating(self):
        if self.vulnerabilities is None:
            return Rating.NOT_CALCULATED
        non_dependency_vulnerabilities_rating = [rating_from_vulnerability(vulnerability) for vulnerability in self.vulnerabilities if
                                                 vulnerability[ISSUES_RULE_KEY] != DEPENDENCY_VULNERABILITY_RULE]
        if not non_dependency_vulnerabilities_rating:
            return Rating.A
        return max(non_dependency_vulnerabilities_rating)

    def dependency_security_rating(self):
        if self.vulnerabilities is None:
            return Rating.NOT_CALCULATED
        dependency_vulnerabilities_rating = [rating_from_vulnerability(vulnerability) for vulnerability in self.vulnerabilities if
                                             vulnerability[ISSUES_RULE_KEY] == DEPENDENCY_VULNERABILITY_RULE]
        if not dependency_vulnerabilities_rating:
            return Rating.A
        return max(dependency_vulnerabilities_rating)

    def calculated_coverage(self):
        if self.lines_to_cover + self.conditions_to_cover == 0:
            return None
        return calculate_coverage_in_percent(self.lines_to_cover, self.uncovered_lines, self.conditions_to_cover, self.uncovered_conditions)