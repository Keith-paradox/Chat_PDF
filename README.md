# Chat With PDF — Backend

**Production-ready RAG backend for academic Q&A over PDFs via FastAPI (Python 3.11), ChromaDB, OpenRouter LLM, multi-agent orchestration, and Redis-based session memory.**

---

## Architecture

```mermaid
flowchart TD
    subgraph Ingestion
        A1[PDF File] --> A2[PyMuPDF Extractor]
        A2 --> A3[Chunking (~1000 tokens, 200 overlap)]
        A3 --> A4[Sentence-Transformers Embeddings]
        A4 --> A5[Chroma Vectorstore]
    end
    subgraph QAPipeline
       B1[[User Question]]
       B1 --> B2[PlannerAgent]
       B2 -->|RETRIEVE| B3[RetrieverAgent]
       B3 -->|Chunks| B4[ReaderAgent]
       B4 -->|Answer| B7[API Response]
       B2 -.->|SEARCH_WEB| B5[WebSearchAgent]
       B5 -- Web context --> B4
       B2 -.->|ASK_CLARIFY| B6[API Clarify]
    end
    A5 --(query)--> B3
```

---

## Overview

- **PDFs** ingested, chunked, embedded locally (sentence-transformers), indexed in **ChromaDB**
- **PlannerAgent** triggers optimal path for each question (retrieve, answer, search web, clarify)
- **RetrieverAgent** runs vector search (Chroma)
- **ReaderAgent** synthesizes answer (OpenRouter LLM)
- **WebSearchAgent** (DuckDuckGo) supplements context if needed
- **SessionMemory** (Redis) for context/session-based memory

---

## Setup & Run

```sh
git clone https://github.com/your-org/chat-with-pdf.git
cd chat-with-pdf
cp .env.example .env
# Fill in your API keys in .env
docker-compose up --build
```

- Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI

---

## Ingestion

```sh
docker-compose exec app python app/ingest/ingest_pdfs.py data/your-paper.pdf --doc-id my_paper
```

---

## API

### Ask Question
POST `/v1/ask`
```json
{ "session_id": "uuid", "question": "What is the main result?" }
```
Response:
```json
{ "answer": "string", "sources": ["..."], "plan": [{"action": "RETRIEVE"}, {"action": "ANSWER"}] }
```

### Clear Memory
POST `/v1/clear_memory`
```json
{ "session_id": "uuid" }
```
Response: `{ "status": "cleared" }`

---

## Future

- Pinecone/Milvus vector store backend switch
- Re-ranking
- Streamed LLM answers
- Authentication and multi-user API