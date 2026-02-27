# stratify-agent
Strategic reasoning agent for Microsoft Agents League 

# Resource requirement
Copilot Studio for agent creation

Azure subscription + resource group
Azure AI Search service
Azure Open AI service
    - One model deployment for embedding
    - One model deployment for chat completion
Azure Document Intelligence service
Azure Storage Account service
    - a container created under Azure Blob Storage

# Tool requirement for running solution locally
Visual Studio Code for development
Python 3.13.x for FastAPI development
Postman for calling FastAPI in local system
ngrok account setup
ngrok tunneling localhost so that Copilot Studio can access FastAPI running in localhost:8000

Some sample files to be uploaded in Azure Blob Container which will be ingested into Azure AI Search Index

# Ingestion process
To be written later

# Agent process flow architecture

![Tech Diagram](H:\Work\StratifyAgent\stratify-agent\Images)

![Memaid Diagram](stratify-agent\Images\Mermaid.png)

End user asks question about project requirement in Copilot Studio
Copilot Studio Orchestrator agent splits the query into two prompts - technology oriented and finance oriented
Orchestrator agent calls back end Fast API endpoint for both technology and finance
For both API calls, below steps are performed -
    Back end retrieval API accepts prompt and performs hybrid search against AI Search Index
    Top 5 chunks are retrieved and context is generated from the chunks
    Prompt + prompt type + chunks are sent to the LLM for answer generation
    LLM generated answer is passed through guardrail validation for hallucination check
        - LLM generated answer is split into atomic claims and compared with context
        - Based on the claims comparison, verdict and confidence score is generated
        - Finally actual answer, citations, verdict, confidence, issues are combined into a json
    Finally strutured Json is sent back to the Copilot with all details available
Copilot receives structured output for both technology and finance
Copilot performs parsing and displays comprehenseive analysis with all ddetails into an adaptive card to the end user