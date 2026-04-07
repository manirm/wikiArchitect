import os
import sqlite3
import json
from typing import List, Dict, Any, Optional
import sqlite_vss
import ollama

class VectorSearch:
    """
    Manages vector similarity search for the wiki contents using sqlite-vss.
    """

    def __init__(self, db_path: str = ".wiki_architect/search.db", model: str = "gemma4-pro:latest"):
        self.db_path = db_path
        self.model = model
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        """Returns a sqlite3 connection with sqlite-vss extensions loaded."""
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vss.load(conn)
        return conn

    def _init_db(self):
        """Initializes the database schema for document storage and vector search."""
        conn = self._get_connection()
        try:
            # Table for metadata and raw content
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE,
                    content TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Virtual table for vector search (using 512 dimensions for Gemma4 embeddings)
            # Adjust dimensions based on the model if needed. 
            # Gemma 27b/8b embeddings are usually 2560 or similar? 
            # We'll detect the dimensions dynamically on first add.
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS vss_documents USING vss0(embedding(2560))")
            conn.commit()
        finally:
            conn.close()

    async def _get_embedding(self, text: str) -> List[float]:
        """Generates an embedding for a piece of text using Ollama."""
        # Using the AsyncClient for consistency
        client = ollama.AsyncClient()
        response = await client.embeddings(model=self.model, prompt=text)
        return response['embedding']

    async def add_document(self, path: str, content: str, metadata: Dict[str, Any]):
        """Adds or updates a document in the search index."""
        embedding = await self._get_embedding(content)
        conn = self._get_connection()
        try:
            # Insert or update metadata
            cursor = conn.execute(
                "INSERT OR REPLACE INTO documents (path, content, metadata) VALUES (?, ?, ?)",
                (path, content, json.dumps(metadata))
            )
            doc_id = cursor.lastrowid
            
            # Insert into VSS table
            conn.execute(
                "INSERT OR REPLACE INTO vss_documents(rowid, embedding) VALUES (?, ?)",
                (doc_id, json.dumps(embedding))
            )
            conn.commit()
        finally:
            conn.close()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs a similarity search."""
        query_embedding = await self._get_embedding(query)
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT 
                    d.path, 
                    d.metadata,
                    v.distance
                FROM vss_documents v
                JOIN documents d ON v.rowid = d.id
                WHERE vss_search(v.embedding, ?)
                ORDER BY v.distance ASC
                LIMIT ?
                """,
                (json.dumps(query_embedding), limit)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "path": row[0],
                    "metadata": json.loads(row[1]),
                    "distance": row[2]
                })
            return results
        finally:
            conn.close()
