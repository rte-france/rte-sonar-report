# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import configparser

import pytest

from rte_sonar_reports.app import Rating, Module
from rte_sonar_reports.loaders import ApplicationLoader
from rte_sonar_reports.sonar import SonarClient, \
    MAINTAINABILITY_RATING_METRIC_KEY, LINES_TO_COVER_METRIC_KEY, \
    UNCOVERED_LINES_METRIC_KEY, CONDITIONS_TO_COVER_METRIC_KEY, \
    UNCOVERED_CONDITIONS_METRIC_KEY

FAKE_SONAR_CONFIG = {"base_url": "https://my-sonar-test-url.com",
                     "token": "my_sonar_token"}


@pytest.mark.parametrize(
    "lines_to_cover_from_api, uncovered_lines_from_api, conditions_to_cover_from_api, uncovered_conditions_from_api",
    [
        (0, 0, 0, 0),
        (50, 0, 10, 0),
        (50, 24, 10, 3),
    ]
)
def test_sonar_get_coverage_for_module(requests_mock, lines_to_cover_from_api, uncovered_lines_from_api, conditions_to_cover_from_api, uncovered_conditions_from_api):
    project_key = "my_project_key"
    requests_mock.get(FAKE_SONAR_CONFIG["base_url"] + "/api/project_branches/list?project=my_project_key",
                      text="""
                      {
                        "branches": [
                          {
                            "name": "main",
                            "isMain": true
                          }
                        ]
                      }
                      """)
    requests_mock.get(FAKE_SONAR_CONFIG["base_url"] + "/api/measures/component",
                      text=f"""
                      {{
                        "component": {{
                          "key": "{project_key}",
                          "measures": [
                            {{
                              "metric": "{LINES_TO_COVER_METRIC_KEY}",
                              "value": "{lines_to_cover_from_api}"
                            }},
                            {{
                              "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                              "value": "{uncovered_lines_from_api}"
                            }},
                            {{
                              "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                              "value": "{conditions_to_cover_from_api}"
                            }},
                            {{
                              "metric": "{UNCOVERED_CONDITIONS_METRIC_KEY}",
                              "value": "{uncovered_conditions_from_api}"
                            }}
                          ]
                        }}
                      }}
                      """)
    indicators = SonarClient(FAKE_SONAR_CONFIG).get_all_indicators(project_key, None)
    assert indicators[LINES_TO_COVER_METRIC_KEY] == lines_to_cover_from_api
    assert indicators[UNCOVERED_LINES_METRIC_KEY] == uncovered_lines_from_api
    assert indicators[CONDITIONS_TO_COVER_METRIC_KEY] == conditions_to_cover_from_api
    assert indicators[UNCOVERED_CONDITIONS_METRIC_KEY] == uncovered_conditions_from_api


@pytest.mark.parametrize(
    "rating_value_from_api, rating",
    [
        ("1.0", Rating.A),
        ("2.0", Rating.B),
        ("3.0", Rating.C),
        ("4.0", Rating.D),
        ("5.0", Rating.E)
    ]
)
def test_sonar_get_maintainability_rating_for_module(requests_mock, rating_value_from_api, rating):
    project_key = "my_project_key"
    requests_mock.get(FAKE_SONAR_CONFIG["base_url"] + "/api/project_branches/list?project=my_project_key",
                      text="""
                      {
                        "branches": [
                          {
                            "name": "main",
                            "isMain": true
                          }
                        ]
                      }
                      """)
    requests_mock.get(FAKE_SONAR_CONFIG["base_url"] + "/api/measures/component",
                      text=f"""
                      {{
                        "component": {{
                          "key": "{project_key}",
                          "measures": [
                            {{
                              "metric": "{MAINTAINABILITY_RATING_METRIC_KEY}",
                              "value": "{rating_value_from_api}"
                            }}
                          ]
                        }}
                      }}
                      """)
    indicators = SonarClient(FAKE_SONAR_CONFIG).get_all_indicators(project_key, None)
    assert indicators[MAINTAINABILITY_RATING_METRIC_KEY] == rating


def test_application_loading_with_sonar_configuration(requests_mock):
    sonar_configs = configparser.ConfigParser()
    sonar_configs.read_string("""
        [Sonar config 1]
        base_url = https://my-sonar-test-url-v1.com
        token = my_sonar_token_v1
        
        [Sonar config 2]
        base_url = https://my-sonar-test-url-v2.com
        token = my_sonar_token_v2
        """)
    requests_mock.get("https://my-sonar-test-url-v1.com/api/project_branches/list?project=frontend_module",
                      text="""
                      {
                        "branches": [
                          {
                            "name": "main",
                            "isMain": true
                          }
                        ]
                      }
                      """)
    requests_mock.get("https://my-sonar-test-url-v1.com/api/measures/component",
                      text=f"""{{
                            "component": {{
                              "key": "frontend_module",
                              "measures": [ {{
                                  "metric": "{LINES_TO_COVER_METRIC_KEY}",
                                  "value": "225"
                                }},
                                {{
                                  "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                                  "value": "10"
                                }},
                                {{
                                  "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                                  "value": "47"
                                }},
                                {{
                                  "metric": "{UNCOVERED_CONDITIONS_METRIC_KEY}",
                                  "value": "10"
                                }},
                                {{
                                  "metric": "{MAINTAINABILITY_RATING_METRIC_KEY}",
                                  "value": "2.0"
                                }}
                              ]
                            }}
                          }}
                          """)
    requests_mock.get("https://my-sonar-test-url-v1.com/api/issues/search",
                      text="""{
                                "p": 1,
                                "ps": 100,
                                "total": 1,
                                "issues": [{
                                    "rule":"OWASP:UsingComponentWithKnownVulnerability",
                                    "severity":"BLOCKER",
                                    "status":"OPEN","message":"Filename: ...",
                                    "type":"VULNERABILITY"
                                    }]
                                }
                          """)
    requests_mock.get("https://my-sonar-test-url-v2.com/api/project_branches/list?project=backend_module",
                      text="""
                      {
                        "branches": [
                          {
                            "name": "main",
                            "isMain": true
                          }
                        ]
                      }
                      """)
    requests_mock.get("https://my-sonar-test-url-v2.com/api/measures/component",
                      text=f"""{{
                            "component": {{
                              "key": "backend_module",
                              "measures": [ {{
                                  "metric": "{LINES_TO_COVER_METRIC_KEY}",
                                  "value": "2524"
                                }},
                                {{
                                  "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                                  "value": "2007"
                                }},
                                {{
                                  "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                                  "value": "265"
                                }},
                                {{
                                  "metric": "{UNCOVERED_CONDITIONS_METRIC_KEY}",
                                  "value": "224"
                                }},
                                {{
                                  "metric": "{MAINTAINABILITY_RATING_METRIC_KEY}",
                                  "value": "3.0"
                                }}
                              ]
                            }}
                          }}
                          """)
    requests_mock.get("https://my-sonar-test-url-v2.com/api/issues/search",
                      text="""{
                                "p": 1,
                                "ps": 100,
                                "total": 1,
                                "issues": [{
                                    "rule":"any",
                                    "severity":"MINOR",
                                    "status":"OPEN","message":"Filename: ...",
                                    "type":"VULNERABILITY"
                                    }]
                                }
                          """)
    app = ApplicationLoader(sonar_configs).load("""
        application:
          name: My complete test application
          version: 1.0.0
          modules:
            - name: Frontend module
              project_key: frontend_module
              sonar_config: Sonar config 1
              type: frontend
            - name: Backend module
              project_key: backend_module
              sonar_config: Sonar config 2
              type: backend
        """)
    assert app.name == "My complete test application"
    assert app.version == "1.0.0"
    assert len(app.modules) == 2
    assert app.modules[0].name == "Frontend module"
    assert app.modules[0].module_type == Module.Type.FRONTEND
    assert app.modules[0].non_dependency_security_rating() == Rating.A
    assert app.modules[0].dependency_security_rating() == Rating.E
    assert app.modules[0].lines_to_cover == 225
    assert app.modules[0].uncovered_lines == 10
    assert app.modules[0].conditions_to_cover == 47
    assert app.modules[0].uncovered_conditions == 10
    assert app.modules[0].maintainability_rating == Rating.B
    assert app.modules[1].name == "Backend module"
    assert app.modules[1].module_type == Module.Type.BACKEND
    assert app.modules[1].non_dependency_security_rating() == Rating.B
    assert app.modules[1].dependency_security_rating() == Rating.A
    assert app.modules[1].lines_to_cover == 2524
    assert app.modules[1].uncovered_lines == 2007
    assert app.modules[1].conditions_to_cover == 265
    assert app.modules[1].uncovered_conditions == 224
    assert app.modules[1].maintainability_rating == Rating.C



def test_sonar_get_all_vulnerabilities_with_multiple_pages(requests_mock):
    project_key = "my_project_key"
    requests_mock.get(FAKE_SONAR_CONFIG["base_url"] + "/api/project_branches/list?project=my_project_key",
                      text="""
                      {
                        "branches": [
                          {
                            "name": "main",
                            "isMain": true
                          }
                        ]
                      }
                      """)
    requests_mock.register_uri("GET", FAKE_SONAR_CONFIG["base_url"] + "/api/issues/search",
                               [
                                   {"text": """
                                      {
                                        "p": 1,
                                        "ps": 2,
                                        "total": 3,
                                        "issues": [{
                                            "rule":"OWASP:UsingComponentWithKnownVulnerability",
                                            "severity":"CRITICAL",
                                            "status":"OPEN","message":"Filename: ...",
                                            "type":"VULNERABILITY"
                                            },{
                                            "rule":"any",
                                            "severity":"MINOR",
                                            "status":"OPEN","message":"Filename: ...",
                                            "type":"VULNERABILITY"
                                            }]
                                        }
                                      """
                                    },
                                   {"text": """
                                      {
                                        "p": 2,
                                        "ps": 2,
                                        "total": 3,
                                        "issues": [{
                                            "rule":"OWASP:UsingComponentWithKnownVulnerability",
                                            "severity":"INFO",
                                            "status":"OPEN","message":"Filename: ...",
                                            "type":"VULNERABILITY"
                                            }]
                                        }
                                      """}])
    all_sorted_vulnerabilities = SonarClient(FAKE_SONAR_CONFIG).get_all_vulnerabilities_sorted(project_key, None)
    assert len(all_sorted_vulnerabilities) == 3