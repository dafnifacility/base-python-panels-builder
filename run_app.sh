#!/usr/bin/env bash

python download-data.py
panel serve panels-app.py --autoreload --show --port=3000