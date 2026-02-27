# Stratify AI Agent

Stratify AI is a project-requirement analysis assistant. It helps teams strategically evaluate solution options from two critical dimensions at the same time: technical feasibility and financial impact.

Given a user query, the Copilot Studio orchestrator decomposes it into technology and finance prompts, calls backend RAG APIs, runs a reasoning-based guardrail validation to verify grounding, and presents a consolidated recommendation with citations. This repository includes the FastAPI ingestion/retrieval services and the exported Copilot solution package so the full workflow can be run locally end-to-end.

## Solution overview

The solution provides project requirement analysis through two perspectives:
- Technology analysis
- Financial analysis

High-level flow:
1. End user asks a project requirement question in Copilot Studio.
2. Copilot Studio orchestration logic decomposes the request into two prompts:
   - `tech_prompt`
   - `finance_prompt`
3. Copilot invokes two flow actions:
   - `POST_API_Respone_Tech`
   - `POST_API_Respone_Finance`
4. Each flow sends `POST` request to local retrieval API endpoint (through ngrok).
5. Backend performs hybrid retrieval (vector + semantic) on Azure AI Search.
6. Retrieved chunks are passed to Azure OpenAI for grounded answer generation.
7. A reasoning-based guardrail validator breaks answers into claims and checks each claim against retrieved context.
8. Backend response is returned to Copilot, parsed, and displayed in adaptive card sections for technology and finance.

## Repository structure

- `ingestion/`: Ingestion API to create/clear index and ingest blob documents into Azure AI Search.
- `retrieval/`: Retrieval API used by Copilot Studio flows for technology/finance responses.
- `demo-files/`: Sample documents for testing ingestion.
- `copilot-export/StratifyAgent_1_0_0_1_managed.zip`: Exported Copilot Studio managed solution package.

## Copilot package details

- Solution unique name: `StratifyAgent`
- Solution display name: `Stratify AI`
- Solution version: `1.0.0.1`
- Package type: `Managed`
- Copilot name: `Stratify AI`
- Main topic (display name): `Data Orchestrator`
- Identity topic (display name): `Agent Identification`
- AI Builder model used for prompt decomposition: `Orch_Two_domain_prompts`
- Flow IDs used by topic:
  - Finance flow: `4100834b-0c13-f111-8341-7ced8daf54b2`
  - Tech flow: `95bffa7c-470f-f111-8341-7ced8daf0540`
- Environment variables expected by both flows:
  - `sai_var_ngrok_api_base_url` (example value of an ngrok URL)
  - `sai_var_ngrok_api_method_name` (default `/get-response`)

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

## Step 0: Clone the repository

```powershell
git clone <your-repo-url>
cd stratify-agent
```

## Step 1: Prepare Azure resources

### 1.1 Azure Storage
1. Create a blob container (for example `rag-inputs`).
2. Upload files from `demo-files/` or your own documents.

Supported file types by current ingestion code:
- `.pdf`
- `.docx`

### 1.2 Azure AI Search
1. Create an Azure AI Search service.
2. Note endpoint and admin key.
3. Choose an index name (example: `stratify-index`).

Important:
- Ingestion API can create the index schema via `POST /create-index`.
- Schema uses vector `embedding` dimension `1536`.
- Your embedding deployment must output 1536-dimensional vectors (example: `text-embedding-3-small`).

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
Create `ingestion/.env`:

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
Create `retrieval/.env`:

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

```powershell
cd ingestion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

In another terminal or Postman:

### 3.1 Create search index

```http
POST http://localhost:8001/create-index
```

### 3.2 Run ingestion

```http
POST http://localhost:8001/ingest
```

Ingestion behavior:
- Reads documents from blob container
- Parses with Document Intelligence
- Chunks content
- Summarizes tables into text rows
- Generates embeddings
- Replaces prior chunks for same `source_url`
- Uploads chunks to Azure AI Search

Optional maintenance endpoint:

```http
POST http://localhost:8001/clear-index
```

## Step 4: Run retrieval service locally

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

`type` values used by Copilot flows:
- `technology`
- `finance`

Response shape expected by Copilot topic parsing:

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

Copilot flows must call your local retrieval API through public HTTPS URL.

```powershell
ngrok http 8000
```

Copy HTTPS forwarding URL, for example:
- `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

## Step 7: Import Copilot Studio solution

### 7.1 Import package
1. Open Power Platform / Copilot Studio environment.
2. Import solution package from:
   - `copilot-export/StratifyAgent_1_0_0_1_managed.zip`
3. Complete import.

### 7.2 Update environment variable values after import
Set these values in the target environment:
1. `sai_var_ngrok_api_base_url` = your current ngrok HTTPS base URL
   - Example: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`
2. `sai_var_ngrok_api_method_name` = `/get-response`

These two variables are consumed by both flow actions.

### 7.3 Validate flow request/response contracts
Both flows send this payload to retrieval API:

```json
{
  "prompt": "<text>",
  "type": "technology|finance"
}
```

The flow returns `apiresponse` as stringified HTTP body and the topic parses it into structured fields.

### 7.4 Publish Copilot
After updating variables and confirming flows, publish the Copilot agent.

## Step 8: End-to-end test flow

1. Run ingestion and complete index ingestion.
2. Run retrieval API locally.
3. Start ngrok for port `8000`.
4. Update imported solution environment variables with current ngrok URL.
5. Publish Copilot.
6. Ask project requirement question in Copilot chat.
7. Verify adaptive card contains:
   - Technical Analysis section
   - Financial Analysis section
   - Guardrail verdict and confidence for both
   - Source links from citations

## Troubleshooting

### Copilot returns no response
- Confirm retrieval API is running on `localhost:8000`.
- Confirm ngrok session is active.
- Confirm `sai_var_ngrok_api_base_url` points to active ngrok URL.
- Confirm `sai_var_ngrok_api_method_name` is `/get-response`.
- Check if flows `POST_API_Respone_Tech` and `POST_API_Respone_Finance` are turned on.

### Retrieval returns empty or "I do not know"
- Verify ingestion completed successfully.
- Verify both services use same `AZURE_SEARCH_INDEX`.
- Check that relevant content exists in uploaded docs.

### Ingestion/index errors
- Validate Azure Search endpoint/admin key.
- Ensure embedding model is 1536-dimensional.
- Validate Blob container and connection string.
- Validate Document Intelligence endpoint/key.

### JSON parsing issues in Copilot topic
- Ensure retrieval API returns valid JSON object with exact keys:
  - `answer`
  - `citations`
  - `guardrail`
- Avoid non-JSON wrappers in backend response.
