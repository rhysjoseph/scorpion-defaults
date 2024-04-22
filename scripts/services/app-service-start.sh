#!/bin/bash
cd {{HOME}}/ct-flows
source .venv/bin/activate
streamlit run {{HOME}}/ct-flows/src/app.py --server.port=8501 --server.address=localhost