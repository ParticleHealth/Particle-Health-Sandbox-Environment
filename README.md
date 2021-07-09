# Particle Health Sandbox

 This GitHub Repository is published as a part of the ONC's Synthetic Health Data Challenge.  This includes a Synthea synthetic patient population generator that outputs point-in-time CCDA files with in-document provider notes, as well as stores the original
 Synthea CCDA, FHIR, and Note files for reference.  A CSV for Validation results as well as population demographics will also be output to the resulting folder.   

## Requirements:

 - brew install jenv
 - os.system('brew install jenv')
 - os.system('jenv local 1.8')

## Open Source Tools and Libraries Used:

Tools and Languages:
 - Python 3.8.3
 - jenv 1.8
 - Synthea (latest release)
 - HealthIT.gov’s open source CCDA 2.0 scorecard API (For Validation)

Python Libraries:
 - import os
 - import argparse
 - import sys
 - from difflib import get_close_matches
 - import re
 - import shutil
 - from shutil import copyfile
 - from datetime import date
 - import pandas as pd
 - import json
 - import requests
 - import urllib3
 - import jinja2
 - from jinja2 import Environment
 - from jinja2 import FileSystemLoader
 - from lxml import etree
 - from io import StringIO, BytesIO
 - import csv
 - import string

## Usage:

Ensure you are working in the 'synthea-master' directory

Run:

```
python Synthea_Runner.py --condition {condition_of_interest} --num-patients {population}
```

Entry options for condition_of_interest include: ['covid19', 'diabetes', 'lung cancer', 'opioid addiction']

Recommended entry options for population are any numerical value 1 - 5000

Example:

```
  python Synthea_Runner.py --condition 'diabetes' --num-patients 50
```

## Output:

A folder names with the condition specified, as well as the date of generation will be output

- Example output folder:  'diabetes_output_2021-07-07'

The following sub-directories and files will be contained:

1. generator_output: (main)
  * contains output point-in-time CCDA files with in-document provider notes
2. synthea_ccda:
  * contains original synthea CCDA documents for reference
3. synthea_fhir:
  * contains original synthea FHIR documents for reference
4. synthea_notes:
 * contains original synthea txt note files for reference
5. output_directory.csv:
 * CSV file containing demographics of the population created
6. validation_results.csv:
 * CSV file containing the validation results for each point-in-time document generated (from HealthIT.gov’s open source CCDA 2.0 scorecard API)
