# Orchestration library with fake providers #

Three LLMs faked
Concurrency
Retries
No API Key
GIL 

The GIL (Global Interpreter Lock) means that, in standard Python, threads effectively run Python code one at a time, creating the illusion of parallelism. 
They are still very efficient for I/O tasks—such as network requests and reading or writing files—because they can make progress while waiting. They are not ideal for CPU-heavy calculations.
This workload is I/O-bound. asyncio (and threads) overlap the waits.
Extra processes would not make sleep() faster, so no multiprocessing here.

Ideal for background tasks: I/O and network operations that should not block an interactive app.

Concurrency lets tasks make progress seemingly at the same time, though not necessarily at the exact same instant. 
It works well for I/O, such as web or server requests and other operations that wait for resources.

Parallelism means multiple tasks run at the same instant across multiple CPU cores, providing more computing power. 
It is useful for CPU-intensive work, such as processing large datasets, scientific calculations, parallel image processing, and AI.

Benchmark (can vary on different pc);
----------------------------------------------------------------------
strategy      conc     seconds
------------------------------
sequential   n/a      0.535
asyncio      1        0.549
asyncio      2        0.257
asyncio      5        0.128
threading    1        0.605
threading    2        0.302
threading    5        0.126
----------------------------------------------------------------------

- `asyncio` at conc 1 in above table is about as fast as sequential execution, but a little slower: `gather` and semaphore overhead adds up when there is no overlap.
- From 1 to 2 to 5 workers: the runtime roughly halves each time, so the concurrency limit is working as expected.
- With 1 or 2 workers, threading is slower than `asyncio` because each worker calls `asyncio.run`, which creates a new event loop. 
- With 5 workers, they are about the same (~0.13s). 

# How is done #

The project includes :
- concurrency semaphore
- provider registry
- decorators
- Pydantic validation (`prompt` and `fields` for extraction tasks)
- logging with a sensitive-data filter
- Poetry dependency management (`pydantic` runtime dependency , `pytest` development dependency).

# poetry add pytest only for dev #
poetry new llmsharing
poetry add pydantic
poetry add --group dev pytest

# TDD #
Can be seen in GitHub pushes 4fd86fa , 0b84120
Red commit, then Green
see TDD.md

# code verify, global install #
ruff check . --fix

# install, run #
poetry install
poetry run python -m unittest
poetry run llm-orchestrator
poetry run python benchmarks.py


