# QueryNest

QueryNest is a terminal-first, Python-based Retrieval Augmented Generation (RAG) application that allows users to ask natural language questions against external knowledge sources directly from the command line.

It is designed to be developer-friendly, fully self-hostable, and incrementally extensible, with a strong focus on local execution and minimal external dependencies.

---

## Contents

- [Installation](#installation)
  - [Option 1: Install via PyPI (Python Package)](#option-1-install-via-pypi-python-package)
  - [Option 2: Use via Docker (Recommended for Isolated Usage)](#option-2-use-via-docker-recommended-for-isolated-usage)
  - [Docker Security Note](#docker-security-note)
- [CLI Usage](#cli-usage)
- [Features](#features)
- [Supported Data Sources](#supported-data-sources)
  - [Websites](#websites)
  - [PDF Documents](#pdf-documents)
- [High-Level Architecture](#high-level-architecture)
- [Technical Stack](#technical-stack)
- [Memory Design](#memory-design)
  - [Knowledge Memory (Vector Memory)](#1-knowledge-memory-vector-memory)
  - [Conversational Memory (Chat History)](#2-conversational-memory-chat-history)
- [Local Storage Structure](#local-storage-structure)
- [Session Management](#session-management)
- [Prompt Construction Strategy](#prompt-construction-strategy)
- [Roadmap](#roadmap)
- [Distribution](#distribution)
- [Security Principles](#security-principles)
- [Engineering Principles](#engineering-principles)
- [License](#license)
- [Status](#status)

----



## Installation

QueryNest can be used either as a **Python CLI (via PyPI)** or as a **Docker-based CLI**.

---

### Option 1: Install via PyPI (Python Package)

QueryNest is distributed as a Python package and can be installed directly from **PyPI**.

#### Requirements

* Python **3.10 or higher**
* `pip` installed and available in PATH
* Internet access for first-time dependency installation

#### Install using pip

```bash
pip install querynest-cli==1.0.1
```

This installs the `querynest` CLI in your environment.

#### Verify Installation

```bash
querynest --help
```

If installed correctly, you should see the available CLI commands.

#### PyPI Package

Official PyPI release:
[https://pypi.org/project/querynest-cli/1.0.1/](https://pypi.org/project/querynest-cli/1.0.1/)

---

### Option 2: Use via Docker (Recommended for Isolated Usage)

QueryNest is also available as a Docker image, allowing you to use the CLI **without installing Python or dependencies locally**.

#### Pull the Docker image

```bash
docker pull divyansh1552005/querynest:latest
```

#### Run QueryNest using Docker

```bash
docker run --rm divyansh1552005/querynest --help
```

#### Example: Chat with a web page

```bash
docker run --rm \
  -e GEMINI_API_KEY=YOUR_API_KEY \
  divyansh1552005/querynest chat --web "https://example.com"
```

#### Interactive mode (TTY)

```bash
docker run -it --rm \
  -e GEMINI_API_KEY=YOUR_API_KEY \
  divyansh1552005/querynest chat
```

---

### Docker Security Note

Docker Scout may report OS-level CVEs inherited from the base image.
QueryNest does **not** expose network services and is safe for **CLI usage**.

---

# CLI Usage

The CLI supports:

* Chatting with a single web page or a PDF (or folder of PDFs)
* Automatic session creation and resume
* Session inspection, search, rename, and deletion
* Viewing chat history
* Configuration management (API key)

---

## Entry Point

After installation (editable or normal), the CLI is exposed as:

```bash
querynest
```

Internally, this maps to:

```python
querynest.cli.main:main
```

On startup, the CLI:

1. Runs the bootstrap process (ensures config and API key exist)
2. Registers all subcommands
3. Dispatches to the appropriate command handler

---

## Command Structure

```text
querynest
├── chat        # Core chat functionality
├── config      # Configuration management
├── history     # View chat history
└── sessions    # Session management
```

Each top-level command is isolated and does not share side effects with others.

---

## 1. Chat Command

### Purpose

The `chat` command is the primary entry point for QueryNest. It allows you to start or resume a conversational session with a single knowledge source.

### Supported Sources

* One web page URL
* One PDF file
* One folder containing multiple PDFs

Only **one source** is allowed per session.

### Usage

```bash
querynest chat --web "https://example.com"
querynest chat --pdf "/path/to/file.pdf"
querynest chat --pdf "/path/to/folder/"
```

### Behavior

* A deterministic session ID is generated from the source
* If a session already exists for the source, it is resumed automatically
* If not, a new session is created
* On first creation, the user is prompted for a session name
* Documents are loaded, split, embedded, and indexed using FAISS
* A conversational chat loop is started

### Key Characteristics

* Interactive REPL-style chat
* Markdown-rendered assistant responses
* Sliding window memory
* Automatic persistence of chat and vectors
* Graceful handling of Ctrl+C and EOF

### Exit

Type either of the following to end the chat:

```text
exit
quit
```

---

## 2. Config Command

### Purpose

Manage QueryNest configuration, primarily the Gemini API key.

### Commands

#### Set API Key

```bash
querynest config set-api-key
```

* Prompts securely for a new API key
* Updates the local configuration file
* Takes effect immediately

---

## 3. History Command

### Purpose

View the chat history associated with a session.

### Usage

History can be accessed in three mutually exclusive ways:

```bash
querynest history show --session-id <SESSION_ID>
querynest history show --web "https://example.com"
querynest history show --pdf "/path/to/file.pdf"
```

### Rules

* Exactly one of `--session-id`, `--web`, or `--pdf` must be provided
* History is read-only
* Messages are shown in chronological order

### Output

Each message is displayed with its role:

```text
USER: ...
ASSISTANT: ...
```

---

## 4. Sessions Command

The `sessions` command provides full control and visibility over stored sessions.

### 4.1 List Sessions

#### Basic Listing

```bash
querynest sessions list
```

Displays:

* Session ID
* Session name
* Source type (WEB / PDF)

#### Full Metadata

```bash
querynest sessions list --all
```

Displays all metadata fields for every session.

#### Sorting Options

Sorting flags are mutually exclusive:

```bash
querynest sessions list --recent   # Sort by last_used_at (descending)
querynest sessions list --oldest   # Sort by created_at (ascending)
querynest sessions list --name     # Sort alphabetically by name
```

The `--all` flag may be combined with any single sorting flag.

---

### 4.2 Session Information

```bash
querynest sessions info <SESSION_ID>
```

Displays detailed metadata for the specified session.

---

### 4.3 Rename Session

```bash
querynest sessions rename <SESSION_ID> "New Session Name"
```

* Updates only the session metadata
* Does not affect vectors or chat history

---

### 4.4 Delete Session

```bash
querynest sessions delete <SESSION_ID>
```

* Requires confirmation
* Permanently removes:

  * Vector index
  * Chat history
  * Metadata

---

### 4.5 Search Sessions

Search across stored sessions using metadata fields.

#### Search by Name (default)

```bash
querynest sessions search "query"
```

#### Search by Source

```bash
querynest sessions search "example.com" --source
```

#### Search by Source Type

```bash
querynest sessions search "pdf" --type
```

#### Search Everywhere

```bash
querynest sessions search "http" --all
```

Search is:

* Case-insensitive
* Partial match
* Metadata-only (no vector loading)

---




## Design Constraints and Guarantees

* One session corresponds to exactly one source
* Sessions are resumed automatically
* Multiple PDFs are supported only via a single folder
* JavaScript-rendered web pages are not supported
* Image-only documents are not supported

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
