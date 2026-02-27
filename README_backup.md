# stratify-agent

Strategic reasoning agent for Microsoft Agent League Hackathon.

This repository contains the backend services used by a Copilot Studio orchestrator agent. The Copilot asset will be exported and added to this repo separately. This README is designed so evaluators can set up all required Azure resources, run the FastAPI services locally, import the Copilot Studio agent, and test the full end-to-end flow.

## Solution overview

The solution provides project requirement analysis through two perspectives:
- Technology analysis
- Financial analysis

High-level flow:
1. End user asks a project requirement question in Copilot Studio.
2. Copilot Studio orchestrator splits the request into two tracks: technology and finance.
3. Copilot calls backend FastAPI endpoint for both tracks.
4. Backend performs hybrid retrieval (vector + semantic) on Azure AI Search.
5. Retrieved chunks are passed to Azure OpenAI for grounded answer generation.
6. A guardrail validation pass checks answer claims against retrieved context.
7. Backend returns structured JSON containing answer, citations, verdict, confidence, and issues.
8. Copilot combines both outputs and renders comprehensive results in an adaptive card.

## Repository structure

- `ingestion/`: Ingestion API to create/clear index and ingest blob documents into Azure AI Search.
- `retrieval/`: Retrieval API used by Copilot Studio for technology/finance responses.
- `demo-files/`: Sample documents for testing ingestion.

## Prerequisites

### Local tools
- Visual Studio Code
- Python 3.13.x
- Postman (or similar API client)
- ngrok account and CLI

### Azure services
Create resources in one Azure subscription/resource group:
- Azure AI Search
- Azure OpenAI
  - One embedding model deployment
  - One chat-completion model deployment
- Azure AI Document Intelligence
- Azure Storage Account
  - One Blob container for source files

## Step 1: Prepare Azure resources

### 1.1 Azure Storage
1. Create a blob container (for example `rag-inputs`).
2. Upload files from `demo-files/` or your own documents.

Supported file types by current ingestion code:
- `.pdf`
- `.docx`

### 1.2 Azure AI Search
1. Create an Azure AI Search service.
2. Note the endpoint and admin key.
3. Choose an index name (example: `stratify-index`).

Important:
- The ingestion API can create the index schema automatically using `POST /create-index`.
- The schema includes `embedding` vector dimension `1536`, so your embedding deployment must output 1536-dimensional vectors.

### 1.3 Azure OpenAI
1. Create Azure OpenAI resource.
2. Deploy one embedding model.
3. Deploy one chat completion model.
4. Capture endpoint, key, and deployment names.

### 1.4 Azure AI Document Intelligence
1. Create Document Intelligence resource.
2. Capture endpoint and key.
3. Model used by this project: `prebuilt-layout`.

## Step 2: Configure environment variables

Create `.env` files from examples.

### 2.1 Ingestion service env
From `ingestion/example_env.txt`, create `ingestion/.env`:

```env
AZURE_SEARCH_ENDPOINT=<your_search_endpoint>
AZURE_SEARCH_ADMIN_KEY=<your_search_key>
AZURE_SEARCH_INDEX=<your_index_name>

AZURE_OPENAI_ENDPOINT=<your_openai_endpoint>
AZURE_OPENAI_API_KEY=<your_openai_key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<your_deployed_model_for_embedding>
AZURE_OPENAI_MODEL_DEPLOYMENT=<your_deployed_model_for_chat_completion>

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=<your_di_endpoint>
AZURE_DOCUMENT_INTELLIGENCE_KEY=<your_di_key>
AZURE_DOCUMENT_INTELLIGENCE_MODEL=prebuilt-layout

AZURE_STORAGE_CONNECTION_STRING=<your_storage_account_connection_string>
AZURE_STORAGE_CONTAINER=<your_container>

DEFAULT_CHUNK_SIZE=1200
DEFAULT_CHUNK_OVERLAP=150
EMBEDDING_BATCH_SIZE=64
SEARCH_FILTER_BATCH_SIZE=50
SEARCH_BATCH_SIZE=200
```

### 2.2 Retrieval service env
From `retrieval/example_env.txt`, create `retrieval/.env`:

```env
AZURE_SEARCH_ENDPOINT=<your_search_endpoint>
AZURE_SEARCH_ADMIN_KEY=<your_search_key>
AZURE_SEARCH_INDEX=<your_index_name>

AZURE_OPENAI_ENDPOINT=<your_openai_endpoint>
AZURE_OPENAI_API_KEY=<your_openai_key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<your_deployed_model_for_embedding>
AZURE_OPENAI_MODEL_DEPLOYMENT=<your_deployed_model_for_chat_completion>
```

## Step 3: Run ingestion service locally

Open terminal in repo root:

```powershell
cd ingestion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

In another terminal (or Postman), call ingestion APIs.

### 3.1 Create search index

```http
POST http://localhost:8001/create-index
```

### 3.2 Run ingestion

```http
POST http://localhost:8001/ingest
```

What ingestion does:
- Reads files from Azure Blob container
- Parses documents with Document Intelligence
- Chunks content
- Summarizes table content into text rows
- Generates embeddings
- Removes older chunks for same `source_url`
- Uploads new chunks to Azure AI Search index

Optional maintenance endpoint:

```http
POST http://localhost:8001/clear-index
```

## Step 4: Run retrieval service locally

Open a new terminal in repo root:

```powershell
cd retrieval
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```http
GET http://localhost:8000/
```

Expected response:

```json
{"response":"hello world v2"}
```

## Step 5: Validate retrieval API with Postman

Endpoint:

```http
POST http://localhost:8000/get-response
Content-Type: application/json
```

Sample request:

```json
{
  "prompt": "Should we choose SaaS or open source for our AI chatbot platform?",
  "type": "technology"
}
```

`type` values:
- `technology`
- `finance`

Response shape:

```json
{
  "answer": "...",
  "citations": [
    {
      "title": "...",
      "source_url": "...",
      "chunk_id": "..."
    }
  ],
  "guardrail": {
    "verdict": "grounded | partially_grounded | not_grounded | unknown",
    "confidence": 0.0,
    "issues": [],
    "notes": null
  }
}
```

## Step 6: Expose retrieval API via ngrok

Copilot Studio needs a public callback URL to access your local FastAPI retrieval service.

Run:

```powershell
ngrok http 8000
```

Copy the HTTPS forwarding URL (example: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`).

You will use this URL in Copilot Studio action/plugin configuration that calls `/get-response`.

## Step 7: Import and configure Copilot Studio agent

The exported Copilot Studio agent package will be added to this repository.

After it is available:
1. Import the solution/package into your Copilot Studio environment.
2. Open the orchestrator agent.
3. Update backend action/plugin endpoint to your current ngrok HTTPS URL.
4. Ensure request mapping sends:
   - `prompt` (user question)
   - `type` (`technology` or `finance`)
5. Publish the agent.

## Step 8: End-to-end test flow

1. Confirm ingestion is completed successfully.
2. Confirm retrieval API responds in Postman.
3. Confirm ngrok tunnel is active and HTTPS URL is configured in Copilot.
4. Ask a project requirement question in Copilot chat.
5. Verify adaptive card shows:
   - technology analysis
   - finance analysis
   - grounded citations and guardrail details

## Troubleshooting

### Retrieval returns empty or "I do not know"
- Verify documents are ingested into the expected Azure Search index.
- Verify both services use same `AZURE_SEARCH_INDEX`.
- Check if question terms exist in uploaded documents.

### Index creation or ingestion fails
- Confirm Azure Search endpoint/admin key are correct.
- Confirm embedding deployment outputs 1536 dimensions.
- Check Blob container name and connection string.
- Verify Document Intelligence endpoint/key and supported file type.

### Copilot cannot call local API
- Check ngrok is running and URL is HTTPS.
- Verify Copilot action endpoint points to `/get-response`.
- Ensure retrieval API is running on local port `8000`.

### JSON parsing errors from model
- Ensure model deployment is correct and accessible.
- Keep prompts grounded in indexed context.
- Re-run request; transient model formatting issues can happen.

## Notes for hackathon evaluators

- Start with `demo-files/` for quick validation.
- Ingestion and retrieval are decoupled services; both must be configured.
- Copilot Studio package import is required for full orchestration UI experience.

## Current status

- FastAPI ingestion service: implemented
- FastAPI retrieval + guardrail service: implemented
- Copilot Studio export package: to be added in this repository
- This README: setup guide for local end-to-end testing
