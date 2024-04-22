#!/bin/bash
cd /home/{{USER}}/{{REPO_NAME}}
source .venv/bin/activate
nohup streamlit run /home/{{USER}}/{{REPO_NAME}}/src/app.py --server.port=8501 --server.address=0.0.0.0