We still have two agents — the Coder and Sheriff are both LLM calls with different system prompts. What changed is who executes the script:

Before: Sheriff was supposed to call execute_code tool → the model didn't use tools
Now: The orchestrator executes the script directly, then feeds the stdout/stderr/exit_code into the Sheriff's prompt so the Sheriff can analyze the results and decide PASS/FAIL
Why this is better:

Small quantized models (4-bit 7B) are unreliable at tool calling — they output code in markdown instead. This is a well-known limitation.
The Sheriff's real value is analyzing execution results and suggesting fixes — that's a text-in, text-out task that doesn't need tools.
The Coder still tries tools first, but if it outputs code in markdown instead, we extract it (fallback).
The two-agent design is preserved: Coder generates, Sheriff judges. The orchestrator just handles the mechanical execution step.
Analogy: It's like a code review — the reviewer doesn't need to run gcc themselves. A CI system runs the build, and the reviewer reads the output.

Let me verify tests pass, update the docs, then run Scenario 1.