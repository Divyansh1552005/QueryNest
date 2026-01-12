# QueryNest – Terminal-based RAG Chat Application (PRD)

## 1. Product Overview

**QueryNest** is a **terminal-first, Python-based RAG (Retrieval Augmented Generation) application** that enables users to ask natural language questions against external knowledge sources directly from the command line.

QueryNest supports three primary data sources:

1. **YouTube videos** (via transcripts)
2. **Website URLs** (via cleaned page content)
3. **PDF documents** (via local file upload)

The product is designed to be:

* Developer-friendly
* Self-hostable
* Incrementally extensible
* Free from frontend or browser dependencies

This document serves as the **Product Requirements Document (PRD)** for QueryNest.

---

## 2. Goals & Non-Goals

### 2.1 Goals

* Provide a reliable terminal-based chat interface for querying external content
* Support Bring-Your-Own (BYO) Gemini API keys
* Enable conversational context awareness (recent chat memory)
* Allow session persistence and resumption
* Offer multiple distribution formats (Docker, CLI, native packages)

### 2.2 Non-Goals (Initial Versions)

* No graphical user interface (GUI)
* No browser-based frontend
* No real-time streaming responses (initially)
* No built-in authentication system

---

## 3. Target Users

* Developers
* Students
* Researchers
* Power users comfortable with terminal workflows
* Users wanting local/self-hosted AI tools

---

## 4. Supported Use Cases

### 4.1 Chat with YouTube Videos

* User provides a YouTube URL
* QueryNest extracts the transcript
* User asks questions about the video content

### 4.2 Chat with Website Content

* User provides a website URL
* QueryNest fetches and cleans page content
* User queries the semantic meaning of the page

### 4.3 Chat with PDF Documents

* User provides a local PDF file path
* QueryNest extracts text from the document
* User queries the document content

---

## 5. High-Level System Architecture

```
User (Terminal)
     ↓
QueryNest CLI
     ↓
Source Loader (YT / Web / PDF)
     ↓
Text Cleaning & Normalization
     ↓
Text Chunking
     ↓
Gemini Embeddings
     ↓
Vector Store (FAISS / Chroma)
     ↓
Similarity Search
     ↓
Gemini LLM
     ↓
Terminal Response
```

---

## 6. Core Technical Stack

### 6.1 Language

* Python 3.10+

### 6.2 LLM & Embeddings

* Gemini 1.5 Pro (LLM)
* Gemini Embedding Model (`embedding-001`)

### 6.3 Vector Storage

* **Primary:** FAISS (CPU)
* **Future:** Chroma (persistent vector DB)

### 6.4 Content Extraction

* YouTube: `youtube-transcript-api`
* Website: `requests`, `beautifulsoup4`, `readability-lxml`
* PDF: `pypdf` / `pdfplumber`

---

## 7. Memory Design

QueryNest separates memory into **two independent systems**.

### 7.1 Knowledge Memory (Vector Memory)

* Stores embeddings of source content
* Used only for semantic retrieval
* Implemented using FAISS or Chroma

### 7.2 Conversational Memory (Chat History)

* Stores user–assistant messages
* Maintains conversational continuity
* Sliding window approach (last 4–5 messages)
* Stored as JSON files

---

## 8. Local Data & Configuration Storage

QueryNest stores all persistent data locally on the user's machine.

### 8.1 Base Directory

```
~/.querynest/
```

### 8.2 Directory Structure

```
~/.querynest/
├── config.json
└── sessions/
    └── <session_id>/
        ├── chat.json
        └── vectors.faiss
```

### 8.3 Configuration File (`config.json`)

Stores user-specific configuration such as:

* Gemini API key

---

## 9. Session Management

* Each session is deterministically generated using a hash of the input source
* Same source → same session → same memory
* Enables automatic session resume

---

## 10. Prompt Construction Strategy

Each LLM request consists of:

* Retrieved context chunks (from vector store)
* Recent conversation history (sliding window)
* Current user query

The LLM is explicitly instructed to:

* Answer only from provided context
* Respond with "I don't know" when information is missing

---

## 11. Versioned Roadmap

---

## v1 – Functional Prototype

**Objective:** End-to-end working system

### Features

* Terminal-based interaction (`print` / `input`)
* Three data source modes (YT / Web / PDF)
* Gemini embeddings
* FAISS (in-memory)
* Stateless execution
* No persistence

---

## v1.5 – Local Persistence

**Objective:** Enable memory and session resume

### Features

* FAISS index saved to disk
* JSON-based chat history
* Sliding window conversational memory
* Session resume support

---

## v2 – Dockerized Self-hosting

**Objective:** Simplify deployment

### Features

* Dockerfile
* Docker Compose support
* Volume-mounted persistent storage
* Same terminal-based UX inside container

---

## v3 – Full CLI Tool

**Objective:** Professional CLI experience

### Features

* Command-based CLI interface
* `init` command for API key setup
* Chroma persistent vector store
* Improved prompt engineering
* Better error handling

---

## v4 – Advanced & Scalable Architecture

**Objective:** Multi-user and cloud readiness

### Features

* Optional MongoDB for chat storage
* Vector DB abstraction layer
* Multi-session and multi-user support
* Server and cloud deployment readiness

---

## 12. Distribution Strategy

QueryNest supports multiple distribution formats:

* Docker Image (primary self-host method)
* pip package
* Windows executable (`.exe` via PyInstaller)
* Linux packages (`.rpm`, `.deb`)

Secrets are never bundled in binaries.

---

## 13. Security Considerations

* API keys stored locally
* No telemetry or external logging
* No data sent except to Gemini API

---

## 14. Engineering Principles

* Clear separation of concerns
* No premature optimization
* Incremental complexity
* Storage and memory abstractions for easy migration

---

## 15. Summary

QueryNest is designed as a **robust, extensible, terminal-based AI assistant** for querying external knowledge sources.

By evolving incrementally across versions, QueryNest balances rapid development with long-term maintainability, making it suitable for both personal use and open-source collaboration.
