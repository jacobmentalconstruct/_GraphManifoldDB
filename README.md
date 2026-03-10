# Graph Manifold

A deterministic, graph-native manifold system for structured knowledge retrieval
and contextual synthesis.

## Status: Phase 11 — Query Embedding Integration / Semantic Scoring Activation

The system has a complete, executable retrieval-to-generation pipeline from manifold
creation through projection, fusion, scoring, extraction, hydration, and model synthesis.
Semantic scoring is now active — the full gravity formula `G(v) = α·S + β·T` uses both
structural centrality (PageRank) and semantic similarity (cosine) when a model bridge
is available for query embedding.
445 tests passing across 11 implementation phases.

**What exists now**:
- **Types & Contracts** — 9 typed IDs, 12 enums, full graph types (Node, Edge, Chunk,
  Embedding, Hierarchy, Provenance, Bindings), 6 contract ABCs
- **Manifold Storage** — SQLite-backed persistence via ManifoldStore (16 tables, WAL mode),
  ManifoldFactory for creation and opening, same-schema rule enforced
- **Projection** — Identity and External projectors with dual SQLite/RAM code paths,
  Query Projection turns raw queries into graph-native QUERY nodes
- **Fusion** — FusionEngine combines projected slices into a VirtualManifold with
  explicit bridge requests, auto-bridging by canonical key, and label-fallback bridging
- **Scoring** — PageRank (power iteration), cosine similarity, gravity fusion
  (G = α·S + β·T), spreading activation, min-max normalisation, friction detection
- **Extraction** — Gravity-greedy evidence bag extraction with BFS expansion, token
  budget enforcement, hard limits (max_nodes, max_edges, max_chunks), deterministic
  bag IDs, and construction trace
- **Hydration** — Evidence bag materialisation into structured HydratedBundles with
  chunk text resolution, edge translation, hierarchy context, score annotations,
  budget enforcement, and three modes (FULL, SUMMARY, REFERENCE)
- **Model Bridge** — Ollama HTTP backend for embedding (text → vector via /api/embed),
  synthesis (evidence → generated output via /api/generate), canonical token estimation,
  and model identity reporting
- **Runtime Pipeline** — Full end-to-end orchestration via RuntimeController.run(),
  typed PipelineConfig/PipelineResult/PipelineError, stage-boundary logging,
  structural-only scoring fallback, graceful degradation when model unavailable
- **Debug** — Score dump and 5 structured inspection helpers for all major pipeline
  artifacts (ProjectedSlice, FusionResult, EvidenceBag, HydratedBundle, PipelineResult)
- **Hardening** — FusionConfig for bridge policy control, HASH_TRUNCATION_LENGTH constant,
  store input validation, JSON parse safety, structured logging across projection/fusion/
  scoring/store, pre-indexed binding lookups (O-011), timing instrumentation

**What remains**: See `TODO.md` for the full phased task list (ingestion, CLI, UI, and more).

## Architecture

The system is built on a **three-manifold model** where every manifold shares
the same graph-native schema:

- **Identity Manifold** — session memory, user/agent/role graph
- **External Manifold** — persistent corpus, source evidence, domain knowledge
- **Virtual Manifold** — ephemeral fused workspace, runtime-only scores

## Quick Start

```
setup_env.bat              # creates .venv, installs project (run once)
run.bat                    # activates .venv, runs python -m src.app
test.bat                   # activates .venv, runs pytest
diag.bat                   # activates .venv, launches diagnostic UI
```

Or manually:
```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m src.app
```

## Documentation

- `TODO.md` — **master task list** for all remaining phases (at project root)
- `docs/ARCHITECTURE.md` — system design, processing flow, module layout, dependency map
- `docs/DEVLOG.md` — chronological record of each implementation phase
- `docs/SYSTEM_MAP.md` — living map of system ownership and boundaries
- `docs/UI_WIRING.md` — comprehensive UI integration guide (API surfaces, panel layouts, wiring patterns)
- `docs/WATCHLIST.md` — tracked architectural concerns, debt, and hardening targets
- `docs/OPPORTUNITIES.md` — forward-looking enhancements and fortifications
- `docs/EXTRACTION_RULES.md` — strangler-fig migration protocol
- `docs/TRANSLATION_THEORY.md` — theoretical foundation: ingestion as dimensional translation, graphs as relation-preserving carriers

## Migration Discipline

This project uses a **strangler-fig pattern** to selectively extract logic from
a legacy codebase. The rules are strict:

- Never copy an entire legacy script
- Extract only narrow, well-bounded functions or classes
- Every extracted unit is assigned to exactly one owner module
- If ownership is unclear, the function stays in the legacy project
- All extractions are tracked in `src/adapters/legacy_source_notes.md`

See `docs/EXTRACTION_RULES.md` for the full extraction protocol.
