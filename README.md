# AI Knowledge Engineering Platform

An end-to-end AI engineering platform for document intelligence, semantic retrieval, RAG, conversational memory, and LLM-powered question answering.

The platform allows users to upload PDF documents, transform them into searchable knowledge, retrieve relevant information using embeddings, and interact with that knowledge through a conversational AI interface.

## Overview

The system combines several AI engineering components into one application:

* PDF document ingestion
* Text extraction and chunking
* Semantic embeddings
* Vector similarity retrieval
* Retrieval-Augmented Generation (RAG)
* Conversational memory
* LangGraph workflow orchestration
* PostgreSQL persistence
* User authentication
* AI response generation
* Streamlit interface
* Evaluation and observability foundations

The goal is to demonstrate how a complete AI application is engineered around an LLM rather than simply calling an LLM API.

## Architecture

```text
                         ┌─────────────────────┐
                         │      Streamlit      │
                         │      Interface      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │        APIs         │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌─────────────┐      ┌─────────────┐     ┌─────────────┐
        │  Document   │      │ PostgreSQL  │     │ Conversation│
        │  Pipeline   │      │  Database   │     │   Memory    │
        └──────┬──────┘      └─────────────┘     └─────────────┘
               │
               ▼
        ┌─────────────┐
        │  Chunking   │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │  Embeddings │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │  Semantic   │
        │  Retrieval  │
        └──────┬──────┘
               │
               ▼
        ┌─────────────────────┐
        │      LangGraph      │
        │     AI Workflow     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   LLM Generation    │
        └─────────────────────┘
```

## AI Pipeline

When a user asks a question:

```text
User Question
      ↓
Question Embedding
      ↓
Semantic Retrieval
      ↓
Relevant Document Chunks
      ↓
Conversation History
      ↓
Context Construction
      ↓
LangGraph Workflow
      ↓
LLM Generation
      ↓
Assistant Response
      ↓
Conversation Storage
```

## Document Pipeline

When a PDF is uploaded:

```text
PDF
 ↓
PyMuPDF Text Extraction
 ↓
Text Chunking
 ↓
Embedding Generation
 ↓
PostgreSQL Storage
```

During retrieval, the question embedding is compared with stored document embeddings using cosine similarity.

The current implementation stores embeddings as JSON in PostgreSQL and performs similarity calculations in Python rather than using `pgvector`.

## Project Structure

```text
app/
├── api/
│   ├── auth.py
│   ├── chat.py
│   └── documents.py
│
├── core/
│   ├── config.py
│   └── security.py
│
├── db/
│   ├── database.py
│   ├── init_db.py
│   └── models.py
│
├── documents/
│   ├── chunker.py
│   ├── embeddings.py
│   └── loader.py
│
├── evaluation/
│   └── evaluator.py
│
├── graph/
│   ├── state.py
│   └── workflow.py
│
├── langgraph/
│   └── workflow.py
│
├── memory/
│   └── memory.py
│
├── observability/
│   └── logging.py
│
├── rag/
│   ├── generator.py
│   └── retriever.py
│
├── tools/
│   └── search.py
│
└── main.py

streamlit_app.py
```

## Tech Stack

| Technology | Purpose                   |
| ---------- | ------------------------- |
| Python     | Application logic         |
| FastAPI    | Backend API               |
| Streamlit  | User interface            |
| PostgreSQL | Persistent data storage   |
| SQLAlchemy | Database ORM              |
| LangGraph  | AI workflow orchestration |
| LangChain  | AI application framework  |
| OpenAI     | LLM and embeddings        |
| PyMuPDF    | PDF processing            |
| Pydantic   | Data validation           |
| uv         | Dependency management     |

## Core Engineering Concepts

### RAG

The system retrieves relevant document content before asking the LLM to generate an answer.

This reduces the need for the model to rely entirely on its pretrained knowledge.

### Semantic Retrieval

Documents and questions are converted into numerical embeddings.

The system calculates cosine similarity between the question embedding and stored document embeddings to find relevant chunks.

### Conversational Memory

User and assistant messages are persisted in PostgreSQL.

Previous conversation history can then be supplied to later AI requests.

### LangGraph

The AI workflow is represented as explicit processing stages:

```text
Question
   ↓
Document Retrieval
   ↓
Conversation Memory
   ↓
Response Generation
```

This provides a foundation for adding additional AI workflow stages later.

## Local Setup

Clone the repository:

```bash
git clone https://github.com/zubairanjumm/mini-ai-engineering-platform.git
cd mini-ai-engineering-platform
```

Install dependencies:

```bash
uv sync
```

Create `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/mini_ai_platform
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
```

Initialize PostgreSQL tables:

```bash
uv run python -m app.db.init_db
```

Run the application:

```bash
uv run streamlit run streamlit_app.py
```

## Current Capabilities

* User registration and login
* PostgreSQL database integration
* PDF ingestion
* Text extraction
* Document chunking
* OpenAI embeddings
* Semantic retrieval
* RAG
* Conversation persistence
* LangGraph orchestration
* Streamlit interface
* Basic evaluation infrastructure
* Application logging

## Future Improvements

Potential extensions include:

* Better retrieval and reranking
* More advanced evaluation
* Streaming responses
* Tool calling
* Agent workflows
* Document metadata filtering
* Multi-document conversations
* Improved authentication
* Production deployment architecture
* More detailed observability

## Engineering Focus

The project focuses on the engineering layers surrounding modern AI systems:

```text
Data
 ↓
Ingestion
 ↓
Embeddings
 ↓
Retrieval
 ↓
Memory
 ↓
Workflow Orchestration
 ↓
LLM
 ↓
Evaluation
 ↓
Persistence
```

Rather than building only a chatbot, the project demonstrates how these components can be assembled into a complete AI application.

## License

MIT
