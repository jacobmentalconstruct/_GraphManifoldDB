"""
NPMI Friction Matrix Builder — co-occurrence counts → sparse distance matrix.

Ownership: src/core/training/npmi_matrix.py
    Owns NPMI normalisation and the friction transformation.  Converts
    raw pair/token counts (from cooccurrence.py) into a symmetric sparse
    CSR matrix of friction values suitable for truncated SVD.

Responsibilities:
    - Compute marginal and joint co-occurrence probabilities
    - Compute NPMI (Normalised Pointwise Mutual Information)
    - Apply friction transform: friction = 1 - NPMI  (range ~[0, 2])
    - Return a symmetric scipy.sparse.csr_matrix (V × V)

Design constraints:
    - scipy.sparse imported at module level (training-only dependency)
    - numpy NOT imported at module level (math.log used for scalar ops)
    - No side effects at import time
    - Single ownership: does not tokenise text or perform SVD

# Extracted from: _STUFF-TO-INTEGRATE/deterministic_embedder/pmi_matrix.py :: build_npmi_matrix
# Scope: NPMI calculation + friction transformation + sparse matrix construction
# Rewritten per EXTRACTION_RULES.md — not verbatim copy
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from scipy.sparse import csr_matrix, dok_matrix  # type: ignore[import-untyped]


def build_npmi_matrix(
    pair_counts: Dict[Tuple[int, int], int],
    token_counts: Dict[int, int],
    vocab_size: int,
) -> csr_matrix:
    """Build a symmetric sparse friction matrix from co-occurrence counts.

    For each observed token pair (a, b) the friction value is computed as:

        P(a,b) = count(a,b) / total_pair_observations
        P(a)   = count(a)   / total_token_occurrences
        P(b)   = count(b)   / total_token_occurrences

        PMI(a,b)  = log( P(a,b) / (P(a) * P(b)) )
        NPMI(a,b) = PMI(a,b) / ( -log( P(a,b) ) )   ∈ [-1, +1]

        friction(a,b) = 1 - NPMI(a,b)                ∈ [~0, ~2]

    Low friction (≈ 0) means strong association.  High friction (> 1)
    means anti-association.  Independence gives friction ≈ 1.

    Parameters
    ----------
    pair_counts : Dict[Tuple[int, int], int]
        Unordered token pair co-occurrence counts (from cooccurrence.py).
    token_counts : Dict[int, int]
        Per-token frequency counts (from cooccurrence.py).
    vocab_size : int
        Total vocabulary size — defines the matrix dimensions (V × V).

    Returns
    -------
    scipy.sparse.csr_matrix
        Symmetric friction matrix of shape (vocab_size, vocab_size).
        Unobserved pairs have a stored value of 0.
    """
    total_tokens = sum(token_counts.values())
    total_pairs = sum(pair_counts.values())

    if total_tokens == 0 or total_pairs == 0:
        return csr_matrix((vocab_size, vocab_size), dtype=float)

    matrix = dok_matrix((vocab_size, vocab_size), dtype=float)

    for (a, b), count_ab in pair_counts.items():
        if a < 0 or b < 0 or a >= vocab_size or b >= vocab_size:
            continue
        if count_ab == 0:
            continue

        p_ab = count_ab / total_pairs
        p_a = token_counts.get(a, 0) / total_tokens
        p_b = token_counts.get(b, 0) / total_tokens

        if p_a == 0.0 or p_b == 0.0 or p_ab == 0.0:
            continue

        pmi = math.log(p_ab / (p_a * p_b))
        npmi = pmi / (-math.log(p_ab))
        friction = 1.0 - npmi

        matrix[a, b] = friction
        matrix[b, a] = friction

    return matrix.tocsr()
