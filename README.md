# QueryNest

QueryNest is a terminal-first, Python-based Retrieval Augmented Generation (RAG) application that allows users to ask natural language questions against external knowledge sources directly from the command line.

It is designed to be developer-friendly, fully self-hostable, and incrementally extensible, with a strong focus on local execution and minimal external dependencies.

---

## Installation

QueryNest is distributed as a Python package and can be installed directly from **PyPI**.

### Requirements

- Python **3.10 or higher**
- `pip` installed and available in PATH
- Internet access for first-time dependency installation

### Install via pip

    pip install querynest-cli==1.0.0

This installs the `querynest` CLI globally in your environment.

### Verify Installation

    querynest --help

If installed correctly, you should see the available CLI commands.

### PyPI Package

Official PyPI release:  
https://pypi.org/project/querynest-cli/1.0.0/#description



---

## Features

* Terminal-based conversational interface
* Query external knowledge sources using natural language
* Support for multiple data sources:

  * Website URLs (cleaned page content)
  * PDF documents (local files)
* Retrieval Augmented Generation (RAG) pipeline
* Conversational context awareness (sliding window memory)
* Deterministic session creation and automatic session resume
* Fully local storage of data and configuration
* Bring-your-own API key model
* No frontend, browser, or GUI dependency

---

## Supported Data Sources

### Websites

* Accepts a website URL
* Fetches and cleans main page content
* Allows semantic querying over web pages

**Limitations:**
- JavaScript-rendered pages are NOT supported
- Image-only pages are NOT supported
- Login / paywall pages are NOT supported

### PDF Documents

* Accepts a local PDF file path
* Extracts document text
* Enables question answering over document content

---

## High-Level Architecture

```
User (Terminal)
     ↓
QueryNest CLI
     ↓
Source Loader (Web / PDF)
     ↓
Text Cleaning & Normalization
     ↓
Text Chunking
     ↓
Embeddings (Gemini)
     ↓
Vector Store (FAISS / Chroma)
     ↓
Similarity Search
     ↓
LLM (Gemini)
     ↓
Terminal Response
```

---

## Technical Stack

### Language

* Python 3.10+

### LLM and Embeddings

* For embedding (models/text-embedding-004)
* For LLM, gemini-2.5-flash

> Planned: Support for OpenAI, Claude, and Hugging Face models via user-provided API keys.

### Vector Storage

* FAISS (CPU-based, default)
* Chroma (planned for persistent storage)

### Content Extraction

* Websites: `requests`, `beautifulsoup4`, `readability-lxml`
* PDFs: `pypdf`

---

## Memory Design

QueryNest separates memory into two independent systems:

### 1. Knowledge Memory (Vector Memory)

* Stores embeddings of source content
* Used only for semantic retrieval
* Implemented using FAISS or Chroma

### 2. Conversational Memory (Chat History)

* Stores user–assistant messages
* Maintains conversational continuity
* Sliding window of recent messages (typically last 4–5)
* Stored as local JSON files

---

## Local Storage Structure

All persistent data is stored locally on the user’s machine.

### Base Directory

```
~/.querynest/
```

### Directory Layout

```
~/.querynest/
├── config.json
└── sessions/
    └── <session_id>/
        ├── chat.json
        └── vectors.faiss
```

### Configuration (`config.json`)

* Stores user-specific configuration
* API keys are never bundled in binaries

---

## Session Management

* Sessions are deterministically generated using a hash of the input source
* Same source results in the same session and memory
* Enables automatic session resume without manual configuration

---

## Prompt Construction Strategy

Each LLM request includes:

* Retrieved context chunks from the vector store
* Recent conversation history (sliding window)
* Current user query

The LLM is explicitly instructed to:

* Answer only from the provided context
* Respond with "I don't know" if the answer cannot be inferred

---

## Roadmap

### v1 – Terminal-Based Application

* Basic terminal-based interaction using input/output
* Support for Website and PDF sources
* Gemini embeddings and LLM integration
* FAISS (in-memory)
* No persistence

### v2 – Full CLI Tool

* Professional command-based CLI interface
* `init` command for API key setup
* Local persistence (sessions, chat history, vectors)
* Improved prompt handling and error management

### v3 – Dockerized Self-Hosting

* Dockerfile and Docker Compose support
* Volume-mounted persistent storage
* Same CLI experience inside containers
* Simplified self-hosted deployment

---

## Distribution

QueryNest is distributed through multiple formats:

* Docker image (primary self-hosting method)
* pip package
* Windows executable (`.exe` via PyInstaller)
* Linux packages (`.rpm`, `.deb`)

Secrets and API keys are never bundled in distributed artifacts.

---

## Security Principles

* All data stored locally by default
* No telemetry or external logging
* No data shared externally except with the configured LLM provider

---

## Engineering Principles

* Clear separation of concerns
* Incremental complexity
* No premature optimization
* Storage and memory abstractions for easy migration

---

## License

QueryNest is licensed under the GNU General Public License v3 (GPL-3.0).

---

## Status

QueryNest is under active development. APIs, CLI commands, and internal architecture may evolve across releases.
