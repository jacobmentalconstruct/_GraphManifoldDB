# Watch List

Tracked architectural concerns, technical debt, and hardening targets.
Each item has an origin phase and a disposition: **watch** (monitor, address when relevant),
**fix** (address in a named phase), or **remove** (delete once superseded).

---

## Architectural Watch Items

### ~~W-001 · Virtual Manifold ID is non-deterministic~~ → ACCEPTED-BY-DESIGN (Phase 10)
- **Origin**: Phase 4 review
- **Status**: accepted-by-design
- **Location**: `src/core/fusion/fusion_engine.py` — VM ID seed includes UTC timestamp
- **Resolution**: VMs are ephemeral working graphs — intentionally non-deterministic IDs (timestamp-seeded). Accepted as permanent policy since VMs are never cached, compared, or persisted. Documented with inline policy comment in fusion_engine.py. HASH_TRUNCATION_LENGTH constant (ids.py) replaces magic `[:16]`.

### ~~W-002 · Label-fallback auto-bridging is low-confidence~~ → RESOLVED (Phase 10)
- **Origin**: Phase 4 review
- **Status**: resolved
- **Location**: `src/core/fusion/fusion_engine.py` — `_auto_bridge_by_key()` label matching
- **Resolution**: Label fallback is now configurable via `FusionConfig` dataclass (fusion_contract.py). `enable_label_fallback` (default True for backward compat), `label_fallback_weight` (default 0.7), `canonical_key_weight` (default 1.0). FusionEngine respects config throughout bridge creation. Wired through PipelineConfig.fusion_config. Ancestry parameters record the policy used.

### ~~W-003 · sys.path insertion in app.py~~ → RESOLVED (Phase 10)
- **Origin**: Phase 1 scaffold
- **Status**: resolved
- **Location**: `src/app.py`
- **Resolution**: Removed `sys.path.insert` hack, `import sys`, and `from pathlib import Path`. Entry point now relies on `pip install -e .` (editable install) or `python -m src.app` (module invocation). pytest.ini `pythonpath = ["."]` handles test execution.

---

## Technical Debt — Placeholder Modules

These are Phase 1 stubs that raise `NotImplementedError`. They will be replaced in their designated phases.

### ~~D-001 · Scoring placeholders~~ → RESOLVED (Phase 5)
- **Location**: `src/core/math/scoring_placeholders.py`
- **Resolution**: Real implementations in `src/core/math/scoring.py`. Placeholders file is now a re-export shim.

### ~~D-002 · Extraction placeholders~~ → RESOLVED (Phase 6)
- **Location**: `src/core/extraction/extractor_placeholder.py`
- **Resolution**: Real implementation in `src/core/extraction/extractor.py`. Placeholders file is now a re-export shim.

### ~~D-003 · Hydration placeholders~~ → RESOLVED (Phase 7)
- **Location**: `src/core/hydration/hydrator_placeholder.py`
- **Resolution**: Real implementation in `src/core/hydration/hydrator.py`. Placeholders file is now a re-export shim.

### ~~D-004 · Model bridge placeholders~~ → RESOLVED (Phase 8)
- **Location**: `src/core/model_bridge/model_bridge.py`
- **Resolution**: Real Ollama HTTP implementation. `embed()` via `/api/embed`, `synthesize()` via `/api/generate`, `estimate_tokens()` with canonical split heuristic, `get_model_identity()` from config.

### ~~D-005 · Runtime controller run()~~ → RESOLVED (Phase 9)
- **Location**: `src/core/runtime/runtime_controller.py`
- **Resolution**: Real pipeline orchestration. `run()` coordinates projection → fusion → scoring → extraction → hydration → synthesis with typed artifact handoffs, stage-boundary logging, PipelineError with stage attribution, and PipelineResult with all intermediate artifacts.

---

## Legacy Migration Targets

Documented "Future extraction targets" in module docstrings. These track which legacy
DeterministicGraphRAG patterns will be extracted into each module.

| Module | Legacy source | Notes |
|--------|--------------|-------|
| `identity_manifold.py` | Mind 2 session seam, Backend orchestrator | Session context, chat history |
| `external_manifold.py` | ContentStoreMS, NetworkX KG, FaissIndexMS, CartridgeServiceMS | CIS chunks, graph structure, vectors, cartridge loading |
| `virtual_manifold.py` | GravityScorerMS, SeamBuilderMS, TokenPackerMS | Gravity scores, seam composition, token packing |
| `query_projection.py` | Query embedding generation, query parsing | Embedding refs, structured intent |
| `identity_projection.py` | NetworkX query API | Selection refinement, batch projection |
| `external_projection.py` | ContentStoreMS, FaissIndexMS | Cartridge queries, chunk-to-vector mapping |
| `fusion_engine.py` | Mind2Manager, Mind3Manager | Seam composition, gravity fusion, bridge patterns |

---

## Resolved

### R-001 · Chunk identity model mismatch (RESOLVED — Phase 4.1)
- `make_chunk_hash()` was location-based (legacy), contradicting the content-addressed Chunk model.
- Fixed: `make_chunk_hash(content)` now hashes text. Legacy helper preserved as `make_legacy_chunk_hash()`.

### R-002 · Scoring placeholders (RESOLVED — Phase 5)
- All five stubs in `scoring_placeholders.py` raised `NotImplementedError`.
- Fixed: Real implementations in `scoring.py` (PageRank, cosine, gravity, min-max, spreading activation). Placeholders file is now a backward-compatible re-export shim.

### R-003 · Extraction placeholders (RESOLVED — Phase 6)
- Three stubs in `extractor_placeholder.py` raised `NotImplementedError`.
- Fixed: Real implementation in `extractor.py` (gravity-greedy extraction with BFS expansion, token budget enforcement, hard limits). Placeholders file is now a backward-compatible re-export shim.

### R-004 · Hydration placeholders (RESOLVED — Phase 7)
- Three stubs in `hydrator_placeholder.py` raised `NotImplementedError`.
- Fixed: Real implementation in `hydrator.py` (content resolution, edge translation, hierarchy context, budget enforcement, three hydration modes). Placeholders file is now a backward-compatible re-export shim.

### R-005 · Model bridge placeholders (RESOLVED — Phase 8)
- Three stubs in `model_bridge.py` raised `NotImplementedError` (`embed()`, `synthesize()`, `estimate_tokens()`).
- Fixed: Real Ollama HTTP backend in same file. `embed()` via `/api/embed`, `synthesize()` via `/api/generate`, `estimate_tokens()` with canonical split heuristic. `ModelBridgeConfig` for endpoint/model configuration. `get_model_identity()` from config.

### R-006 · Runtime controller run() (RESOLVED — Phase 9)
- `run()` was a logging-only placeholder with no pipeline orchestration.
- Fixed: Real pipeline orchestration in `runtime_controller.py`. `run()` coordinates projection → fusion → scoring → extraction → hydration → synthesis. PipelineConfig for unified configuration, PipelineResult for typed artifacts and timing, PipelineError for stage-attributed failures. Stage-boundary logging, RuntimeState lifecycle tracking, graceful degradation when model bridge unavailable.

### R-007 · sys.path hack in app.py (RESOLVED — Phase 10)
- `app.py` contained `sys.path.insert(0, ...)` for direct script execution — fragile bootstrap scaffolding.
- Fixed: Removed entirely. Entry point relies on editable install or module invocation.

### R-008 · Label-fallback bridge policy (RESOLVED — Phase 10)
- Label-fallback auto-bridging was always-on with hidden weight (0.7), no way to control it.
- Fixed: `FusionConfig` dataclass makes label fallback configurable. Can be disabled entirely via `enable_label_fallback=False`. Weights configurable. Wired through PipelineConfig.

### R-009 · VM ID ephemeral policy (ACCEPTED — Phase 10)
- VM IDs were non-deterministic (timestamp-seeded) with no documented policy.
- Accepted-by-design: VMs are ephemeral working graphs. Added inline policy comment, `HASH_TRUNCATION_LENGTH` constant, and test coverage confirming ephemeral behavior.
