# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import math

import pytest
from jsonschema.exceptions import ValidationError

from rte_sonar_reports.loaders import ApplicationLoader
from rte_sonar_reports.app import Module, Rating


def test_loading_fails_in_case_of_empty_application():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("")


def test_loading_fails_in_case_of_application_without_name():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("""
        application:
          version: 1.0.0
          modules:
        """)


def test_loading_fails_in_case_of_application_without_version():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("""
        application:
          name: My test application
          modules:
        """)


def test_loading_fails_in_case_of_module_without_name():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("""
        application:
          name: My test application
          version: 1.0.0
          modules:
            - type: backend
        """)


def test_loading_application_with_no_module():
    app = ApplicationLoader({}).load("""
    application:
      name: My test application with no modules
      version: 1.0.0
    """)
    assert app.name == "My test application with no modules"
    assert app.version == "1.0.0"


def test_loading_application_should_fail_when_no_module_but_property_defined():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("""
        application:
          name: My test application with no modules
          version: 1.0.0
          modules:
        """)


def test_loading_application_should_fail_when_invalid_module_type_provided():
    with pytest.raises(ValidationError):
        ApplicationLoader({}).load("""
        application:
          name: My test application with one module
          version: 2.0.0
          modules:
            - name: Only frontend module
              type: unknown
        """)


def test_loading_application_with_one_module():
    app = ApplicationLoader({}).load("""
    application:
      name: My test application with one module
      version: 2.0.0
      modules:
        - name: Only frontend module
          type: frontend
          project_key: project key
          sonar_config: sonar config
    """)
    assert app.name == "My test application with one module"
    assert app.version == "2.0.0"
    assert len(app.modules) == 1
    assert app.modules[0].name == "Only frontend module"
    assert app.modules[0].module_type == Module.Type.FRONTEND


def test_loading_application_with_one_module_with_unprovided_sonar_config_returns_default_values():
    app = ApplicationLoader({}).load("""
    application:
      name: My test application with one module
      version: 2.0.0
      modules:
        - name: Only module
          type: frontend
          project_key: project key
          sonar_config: sonar config
    """)
    assert app.name == "My test application with one module"
    assert app.version == "2.0.0"
    assert len(app.modules) == 1
    assert app.modules[0].name == "Only module"
    assert app.modules[0].module_type == Module.Type.FRONTEND
    assert app.modules[0].non_dependency_security_rating() == Rating.NOT_CALCULATED
    assert app.modules[0].dependency_security_rating() == Rating.NOT_CALCULATED
    assert math.isclose(app.modules[0].coverage, 0.0)
    assert app.modules[0].maintainability_rating == Rating.NOT_CALCULATED


def test_loading_application_without_branch_returns_default_branch():
    app = ApplicationLoader({}).load("""
    application:
      name: My test application with one module
      version: 2.0.0
      modules:
        - name: Only module
          type: frontend
          project_key: project key
          sonar_config: sonar config
    """)
    assert app.name == "My test application with one module"
    assert app.version == "2.0.0"
    assert len(app.modules) == 1
    assert app.modules[0].name == "Only module"
    assert app.modules[0].module_type == Module.Type.FRONTEND
    assert app.modules[0].non_dependency_security_rating() == Rating.NOT_CALCULATED
    assert app.modules[0].dependency_security_rating() == Rating.NOT_CALCULATED
    assert math.isclose(app.modules[0].coverage, 0.0)
    assert app.modules[0].maintainability_rating == Rating.NOT_CALCULATED
    assert app.modules[0].branch_name is None


def test_loading_complete_application():
    app = ApplicationLoader({}).load("""
    application:
      name: My complete test application
      version: 1.0.0
      modules:
        - name: Frontend module
          sonar_config: SonarCloud
          project_key: frontend
          branch: main
          type: frontend
        - name: First backend module
          sonar_config: SonarCloud
          project_key: backend
          branch: main
          type: backend
        - name: Second backend module
          sonar_config: SonarQube
          project_key: backend
          branch: v1.2
          type: backend
        - name: Other module
          sonar_config: SonarQube
          project_key: other
          branch: main
          type: other
    """)
    assert app.name == "My complete test application"
    assert app.version == "1.0.0"
    assert len(app.modules) == 4
    assert app.modules[0].name == "Frontend module"
    assert app.modules[0].module_type == Module.Type.FRONTEND
    assert app.modules[0].branch_name == "main"
    assert app.modules[1].name == "First backend module"
    assert app.modules[1].module_type == Module.Type.BACKEND
    assert app.modules[1].branch_name == "main"
    assert app.modules[2].name == "Second backend module"
    assert app.modules[2].module_type == Module.Type.BACKEND
    assert app.modules[2].branch_name == "v1.2"
    assert app.modules[3].name == "Other module"
    assert app.modules[3].module_type == Module.Type.OTHER
    assert app.modules[3].branch_name == "main"
