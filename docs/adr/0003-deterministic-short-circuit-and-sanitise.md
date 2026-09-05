# Deterministic Short-Circuiting and Sanitisation Before LLM Calls

We decided that exact duplicate detection (sender email and channel hash) and input sanitisation must execute deterministically before any LLM API invocation. This avoids wasted token expenses on identical submissions and neutralizes prompt-injection attempts in raw message bodies or attachments before untrusted text reaches LLM context.
