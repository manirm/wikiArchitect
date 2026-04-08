import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from src.core.agent import WikiArchitectAgent

class AutonomousArchitect:
    """The Autonomous Architect is a background task engine for vault curation."""
    
    def __init__(self, agent: WikiArchitectAgent):
        self.agent = agent
        self._is_running = False
        
    async def generate_moc(self) -> str:
        """Generates or updates the Map of Content (MOC.md) using the canonical template."""
        template_path = os.path.join(self.agent.base_dir, "schema", "MOC_TEMPLATE.md")
        template_content = ""
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                template_content = f.read()

        prompt = f"Using this template structure:\n\n{template_content}\n\nScan the vault and generate a comprehensive MOC.md. Replace tokens like {{{{date}}}}, {{{{recent_breakthroughs}}}}, and {{{{emergent_clusters}}}} with real insights from the notes. Keep the professional formatting."
        
        response = await self.agent.propose_query(prompt)
        
        moc_path = os.path.join(self.agent.base_dir, "MOC.md")
        with open(moc_path, "w") as f:
            f.write(response.main_response)
            
        return moc_path

    async def generate_weekly_briefing(self) -> str:
        """Parses log.md and synthesizes the last 7 days of activity into a structured report."""
        log_path = os.path.join(self.agent.base_dir, "log.md")
        recent_logs = []
        
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                lines = f.readlines()
                # Simple logic to grab the last 20 entries for synthesis
                # In a full production app, we would parse timestamps
                recent_logs = lines[-20:]

        prompt = f"Analyze these recent vault logs:\n\n{''.join(recent_logs)}\n\nSynthesize a 'Weekly Progress Report' (WEEKLY_BRIEFING.md). Group updates by domain, identify core trends, and propose the 'Next Big Milestone' for the vault's intelligence."
        
        response = await self.agent.propose_query(prompt)
        
        briefing_path = os.path.join(self.agent.base_dir, "WEEKLY_BRIEFING.md")
        with open(briefing_path, "w") as f:
            f.write(response.main_response)
            
        return briefing_path

    async def audit_vault(self) -> Dict[str, Any]:
        """Performs a structural audit of the vault to detect orphans or broken links."""
        prompt = "Perform a Structural Audit of the vault. Find any orphaned notes (no incoming links) or dead wiki-links. Provide a report in vault/AUDIT.md."
        
        response = await self.agent.propose_query(prompt)
        
        audit_path = os.path.join(self.agent.base_dir, "AUDIT.md")
        with open(audit_path, "w") as f:
            f.write(response.main_response)
            
        return {"status": "Complete", "report_path": audit_path}

    async def run_daily_maintenance(self):
        """Standard sequence of maintenance tasks."""
        print(f"[{datetime.now()}] Starting Daily Maintenance...")
        await self.generate_moc()
        await self.audit_vault()
        print(f"[{datetime.now()}] Maintenance Complete.")
