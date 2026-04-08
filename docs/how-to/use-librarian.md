# Using the Librarian's Background Tasks
### Automating the heavy lifting of knowledge management.

The **Librarian Menu** in the top toolbar is your console for automated vault maintenance. These tasks are performed by the `AutonomousArchitect` engine.

---

## 🗺️ Generate/Update Map of Content (MOC)
An MOC is a strategic entry point into your vault.
- **When to Use**: When you've added several notes on a new topic and it feels "cluttered."
- **What Happens**: The Librarian scans your current index, identifies clusters of related information, and organizes them into a structured `MOC.md` file using the canonical template.
- **Review**: You will be presented with a side-by-side diff. If you approve, your MOC is updated.

## 📝 Generate Weekly Briefing
This is your personal synthesis report.
- **When to Use**: Every Friday or after a long research session.
- **What Happens**: The Librarian parses your `log.md` file (which records every ingestion and change) and synthesizes the last 7 days into a strategic summary (`WEEKLY_BRIEFING.md`).
- **Insights**: It identifies breakthroughs, highlights recent work, and proposes future paths based on your activity.

---
**Next Step:** Learn about the [System Architecture](../reference/architecture.md).
