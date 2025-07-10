# Makefile for Azure AgentOps

run:
	streamlit run main.py

build:
	az acr build --registry $(REGISTRY_NAME) --image azure-agentops:latest .

deploy:
	az containerapp create \
		--name azure-agentops \
		--resource-group $(RESOURCE_GROUP) \
		--environment $(ENVIRONMENT_NAME) \
		--image $(REGISTRY_NAME).azurecr.io/azure-agentops:latest \
		--target-port 8501 \
		--ingress external

setup:
	pip install -r requirements.txt

azure-setup:
	az group create --name $(RESOURCE_GROUP) --location $(LOCATION)
	az acr create --resource-group $(RESOURCE_GROUP) --name $(REGISTRY_NAME) --sku Basic
	az cosmosdb create --name $(COSMOS_NAME) --resource-group $(RESOURCE_GROUP)
	az cognitiveservices account create --name $(OPENAI_NAME) --resource-group $(RESOURCE_GROUP) --kind OpenAI --sku S0 --location $(LOCATION)

# Default values
RESOURCE_GROUP ?= agentops-rg
LOCATION ?= eastus
REGISTRY_NAME ?= agentopsregistry
COSMOS_NAME ?= agentops-cosmos
OPENAI_NAME ?= agentops-openai
ENVIRONMENT_NAME ?= agentops-env