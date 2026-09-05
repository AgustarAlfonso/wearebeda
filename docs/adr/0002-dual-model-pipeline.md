# Tiered Dual-Model Pipeline for Extraction and Drafting

We decided to split LLM workloads into two distinct tiers: high-volume classification and extraction using Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) with strict JSON schema tool enforcement, and lower-volume response drafting using Claude Sonnet (`claude-sonnet-5`) grounded on verified CRM data. This optimizes cost and latency on the critical path while guaranteeing high-fidelity, grounded natural language drafting only for pre-filtered, legitimate enquiries.
