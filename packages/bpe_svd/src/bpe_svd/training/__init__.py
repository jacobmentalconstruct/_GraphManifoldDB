"""bpe_svd.training — offline training pipeline (requires scipy extra).

Install with:  pip install bpe-svd[training]
"""

from bpe_svd.training.bpe_trainer import BPETrainer
from bpe_svd.training.cooccurrence import compute_counts, sliding_window_cooccurrence
from bpe_svd.training.npmi_matrix import build_npmi_matrix
from bpe_svd.training.spectral import compute_embeddings

__all__ = [
    "BPETrainer",
    "compute_counts",
    "sliding_window_cooccurrence",
    "build_npmi_matrix",
    "compute_embeddings",
]
