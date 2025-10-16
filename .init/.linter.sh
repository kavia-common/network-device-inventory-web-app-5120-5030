#!/bin/bash
cd /home/kavia/workspace/code-generation/network-device-inventory-web-app-5120-5030/FlaskBackendAPI
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

