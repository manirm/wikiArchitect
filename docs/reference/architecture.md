# Implementation Plan: WikiArchitect 2.0 (Semantic RAG & Autonomous Architect)

This phase evolves WikiArchitect from a simple wiki editor into a proactive knowledge agent. We will integrate a local-first vector search engine (RAG) and an autonomous task loop for consistent knowledge maintenance.

## User Review Required

> [!IMPORTANT]
> - **Local Data Storage**: The semantic index will be stored in a hidden `.wiki/` folder within your vault.
> - **Embeddings**: We will use the `nomic-embed-text` model via Ollama. It is fast and runs entirely offline.
> - **Concurrency**: Autonomous tasks (like indexing and linting) will run in the background to keep the UI snappy.

## Proposed Changes

### [Semantic Engine (RAG)]

#### [NEW] [semantic_engine.py](file:///Users/manir/projects/python/wikiArchitech/src/core/semantic_engine.py)
- Implement a `SemanticEngine` class using `sqlite-vss`.
- Handle vector storage, similarity search, and incremental indexing.

#### [MODIFY] [agent.py](file:///Users/manir/projects/python/wikiArchitech/src/core/agent.py)
- Update the `propose_query` flow to retrieve relevant note context from the `SemanticEngine` before answering.
- Improve the system prompt to use this retrieved context.

---

### [Autonomous Architect]

#### [NEW] [autonomous_architect.py](file:///Users/manir/projects/python/wikiArchitech/src/core/autonomous_architect.py)
- A background "Project Manager" for the vault.
- **Task: MOC Generation**: Periodically proposes a `vault/MOC.md` (Map of Content).
- **Task: Vault Audit**: Uses the agent to find broken links or missing tags.
- **Task: Daily Briefing**: Summarizes `vault/log.md` into a "Daily Briefing" for the user.

---

### [UI & Monitoring]

#### [MODIFY] [main_frame.py](file:///Users/manir/projects/python/wikiArchitech/src/ui/main_frame.py)
- **Real-time Indexing**: Use `watchdog` to monitor file saves in the vault.
- **Status Indicators**: Add a small indicator for "Indexing..." or "Architect at Work" in the status bar.

## Verification Plan

### Automated Verification
- **Search Accuracy**: Test if `searching("Thought A")` correctly retrieves the `Thought_A.md` content via vector similarity.
- **Concurrency**: Ensure the app doesn't freeze during library-wide indexing.

### Manual Verification
- **Deep Search**: Ask the Architect "What did I learn about Thought B yesterday?" and verify it uses RAG context to answer accurately.
- **Autonomous MOC**: Trigger a manual "Generate MOC" command and review the proposed markdown.
