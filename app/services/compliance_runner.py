import asyncio

from app.agents.compliance_manager import run_compliance_flow


async def run_compliance_assist(query: str):
    """
    Async wrapper used by event triggers / web handlers.
    Runs the synchronous compliance flow in a worker thread to avoid blocking.
    """
    return await asyncio.to_thread(run_compliance_flow, query)


# Backwards-compatible alias
async def run_compliance(query: str):
    return await run_compliance_assist(query)
