# QueryNest – Terminal-based RAG Chat Application (PRD)

## 1. Product Overview

**QueryNest** is a **terminal-first, Python-based RAG (Retrieval Augmented Generation) application** that enables users to ask natural language questions against external knowledge sources directly from the command line.

QueryNest supports two primary data sources:

1. **Website URLs** (via cleaned page content)
2. **PDF documents** (via local file upload)

The product is designed to be:

* Developer-friendly
* Self-hostable
* Incrementally extensible
* Free from frontend or browser dependencies
* Fully local execution with minimal external dependencies

This document serves as the **Product Requirements Document (PRD)** for QueryNest.

---

## 2. Goals & Non-Goals

### 2.1 Goals

* Provide a reliable terminal-based chat interface for querying external content
* Support Bring-Your-Own (BYO) API keys (Gemini)
* Enable conversational context awareness (recent chat memory)
* Allow deterministic session creation and automatic session resumption
* Offer multiple distribution formats (Docker, pip, native packages)
* Maintain fully local storage of data and configuration
* Zero telemetry or external logging

### 2.2 Non-Goals (Initial Versions)

* No graphical user interface (GUI)
* No browser-based frontend
* No real-time streaming responses (initially)
* No built-in authentication system
* No YouTube support (removed due to transcript blocking issues)

---

## 3. Target Users

* Developers
* Students
* Researchers
* Power users comfortable with terminal workflows
* Users wanting local/self-hosted AI tools
* Privacy-conscious users who prefer local data storage

---

## 4. Supported Use Cases

### 4.1 Chat with Website Content

* User provides one or more website URLs (comma-separated)
* QueryNest fetches and cleans page content
* User asks questions about the semantic meaning of the page(s)
* System maintains conversation context across multiple queries

### 4.2 Chat with PDF Documents

* User provides a local PDF file path or directory path (for multiple PDFs)
* QueryNest extracts text from the document(s)
* User queries the document content
* System provides contextual answers based on document content

### 4.3 Session Resume

* User returns to a previously created session
* QueryNest automatically detects existing session based on source hash
* Previous vector store and chat history are restored
* User continues conversation from where they left off

---

## 5. High-Level System Architecture

```
User (Terminal)
     ↓
QueryNest CLI
     ↓
Source Loader (Web / PDF)
     ↓
Text Cleaning & Normalization
     ↓
Text Chunking (RecursiveCharacterTextSplitter)
     ↓
Embeddings (Gemini embedding-001)
     ↓
Vector Store (FAISS)
     ↓
Similarity Search (k=6 chunks)
     ↓
LLM (Gemini 1.5 Pro)
     ↓
Terminal Response
```

---

## 6. Core Technical Stack

### 6.1 Language

* Python 3.10+

### 6.2 LLM & Embeddings

* **LLM:** Gemini 1.5 Pro
* **Embeddings:** Gemini Embedding Model (`embedding-001`)

> **Planned:** Support for OpenAI, Claude, and Hugging Face models via user-provided API keys.

### 6.3 Vector Storage

* **Primary:** FAISS (CPU-based, default)
* **Future:** Chroma (planned for persistent storage with metadata filtering)

### 6.4 Content Extraction

* **Websites:** `requests`, `beautifulsoup4`, `readability-lxml`
* **PDFs:** `pypdf`, `pdfplumber`

### 6.5 Framework

* LangChain for RAG pipeline orchestration
* LangChain Community for document loaders

---

## 7. Memory Design

QueryNest separates memory into **two independent systems** to ensure clean architecture and easy maintainability.

### 7.1 Knowledge Memory (Vector Memory)

* **Purpose:** Stores embeddings of source content
* **Usage:** Semantic retrieval only
* **Implementation:** FAISS vector store
* **Storage:** `~/.querynest/sessions/<session_id>/vectors.faiss`
* **Retrieval:** Top-k similarity search (k=6)

### 7.2 Conversational Memory (Chat History)

* **Purpose:** Stores user–assistant message exchanges
* **Usage:** Maintains conversational continuity
* **Implementation:** Sliding window approach (last 4–5 messages)
* **Storage:** `~/.querynest/sessions/<session_id>/chat.json`
* **Format:** JSON array of message objects with roles and content

---

## 8. Local Data & Configuration Storage

QueryNest stores all persistent data locally on the user's machine. **No data is sent to external services except the configured LLM provider.**

### 8.1 Base Directory

```
~/.querynest/
```

### 8.2 Directory Structure

```
~/.querynest/
├── config.json                    # API keys and user configuration
└── sessions/
    └── <session_id>/              # Deterministic hash-based ID
        ├── meta.json              # Session metadata (name, source, timestamps)
        ├── chat.json              # Conversational history
        └── faiss_index/           # Vector store files
            ├── index.faiss
            └── index.pkl
```

### 8.3 Configuration File (`config.json`)

Stores user-specific configuration:

* Gemini API key
* Future: Model selection preferences
* Future: Retrieval parameters

**Security:** API keys are stored locally and never bundled in distributed binaries.

---

## 9. Session Management

### 9.1 Deterministic Session Creation

* Sessions are deterministically generated using SHA-256 hash of the input source
* Same source → same session ID → same memory and vectors
* Enables automatic session resume without user intervention

### 9.2 Session Lifecycle

1. **Source Input:** User provides source (PDF path or URL)
2. **Hash Computation:** System computes SHA-256 hash of source
3. **Session Check:** System checks if FAISS index exists for session ID
4. **Resume or Create:**
   * **If exists:** Load existing vectors and chat history
   * **If new:** Fetch content, create embeddings, build vector store

### 9.3 Session Metadata

Each session stores metadata including:

* Session ID
* Session name (user-provided or auto-generated)
* Source type (pdf/web)
* Source path/URL
* Created timestamp
* Last used timestamp

---

## 10. Prompt Construction Strategy

Each LLM request is carefully constructed to include:

1. **Retrieved Context Chunks:** Top 6 most relevant chunks from vector store
2. **Recent Conversation History:** Sliding window of last 4-5 exchanges
3. **Current User Query:** The user's latest question

### 10.1 System Instructions

The LLM is explicitly instructed to:

* Answer **only** from the provided context
* Respond with "I don't know" or "I cannot answer based on the provided context" when information is missing
* Maintain conversational continuity by referencing chat history
* Provide concise, accurate answers

### 10.2 RAG Chain Architecture

```
User Query
    ↓
Vector Store Retrieval (k=6)
    ↓
Context + Chat History + Query
    ↓
Prompt Template
    ↓
Gemini LLM
    ↓
Response
```

---

## 11. Versioned Roadmap

### v1 – Terminal-Based Application ✅

**Status:** Complete

**Objective:** Basic terminal-based interaction

**Features:**
* Basic terminal interaction using `input()`/`print()`
* Support for Website and PDF sources
* Gemini embeddings and LLM integration
* FAISS (in-memory)
* No persistence

---

### v2 – Full CLI Tool ✅

**Status:** Complete

**Objective:** Professional CLI with persistence

**Features:**
* Local persistence (sessions, chat history, vectors)
* Deterministic session creation and resume
* Session metadata tracking
* Sliding window conversational memory
* Input validation
* Error handling and user-friendly messages
* API key configuration management

---

### v3 – Dockerized Self-Hosting (Current)

**Status:** In Progress

**Objective:** Simplify deployment for self-hosting

**Features:**
* Dockerfile for containerized deployment
* Docker Compose support
* Volume-mounted persistent storage
* Same CLI experience inside containers
* Simplified self-hosted deployment
* Documentation for deployment

---

### v4 – Enhanced CLI & Distribution

**Status:** Planned

**Objective:** Professional packaging and distribution

**Features:**
* Professional command-based CLI interface
* `querynest init` - API key setup
* `querynest chat` - Start chat session
* `querynest sessions` - List/manage sessions
* Multiple distribution formats:
  * pip package
  * Windows executable (`.exe`)
  * Linux packages (`.rpm`, `.deb`)
* Improved error messages and help text

---

### v5 – Advanced Features

**Status:** Planned

**Objective:** Enhanced capabilities and flexibility

**Features:**
* Chroma persistent vector store (with metadata filtering)
* Multiple LLM provider support (OpenAI, Claude, Hugging Face)
* Configurable chunk sizes and retrieval parameters
* Export chat history (Markdown, PDF)
* Session search and filtering
* Improved prompt engineering

---

## 12. Distribution Strategy

QueryNest will support multiple distribution formats to reach different user segments:

### 12.1 Primary Distribution Methods

* **Docker Image** (primary self-hosting method)
* **pip package** (for Python developers)
* **Windows executable** (`.exe` via PyInstaller)
* **Linux packages** (`.rpm`, `.deb`)

### 12.2 Security in Distribution

* API keys and secrets are **never bundled** in distributed artifacts
* Users must provide their own API keys during setup
* Configuration is stored locally on user machines
* No telemetry or tracking in distributed binaries

---

## 13. Security & Privacy Principles

### 13.1 Data Privacy

* All data stored locally by default
* No telemetry or external logging
* No data shared externally except with the configured LLM provider (Gemini)
* User maintains full control over their data

### 13.2 API Key Management

* API keys stored locally in `~/.querynest/config.json`
* Keys never transmitted except to authenticate with LLM provider
* Support for key rotation via `reset-key` command
* Clear documentation on key management best practices

### 13.3 Open Source

* Full source code transparency (GPL-3.0 license)
* Community auditable
* No hidden data collection

---

## 14. Engineering Principles

### 14.1 Architecture Principles

* **Separation of Concerns:** Clear module boundaries (loaders, embeddings, vector store, RAG, memory)
* **Incremental Complexity:** Start simple, add features progressively
* **Storage Abstractions:** Easy migration between storage backends
* **No Premature Optimization:** Focus on correctness first, performance later

### 14.2 Code Quality

* Type hints throughout codebase
* Comprehensive docstrings
* Modular, testable code
* Clear error messages for users

### 14.3 User Experience

* Clear, actionable error messages
* Validation of user inputs
* Progress indicators for long operations
* Graceful degradation when services unavailable

---

## 15. Known Limitations & Future Improvements

### 15.1 Current Limitations

* **No YouTube Support:** YouTube blocks transcript API requests, making this source unreliable
* **Single-User Design:** Not optimized for multi-user scenarios
* **No Streaming:** Responses are returned in full (not streamed)
* **Limited Document Types:** Only PDF and web sources supported
* **No Document Structure Awareness:** Tables, images not processed specially

### 15.2 Future Improvements

* Support for additional document types (DOCX, TXT, Markdown, EPUB)
* Table and image extraction from PDFs
* Multi-modal support (image understanding)
* Streaming responses for better UX
* Web scraping for paginated content
* Advanced retrieval strategies (hybrid search, re-ranking)

---

## 16. Success Metrics

### 16.1 Technical Metrics

* Session resume success rate
* Vector store build time
* Query response time
* Context retrieval accuracy

### 16.2 User Experience Metrics

* Ease of setup (time to first query)
* Session reuse rate
* User retention (return usage)

---

## 17. Summary

**QueryNest** is designed as a **robust, extensible, terminal-based RAG application** for querying external knowledge sources with strong focus on:

* **Privacy:** Local-first architecture
* **Simplicity:** Terminal-based, no complex setup
* **Extensibility:** Clean architecture for future enhancements
* **Self-hosting:** Docker support for easy deployment

By evolving incrementally across versions, QueryNest balances rapid development with long-term maintainability, making it suitable for both personal use and open-source collaboration.

The removal of YouTube support reflects our commitment to reliability—we only support sources that work consistently. As the project evolves, we'll continue to prioritize features that provide value to our users while maintaining our core principles of privacy, simplicity, and local execution.