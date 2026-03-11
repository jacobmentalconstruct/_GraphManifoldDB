"""
run_phase_1.py
--------------

This script executes Phase 1 of the Deterministic Graph‑SVD Embedder
pipeline:

1. Trains the Byte‑Pair Encoding (BPE) tokenizer on a raw text corpus.
2. Generates topological co‑occurrence counts using a sliding window.

Output:

* data/tokenizer.json – vocabulary and merge rules
* data/pair_counts.pkl – serialized co‑occurrence pair counts
* data/token_counts.json – token frequency counts

Usage:

Run this script from the project root.  Ensure a ``corpus/`` folder
containing ``.txt`` files exists.  The script will create a ``data/``
directory and populate it with the phase 1 artifacts.

This script depends on modules in the ``deterministic_embedder`` package
(``tokenizer_trainer.py`` and ``cooccurrence_graph.py``).
"""

import os
import json
import pickle

from deterministic_embedder.tokenizer_trainer import BPETokenizerTrainer
from deterministic_embedder.cooccurrence_graph import compute_counts


def main() -> None:
    """Execute Phase 1 of the deterministic embedding pipeline."""
    # Configuration
    corpus_dir = "corpus"      # Folder containing your .txt files
    output_dir = "data"        # Folder for artifacts
    vocab_size = 5000          # Adjust based on corpus size
    window_size = 5            # Sliding window width

    tokenizer_path = os.path.join(output_dir, "tokenizer.json")
    pair_counts_path = os.path.join(output_dir, "pair_counts.pkl")
    token_counts_path = os.path.join(output_dir, "token_counts.json")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check for corpus
    if not os.path.isdir(corpus_dir) or not os.listdir(corpus_dir):
        print(f"Error: No text files found in '{corpus_dir}'. Please add some .txt files.")
        return

    # Step 1: Train tokenizer
    print(f"--- Step 1: Training BPE Tokenizer (Vocab: {vocab_size}) ---")
    trainer = BPETokenizerTrainer(vocab_size=vocab_size)
    trainer.train(corpus_dir=corpus_dir, output_path=tokenizer_path)
    print(f"Success: Tokenizer saved to {tokenizer_path}")

    # Step 2: Compute co‑occurrence counts
    print(f"--- Step 2: Mapping Co-occurrences (Window: {window_size}) ---")
    pair_counts, token_counts = compute_counts(
        tokenizer_path=tokenizer_path,
        corpus_dir=corpus_dir,
        window_size=window_size,
    )

    # Save token counts as JSON (readable)
    with open(token_counts_path, "w", encoding="utf-8") as f:
        json.dump(token_counts, f, indent=2)

    # Save pair counts as Pickle (tuple keys aren't JSON-friendly)
    with open(pair_counts_path, "wb") as f:
        pickle.dump(pair_counts, f)

    print(f"Success: Token counts saved to {token_counts_path}")
    print(f"Success: Pair counts saved to {pair_counts_path}")
    print("\nPhase 1 Complete. You are ready for Phase 2 (NPMI Friction Matrix).")


if __name__ == "__main__":
    main()