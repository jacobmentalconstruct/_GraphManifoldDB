# Legacy Source Notes

## Rules for Future Extraction Passes

1. The old project is **source material only** — never paste whole scripts
2. Extract only narrow, well-bounded functions or small dataclasses
3. Every extraction must record:
   - Source file path in legacy project
   - Function/class name extracted
   - Target module in this project
   - Date of extraction
4. If a function touches multiple ownership domains, do NOT extract it
5. Adapters in this directory are **temporary bridges**, not final homes

## Legacy Project Location

```
C:\Users\jacob\Documents\_UsefulHelperSCRIPTS\_DeterministicGraphRAG
```

## Extraction Log

| Date | Legacy Source File | Function/Class | Target Module | Notes |
|------|-------------------|----------------|---------------|-------|
| — | — | — | — | No extractions yet (Phase 1 is scaffold only) |
| Phase 12 | `_STUFF-TO-INTEGRATE/deterministic_embedder/inference_engine.py` | `DeterministicEmbedder` (BPE encoding + vector lookup + mean pooling) | `src/core/model_bridge/deterministic_provider.py` | Inference-side only. Rewritten per EXTRACTION_RULES.md. Training pipeline (tokenizer, co-occurrence, PMI, SVD) is separate. |
