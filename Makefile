# Makefile

run:
	streamlit run main.py

deploy:
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/agentops
	gcloud run deploy agentops --image gcr.io/$(PROJECT_ID)/agentops --platform managed --region $(REGION) --allow-unauthenticated

setup:
	pip install -r requirements.txt