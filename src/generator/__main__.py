#!/usr/bin/env python
"""This script is the entry point for the jenkinsfile generator module"""

import sys

from generator.main import main

if __name__ == "__main__":
    sys.exit(main())
