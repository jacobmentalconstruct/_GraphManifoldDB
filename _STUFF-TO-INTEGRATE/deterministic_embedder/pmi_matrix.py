"""
deterministic_embedder.pmi_matrix
---------------------------------

This module provides utilities to transform raw token co‑occurrence counts
into a sparse matrix of semantic distances using Normalised Pointwise
Mutual Information (NPMI).  The resulting matrix can then be passed to
spectral decomposition routines for dimensionality reduction.

Single responsibility: this module only computes the NPMI and friction
weights and writes them into a sparse matrix.  It does not perform
truncated SVD or any embedding pooling.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np  # Only used for type hints; no heavy use here
from scipy.sparse import dok_matrix, csr_matrix


def build_npmi_matrix(
    pair_counts: Dict[Tuple[int, int], int],
    token_counts: Dict[int, int],
    vocab_size: int,
) -> csr_matrix:
    """Compute a symmetric sparse matrix of friction values from co‑occurrence counts.

    Given the raw co‑occurrence counts ``pair_counts`` and individual token
    frequencies ``token_counts``, this function calculates the normalised
    pointwise mutual information (NPMI) for each observed pair (A, B) and
    converts it into a friction score: ``1.0 - NPMI``.  Values closer to
    zero denote strong association (low friction), while values closer to
    one denote weak or anti‑association (high friction).

    Parameters
    ----------
    pair_counts: Dict[Tuple[int, int], int]
        A mapping from unordered token ID pairs to their co‑occurrence counts.
    token_counts: Dict[int, int]
        A mapping from token ID to its frequency in the corpus.
    vocab_size: int
        The total number of tokens in the vocabulary.  This defines the
        dimensions of the resulting matrix.

    Returns
    -------
    scipy.sparse.csr_matrix
        A symmetric CSR matrix where ``matrix[a, b]`` is the friction between
        tokens ``a`` and ``b``.  Unobserved pairs remain zero.
    """
    # Compute total counts for probability calculations
    total_tokens = sum(token_counts.values())
    total_pairs = sum(pair_counts.values())
    # Avoid division by zero if counts are empty
    if total_tokens == 0 or total_pairs == 0:
        return csr_matrix((vocab_size, vocab_size), dtype=float)
    matrix = dok_matrix((vocab_size, vocab_size), dtype=float)
    for (a, b), count_ab in pair_counts.items():
        # Skip invalid IDs
        if a < 0 or b < 0:
            continue
        # Compute probabilities
        p_ab = count_ab / total_pairs
        p_a = token_counts.get(a, 0) / total_tokens
        p_b = token_counts.get(b, 0) / total_tokens
        # Protect against log(0)
        if p_ab == 0 or p_a == 0 or p_b == 0:
            continue
        # Compute NPMI
        npmi = math.log(p_ab / (p_a * p_b)) / (-math.log(p_ab))
        # Convert to friction (distance)
        friction = 1.0 - npmi
        # Fill symmetric entries
        matrix[a, b] = friction
        matrix[b, a] = friction
    # Convert to compressed row format for downstream SVD
    return matrix.tocsr()
