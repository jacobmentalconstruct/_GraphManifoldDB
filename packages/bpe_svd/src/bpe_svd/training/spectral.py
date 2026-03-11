"""
Spectral Compression — truncated SVD on the NPMI friction matrix.

Ownership: bpe_svd/training/spectral.py
    Owns the SVD step that compresses the (V × V) sparse friction matrix
    into a dense (V × k) token embedding matrix.  This is the ONLY module
    in src/ that is permitted to import scipy.

Responsibilities:
    - Accept a scipy sparse matrix from npmi_matrix.py
    - Run truncated SVD (scipy.sparse.linalg.svds)
    - Return the top-k left singular vectors (U_k), shape (V, k)
    - Ensure singular values are ordered descending (most significant first)

Design constraints:
    - scipy and numpy imported at module level (training-only dep)
    - Explicit guard for trivial/empty matrices
    - Returns raw U_k (singular values NOT applied as scaling)
    - Single ownership: does not own NPMI calculation or inference pooling

# Extracted from: _STUFF-TO-INTEGRATE/deterministic_embedder/spectral_compression.py :: compute_embeddings
# Scope: truncated SVD + descending sort
# Rewritten per EXTRACTION_RULES.md — not verbatim copy
"""

from __future__ import annotations

import numpy as np  # type: ignore[import-untyped]
from scipy.sparse import spmatrix  # type: ignore[import-untyped]
from scipy.sparse.linalg import svds  # type: ignore[import-untyped]


def compute_embeddings(
    friction_matrix: spmatrix,
    k: int = 300,
) -> np.ndarray:
    """Compute token embeddings via truncated SVD of the friction matrix.

    Decomposes `friction_matrix` ≈ U_k · diag(s_k) · V_k^T and returns
    U_k — the left singular vectors corresponding to the k largest singular
    values.  Each row of U_k is the k-dimensional embedding for one token.

    Parameters
    ----------
    friction_matrix : scipy.sparse.spmatrix
        The symmetric (V × V) friction matrix from build_npmi_matrix().
        Row/column index corresponds to token vocabulary ID.
    k : int
        Number of dimensions to retain (default 300).  Must be less than
        both dimensions of the matrix.

    Returns
    -------
    np.ndarray
        Dense array of shape (V, k).  Row i is the embedding for token i.
        Singular values are NOT applied; vectors are the raw left singular
        vectors from scipy.sparse.linalg.svds.
    """
    v = friction_matrix.shape[0]
    if v == 0 or friction_matrix.shape[1] == 0:
        return np.empty((0, k), dtype=float)

    # Clamp k so it never exceeds what svds supports
    effective_k = min(k, v - 1)
    if effective_k <= 0:
        return np.zeros((v, k), dtype=float)

    # svds returns singular values in ascending order → reverse to descending
    U, _s, _Vt = svds(friction_matrix, k=effective_k)
    U = U[:, ::-1]  # most significant dimension first

    # Pad with zeros if effective_k < k (tiny matrices in tests)
    if effective_k < k:
        padding = np.zeros((v, k - effective_k), dtype=float)
        U = np.hstack([U, padding])

    return U
