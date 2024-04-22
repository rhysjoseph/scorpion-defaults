#!/bin/bash
cd /home/cmxeon/ct-flows
source .venv/bin/activate
nohup streamlit run /home/cmxeon/ct-flows/src/app.py --server.port=8501 --server.address=localhost