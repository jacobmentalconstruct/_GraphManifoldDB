# Graph Manifold — Master TODO

Everything that remains to be done, in verbose detail.
Iterate through these with the builder when ready.

**Current state**: Phase 11 complete, 445 tests passing, 0 test failures.
Pipeline fully wired from projection through synthesis. Semantic scoring active.
No UI, no ingestion pipeline, no CLI query path.
Diagnostic UI available (`diag.bat` — test runner + API explorer).

---

## Status Key

- [ ] Not started
- [~] Partially done / known foundation exists
- [x] Complete

---

## PHASE 12 — Ingestion Pipeline

**Why**: There is currently no way to get data INTO manifolds except by manually constructing Node/Edge/Chunk objects in Python. Without ingestion, the system is an engine with no fuel pump.

**What needs to happen**:

- [ ] **12.1 · Text file ingestion** — Read a plain text file, chunk it (fixed-size or sentence-boundary), create CHUNK-type nodes with content-addressed ChunkHash, wire up NodeChunkBindings. Store into an External manifold via ManifoldStore or direct RAM mutation.

- [ ] **12.2 · Chunking strategy** — Implement at least one production chunker. Options: fixed token window with overlap, sentence-boundary, paragraph-boundary. Should be configurable via a `ChunkingConfig` dataclass. The `Chunk` dataclass already auto-computes `byte_length`, `char_length`, `token_estimate` in `__post_init__`, so the chunker just needs to produce text segments.

- [ ] **12.3 · Source file node creation** — For each ingested file, create a SOURCE-type node. For each section/heading detected, create SECTION-type nodes. Wire CONTAINS edges from SOURCE → SECTION → CHUNK.

- [ ] **12.4 · Hierarchy entry creation** — Build HierarchyEntry records capturing the structural containment (file → section → chunk). Wire NodeHierarchyBindings. The hierarchy is used during hydration to provide context about where evidence came from.

- [ ] **12.5 · Embedding generation during ingestion** — For each chunk, call `ModelBridge.embed()` to get a vector. Create an Embedding dataclass instance, store it, and wire NodeEmbeddingBinding. This is what enables semantic scoring at query time — without chunk embeddings, the `semantic_score()` function has nothing to compare the query embedding against.

- [ ] **12.6 · Provenance stamping** — Every ingested element gets a Provenance record with stage=INGESTION, source_document=file_path, parser_name, timestamp. The Provenance dataclass and ProvenanceStage.INGESTION enum already exist.

- [ ] **12.7 · Directory / project ingestion** — Walk a directory tree, ingest all supported files, create DIRECTORY and PROJECT nodes, wire CONTAINS edges for the file tree structure.

- [ ] **12.8 · Ingestion idempotency** — Content-addressed chunks (via `make_chunk_hash(content)`) already handle dedup at the chunk level. Need to handle re-ingestion of updated files: detect changed content, update chunks, preserve unchanged chunks, update edges/bindings.

**Dependencies**: ManifoldStore (done), ManifoldFactory (done), ModelBridge.embed() (done), all graph types (done).

**Builder questions to resolve**:
- Which file types to support first? (plain text, markdown, Python, JSON?)
- Single ingestion entry point function or separate per-file-type?
- Should ingestion be a class (IngestEngine) or functional (ingest_file, ingest_directory)?
- Where does it live? `src/core/ingestion/` or `src/adapters/`?
- Chunking strategy preference for v1?

---

## PHASE 13 — CLI Query Path

**Why**: `app.py` is currently bootstrap-only — it instantiates RuntimeController, calls `bootstrap()`, and exits. There is no way to actually run a query from the command line. The RuntimeController.run() API exists but has no CLI caller.

**What needs to happen**:

- [ ] **13.1 · CLI argument parsing** — Accept at minimum: `--query "text"`, `--manifold path/to/db`, `--config path/to/config.json`. Consider using `argparse` (stdlib, no deps).

- [ ] **13.2 · Manifold loading** — Open an existing disk manifold via `ManifoldFactory.open_manifold(db_path)`. Support loading both identity and external manifolds from separate paths.

- [ ] **13.3 · Config loading** — Read PipelineConfig from a JSON/TOML file, or accept key overrides on command line (`--alpha 0.7 --skip-synthesis`).

- [ ] **13.4 · Pipeline execution** — Call `RuntimeController.run()` with loaded manifolds and config. Print the answer text to stdout. Optionally dump intermediate artifacts (scores, evidence bag, timing) to stderr or a JSON file.

- [ ] **13.5 · Output formatting** — Plain text answer by default. `--json` flag for machine-readable output including all PipelineResult fields. `--verbose` for stage timing and score summaries.

- [ ] **13.6 · Error handling** — Catch PipelineError, ValueError, ModelConnectionError. Print human-readable error messages with stage attribution.

**Dependencies**: RuntimeController.run() (done), ManifoldFactory.open_manifold() (done), PipelineConfig (done). Requires Phase 12 (ingestion) to have data to query against, unless test fixtures or a pre-populated DB are used.

**Builder questions to resolve**:
- argparse or click/typer (external dep)?
- Single `python -m src.app query "..."` subcommand or separate entry points?
- Interactive REPL mode? (multiple queries in one session)

---

## PHASE 14 — UI Interface

**Why**: The user explicitly requested a UI. Currently CLI-only. The `docs/UI_WIRING.md` document describes all API surfaces, data flows, and suggested panel layouts for a UI.

**What needs to happen**:

- [ ] **14.1 · Technology selection** — Choose UI framework. Options: web-based (FastAPI + React/Svelte), desktop (Tkinter/PyQt), terminal (Rich/Textual). The UI_WIRING.md doc is framework-agnostic.

- [ ] **14.2 · Query panel** — Text input for query, config overrides (alpha/beta sliders, token budget, max hops, hydration mode, skip synthesis toggle), run button calling `RuntimeController.run()`.

- [ ] **14.3 · Pipeline status panel** — Stage progress indicator, per-stage timing bars from `result.timing`, degraded/skipped stage warnings.

- [ ] **14.4 · Graph visualization panel** — Render the VirtualManifold as a node-edge graph. Color nodes by gravity score. Highlight bridge edges. Show labels, types, canonical keys on hover/click. Data source: `result.fusion_result.virtual_manifold.get_nodes()` and `.get_edges()`.

- [ ] **14.5 · Score explorer panel** — Sortable table of node scores (structural, semantic, gravity). Bar chart of top-N gravity. Friction warnings from `detect_all_friction()`. Alpha/beta contribution visualization.

- [ ] **14.6 · Evidence bag inspector panel** — Node list in gravity order, token budget usage bar, chunk references per node, extraction trace metadata.

- [ ] **14.7 · Hydrated content panel** — Per-node resolved text, score annotations, edge relationships, total tokens, mode indicator.

- [ ] **14.8 · Synthesis output panel** — Final answer (markdown), token usage stats, model identity, raw evidence context view.

- [ ] **14.9 · Manifold manager panel** — List loaded manifolds, per-manifold stats, create/open manifold controls, browse manifold contents.

- [ ] **14.10 · API layer** — If web-based: REST or WebSocket API wrapping RuntimeController.run() and inspection functions. All debug dump functions already return JSON-serializable dicts.

**Dependencies**: Everything above. Ingestion (Phase 12) for populating manifolds. CLI path (Phase 13) may inform the API design.

**Reference**: `docs/UI_WIRING.md` has complete import maps, wiring patterns, type shapes, and panel-to-data-source mappings.

**Builder questions to resolve**:
- Web (FastAPI + frontend) vs desktop (Tkinter/PyQt) vs terminal (Textual)?
- If web: SPA or server-rendered?
- Graph visualization library preference? (D3.js, Cytoscape.js, vis.js, etc.)
- Streaming pipeline results (O-030) needed for UI responsiveness?

---

## PHASE 15 — Weighted PageRank (O-019)

**Why**: Currently all edges contribute equally to PageRank regardless of their `weight` field. Bridge edges from label fallback (weight 0.7) should contribute less structural influence than canonical key matches (weight 1.0). This is a scoring accuracy improvement.

**What needs to happen**:

- [ ] **15.1 · Modify `structural_score()` in `scoring.py`** — Use `edge.weight` as transition probability modifier. Normalize outgoing weights per node so they sum to 1.0. Preserve all existing edge cases (empty graph, single node, dangling nodes, disconnected components).

- [ ] **15.2 · Backward compatibility** — Default behavior should be identical when all edges have weight=1.0 (current default). Only diverges when edges have non-uniform weights.

- [ ] **15.3 · Test coverage** — Add tests proving that weight=0.5 edges carry half the structural influence. Verify bridge edges (weight 0.7 from label fallback) produce lower structural influence than canonical matches (weight 1.0).

**Location**: `src/core/math/scoring.py` — `structural_score()` function.

---

## PHASE 16 — ScoringConfig Dataclass (O-021)

**Why**: Scoring parameters (damping, tolerance, alpha, beta, decay) are scattered as function-level defaults. Extracting to a ScoringConfig makes them visible, grep-able, serializable, and tunable from a single place.

**What needs to happen**:

- [ ] **16.1 · Create ScoringConfig dataclass** — Fields: `damping` (0.85), `max_iterations` (100), `tolerance` (1e-8), `alpha` (0.6), `beta` (0.4), `decay` (0.5 for spreading activation).

- [ ] **16.2 · Wire into scoring functions** — Each function accepts optional ScoringConfig and falls back to field defaults. No behavioral change when ScoringConfig is not provided.

- [ ] **16.3 · Wire into PipelineConfig** — Add `scoring_config: Optional[ScoringConfig] = None` to PipelineConfig. RuntimeController reads it in `_run_scoring()`. Alpha/beta currently on PipelineConfig directly would be deprecated in favor of ScoringConfig fields (or kept as aliases).

---

## PHASE 17 — Real SUMMARY Hydration Mode

**Why**: `HydrationMode.SUMMARY` currently behaves identically to FULL — it was stubbed in Phase 7 with a comment that real summarization requires model calls. Now that ModelBridge exists, SUMMARY can produce compressed evidence.

**What needs to happen**:

- [ ] **17.1 · SUMMARY mode implementation** — When `HydrationConfig.mode == SUMMARY`, call `ModelBridge.synthesize()` per-node (or batched) to produce condensed summaries of chunk text. Store summaries as `HydratedNode.content` instead of raw chunk text.

- [ ] **17.2 · Token savings tracking** — Record original vs. summarized token counts in HydratedBundle.properties so the UI can show compression ratio.

- [ ] **17.3 · Fallback** — If ModelBridge is unavailable, fall back to FULL mode with a warning (same graceful degradation pattern as synthesis).

**Dependencies**: ModelBridge.synthesize() (done). May want a dedicated summary prompt template.

---

## PHASE 18 — Connection Lifecycle Management (O-015)

**Why**: BaseManifold has a `_connection` attribute set by the factory but never formally closed. No context manager. Tests manually call `m.connection.close()`. Risk of leaked connections on disk manifolds.

**What needs to happen**:

- [ ] **18.1 · Add `close()` method to BaseManifold** — Closes the SQLite connection if present. No-op for RAM manifolds.

- [ ] **18.2 · Add `__enter__` / `__exit__`** — Support `with ManifoldFactory.open_manifold("db") as m:` pattern.

- [ ] **18.3 · Update factory** — `create_disk_manifold()` and `open_manifold()` return manifolds that are context managers.

- [ ] **18.4 · Update tests** — Use `with` blocks or explicit `close()` to prevent connection leaks.

---

## PHASE 19 — Multi-Provider Model Bridge

**Why**: Currently locked to Ollama. Future needs: OpenAI API, Anthropic Claude, local HuggingFace models, etc.

**What needs to happen**:

- [ ] **19.1 · Provider abstraction** — Extract an interface/ABC that ModelBridge implements. New providers implement the same interface.

- [ ] **19.2 · Provider registry** — Select provider by config string (e.g., `provider: "ollama"`, `provider: "openai"`).

- [ ] **19.3 · At least one additional provider** — OpenAI-compatible API is the most useful second target.

- [ ] **19.4 · Provider-specific config** — Each provider has its own config shape (API keys, base URLs, model names, etc.).

**Dependencies**: ModelBridge (done), ModelBridgeConfig (done), ModelBridgeContract ABC (done).

---

## PHASE 20 — Advanced Extraction Strategies (O-026)

**Why**: Currently only `gravity_greedy` (BFS from top-gravity seeds). Different query types benefit from different extraction shapes.

**What needs to happen**:

- [ ] **20.1 · `neighborhood_cluster` strategy** — Community detection to extract dense subgraph neighborhoods rather than ego-graphs.

- [ ] **20.2 · `path_trace` strategy** — Find shortest paths between high-gravity nodes. Good for reasoning queries that need logical chains.

- [ ] **20.3 · `query_focus` strategy** — Bias expansion toward query-adjacent nodes using spreading activation scores.

- [ ] **20.4 · Strategy selection via ExtractionConfig** — Add `strategy: str = "gravity_greedy"` field to ExtractionConfig.

**Location**: `src/core/extraction/extractor.py`

---

## PHASE 21 — Pipeline Caching (O-029)

**Why**: Every `run()` call recomputes everything from scratch. If the same manifolds and query repeat, projection/fusion/scoring could be cached.

**What needs to happen**:

- [ ] **21.1 · Cache key computation** — Hash of manifold contents + query + config = cache key.

- [ ] **21.2 · Cache layer** — LRU or TTL cache for scored VirtualManifold, EvidenceBag, HydratedBundle.

- [ ] **21.3 · Cache invalidation** — When manifold contents change, cached results for that manifold are invalidated.

- [ ] **21.4 · Optional** — Cache should be opt-in via PipelineConfig flag.

---

## PHASE 22 — Streaming Pipeline Results (O-030)

**Why**: `run()` returns only after all stages complete. No way to observe intermediate artifacts progressively. Important for UI responsiveness.

**What needs to happen**:

- [ ] **22.1 · Callback interface** — `run()` accepts optional `on_stage_complete(stage_name, artifact)` callback.

- [ ] **22.2 · Generator variant** — `run_stream()` that yields `(stage_name, artifact)` tuples as each stage completes.

- [ ] **22.3 · Early-stop** — Caller can signal stop after any stage (e.g., stop after scoring to inspect scores without running extraction).

---

## Open Opportunities (not phased yet)

These are tracked in `docs/OPPORTUNITIES.md` and may be rolled into phases above or addressed ad-hoc:

- [~] **O-005** · Fusion/query projection timing instrumentation (projection core done, fusion/query not yet)
- [~] **O-008** · Failed bridge requests not returned in FusionResult for programmatic access
- [ ] **O-010** · NewType IDs have no runtime validation (consider boundary validators)
- [ ] **O-012** · Auto-bridging is O(identity × external) per shared key (quadratic risk)
- [~] **O-014** · Magic numbers: `[:100]` query label truncation, `1.3`/`+1` token heuristic still inline
- [ ] **O-016** · Fusion provenance has no upstream chain (upstream_ids empty)
- [ ] **O-017** · Projection doesn't track requested-vs-found counts
- [ ] **O-018** · Dataclass repr is verbose for large objects (compact __repr__ needed)
- [~] **O-020** · friction.py and annotator.py still run silently (scoring.py logging done)
- [ ] **O-022** · Spreading activation has no max-activation cap
- [ ] **O-023** · Propagation-based graph activation for extraction
- [ ] **O-024** · Alias and canonicalization layer
- [ ] **O-025** · Advanced token packing (knapsack)
- [ ] **O-027** · Structural graph metrics for extraction quality

---

## Orphaned / Housekeeping Items

These are cleanup items identified during the Phase 10 audit:

- [ ] **Orphaned ABCs** — `EvidenceBagContract` and `HydrationContract` have no implementations. Both subsystems went functional (free functions) instead of OOP. Options: remove the ABCs, or wrap the functions in classes that implement them.
- [ ] **16 unused imports** — Cosmetic. Identified in Phase 10 audit. Low priority.
- [ ] **app.py is bootstrap-only** — No query path. Addressed by Phase 13 above.
- [ ] **Placeholder re-export shims** — `scoring_placeholders.py`, `extractor_placeholder.py`, `hydrator_placeholder.py` exist only for backward-compat import paths. Can be removed when confident no legacy imports remain.

---

## Priority Order (suggested)

| Priority | Phase | Why |
|----------|-------|-----|
| **1 (critical)** | Phase 12 — Ingestion | Can't query without data |
| **2 (critical)** | Phase 13 — CLI Query | Can't use the system without a query path |
| **3 (high)** | Phase 14 — UI Interface | Explicit user request |
| **4 (medium)** | Phase 15 — Weighted PageRank | Scoring accuracy, small change |
| **5 (medium)** | Phase 16 — ScoringConfig | Config hygiene, small change |
| **6 (medium)** | Phase 18 — Connection Lifecycle | Resource safety, small change |
| **7 (medium)** | Phase 17 — SUMMARY Hydration | Feature completeness |
| **8 (low)** | Phase 19 — Multi-Provider Bridge | Flexibility |
| **9 (low)** | Phase 20 — Extraction Strategies | Advanced feature |
| **10 (low)** | Phase 21 — Pipeline Caching | Performance optimization |
| **11 (low)** | Phase 22 — Streaming Pipeline | UX enhancement |

Phases 15, 16, and 18 are small enough to bundle into a single "hardening II" phase if preferred.

---

## North Star — Agent-Driven Project Interface

The long-term target for Graph Manifold is a **general-purpose agent interface for working on any software project**. Not a self-aware system — a project-aware tool where the project under development is loaded into the manifold and an AI agent reasons over it, proposes changes, and executes them in a controlled loop.

**The model**:

- **External manifold** = the target project (code, docs, configs, tests — any repo)
- **Identity manifold** = the agent's working context (session state, prior queries, accumulated understanding)
- **Query pipeline** = the agent asks questions about the project and gets gravity-ranked, topology-preserving evidence bags grounded back to source
- **Sandbox execution** = the agent proposes changes against a **sandboxed copy** of the project, never touching live state
- **Version-tagged diffs** = changes are captured as graph deltas against a tagged manifold version. Each delta carries provenance linking it to the version it branched from
- **Approval gate** = human reviews the diff. If accepted, the delta applies as a new versioned state in the project's manifold history. If rejected, the sandbox VM is destroyed

**Key architectural properties**:

- The manifold versions itself using its own primitives — content-addressed chunks + provenance chains give Merkle-like history without needing git
- The sandbox is just another Virtual manifold — ephemeral, derived, disposable
- The agent is not special-cased. It uses the same `RuntimeController.run()` pipeline as any other consumer. The "self-diagnosis" case (agent working on Graph Manifold's own code) is an emergent property of pointing the tool at its own repo

**Context isolation principle**:

Every manifold load is a deliberate, bounded act. The agent has no ambient self-awareness, no residual context bleeding between projects, and no implicit cross-referencing between separate loads. When the agent works on project X, it knows project X — nothing else.

- Loading the agent's own repo is not "self-awareness." It is the same retrieval pipeline processing data that happens to be its own source code. The agent does not get special access, special treatment, or special framing because the target is itself.
- Cross-project context (e.g., comparing two repos, or letting the agent reference its own architecture while working on another project) is only permitted through **explicit, intentional fusion** — never through leakage, ambient state, or accumulated memory across sessions.
- Automated self-curation cycles (learning, cleanup, optimization of its own manifolds) are valid use cases, but must always be **intentional acts** — triggered deliberately, scoped clearly, and never running as invisible background processes that the user hasn't chosen to enable.
- The system is honest about what it is at every level. The agent is a tool. The manifold is a data structure. The graph is a representation. None of these pretend to be more than what they are.

**Theoretical grounding**: See `docs/TRANSLATION_THEORY.md` — ingestion as translation between representational bases, the round-trip guarantee (source → relational space → grounded reconstruction), and the manifold as a "translation lattice of meaning spaces" rather than a database.

**Prerequisites**: Phase 12 (Ingestion), Phase 13 (CLI), Phase 14 (UI), manifold versioning/diff system (not yet phased).

---

*Last updated: Phase 11 (445 tests passing)*
