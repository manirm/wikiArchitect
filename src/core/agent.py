import asyncio
import json
import re
import os
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import ollama
import httpx
from src.core.semantic_engine import SemanticEngine

# --- Data Models ---

class FileChange(BaseModel):
    """Represents a proposed change to a file in the wiki."""
    file_path: str = Field(..., description="Target file path (e.g., 'vault/topic.md')")
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

    def set_base_dir(self, new_dir: str):
        """Updates the agent's workspace and reloads core instructions."""
        self.base_dir = new_dir
        self._system_prompt = self._load_system_prompt()

    def __init__(self, model: str = "gemma4-pro:latest", base_dir: str = "vault"):
        self.model = model
        self.base_dir = os.path.abspath(base_dir)
        self._lock = asyncio.Lock()
        self._client = ollama.AsyncClient()
        self._system_prompt = self._load_system_prompt()
        self.semantic_engine = SemanticEngine(self.base_dir)

    def _load_system_prompt(self) -> str:
        """Loads the master instructions from schema/CLAUDE.md."""
        path = f"{self.base_dir}/schema/CLAUDE.md"
        if not os.path.exists(path):
            # Fallback to internal app default if the wiki lacks custom rules
            return "You are WikiArchitect, a Knowledge Librarian."
            
        with open(path, "r") as f:
            return f.read()

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
2. Propose new wiki pages or updates to existing ones in `vault/`.
3. Update `vault/index.md` if new domains are added.
4. Update `vault/log.md` with an audit entry.

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
        Synthesizes an answer from the wiki using RAG context and proposes updates.
        """
        # 1. Semantic Retrieval
        context_notes = await self.semantic_engine.search(user_query, limit=3)
        context_str = ""
        if context_notes:
            context_str = "\nRELEVANT CONTEXT FROM VAULT:\n---\n"
            for note in context_notes:
                try:
                    with open(os.path.join(self.base_dir, note['path']), 'r') as f:
                        content = f.read()
                        context_str += f"FILE: {note['path']}\nCONTENT:\n{content[:2000]}\n---\n"
                except Exception: continue

        # 2. Augmented Prompt
        prompt = f"""
TASK: QUERY KNOWLEDGE BASE
QUERY: {user_query}
{context_str}

INSTRUCTIONS:
Provide a detailed answer. Use the 'RELEVANT CONTEXT' provided above to ensure accuracy.
If you identify missing links or see opportunities to cross-reference existing wiki pages, propose those changes.

Output JSON with 'main_response' and 'file_changes'.
"""
        raw_output = await self._call_llm(prompt)
        return self._parse_structured_output(raw_output)

    async def propose_lint(self) -> AgentResponse:
        """
        Evaluates the wiki for consistency and broken links.
        """
        # Logic to scan vault/ directory would go here to provide context to the LLM.
        prompt = """
TASK: LINT KNOWLEDGE BASE
INSTRUCTIONS:
Check for broken wikilinks, missing metadata blocks, or naming inconsistencies.
Propose fixes in the standard JSON format.
"""
        raw_output = await self._call_llm(prompt)
        return self._parse_structured_output(raw_output)
