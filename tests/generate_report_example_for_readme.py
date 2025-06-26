# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import configparser
import logging

import requests_mock
from pdf2image import convert_from_path

from rte_sonar_reports import pdf
from rte_sonar_reports.loaders import ApplicationLoader
from rte_sonar_reports.sonar import MAINTAINABILITY_RATING_METRIC_KEY, \
    LINES_TO_COVER_METRIC_KEY, UNCOVERED_LINES_METRIC_KEY, CONDITIONS_TO_COVER_METRIC_KEY, \
    UNCOVERED_CONDITIONS_METRIC_KEY


@requests_mock.Mocker()
def example_report_generation_with_mocks(mocker):
    logging.basicConfig(level=logging.DEBUG)
    mocker.get("https://sonarcloud.io/api/measures/component?component=frontend",
               text=f"""{{
                                "component": {{
                                  "key": "frontend",
                                  "measures": [ {{
                                      "metric": "{LINES_TO_COVER_METRIC_KEY}",
                                      "value": "12500"
                                    }},
                                    {{
                                      "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                                      "value": "10250"
                                    }},
                                    {{
                                      "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                                      "value": "235"
                                    }},
                                    {{
                                      "metric": "{UNCOVERED_CONDITIONS_METRIC_KEY}",
                                      "value": "197"
                                    }},
                                    {{
                                      "metric": "{MAINTAINABILITY_RATING_METRIC_KEY}",
                                      "value": "1.0"
                                    }}
                                  ]
                                }}
                              }}
                              """)
    mocker.get("https://sonarcloud.io/api/issues/search?componentKeys=frontend",
                              text="""
                                  {
                                    "p": 1,
                                    "ps": 100,
                                    "total": 2,
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
                                  """)
    mocker.get("https://sonarcloud.io/api/measures/component?component=backend",
               text=f"""{{
                                "component": {{
                                  "key": "backend",
                                  "measures": [ {{
                                      "metric": "{LINES_TO_COVER_METRIC_KEY}",
                                      "value": "1250"
                                    }},
                                    {{
                                      "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                                      "value": "100"
                                    }},
                                    {{
                                      "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                                      "value": "25"
                                    }},
                                    {{
                                      "metric": "{UNCOVERED_CONDITIONS_METRIC_KEY}",
                                      "value": "7"
                                    }},
                                    {{
                                      "metric": "{MAINTAINABILITY_RATING_METRIC_KEY}",
                                      "value": "2.0"
                                    }}
                                  ]
                                }}
                              }}
                              """)
    mocker.get("https://sonarcloud.io/api/issues/search?componentKeys=backend",
                              text="""
                                  {
                                    "p": 1,
                                    "ps": 100,
                                    "total": 1,
                                    "issues": [{
                                        "rule":"any",
                                        "severity":"INFO",
                                        "status":"OPEN","message":"Filename: ...",
                                        "type":"VULNERABILITY"
                                        }]
                                  }
                                  """)
    mocker.get("https://my.sonarqube.instance/api/measures/component?component=backend",
               text=f"""{{
                                "component": {{
                                  "key": "backend",
                                  "measures": [ {{
                                      "metric": "{LINES_TO_COVER_METRIC_KEY}",
                                      "value": "1500"
                                    }},
                                    {{
                                      "metric": "{UNCOVERED_LINES_METRIC_KEY}",
                                      "value": "10"
                                    }},
                                    {{
                                      "metric": "{CONDITIONS_TO_COVER_METRIC_KEY}",
                                      "value": "235"
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
    mocker.get("https://my.sonarqube.instance/api/issues/search?componentKeys=backend",
                              text="""
                                  {
                                    "p": 1,
                                    "ps": 100,
                                    "total": 0,
                                    "issues": []
                                  }
                                  """)
    mocker.get("https://my.sonarqube.instance/api/measures/component?component=other",
               text="""{
                        "component": {
                          "key": "other",
                          "measures": []
                        }
                      }
                      """)
    mocker.get("https://my.sonarqube.instance/api/issues/search?componentKeys=other",
                              text="""
                                  {
                                    "p": 1,
                                    "ps": 100,
                                    "total": 0,
                                    "issues": []
                                  }
                                  """)
    sonar_configs = configparser.ConfigParser()
    sonar_configs.read("sonar_config_example.ini")
    app = ApplicationLoader(sonar_configs).load_file("application_description_example.yml")
    pdf.export("report_example.pdf", app)
    images = convert_from_path("report_example.pdf", size=(1000, None))
    images[0].save("report_example.png")


if __name__ == '__main__':
    example_report_generation_with_mocks()
