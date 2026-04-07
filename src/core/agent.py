import asyncio
import json
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import ollama
import httpx

# --- Data Models ---

class FileChange(BaseModel):
    """Represents a proposed change to a file in the wiki."""
    file_path: str = Field(..., description="Target file path (e.g., 'wiki/topic.md')")
    original_content: Optional[str] = Field(None, description="Snippet of current content for context")
    new_content: str = Field(..., description="The complete new content for the file")
    reasoning: str = Field(..., description="Why this change is being proposed")

class AgentResponse(BaseModel):
    """The structured response from the agent to the UI."""
    file_changes: List[FileChange] = Field(default_factory=list)
    main_response: Optional[str] = Field(None, description="The textual answer or summary from the LLM")

# --- Core Agent ---

class WikiArchitectAgent:
    """
    The core LLM-based agent responsible for maintaining the WikiArchitect knowledge base.
    Follows the protocols defined in schema/CLAUDE.md.
    """

    def __init__(self, model: str = "gemma4-pro:latest", base_dir: str = "."):
        self.model = model
        self.base_dir = base_dir
        self._lock = asyncio.Lock()
        self._client = ollama.AsyncClient()
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Loads the master instructions from schema/CLAUDE.md."""
        try:
            with open(f"{self.base_dir}/schema/CLAUDE.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "You are the WikiArchitect AI. Maintain the wiki with rigor and mapping to sources."

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # AsyncClient in ollama doesn't require explicit close in current versions, 
        # but we keep this for protocol consistency and future-proofing.
        pass

    async def _call_llm(self, user_prompt: str) -> str:
        """Calls the local Ollama model with the fixed system prompt and concurrency lock."""
        async with self._lock:
            try:
                response = await self._client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response['message']['content']
            except Exception as e:
                raise RuntimeError(f"Ollama communication error: {str(e)}")

    def _parse_structured_output(self, raw_text: str) -> AgentResponse:
        """
        Parses the JSON block typically returned by the LLM in its scratchpad.
        Falls back to a default empty response if parsing fails.
        """
        try:
            # Look for a JSON block in the markdown output
            json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return AgentResponse(**data)
            
            # Try parsing the whole text if no code blocks are found
            data = json.loads(raw_text)
            return AgentResponse(**data)
        except (json.JSONDecodeError, ValidationError, AttributeError):
            # Fallback: Treat the whole thing as a text response with no file changes
            return AgentResponse(main_response=raw_text, file_changes=[])

    async def propose_ingest(self, source_text: str, source_name: str) -> AgentResponse:
        """
        Analyzes new source material and proposes wiki updates.
        """
        prompt = f"""
TASK: INGEST SOURCE MATERIAL
SOURCE NAME: {source_name}
CONTENT:
---
{source_text[:10000]} # Truncate for safety
---

INSTRUCTIONS:
1. Synthesize the core concepts from this source.
2. Propose new wiki pages or updates to existing ones in `wiki/`.
3. Update `wiki/index.md` if new domains are added.
4. Update `wiki/log.md` with an audit entry.

Return your proposal as a JSON block matching this schema:
{{
  "file_changes": [
    {{ "file_path": "string", "new_content": "string", "reasoning": "string" }}
  ],
  "main_response": "string summary"
}}
"""
        raw_output = await self._call_llm(prompt)
        return self._parse_structured_output(raw_output)

    async def propose_query(self, user_query: str) -> AgentResponse:
        """
        Synthesizes an answer from the wiki and proposes updates (links, cross-references).
        """
        # In a real RAG implementation, we would fetch relevant documents here first.
        # For now, we rely on the LLM's memory or simplified browsing if provided later.
        prompt = f"""
TASK: QUERY KNOWLEDGE BASE
QUERY: {user_query}

INSTRUCTIONS:
Provide a detailed answer. If you identify missing links or see opportunities to 
cross-reference existing wiki pages, propose those changes.

Output JSON with 'main_response' and 'file_changes'.
"""
        raw_output = await self._call_llm(prompt)
        return self._parse_structured_output(raw_output)

    async def propose_lint(self) -> AgentResponse:
        """
        Evaluates the wiki for consistency and broken links.
        """
        # Logic to scan wiki/ directory would go here to provide context to the LLM.
        prompt = """
TASK: LINT KNOWLEDGE BASE
INSTRUCTIONS:
Check for broken wikilinks, missing metadata blocks, or naming inconsistencies.
Propose fixes in the standard JSON format.
"""
        raw_output = await self._call_llm(prompt)
        return self._parse_structured_output(raw_output)
