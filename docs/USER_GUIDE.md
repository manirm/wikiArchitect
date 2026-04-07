# 📚 WikiArchitect: Knowledge Synthesis & User Guide

**Version:** 1.0.0-RC
**Status:** Alpha / Professional Draft

---

## 🌟 Introduction: The LLM Wiki Paradigm

WikiArchitect redefines the traditional knowledge base. Moving beyond simple document aggregation, it implements a **Cognitive Knowledge Graph** materialized as a local-first, navigable Markdown repository. Instead of users merely *storing* information, WikiArchitect facilitates *synthesis*. 

At the core is the 'Librarian'—an advanced LLM instance (`gemma4-pro:latest` via Ollama). This model ingests disparate, unstructured sources (PDFs, articles, raw text) and actively maps relationships, summarizing core concepts, and generating structured, interconnected wiki pages. 

**The Architect's Role:** You are the **Curator and Validator**. WikiArchitect manages the complexity of grounding large language models, requiring human oversight via the **Diff Viewer** at every stage of knowledge integration to ensure factual integrity and coherence.

## 🚀 Getting Started

### 1. System Prerequisites
*   **Python:** 3.12+ recommended.
*   **Ollama:** Must be installed and running locally.
*   **Model:** Pull the required model: `ollama pull gemma4-pro:latest`.

### 2. Project Structure
- `raw/`: Immutable storage for your original PDF and text sources.
- `wiki/`: The navigable knowledge base (Markdown files).
- `schema/`: System instructions and the `CLAUDE.md` persona.

---

## 🗺️ The Core Workflow

WikiArchitect operates in a structured pipeline: **Ingest → Review → Commit**.

### 1. Knowledge Ingestion
1.  Click the **Ingest** button (+) in the toolbar.
2.  Select a PDF or Text source from your disk.
3.  The system extracts the content and sends it to the Librarian for analysis.

### 2. The Architect Review (Diff Viewer)
**Critical Protocol:** No AI-generated content is ever written directly to your wiki without approval.
1.  After ingestion, the **Review Dialog** opens.
2.  **Left Pane**: Shows current wiki content (if any).
3.  **Right Pane**: Shows the Librarian's proposed additions or revisions (Unified Diff).
4.  Select individual file changes to apply or discard.

### 3. Querying the Librarian
Use the **Assistant Panel** on the right to "talk" to your knowledge base.
- Ask questions about your ingested sources.
- The Librarian will answer based *only* on the provided context, citing sources and proposing wiki updates where it sees missing connections.

---

## 🛠️ Operational Best Practices

### A. Internal Linking
Use standard Wikilinks: `[[Concept Name]]`. The Librarian is trained to recognize these and will attempt to resolve them during ingestion.

### B. The Audit Trail
- `wiki/index.md`: Automatically updated to provide a high-level catalog of your knowledge domains.
- `wiki/log.md`: An immutable chronological record of all ingestions and structural changes.

### C. Security & Privacy
WikiArchitect is **Local-First**. Your data never leaves your machine. All LLM processing is handled by your local Ollama instance.

---

## ❓ FAQ & Troubleshooting

**Q: The Librarian is hallucinating or providing generic answers.**
A: Ensure your sources are cleanly formatted. Use the `Lint` feature to check for inconsistent metadata that might be confusing the LLM context.

**Q: Connection Error with Ollama.**
A: Verify the Ollama service is running (`ollama serve`) and that the `gemma4-pro:latest` model is fully pulled.
