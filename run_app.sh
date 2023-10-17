#!/usr/bin/env bash

python download-data.py
panel serve panels-app.py --log-level trace --warm 