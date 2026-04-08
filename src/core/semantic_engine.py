import sqlite3
import sqlite_vss
import os
import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
import ollama

class SemanticEngine:
    """
    Local-first vector search engine for WikiArchitect.
    Uses sqlite-vss for persistent storage and Ollama for embeddings.
    """
    def __init__(self, vault_dir: str, db_path: Optional[str] = None):
        self.vault_dir = vault_dir
        # Store index in hidden .wiki folder within the vault
        if db_path is None:
            wiki_dir = os.path.join(vault_dir, ".wiki")
            os.makedirs(wiki_dir, exist_ok=True)
            self.db_path = os.path.join(wiki_dir, "semantic.db")
        else:
            self.db_path = db_path
            
        self._init_db()
        self._client = ollama.AsyncClient()

    def _init_db(self):
        """Initializes the SQLite-VSS schema with thread-safety enabled."""
        # Enable multi-threaded access for SQLite
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.enable_load_extension(True)
        sqlite_vss.load(self.conn)
        
        curr = self.conn.cursor()
        
        # 1. Metadata Table
        curr.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                title TEXT,
                hash TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. VSS Index Table (nomic-embed-text is 768 dims)
        # Note: sqlite-vss v0.1.2 uses vss0_index syntax
        curr.execute("CREATE VIRTUAL TABLE IF NOT EXISTS vss_notes USING vss0(embedding(768))")
        
        self.conn.commit()

    async def index_note(self, relative_path: str, content: str):
        """Generates embeddings and updates the semantic index if content changed."""
        abs_path = os.path.join(self.vault_dir, relative_path)
        if not os.path.exists(abs_path) and not content:
            return

        # Simple content hash to avoid redundant LLM calls
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        curr = self.conn.cursor()
        curr.execute("SELECT id, hash FROM notes WHERE path = ?", (relative_path,))
        row = curr.fetchone()
        
        if row and row[1] == content_hash:
            return # Already indexed

        # 1. Generate Embeddings (768 dims)
        try:
            response = await self._client.embeddings(model="nomic-embed-text", prompt=content)
            embedding = response['embedding']
        except Exception as e:
            print(f"Embedding error for {relative_path}: {e}")
            return

        # 2. Upsert Metadata
        if row:
            note_id = row[0]
            curr.execute("UPDATE notes SET hash = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?", (content_hash, note_id))
        else:
            curr.execute("INSERT INTO notes (path, title, hash) VALUES (?, ?, ?)", 
                         (relative_path, os.path.basename(relative_path)[:-3], content_hash))
            note_id = curr.lastrowid

        # 3. Upsert Vector (VSS tables use rowid)
        # We need to manually match rowid if it's a virtual table
        curr.execute("DELETE FROM vss_notes WHERE rowid = ?", (note_id,))
        curr.execute("INSERT INTO vss_notes(rowid, embedding) VALUES (?, ?)", (note_id, json.dumps(embedding)))
        
        self.conn.commit()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs a vector similarity search across the vault."""
        try:
            response = await self._client.embeddings(model="nomic-embed-text", prompt=query)
            query_embedding = response['embedding']
            
            curr = self.conn.cursor()
            # Vector search query using vss0
            curr.execute("""
                with matches as (
                    select rowid, distance
                    from vss_notes
                    where vss_search(embedding, ?)
                    limit ?
                )
                select n.path, n.title, m.distance
                from notes n
                join matches m on n.id = m.rowid
                order by m.distance asc
            """, (json.dumps(query_embedding), limit))
            
            results = []
            for row in curr.fetchall():
                results.append({
                    "path": row[0],
                    "title": row[1],
                    "score": 1.0 - row[2] # Invert distance to score
                })
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
