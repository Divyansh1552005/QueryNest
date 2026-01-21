# QueryNest CLI Documentation

## Overview

QueryNest provides a production-grade command-line interface (CLI) for interacting with documents and web pages using a Retrieval-Augmented Generation (RAG) pipeline. The CLI is built using **Typer** and is designed to be:

* Deterministic (same source always resumes the same session)
* Local-first (all data stored on disk)
* Modular (clean separation between core logic and interface)
* Safe and predictable (explicit commands, no hidden behavior)

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

## Session Model

Each session is uniquely identified by a deterministic hash of its source.

### Storage Layout

```text
~/.querynest/
├── config.json
└── sessions/
    └── <session_id>/
        ├── meta.json
        ├── chat.json
        └── vectors.faiss
```

### Metadata Fields

* `id`
* `name`
* `source`
* `source_type`
* `created_at`
* `last_used_at`

---

## Design Constraints and Guarantees

* One session corresponds to exactly one source
* Sessions are resumed automatically
* Multiple PDFs are supported only via a single folder
* JavaScript-rendered web pages are not supported
* Image-only documents are not supported

---

## Summary

The QueryNest CLI is designed to be explicit, predictable, and extensible. It intentionally avoids ambiguous behavior and prioritizes correctness and usability over feature overload. The CLI serves as a stable foundation for future TUI or GUI interfaces while remaining fully functional on its own.
