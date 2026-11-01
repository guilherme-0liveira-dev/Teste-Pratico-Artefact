# Empório AI — Intelligent Customer Service Agent

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](docs/DOCKER_GUIDE.md)
[![Framework](https://img.shields.io/badge/Streamlit-1.66.1-red.svg)](https://streamlit.io/)
[![ORM](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Validation](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Linting](https://img.shields.io/badge/Ruff-Passed-brightgreen.svg)](https://astral.sh/ruff)
[![Tests](https://img.shields.io/badge/Tests-56%20Passed-success.svg)](https://docs.pytest.org/)

A production-grade, reproducible conversational customer service AI assistant engineered for **Empório da Música**, a retail musical instrument store in Campo Grande / MS, Brazil.

This project was built for the **Artefact AI Engineer Technical Challenge**. It implements a layered, test-driven architecture combining deterministic business rules, BM25 policy retrieval, structured tool calling, and dual LLM support (cloud-free **NVIDIA NIM** or 100% local **Ollama**).

---

## 1. Project Overview & Assessment Objectives

### Scenario
Empório da Música is a regional retail store with more than 15 years in the market, operating in Campo Grande/MS. The customer service team was overburdened with repetitive inquiries regarding store opening hours, catalog availability, live pricing, delivery timelines, payment installment calculations, and return policies.

### Mission
Develop a text-based conversational AI agent that:
- Assumes a welcoming, music-oriented brand persona in **Brazilian Portuguese**.
- Retrieves verified operational data from structured relational storage (products, stock, orders, active promotions).
- Indexes and attributes facts from the official store policy manual (`políticas_da_loja.pdf`) using page-level and section-level citations.
- Executes **pure, deterministic Python calculations** for financial operations (5% PIX discount, tiered credit card installments, shipping thresholds, and CDC return eligibility) rather than relying on hallucination-prone free-form LLM math.
- Gracefully identifies and redirects out-of-scope queries (e.g., musical accessories such as cables, picks, amplifiers, and strings, which the store does not sell).
- Safely escalates sensitive issues to human support.

---

## 2. Architecture & Data Flow

```mermaid
graph TD
    User([Customer / User]) <--> Streamlit[Presentation Layer: Streamlit UI]
    
    subgraph ApplicationLayer ["Application Layer"]
        Streamlit <--> Orchestrator[Agent Orchestrator]
        Orchestrator <--> Prompts[System Prompt & Persona]
        Orchestrator <--> LLM[BaseLLMProvider Interface]
        Orchestrator <--> ToolDispatcher[Tool Registry & Pydantic Schemas]
    end

    subgraph LLMProviders ["LLM Provider Implementations"]
        LLM -.-> Nvidia[NVIDIA NIM Cloud Free<br/>meta/llama-3.3-70b-instruct]
        LLM -.-> Ollama[Ollama Local<br/>qwen2.5-coder / llama3.2]
        LLM -.-> Mock[MockLLMProvider<br/>Deterministic Offline Testing]
    end

    subgraph DomainLayer ["Domain Layer (Pure Deterministic Python)"]
        ToolDispatcher --> CatalogService[Catalog Service]
        ToolDispatcher --> OrderService[Order Tracking Service]
        ToolDispatcher --> RulesEngine[Business Rules Engine<br/>PIX 5% | Installment Tiers | CDC Returns | Shipping]
        ToolDispatcher --> PolicySearch[Policy Search Service<br/>BM25 Okapi Retrieval]
    end

    subgraph InfrastructureLayer ["Infrastructure & Storage Layer"]
        CatalogService --> SQLite[(SQLite: emporio.db)]
        OrderService --> SQLite
        RulesEngine -.-> SQLite
        PolicySearch --> PolicyChunks[(Indexed PDF Policy Sections)]
        
        CSVLoader[CSV Ingestion Pipeline<br/>Pandas + Decimal Parsing] --> SQLite
        PDFLoader[PDF Text Extractor<br/>PyMuPDF + Structure Chunking] --> SQLite
        PDFLoader --> PolicyChunks
    end
```

### Architectural Layering
1. **Presentation Layer (`app/main.py`):** Interactive Streamlit interface featuring brand visuals, quick suggestion chips, message history, session reset, and a live **Developer Diagnostics Panel** revealing tool execution latency and citations.
2. **Application Layer (`app/agent/`):** Orchestrates multi-turn conversation flow, enforces an anti-infinite-loop bounded tool execution limit (capped at 5 hops), validates tool inputs with Pydantic v2 schemas, and synthesizes answers.
3. **Domain Layer (`app/services/`):** Independent, pure Python business rules engine containing zero I/O or LLM dependencies. Computes exact Decimal prices, discount non-cumulativity, installment schedules, and return eligibility.
4. **Infrastructure Layer (`app/db/`, `app/ingestion/`, `app/retrieval/`, `app/llm/`):** SQLite relational persistence with foreign keys, PyMuPDF extraction, Rank-BM25 indexing, and swappable LLM adapters.

---

## 3. Technology Choices & Rationale

| Technology | Selection | Engineering Rationale |
|:---|:---|:---|
| **Language** | Python 3.11+ (Tested on 3.14) | Assessment requirement. High expressiveness, native async, and rich ecosystem for LLMs and data engineering. |
| **User Interface** | Streamlit | Rapid, professional conversational UI with native streaming, session state management, and built-in diagnostic widgets. |
| **Relational Storage** | SQLite + SQLAlchemy 2.0 | Zero external server dependency, embedded ACID compliance, strict foreign key enforcement (`PRAGMA foreign_keys=ON`), and type-safe ORM models. |
| **Schema Validation** | Pydantic v2 | High-performance argument validation for all agent tools; automatic export of JSON schemas for LLM function calling. |
| **Data Ingestion** | Pandas + Python `Decimal` | Clean handling of tabular datasets, normalization of Brazilian currency strings (`R$ 1.299,00` → `Decimal('1299.00')`), and ISO datetime conversion. |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | Robust, high-fidelity PDF parsing preserving layout hierarchy, titles, subsections, and exact page numbers. |
| **Policy Retrieval** | Rank-BM25 (`rank-bm25`) | Lightweight lexical retrieval. Store policies are concise (8 pages) and legal terms require exact keyword matching. Avoids vector database complexity, external embeddings cost, and vector drift. |
| **LLM Provider** | NVIDIA NIM / Ollama / Mock | Provider-agnostic abstraction (`BaseLLMProvider`). Supports low-cost/free cloud models via NVIDIA NIM, 100% private local execution via Ollama, and offline test mocking. |
| **Code Quality** | Ruff + Pytest | Sub-second linting, PEP 8 formatting, and 100% deterministic offline automated testing. |

---

## 4. Deterministic Business Rules Engine

A core design principle of Empório AI is that **the LLM is never allowed to perform financial or policy arithmetic directly through free-form reasoning**. Instead, calculations are executed by deterministic Python functions:

1. **PIX Discount (5%):**
   - Applies a 5% cash discount on regular catalog prices (`price * 0.95`).
   - **Strict Non-Cumulativity:** If a product is already subject to an active promotion, the PIX discount is strictly disallowed or calculated solely from base price (preventing stacked discounts).
2. **Tiered Installments:**
   - **1x to 3x:** Interest-free, no minimum installment amount (except order total < R$ 50.00).
   - **4x to 6x:** Interest-free, strictly requires a minimum monthly installment of **R$ 80.00**.
   - **7x to 12x:** Interest-free, strictly requires a minimum monthly installment of **R$ 100.00**.
3. **Right of Withdrawal (CDC Art. 49):**
   - Strictly enforces 7 calendar days after delivery for online purchases. Store pays return freight.
4. **Defect-Related Exchanges:**
   - Up to 30 calendar days directly with the store; thereafter, refers customer to manufacturer warranty (90 days legal + factory warranty).
5. **Shipping & Freight:**
   - Local delivery (Grande Campo Grande): Free for orders ≥ R$ 500.00 (1–3 business days via motoboy); fixed fee of R$ 35.00 for orders < R$ 500.00.
   - Other cities: External shipping via Correios (PAC/SEDEX) or Jadlog, calculated by postal code at checkout.

---

## 5. Setup & Installation

### Option 1: 🐳 Fast Track via Docker (Recommended — Zero Config)

The entire application, database, and optional local LLM are fully containerized using a senior-grade multi-stage Docker architecture:

```bash
# 1. Clone the repository
git clone https://github.com/guilherme-0liveira-dev/emporio-ai.git
cd emporio-ai

# 2. (Optional) Configure NVIDIA NIM or Ollama in .env (or run offline demonstration mode)
cp .env.example .env

# 3. Build and launch with a single command
docker compose up --build
```
Open **`http://localhost:8501`** in your browser. The container automatically seeds the database on startup if it's not present!

*For advanced Docker operations (Ollama local container, health checks, volumes), see [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md).*

---

### Option 2: 🐍 Local Python Virtual Environment

#### Prerequisites
- Python 3.11, 3.12, or higher
- Git

#### Installation Steps

```powershell
# 1. Clone the repository
git clone https://github.com/your-username/emporio-ai.git
cd emporio-ai

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dev]
```

### Environment Configuration (`.env`)
Copy the example environment template:
```powershell
cp .env.example .env
```

Edit `.env` to configure your preferred LLM backend:

#### Option A: NVIDIA NIM (Free Cloud API — Recommended)
1. Get a free API key at [build.nvidia.com](https://build.nvidia.com).
2. Set in `.env`:
   ```dotenv
   LLM_PROVIDER=nvidia
   LLM_API_KEY=nvapi-your-key-here
   LLM_BASE_URL=https://integrate.api.nvidia.com/v1
   LLM_MODEL=meta/llama-3.3-70b-instruct
   ```

#### Option B: Ollama (Local Execution)
1. Install [Ollama](https://ollama.ai) and pull a tool-calling model:
   ```bash
   ollama pull qwen2.5-coder:7b
   # or: ollama pull llama3.2
   ```
2. Set in `.env`:
   ```dotenv
   LLM_PROVIDER=ollama
   LLM_API_KEY=ollama
   LLM_BASE_URL=http://127.0.0.1:11434/v1
   LLM_MODEL=qwen2.5-coder:7b
   ```

#### Option C: Mock Mode (Offline Testing)
If no API key is provided, the application automatically switches to `MockLLMProvider`, allowing complete offline testing and evaluation without any API keys.

---

## 6. Data Ingestion Pipeline

Run the automated ingestion script to create database tables, ingest the 6 relational CSV datasets, and extract and index the PDF policy manual:

```powershell
python scripts/ingest.py
```

### Ingestion Output Summary:
- **Categories:** 9 instrument categories loaded.
- **Products:** 65 musical instruments with regular prices, specifications, and stock counts.
- **Customers:** 50 customer accounts.
- **Orders:** 20 customer purchase orders.
- **Order Items:** 22 order line items.
- **Promotions:** 25 promotional campaigns (active and historical).
- **Policy Documents:** 28 structured policy chunks indexed into SQLite and BM25.

---

## 7. Running the Application

Launch the Streamlit conversational interface:

```powershell
streamlit run app/main.py
```

Open your browser at `http://localhost:8501`.

### Key Interface Features:
- **Live Model Switcher:** Switch seamlessly between NVIDIA NIM, Ollama Local, and Offline Mock in the sidebar.
- **Quick-Start Prompt Chips:** Clickable suggestions to immediately test product search, store hours, order status, and return policy queries.
- **Developer Diagnostics Panel:** Expandable sidebar inspector displaying turn latency (ms), agent reasoning iterations, and exact tool calls with arguments and returned evidence.

---

## 8. Automated Testing & Code Quality

The project features a comprehensive test suite covering business rules, ingestion idempotency, tool handlers, and agent orchestrator loops with zero external API calls:

```powershell
# Run the complete test suite
python -m pytest tests/ -v

# Run tests with test coverage reporting
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run code style and linting checks with Ruff
python -m ruff check .
python -m ruff format --check .
```

### Test Coverage Matrix:
- `tests/test_business_rules.py`: 16 unit tests for PIX discounts, boundary installment rules, CDC returns, and freight thresholds.
- `tests/test_ingestion.py`: 5 tests validating Decimal currency strings, ISO/Brazilian date parsing, relational foreign-key integrity, and ingestion idempotency.
- `tests/test_tools.py`: 10 integration tests validating catalog filtering, stock checks, order lookup, promotion listing, and BM25 policy retrieval.
- `tests/test_orchestrator.py`: 5 integration tests using `MockLLMProvider` validating multi-step tool loops, anti-infinite-loop safeguards (capped at 5 turns), and provider error handling.
- **Result:** **36 passed tests** in under 4 seconds.

---

## 9. Security, Privacy & Guardrails

- **LGPD & Customer Privacy:** The `get_order_status` tool includes customer verification safeguards (`order_id` + `email` or `name`) before exposing order line items or shipping details, preventing unauthenticated order scraping.
- **SQL Injection Prevention:** 100% of database interactions utilize SQLAlchemy parameterized ORM queries. The agent has no access to execute arbitrary SQL strings.
- **Prompt Injection Defense:** Retrieved policy manual text and database evidence are treated as passive data payloads in tool responses, segregated from system-level instructions. The system prompt explicitly commands the assistant to reject user instructions that attempt to alter persona, bypass rules, or leak system instructions.
- **Data Redaction in Logs:** `app/core/logging.py` includes a custom redacting log formatter that scrubs Brazilian CPFs and API key patterns from stdout and log files.

---

## 10. Known Limitations & Future Improvements

1. **Live Carrier API Integration:** Freight quotations outside of Campo Grande are currently estimated using documented policy guidelines (Correios/Jadlog); integrating live carrier APIs (e.g., Melhor Envio or Correios API) would allow real-time pricing for any Brazilian postal code.
2. **Audio / Voice Support:** Future iterations could incorporate Whisper speech-to-text and ElevenLabs / Edge-TTS to provide audio messaging over WhatsApp.
3. **Customer Self-Service Rescheduling:** Enable authorized customers to update their delivery addresses or cancel unfulfilled orders directly through conversational tool calls.

---

## 11. Disclosure of AI Coding Assistant Usage

In full alignment with the Artefact assessment guidelines:

- **AI Assistant Used:** **Google Antigravity** (powered by DeepMind Gemini models).
- **Workflow & Roles:**
  - **Planning & Discovery:** Antigravity was utilized to parse the assessment specifications, inventory repository files, and draft the initial Architecture Decision Record (ADR).
  - **Scaffolding & Implementation:** Assisted with boilerplate generation (Pydantic models, SQLAlchemy declarative schemas, and Streamlit layouts).
  - **Test Suite Generation:** Antigravity accelerated unit test authoring across edge cases (e.g., boundary installment values at R$ 79.99 vs R$ 80.00).
- **Human Review & Verification:**
  - All mathematical calculations, discount non-cumulativity logic, and CDC legal deadlines were manually verified against `políticas_da_loja.pdf`.
  - Every single test and lint check was executed and confirmed passing in the actual runtime environment before final submission.
