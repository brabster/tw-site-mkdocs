#!/bin/bash

set -euo pipefail


BASEDIR=$(dirname "$0")
TEMP_REQS=${BASEDIR}/requirements.deploy.txt

echo "Setting up deploy requirements.txt"
grep -v mkdocs-material ${BASEDIR}/requirements.txt > ${TEMP_REQS}
echo "git+https://${GH_TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git[imaging]" >> ${TEMP_REQS}
mv ${TEMP_REQS} ${BASEDIR}/requirements.txt

echo "cat ${BASEDIR}/requirements.txt..."
cat ${BASEDIR}/requirements.txt
