# Development Log

Chronological record of each implementation phase, what was built, and key decisions made.

---

## Phase 1 — Graph Manifold Scaffold

**Goal**: Create the receiving scaffold for strangler-fig migration from the legacy DeterministicGraphRAG project. Module layout, contracts, base types, placeholders, and a bootable `src/app.py`.

**What was built**:
- Root project files: README.md, pyproject.toml, requirements.txt, .gitignore
- Documentation anchors: ARCHITECTURE.md, PHASE_1_SCOPE.md, EXTRACTION_RULES.md
- Entry point: src/app.py with RuntimeController bootstrap
- Contracts layer: 6 ABC/dataclass contracts (manifold, evidence_bag, hydration, projection, fusion, model_bridge)
- Shared types: ids.py (NewType wrappers), enums.py, manifests.py, runtime_state.py
- Manifold classes: BaseManifold, IdentityManifold, ExternalManifold, VirtualManifold
- Factory & Store: placeholder stubs
- Projection & Fusion: placeholder stubs
- Math / Extraction / Hydration / Model Bridge: placeholder stubs
- Runtime controller: thin bootstrap coordinator
- Adapters: empty layer with extraction tracking template
- Utils: logging_utils.py, file_utils.py
- Tests: test_imports.py (46 modules), test_scaffold_smoke.py

**Key decisions**:
- Strangler-fig pattern: extract narrow functions only, never whole scripts
- Same-schema rule: all manifolds share identical typed collections
- sys.path fix in app.py for direct script execution

**Result**: 61 files, 46/46 tests passing

---

## Phase 2 — Contracts and Core Types

**Goal**: Make the architecture's objects real with typed dataclasses, enums, and concrete contracts. Replace placeholder shapes with production-ready typed structures.

**What was built**:
- ids.py expanded: 9 NewType IDs + deterministic_hash() + make_chunk_hash()
- enums.py expanded: 12 enums (ManifoldRole, StorageMode, NodeType, EdgeType, ProvenanceStage, etc.)
- New type files: graph.py (Node, Edge, Chunk, ChunkOccurrence, Embedding, HierarchyEntry, MetadataEntry), provenance.py (Provenance), bindings.py (NodeChunkBinding, NodeEmbeddingBinding, NodeHierarchyBinding)
- manifests.py: FileManifest/Entry, ProjectManifest/Entry
- runtime_state.py: RuntimeState + ModelBridgeState
- All 6 contracts rewritten with real typed structures and ABCs
- All 4 manifold classes updated with typed collections
- test_phase2_types.py: 51 tests

**Key decisions**:
- Chunk auto-computes byte_length, char_length, token_estimate via __post_init__
- Explicit cross-layer bindings as first-class typed objects (not collapsed into dicts)
- Provenance carries stage enum and relation_origin enum for pipeline traceability

**Result**: 98/98 tests passing

---

## Phase 3 — Persistent Manifold Storage and Factory Basics

**Goal**: Make manifolds persistable via SQLite. Factory creates, store reads/writes, manifold carries connection handle.

**What was built**:
- _schema.py (NEW): Full SQLite DDL with 16 tables, WAL mode, FK enforcement, initialize_schema(), verify_schema()
- manifold_store.py (REWRITTEN): 11 write methods + 11 read methods, all typed, role-agnostic
- manifold_factory.py (REWRITTEN): create_disk_manifold(), create_memory_manifold(), create_manifold() unified dispatcher, open_manifold()
- base_manifold.py updated: _connection attribute + connection property
- test_phase3_storage.py: 42 tests across 11 test classes

**Key decisions**:
- Store is stateless: takes connection + typed objects per call
- Factory sets m._connection = conn on created manifolds
- Schema uses TEXT for all IDs (human-readable when inspecting DB)
- WAL mode for concurrent read performance
- INSERT OR REPLACE for upsert semantics, INSERT OR IGNORE for content-addressed chunks

**Result**: 140/140 tests passing

---

## Phase 4 — Projection and Fusion

**Goal**: Make the Virtual Manifold real as a fused working graph built from persistent manifolds. Implement projection (selecting records from manifolds), query projection (query becomes graph-native), and fusion (combining slices into VirtualManifold with bridge edges).

**What was built**:
- enums.py: Added NodeType.QUERY
- projection_contract.py (REWRITTEN): ProjectedSlice expanded with materialized typed objects (nodes, edges, chunks, embeddings, hierarchy, metadata, provenance, all 3 binding types); QueryProjectionArtifact expanded with query_node_id and query_node; project_by_ids() convenience method on ABC
- fusion_contract.py (REWRITTEN): BridgeRequest dataclass; FusionContract.fuse() retyped from List[Any] to explicit identity_slice/external_slice/query_artifact/bridge_requests parameters
- _projection_core.py (NEW): Shared gather_slice_by_node_ids() with dual SQLite/RAM code path — resolves nodes, finds closed-subgraph edges, gathers linked chunks/embeddings/hierarchy via bindings, stamps PROJECTION provenance
- identity_projection.py (REWRITTEN): Real projector delegating to _projection_core with IDENTITY source_kind
- external_projection.py (REWRITTEN): Real projector delegating to _projection_core with EXTERNAL source_kind
- query_projection.py (REWRITTEN): Creates QUERY-typed Node with deterministic ID, wraps in QueryProjectionArtifact
- fusion_engine.py (REWRITTEN): Mechanical fusion — ingests slices into VirtualManifold, adds query node, processes explicit BridgeRequests, auto-bridges by canonical_key match then label fallback (weight=0.7), stamps FUSION provenance
- test_phase4_projection_fusion.py: 27 tests across 13 test classes

**Bug fixed during testing**: `isinstance(nid, NodeId)` fails because NodeId is a NewType (not a real class). Simplified to always call `NodeId(nid)` since NewType callables are identity functions on strings.

**Key decisions**:
- ProjectedSlice carries actual objects so fusion doesn't need source connections
- Shared projection core handles both SQLite-backed and RAM manifolds
- Bridge creation: explicit requests + auto canonical_key match + label fallback
- Every projected object gets PROJECTION-stage provenance
- Every bridge edge gets FUSION-stage provenance with FUSED origin
- Deterministic IDs for query nodes (query-{hash[:16]}) and bridge edges (bridge-{hash[:16]})

**Result**: 168/168 tests passing (Phases 1-4)

---

## Phase 4.1 — Chunk Identity Correction

**Goal**: Fix an architectural mismatch between the chunk identity model and the hashing helper. The data model (Chunk + ChunkOccurrence in graph.py) is explicitly content-addressed, but the `make_chunk_hash()` helper was computing location-based hashes from the legacy convention.

**The mismatch**:
- graph.py Chunk docstring: "content-addressed: two chunks with the same text produce the same ChunkHash"
- ChunkOccurrence exists specifically to hold location info (source_path, chunk_index)
- But `make_chunk_hash(source_path, chunk_index)` computed `SHA256(source_path:chunk_index)` — location-based, not content-based
- This was inherited from legacy DeterministicGraphRAG which conflated chunk identity with file position

**What was changed**:
- ids.py: `make_chunk_hash(content: str) -> ChunkHash` now hashes chunk text (content-addressed)
- ids.py: `make_legacy_chunk_hash(source_path, chunk_index)` preserved for migration compatibility, marked deprecated
- ids.py: Module docstring updated to document the content-addressed chunk identity model
- ids.py: Removed misleading "Legacy context" comment from deterministic_hash()
- Phase 2 devlog entry: Removed "Deterministic IDs: SHA256 of source_path:chunk_index" which was incorrect
- test_phase2_types.py: Chunk hash tests updated to verify content-addressing; legacy helper tested separately
- test_phase3_storage.py: Updated to use content-based make_chunk_hash()

**Key decisions**:
- Content identity is the canonical model: same text = same ChunkHash, regardless of file origin
- Location tracking is ChunkOccurrence's job, not ChunkHash's
- Legacy helper preserved (not deleted) for future migration from old DeterministicGraphRAG data
- No schema changes needed — the schema already uses `chunk_hash TEXT PRIMARY KEY` which is agnostic to how the hash is computed

**Result**: 171/171 tests passing (3 new tests added for content-addressing + legacy helper)

---

## Phase 5 — Scoring and Graph Math

**Goal**: Make the VirtualManifold think. Replace placeholder scoring stubs with real algorithms: PageRank for structural importance, cosine similarity for semantic relevance, and gravity fusion to combine both into a single ranking signal. Add friction detection for scoring pathology diagnosis and an annotation bridge to write scores into VirtualManifold runtime_annotations.

**Pre-flight checks passed**:
- `VirtualManifold.runtime_annotations: Dict[NodeId, Dict[str, Any]]` exists — scores stored here
- `NodeEmbeddingBinding` provides direct node→embedding access for semantic scoring
- `ScoreAnnotation` dataclass already defined in `evidence_bag_contract.py`

**What was built**:
- scoring.py (NEW): 5 real algorithms — `normalize_min_max`, `structural_score` (PageRank power iteration), `semantic_score` (cosine similarity), `gravity_score` (fused α·S + β·T), `spreading_activation` (BFS decay propagation)
- friction.py (NEW): 3 friction detectors — `detect_island_effect` (disconnected components), `detect_gravity_collapse` (narrow spread), `detect_normalization_extrema` (all-zero scores), plus `detect_all_friction` summary
- annotator.py (NEW): Score→VM annotation bridge — `annotate_scores()` writes ScoreAnnotation to `vm.runtime_annotations[nid]["score"]`, `read_score_annotation()` reads back
- scoring_placeholders.py (REWRITTEN): Re-export shim for backward compatibility — no more NotImplementedError
- math/__init__.py (UPDATED): Public re-exports from scoring, friction, and annotator modules
- debug/__init__.py (NEW): Debug package for development-time inspection
- debug/score_dump.py (NEW): `dump_virtual_scores(vm)` extracts readable scoring summary with per-node scores and top-10 gravity ranking
- test_phase5_scoring.py (NEW): 49 tests across 9 test classes
- test_imports.py (UPDATED): Added 5 new module import checks

**Key decisions**:
- Pure Python — no numpy, no NetworkX. PageRank is power iteration, cosine is dot product. Works for sub-10K node graphs.
- Graph parameters typed as `Any` (duck typing: `get_nodes()`, `get_edges()`). Math layer depends only on `ids.NodeId` from types — no manifold imports.
- Determinism via `sorted()` iteration throughout. Same inputs → identical outputs.
- Spreading activation uses undirected adjacency — activation propagates both ways through edges.
- Annotator uses canonical key `"score"` — `vm.runtime_annotations[nid]["score"] = ScoreAnnotation(...)`. Downstream consumers know exactly where to find scores.
- scoring_placeholders.py preserved as re-export shim so old import paths still work.

**Result**: 220/220 tests passing (Phases 1-5)

---

## Phase 6 — Evidence Bag Extraction

**Goal**: Extract deterministic, graph-native evidence bags from scored VirtualManifolds. An evidence bag is a bounded contextual subgraph — the minimal set of evidence required to answer a query. It preserves graph topology (nodes, edges, chunk refs, hierarchy refs, score annotations) until hydration in Phase 7.

**What was built**:
- extractor.py (NEW): `ExtractionConfig` dataclass (6 configurable limits) and `extract_evidence_bag(vm, config)` entry point with gravity-greedy algorithm — rank nodes by gravity, select seeds, BFS expand, collect chunk/hierarchy bindings, enforce token budget with hard caps
- extractor_placeholder.py (REWRITTEN): Re-export shim for backward compatibility — no more NotImplementedError
- extraction/__init__.py (UPDATED): Public re-exports for ExtractionConfig and extract_evidence_bag
- test_phase6_extraction.py (NEW): 40 tests across 13 test classes
- test_imports.py (UPDATED): Added extraction.extractor module check

**Key decisions**:
- Single extraction module — all logic in `extractor.py` with small internal helpers. No need for separate ranker/budget/traversal files at this scale.
- VM parameter duck-typed as `Any` — same pattern as scoring.py. Avoids coupling extraction to manifold imports.
- Skip-not-break on budget overflow — when a node's chunks exceed remaining budget, skip it and try smaller nodes later in gravity order. Maximizes evidence within budget.
- Edge limit is secondary — nodes selected first, edges filtered to connecting selected nodes only, then truncated to `max_edges`. Edges cannot cause node removal.
- Chunk truncation per node — if a node's full chunk list would bust `max_chunks`, include the node with truncated chunks. Preserves graph topology even without full text.
- Deterministic bag ID — `deterministic_hash(sorted_node_ids + manifold_id)`. Same VM + same config = same bag.
- Read-only extraction — VM is never modified. Same VM can be extracted multiple times with different configs.
- Reuses existing contracts — EvidenceBag, TokenBudget, EvidenceBagTrace, ScoreAnnotation all already defined in evidence_bag_contract.py. No new contract types needed.

**Result**: 260/260 tests passing (Phases 1-6)

---

## Phase 7 — Evidence Hydration

**Goal**: Materialise evidence bag references into structured, model-readable content. Resolve chunk text, hierarchy context, and edge relationships from the VirtualManifold. Produce HydratedBundle using existing contract types with deterministic output ordering and optional budget enforcement.

**What was built**:
- hydrator.py (NEW): `HydrationConfig` dataclass and `hydrate_evidence_bag(bag, vm, config)` entry point with content resolution, hierarchy resolution, edge translation, budget enforcement, and three hydration modes (FULL, SUMMARY, REFERENCE)
- hydrator_placeholder.py (REWRITTEN): Re-export shim for backward compatibility — no more NotImplementedError
- hydration/__init__.py (UPDATED): Public re-exports for HydrationConfig, hydrate_evidence_bag, and backward-compatible helpers
- test_phase7_hydration.py (NEW): 38 tests across 13 test classes
- test_imports.py (UPDATED): Added hydration.hydrator module check

**Key decisions**:
- Single hydration module — all logic in `hydrator.py` with small internal helpers. Same pattern as scoring.py and extractor.py.
- VM parameter duck-typed as `Any` — accesses get_nodes(), get_edges(), get_chunks(), get_hierarchy(). Same pattern as extraction.
- Reuses existing contract types — HydratedBundle, HydratedNode, HydratedEdge from hydration_contract.py. Score annotations stored in HydratedNode.metadata["score"], hierarchy context in metadata["hierarchy"], provenance and budget metadata in HydratedBundle.properties.
- Node order preserved from EvidenceBag (gravity-descending from extraction). Edge sort by (source_id, target_id, edge_id) for stable secondary ordering.
- Budget enforcement truncates from end — lowest gravity nodes removed first. At least one node always kept. topology_preserved flag set to False when truncation occurs. Edges to dropped nodes are filtered out.
- Three modes: FULL resolves all chunk text, REFERENCE returns empty content with chunk hashes for traceability, SUMMARY behaves as FULL for now (real summarization requires model calls in Phase 8+).
- Defensive resolution — missing chunks, edges, or nodes in VM are silently skipped. Hydration does not crash on partial VMs.
- Read-only — neither VM nor EvidenceBag is modified. Same bag can be hydrated multiple times with different configs.
- Backward-compatible helpers: hydrate_node_payloads(), translate_edges(), format_evidence_bundle() match Phase 1 placeholder signatures and are re-exported by the shim.

**Result**: 299/299 tests passing (Phases 1-7)

---

## Phase 8 — Model Bridge

**Goal**: Replace the three `NotImplementedError` stubs in `ModelBridge` with a real Ollama HTTP backend. Make the system capable of embedding text, synthesizing answers, and estimating tokens through one controlled boundary.

**What was built**:
- model_bridge.py (REWRITTEN): `ModelBridgeConfig` dataclass, `ModelBridgeError` hierarchy (ModelBridgeError → ModelConnectionError / ModelResponseError), and `ModelBridge` class with Ollama HTTP backend — `embed()` via `/api/embed`, `synthesize()` via `/api/generate`, `estimate_tokens()` with canonical split heuristic, `get_model_identity()` from config
- model_bridge/__init__.py (UPDATED): Public re-exports for ModelBridge, ModelBridgeConfig, error classes
- test_phase8_model_bridge.py (NEW): 37 tests across 12 test classes (all mocked, no live Ollama server required)

**Key decisions**:
- Ollama HTTP as the sole Phase 8 backend. No multi-provider abstraction. Code structured so a provider layer can be extracted later but not built now.
- stdlib `urllib.request` for HTTP — no external dependencies. Pure Python constraint maintained.
- `estimate_tokens()` is bridge-canonical: uses `int(len(text.split()) * 1.3 + 1)` heuristic matching Chunk.__post_init__. Works offline, no running server needed. Future upgrade path: swap for real tokenizer.
- `get_model_identity()` is config-driven — no HTTP call to discover model metadata.
- Bridge does NOT own prompt construction. `SynthesisRequest.evidence_context` and `.query` arrive pre-built. Bridge translates to Ollama format and sends.
- Model resolution order: request.model → config model → raise ModelBridgeError. Each method resolves independently.
- Explicit error hierarchy: `ModelConnectionError` for network failures, `ModelResponseError` for data failures. Both extend `ModelBridgeError`.
- All tests mock `_http_post` via `unittest.mock.patch.object`. No live Ollama server required to pass the phase.
- Not built: streaming, multi-provider routing, retry chains, embedding caching, batch orchestration, prompt templating, structured output parsing, tokenizer plugins.

**Result**: 336/336 tests passing (Phases 1-8)

---

## Phase 9 — Runtime Pipeline Orchestration

**Goal**: Replace the no-op `RuntimeController.run()` with a real orchestration path that coordinates all completed subsystems in sequence: projection → fusion → scoring → extraction → hydration → synthesis. The controller remains a thin coordination seam — it calls subsystems but does not reimplement their algorithms.

**What was built**:
- runtime_controller.py (REWRITTEN): `PipelineConfig` dataclass (scoring weights, sub-configs, synthesis params), `PipelineResult` dataclass (all intermediate artifacts, timing, degraded flag), `PipelineError` exception with stage attribution, and `RuntimeController.run()` with 6 private stage methods (`_run_projection`, `_run_fusion`, `_run_scoring`, `_run_extraction`, `_run_hydration`, `_run_synthesis`) plus `_gather_node_embeddings` helper
- runtime/__init__.py (UPDATED): Public re-exports for PipelineConfig, PipelineResult, PipelineError
- test_phase9_pipeline.py (NEW): 37 tests across 11 test classes (all mocked, no live server)

**Key decisions**:
- Controller stays thin — each stage method is a ~10–20 line wrapper calling a subsystem API. No computation, no formatting, no scoring in the controller.
- Typed artifacts as handoffs: ProjectedSlice → FusionResult → scored VM → EvidenceBag → HydratedBundle → SynthesisResponse. No loose dicts at any boundary.
- Controller does NOT embed the query — per the system map, that responsibility belongs to QueryProjection (future O-028). Semantic scoring falls back to structural-only gravity when no embeddings are available.
- RuntimeState lifecycle tracking: existing fields (manifold IDs, evidence_bag_id, current_query) updated during execution, plus stage tracking via session_metadata (bootstrap_complete, current_stage, last_successful_stage, last_error).
- Stage-aware error handling: `PipelineError(stage, message, cause)` gives stage attribution. ModelConnectionError during synthesis → graceful degradation, not crash. All other stage failures → PipelineError with failing stage name.
- Provenance preserved, not generated — controller passes provenance-bearing artifacts through intact. Subsystems own their own provenance creation.
- Context formatting delegated to `format_evidence_bundle()` from hydrator.py — controller does not own formatting logic.
- app.py unchanged — stays as thin bootstrap entry point.
- Not built: streaming, multi-query orchestration, retry chains, caching, agent loops, query embedding generation (O-028).

**Result**: 373/373 tests passing (Phases 1-9)

---

## Phase 10 — Hardening / Stabilization / Policy Tightening

**Goal**: Fortify existing architecture without adding new features. Resolve tracked watch items, address logged opportunities, harden boundaries, add observability, and expand debug tooling.

**What was built**:
- **Packaging cleanup**: Removed `sys.path.insert` hack from `app.py`. Entry point now relies on editable install (`pip install -e .`) or module invocation (`python -m src.app`).
- **Fusion policy hardening**: Added `FusionConfig` dataclass to `fusion_contract.py` — `enable_label_fallback`, `label_fallback_weight`, `canonical_key_weight`. FusionEngine respects config throughout bridge creation. Wired through `PipelineConfig.fusion_config` into the runtime pipeline.
- **VM ID ephemeral policy**: Documented W-001 as accepted-by-design. Added `HASH_TRUNCATION_LENGTH = 16` named constant in `ids.py`, replacing magic `[:16]` across fusion_engine.py and query_projection.py.
- **Observability pass**: Added structured logging to `_projection_core.py` (node resolution counts, timing summary), `fusion_engine.py` (bridge type breakdown, auto-bridge policy decisions, ancestry parameters), `scoring.py` (PageRank convergence stats), `manifold_store.py` (DEBUG-level write logging).
- **Validation pass**: `manifold_store.py` now validates non-empty IDs before SQL execution — `add_node()`, `add_edge()`, `add_chunk()` raise `ValueError` on empty required fields. Self-loop edges emit warnings. JSON deserialization failures (`_json_loads`, `_json_loads_list`) now log warnings instead of failing silently.
- **Debug tooling expansion**: New `src/core/debug/inspection.py` with 5 structured dump functions — `dump_projection_summary()`, `dump_fusion_result()`, `dump_evidence_bag()`, `dump_hydrated_bundle()`, `inspect_pipeline_result()`. All exported from `debug/__init__.py`.
- **Performance fix**: `_projection_core.py` now pre-indexes bindings via `_build_binding_index()` for O(1) per-node lookup, replacing the O(nodes × bindings) scan on the RAM code path (O-011).
- **Timing instrumentation**: Projection core times entire `gather_slice_by_node_ids()` operation and logs duration in summary line.

**Key decisions**:
- FusionConfig is a policy object, not a feature. Makes previously-hidden defaults explicit and configurable without adding new capabilities.
- Label fallback stays enabled by default for backward compatibility. Can be disabled via `FusionConfig(enable_label_fallback=False)`.
- VM ID non-determinism (W-001) accepted-by-design: VMs are ephemeral working graphs, not persistent or cached entities.
- Debug inspection helpers are duck-typed (`Any` parameters) to avoid coupling debug tooling to specific class imports.
- No new subsystems, no architecture changes, no new contract types (FusionConfig added to existing fusion_contract.py).

**Result**: 416/416 tests passing (373 existing + 43 new Phase 10 tests)

---

## Phase 11 — Query Embedding Integration / Semantic Scoring Activation

**Goal**: Activate the semantic half of the scoring system by making QueryProjection produce a query embedding, so scoring can use both structural centrality and semantic similarity to the query. Closes O-028 — the single high-severity gap identified in the Phase 10 audit.

**What was built**:
- **QueryProjection embed_fn callback**: `QueryProjection.project()` now accepts an optional `embed_fn: Callable[[str], Sequence[float]]` keyword argument. When provided, the raw query is embedded and the vector is stored in `QueryProjectionArtifact.properties["query_embedding"]`. Embedding failure is non-fatal — logged as warning, pipeline falls back to structural-only scoring.
- **RuntimeController embed wiring**: `_run_projection()` builds an embed callback from `ModelBridge.embed()` when a bridge is available. The callback wraps `EmbedRequest(texts=[text])` → extracts first vector from `EmbedResponse.vectors`. Keeps QueryProjection decoupled from ModelBridge — it receives a capability, not a backend object.
- **Semantic scoring activation**: The existing scoring stage code in `_run_scoring()` already checked for `query_artifact.properties["query_embedding"]` — it now receives actual embeddings when a model bridge is available. Semantic scoring fires, gravity formula uses both `alpha*S + beta*T`, and score annotations include non-zero semantic components.
- **Logging and visibility**: QueryProjection logs embedding success (with dimensions), failure (with error), or skip (no embed_fn). RuntimeController logs embedding presence in projection summary. Scoring logs whether semantic path was activated or skipped.
- **EmbedFn type alias**: Exported from `query_projection.py` as `EmbedFn = Callable[[str], Sequence[float]]` for external consumers.

**Key decisions**:
- **Callback injection (Option A)**: QueryProjection receives `embed_fn`, not a full ModelBridge object. This preserves ownership boundaries — Projection doesn't know about backend/provider details, RuntimeController owns the wiring, ModelBridge remains the only embedding provider.
- **Non-fatal embed failure**: Embedding errors are caught, logged, and recorded in `artifact.properties["query_embedding_error"]`. The pipeline continues with structural-only gravity. This maintains the existing graceful degradation behavior.
- **No new contract types**: Query embedding stored in the existing `properties: Dict[str, Any]` on QueryProjectionArtifact. No new dataclass fields needed.
- **Scoring code unchanged**: The `_run_scoring()` code that reads `query_embedding` from the artifact was already written in Phase 9 — it just never received non-None input until now. Phase 11 didn't touch scoring.py at all.
- **Not bundled**: No ScoringConfig, no weighted PageRank, no alias registry, no extraction strategies, no app.py CLI. Scope stayed narrow.

**Files changed**:
- `src/core/projection/query_projection.py` (MODIFIED) — embed_fn parameter, logging, EmbedFn type alias
- `src/core/runtime/runtime_controller.py` (MODIFIED) — embed callback wiring, updated docstring, EmbedRequest import
- `tests/test_phase11_query_embedding.py` (NEW) — 29 tests across 7 test classes

**Result**: 445/445 tests passing (416 existing + 29 new Phase 11 tests)
