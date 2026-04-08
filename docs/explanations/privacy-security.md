# Privacy & Security Architecture
### Why your data never leaves your computer.

WikiArchitect was built with a **Zero-Trust** approach to cloud-hosted AI. We believe your intellectual property should be protected by your own hardware.

---

## 🔒 Local Processing (Ollama)
The "Large Language Model" (LLM) at the core of WikiArchitect runs entirely on your local machine using **Ollama**.
- **No API Calls**: We do not send your text to OpenAI, Anthropic, or Google.
- **Offline Functionality**: You can search, link, and chat even if your internet is disconnected.

## 🧱 The Vault Boundary
We implement a strict technical boundary around your project folder.
- **Path Sanitization**: Every file operation is validated before execution.
- **Isolation**: The app is incapable of reading or writing files outside the designated `/vault/` root, protecting your private system documents.

## 🛡️ Cryptographic Integrity
To ensure your knowledge database is consistent, we use **SHA-256** hashing.
- **Deduplication**: When you add a file, we check its hash to see if it’s already been indexed.
- **Verification**: This ensures the Librarian always has the most up-to-date and accurate context for its answers.

---
**Technical Users:** See the [Security Audit](../reference/security-specs.md) for detailed reports.
