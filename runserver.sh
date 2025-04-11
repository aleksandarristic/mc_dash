#!/bin/bash

source ~/mc_dash/.venv/bin/activate
cd ~/mc_dash
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
