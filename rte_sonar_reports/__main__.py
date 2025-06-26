# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import configparser
import logging
import os.path

from rte_sonar_reports import pdf
from rte_sonar_reports.loaders import ApplicationLoader

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO").upper())
    parser = argparse.ArgumentParser(
        prog="RTE Sonar report generator",
        description="""Generate PDF reports used as requirements for deployment
        of an application in RTE production environments.""",
    )
    parser.add_argument("-a", "--application", required=True, help="Application description YAML file")
    parser.add_argument("-c", "--config", required=True, help="Sonar server configuration INI file")
    parser.add_argument("-o", "--output", required=True, help="Output PDF file")
    args = parser.parse_args()

    application_file_path = os.path.abspath(args.application)
    config_file_path = os.path.abspath(args.config)
    output_file_path = os.path.abspath(args.output)

    LOGGER.info(f"Generating Sonar report based on application description file '{application_file_path}'")
    LOGGER.info(f"Sonar configuration used define in file '{config_file_path}'")
    LOGGER.info(f"Output report will be exported in file '{output_file_path}'")

    sonar_configs = configparser.ConfigParser()
    sonar_configs.read(config_file_path)
    application = ApplicationLoader(sonar_configs).load_file(application_file_path)
    pdf.export(output_file_path, application)


if __name__ == '__main__':
    main()
