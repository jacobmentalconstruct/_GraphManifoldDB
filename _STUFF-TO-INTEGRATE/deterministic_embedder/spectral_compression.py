"""
deterministic_embedder.spectral_compression
-------------------------------------------

This module performs spectral compression of a sparse friction matrix using
Truncated Singular Value Decomposition (SVD).  It exposes a single
function, ``compute_embeddings``, which takes a CSR matrix and returns
the left singular vectors corresponding to the largest singular values.

The resulting dense matrix can be saved to disk and used for runtime
embedding lookups.  The order of tokens in the embedding matrix must
correspond to the token IDs in the vocabulary produced by the tokenizer.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds


def compute_embeddings(
    matrix: csr_matrix,
    k: int = 300,
) -> np.ndarray:
    """Compute truncated SVD of a sparse matrix to produce token embeddings.

    Parameters
    ----------
    matrix: csr_matrix
        The symmetric friction matrix where rows/columns correspond to
        token IDs and entries represent pairwise distances.  It is
        expected that this matrix has been normalised or scaled prior to
        decomposition if needed.
    k: int, optional
        The number of singular values/vectors to compute (default 300).

    Returns
    -------
    np.ndarray
        A dense matrix of shape ``(vocab_size, k)`` containing the left
        singular vectors (U matrix) associated with the largest singular
        values, ordered from most significant to least.
    """
    # Guard against trivial matrix
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        return np.empty((0, k), dtype=float)
    # Perform truncated SVD
    # svds returns U, s, Vt where singular values are in ascending order
    U, s, Vt = svds(matrix, k=k)
    # Reverse to descending order
    U = U[:, ::-1]
    # Optionally normalise by singular values to balance scale
    # Here we leave U unscaled; downstream consumers can decide
    return U
