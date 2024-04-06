#!/bin/sh

/usr/bin/ollama serve & sleep 10 && uvicorn main:app --access-log --no-server-header --proxy-headers --host 0.0.0.0 --log-level info --port 8080
