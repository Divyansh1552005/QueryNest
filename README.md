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
- [Key Features In-Depth](#key-features-in-depth)
  - [Multi-Model LLM Support](#multi-model-llm-support)
  - [Rich Progress Bars](#rich-progress-bars)
  - [Streaming Responses](#streaming-responses)
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
pip install querynest-cli==2.0.2
```

This installs the `querynest` CLI in your environment.

#### Verify Installation

```bash
querynest --help
```

If installed correctly, you should see the available CLI commands.

#### PyPI Package

Official PyPI release:
[https://pypi.org/project/querynest-cli/2.0.2/](https://pypi.org/project/querynest-cli/2.0.2/)

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

### Option 3: Download a native Linux package (.rpm / .deb / .tar.xz)

Standalone packages built with PyInstaller + fpm — no Python install required.
See [`packaging/README.md`](packaging/README.md) for how these are built and verified.

* **Fedora / RHEL / openSUSE (.rpm):**
  [querynest-cli-2.0.2-1.x86_64.rpm](https://github.com/Divyansh1552005/QueryNest/releases/download/v2.0.2/querynest-cli-2.0.2-1.x86_64.rpm)
  ```bash
  sudo rpm -i querynest-cli-2.0.2-1.x86_64.rpm
  ```
* **Debian / Ubuntu (.deb):**
  [querynest-cli_2.0.2_amd64.deb](https://github.com/Divyansh1552005/QueryNest/releases/download/v2.0.2/querynest-cli_2.0.2_amd64.deb)
  ```bash
  sudo dpkg -i querynest-cli_2.0.2_amd64.deb
  ```
* **Any x86_64 Linux distro (.tar.xz):**
  [querynest-cli-2.0.2.tar.xz](https://github.com/Divyansh1552005/QueryNest/releases/download/v2.0.2/querynest-cli-2.0.2.tar.xz)
  ```bash
  # archive layout is usr/bin/querynest, so extract to / to land it on PATH
  sudo tar -xJf querynest-cli-2.0.2.tar.xz -C /
  ```
  (Prefer not to touch `/usr` as root? Extract anywhere and run the binary at `<dir>/usr/bin/querynest` directly, or symlink it onto your own `PATH`.)

All release assets: [github.com/Divyansh1552005/QueryNest/releases](https://github.com/Divyansh1552005/QueryNest/releases)

---

# CLI Usage

The CLI supports:

* Chatting with a single web page or a PDF (or folder of PDFs)
* Automatic session creation and resume
* Session inspection, search, rename, and deletion
* Viewing chat history
* Configuration management (API keys and LLM model selection)

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
# Start chat with a web page
querynest chat --web "https://example.com"

# Start chat with a single PDF
querynest chat --pdf "/path/to/file.pdf"

# Start chat with multiple PDFs in a folder
querynest chat --pdf "/path/to/folder/"

# Force rebuild the vector index (useful if the source has been updated)
querynest chat --web "https://example.com" --force
querynest chat --pdf "/path/to/file.pdf" --force
```

### Behavior

* A deterministic session ID is generated from the source
* If a session already exists for the source, it is resumed automatically
* If not, a new session is created with rich progress feedback
* On first creation, the user is prompted for a session name
* Documents are loaded (with progress bars), split into chunks, embedded, and indexed using FAISS
* A conversational chat loop is started with **real-time streaming responses**
* Model used is shown on startup and determined by your current config (defaults to Gemini)

### The `--force` Flag

```bash
querynest chat --web "https://example.com" --force
```

Forces a complete rebuild of the vector index even if a session already exists for the source. Use this when:
- The web page content has been updated
- The PDF has been modified
- You want a fresh index without resuming the old session

This clears the existing chat history and vector index for that source and starts fresh.

### Key Characteristics

* **Interactive REPL-style chat** with streaming token-by-token responses
* **Plain text responses** with structured formatting (headings, lists) — no markdown symbols
* **Sliding window memory** for efficient conversation context
* **Automatic persistence** of chat and vectors
* **Rich progress feedback** during document processing
* **Multi-model support** — Use any LLM through LiteLLM
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

Manage QueryNest configuration — API keys and LLM model selection.

### Commands

#### Set Gemini API Key

```bash
querynest config set-gemini-key
```

* Prompts securely for a new Gemini API key
* Used exclusively for embeddings (`text-embedding-004`)
* Updates the local configuration file
* Takes effect immediately

#### Set LLM Model

```bash
querynest config set-llm
```

* Shows a curated menu of supported LLM providers and models
* Also supports entering a custom model string (e.g. `groq/llama-3.1-8b-instant`)
* Prompts for the provider API key (skipped if Gemini is selected as LLM)
* Available options:

```
1. Gemini 2.5 Flash (default)
2. OpenAI - GPT-4o
3. OpenAI - GPT-4o Mini
4. Anthropic - Claude Sonnet
5. Groq - Llama 3.3 70B
6. Mistral - Large
7. Enter custom model string
```

#### Set LLM API Key (without changing model)

```bash
querynest config set-llm-key
```

* Updates only the API key for the currently configured LLM provider
* Useful when rotating API keys without switching models
* If current LLM is Gemini, redirects to `set-gemini-key`

#### Show Current Models

```bash
querynest config show-models
```

* Displays the currently configured embedding model and LLM
* Example output:

```
Current Configuration:
  Embeddings : Google Gemini (text-embedding-004)
  LLM        : groq/llama-3.3-70b-versatile
```

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
* Embedding model is fixed (Google Gemini) — changing it would invalidate existing indexes

---

## Features

* **Terminal-based conversational interface** with streaming responses for real-time feedback
* **Multi-model LLM support** — Seamlessly switch between Gemini, OpenAI, Claude, Groq, Mistral and 100+ providers via LiteLLM
* **Rich progress bars** for PDF loading, chunking, and embedding operations
* **Streaming responses** — Responses stream token-by-token in real-time
* **Force re-indexing** — Rebuild vector index on demand with `--force`
* Query external knowledge sources using natural language
* Support for multiple data sources:
  * Website URLs (cleaned page content)
  * PDF documents (local files or folders)
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

* Accepts a local PDF file path or folder of PDFs
* Extracts document text with **rich progress feedback**
* Enables question answering over document content

---

## Key Features In-Depth

### Multi-Model LLM Support

QueryNest supports **100+ LLM models** through LiteLLM integration. Embeddings always use Google Gemini (`text-embedding-004`) for consistency across sessions. The LLM is fully configurable:

```bash
# Default: Gemini
querynest chat --pdf "document.pdf"

# Switch to Groq (fast + free tier)
querynest config set-llm   # select option 5

# Switch to OpenAI
querynest config set-llm   # select option 2

# Check what's currently configured
querynest config show-models
```

Configuration is stored in `~/.querynest/config.json` and persists across sessions.

### Rich Progress Bars

Visual feedback during document processing:

- **PDF Loading**: Shows file processing status with filename and progress
- **Embedding**: Live progress bar for vector embedding operations (batched, 50 chunks at a time)

Example output:
```
Using Embeddings: Google Gemini (text-embedding-004)
Using LLM:        groq/llama-3.3-70b-versatile
Loading documents...
⠸ Embedding chunks... ━━━━━━━━━━━━━━━  45% 45/100 chunks
```

### Streaming Responses

LLM responses stream token-by-token in real-time with clean formatted output:

```
You: What is machine learning?

Thinking...

Assistant
Machine learning is a subset of artificial intelligence that enables
systems to learn and improve from experience without being explicitly
programmed...
```

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
Embeddings (Google Gemini — fixed)
     ↓
Vector Store (FAISS)
     ↓
Similarity Search
     ↓
LLM (Configurable via LiteLLM)
     ↓
Terminal Response (Streamed)
```

---

## Technical Stack

### Language

* Python 3.10+

### LLM and Embeddings

* **LLM (via LiteLLM):** Google Gemini (default), OpenAI, Anthropic, Groq, Mistral, and 100+ more
* **Embeddings:** Google Gemini `text-embedding-004` (fixed — ensures index consistency)

### Vector Storage

* FAISS (CPU-based, default)
* Chroma (planned)

### Content Extraction

* Websites: `requests`, `beautifulsoup4`, `readability-lxml`
* PDFs: `pypdf`

### UI & Progress Feedback

* **Rich**: Terminal formatting, live progress bars
* **LiteLLM**: Multi-model LLM abstraction layer
* **tqdm**: Progress bars for directory PDF loading

---

## Memory Design

QueryNest separates memory into two independent systems:

### 1. Knowledge Memory (Vector Memory)

* Stores embeddings of source content
* Used only for semantic retrieval
* Implemented using FAISS

### 2. Conversational Memory (Chat History)

* Stores user–assistant messages
* Maintains conversational continuity
* Sliding window of recent messages (last 4 exchanges)
* Stored as local JSON files

---

## Local Storage Structure

All persistent data is stored locally on the user's machine.

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
        ├── meta.json
        ├── chat.json
        └── vectors.faiss
```

### Configuration (`config.json`)

```json
{
  "gemini_api_key": "...",
  "llm_model": "groq/llama-3.3-70b-versatile",
  "llm_api_key": "..."
}
```

API keys are never bundled in distributed artifacts.

---

## Session Management

* Sessions are deterministically generated using a SHA-256 hash of the input source
* Same source results in the same session and memory
* Enables automatic session resume without manual configuration
* Use `--force` to bypass resume and rebuild from scratch

---

## Prompt Construction Strategy

Each LLM request includes:

* Retrieved context chunks from the vector store
* Recent conversation history (sliding window)
* Current user query

The LLM is explicitly instructed to:

* Answer only from the provided context
* Use plain text formatting (no markdown symbols)
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
* Local persistence (sessions, chat history, vectors)
* Improved prompt handling and error management

### v3 – Dockerized Self-Hosting

* Dockerfile and Docker Compose support
* Volume-mounted persistent storage
* Same CLI experience inside containers

### v4 – Multi-Model Support (Current)

* LiteLLM integration for 100+ LLM providers
* Curated model selection menu with custom model support
* Per-provider API key management
* Rich progress bars for embedding pipeline
* Streaming responses
* Force re-indexing with `--force`

### v5 – Distribution & Introduction Website (Planned)

Distribution formats:

* Docker Image — primary self-host method
* pip package
* Windows executable — `.exe` via PyInstaller
* Linux packages — `.rpm` and `.deb`
* AppImage — packaging format research and build pipeline
* Tarball

Introduction website (TypeScript):

* Home — project intro, tagline, quick feature highlights
* About — what QueryNest is, how it works, the tech behind it
* Download — all distribution options listed clearly (pip, Docker, `.exe`, `.rpm`, `.deb`, AppImage, Tarball)
* Documentation — full usage guide, CLI reference, configuration options, and examples

### v6 – TUI (Planned)

* Build an optional Terminal UI using Textual (Python)
* Panels for chat history, input box, session sidebar, and model info
* All existing CLI logic reusable as-is — Textual acts as a presentation layer only
* CLI commands continue to work as-is — TUI is an alternative, not a replacement
* Run via: `querynest tui`


---

## Distribution

QueryNest is distributed through multiple formats:

* Docker image (`divyansh1552005/querynest:latest`)
* pip package (`querynest-cli` on PyPI)
* Linux packages — `.rpm`, `.deb`, `.tar.xz` (PyInstaller + fpm; see [`packaging/README.md`](packaging/README.md) for the build pipeline)
* Windows executable (`.exe` via PyInstaller) — planned

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