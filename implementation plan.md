# Implementation Plan: WikiArchitect (LLM Wiki Desktop)

A desktop application designed to implement the [LLM Wiki](https://share.google/GtrVAEaaTNsmV7SMH) pattern by Andrej Karpathy. The application serves as an "IDE" for a knowledge base where an LLM (Gemma-Pro via Ollama) acts as the programmer/librarian and the user acts as the architect/curator.

## User Review Required

> [!IMPORTANT]
> **Ollama Dependency**: This application requires a local Ollama instance running with the `gemma4-pro:latest` (or similar) model.
> **Obsidian Compatibility**: The application will use a folder structure compatible with Obsidian (`wiki/` folder with `.md` files and `[[wikilinks]]`).

## Architecture & Proposed Changes

The application will be built as a local-first desktop tool using **wxPython** for the GUI and **uv** for dependency management.

### Project Structure

The app will manage a specific directory structure for each "Knowledge Base":
- `raw/`: Immutable source documents (PDFs, TXT, MD, images).
- `wiki/`: LLM-maintained markdown files.
    - `index.md`: Content-oriented catalog.
    - `log.md`: Chronological audit trail.
- `schema/`: Configuration and instructions for the LLM (e.g., `CLAUDE.md`).
- `.wiki_architect/`: App-specific metadata (state, local embeddings for search).

---

### [NEW] `pyproject.toml`
Defines dependencies:
- `wxpython` (GUI)
- `ollama` (LLM interaction & Embeddings)
- `sqlite-vss` (Local vector search)
- `pypdf` (PDF text extraction)
- `markdown2` (Markdown rendering)
- `watchdog` (File system monitoring)
- `httpx` (API communication)

### [NEW] `src/core/agent.py`
The "Wiki Architect" agent logic.
- Implements `Ingest`, `Query`, and `Lint` operations.
- Manages the prompt orchestration for multi-file edits.
- Interfaces with local Ollama service.

### [NEW] `src/ui/main_frame.py`
The primary window using `wxPython`.
- **Sidebar**: `wx.TreeCtrl` for browsing `raw/` and `wiki/` folders.
- **Center**: A notebook with tabs for:
    - **Editor**: Markdown editor with syntax highlighting.
    - **Preview**: Rendered markdown view.
- **Right Panel**: "Architect Chat" - a dedicated space for giving instructions and reviewing proposed wiki changes.
- **Status Bar**: Shows LLM status and background task progress.

### [NEW] `src/ui/diff_viewer.py`
A custom dialog to review proposed edits by the LLM before they are committed to the file system.

---

## Operational Flows

### 1. Ingest Flow
1. User drags a file into the `raw/` folder or uses the "Ingest" button.
2. The Agent reads the source and identifies relevant wiki pages to update or create.
3. The Agent presents a "Plan" in the Chat panel.
4. User clicks "Apply Plan".
5. App shows a Diff View for each file change.
6. User confirms; App writes files and updates `index.md` and `log.md`.

### 2. Query Flow
1. User types a question in the Chat panel.
2. App triggers a "Search" (Grep-based or Embedding-based).
3. Agent reads relevant Wiki pages and synthesizes an answer.
4. Answer is displayed with clickable `[[wikilinks]]`.

### 3. Lint Flow
1. User triggers "Run Health Check".
2. Agent scans the `wiki/` directory for orphans, contradictions, or missing links.
3. Agent presents a list of "Cleanup Tasks".

## Open Questions

- **Search Engine**: We will implement a local vector search using `sqlite-vss`. Embeddings will be generated via Ollama (using `nomic-embed-text`).
- **PDF Support**: Integrated PDF support using `pypdf` for text extraction.

## Verification Plan

### Automated Tests
- `pytest` for the `core/agent.py` logic (mocking Ollama responses).
- Unit tests for the file-system operations (ensuring `raw/` remains immutable).

### Manual Verification
1. Create a new Knowledge Base.
2. Ingest a sample technical paper.
3. Verify that `index.md` and `log.md` are updated correctly.
4. Ask a question that requires synthesizing information across two pages.
5. Verify the "Diff Review" workflow.
