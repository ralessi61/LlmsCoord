import asyncio
import time

from llmsharing.exceptions import CoordinatorError
from llmsharing.models import LLMRequest, OrchestratorConfig, TaskType
from llmsharing.orchestrator import AsyncioStrategy, ThreadingStrategy, _call_provider

metrics = {
    "sequential": {},
    "asyncio": {},
    "threading": {},
}

PROMPT = "Summarize the document in three sentences."

requests = [
    LLMRequest(
        doc_id=f"DOC-{i}",
        tasktype=TaskType.SUMMARY,
        prompt=PROMPT,
        provider="fast",
    )
    for i in range(20)
]


LEVELS = (1, 2, 5)

# --- 2. sequential: one after another, no semaphore ---
async def run_sequential(batch):
    for request in batch:
        try:
            await _call_provider(request)
        except CoordinatorError:
            pass
        
# --- 3. metrics dict (same idea as 06_confronto_finale.py) ---
metrics = {
    "sequential": {},
    "asyncio": {},
    "threading": {},
}

def timed(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0

# --- 4. sequential once (ignores concurrency) ---
metrics["sequential"]["n/a"] = timed(
    lambda: asyncio.run(run_sequential(requests))
)

# --- 5. two strategies for three levels ---
for conc in LEVELS:
    config = OrchestratorConfig(
        max_concurrency=conc,
        max_tokens=100,
        temperature=0.2,
    )
    metrics["asyncio"][conc] = timed(
        lambda c=config: asyncio.run(AsyncioStrategy(c).run(requests))
    )
    metrics["threading"][conc] = timed(
        lambda c=config: ThreadingStrategy(c).run(requests)
    )

# --- 6. results ---
print("-"*70)
print("strategy      conc     seconds")
print("------------------------------")
for name, rows in metrics.items():
    for conc, seconds in rows.items():
        print(f"{name:<12} {conc!s:<8} {seconds:.3f}")
print("-"*70)    