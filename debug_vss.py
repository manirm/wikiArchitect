import asyncio
import os
import sqlite3
import sqlite_vss
from src.core.semantic_engine import SemanticEngine

async def debug_indexing():
    vault_path = "vault"
    print(f"DEBUG: Indexing vault at {vault_path}...")
    
    try:
        engine = SemanticEngine(vault_path)
        print("DEBUG: Engine initialized.")
        
        # Test a specific file that might be causing the issue
        files = [f for f in os.listdir(vault_path) if f.endswith(".md")]
        for file in files:
            print(f"DEBUG: Indexing {file}...")
            with open(os.path.join(vault_path, file), 'r') as f:
                content = f.read()
            await engine.index_note(file, content)
            print(f"DEBUG: Successfully indexed {file}")
            
        print("DEBUG: All tests passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_indexing())
