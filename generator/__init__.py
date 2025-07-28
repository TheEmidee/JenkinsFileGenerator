#!/usr/bin/env python

"""This module initializes the Jenkinsfile generator package."""
import logging

logger = logging.getLogger("jenkinsfile_generator")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.propagate = False
