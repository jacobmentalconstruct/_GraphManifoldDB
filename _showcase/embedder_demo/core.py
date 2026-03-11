"""Core interface stubs for the BPE-SVD embedder demo.

Every public function here defines the contract that the UI and CLI consume.
Right now they return placeholder data.  When the real embedder is wired in,
only this file changes — the UI and CLI stay untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


# ── Data shapes ──────────────────────────────────────────────────────

@dataclass
class TokenResult:
    """Result of tokenising a single text."""

    text: str
    symbols: List[str]
    token_ids: List[int]


@dataclass
class Hunk:
    """A budget-bounded slice of tokens."""

    index: int
    symbols: List[str]
    token_ids: List[int]
    token_count: int


@dataclass
class ChunkResult:
    """Result of chunking text into budget-bounded hunks."""

    text: str
    budget: int
    hunks: List[Hunk] = field(default_factory=list)
    total_tokens: int = 0


@dataclass
class EmbeddingResult:
    """Vectors produced for a single hunk."""

    hunk_index: int
    vector: List[float]
    dimensions: int
    symbols: List[str]


@dataclass
class NearestToken:
    """A single token recovered by reverse lookup."""

    symbol: str
    similarity: float


@dataclass
class ReverseResult:
    """Nearest tokens recovered from a vector."""

    hunk_index: int
    nearest: List[NearestToken]


# ── Public API (stubs — no embedder wired yet) ───────────────────────

def tokenize(text: str) -> TokenResult:
    """Convert raw text into BPE tokens.

    STUB: returns placeholder tokens.  Will be replaced by the real
    DeterministicEmbedProvider.encode() call.
    """
    # Placeholder: split on characters to simulate BPE output shape
    fake_symbols = list(text.replace(" ", " </w> ").strip().split())
    fake_ids = list(range(len(fake_symbols)))
    return TokenResult(text=text, symbols=fake_symbols, token_ids=fake_ids)


def chunk(text: str, budget: int) -> ChunkResult:
    """Tokenise text and split into budget-bounded hunks.

    STUB: returns placeholder hunks.  Will be replaced by real BPE
    tokenisation with budget-aware slicing.
    """
    tok = tokenize(text)
    hunks: List[Hunk] = []
    for i in range(0, len(tok.symbols), budget):
        slice_syms = tok.symbols[i : i + budget]
        slice_ids = tok.token_ids[i : i + budget]
        hunks.append(
            Hunk(
                index=len(hunks),
                symbols=slice_syms,
                token_ids=slice_ids,
                token_count=len(slice_syms),
            )
        )
    return ChunkResult(
        text=text,
        budget=budget,
        hunks=hunks,
        total_tokens=len(tok.symbols),
    )


def embed_hunk(hunk: Hunk) -> EmbeddingResult:
    """Produce an embedding vector for a single hunk.

    STUB: returns a placeholder vector.  Will be replaced by real
    matrix lookup + mean pooling.
    """
    dims = 8  # placeholder dimensionality (real system uses 300)
    fake_vector = [round(0.1 * (i + hunk.index), 4) for i in range(dims)]
    return EmbeddingResult(
        hunk_index=hunk.index,
        vector=fake_vector,
        dimensions=dims,
        symbols=hunk.symbols,
    )


def reverse_vector(vector: List[float], k: int = 5) -> List[NearestToken]:
    """Find the nearest tokens to a given vector.

    STUB: returns placeholder nearest-token results.  Will be replaced
    by real cosine-similarity search over the embedding matrix.
    """
    placeholders = [
        ("token_a", 0.95),
        ("token_b", 0.87),
        ("token_c", 0.73),
        ("token_d", 0.61),
        ("token_e", 0.44),
    ]
    return [
        NearestToken(symbol=sym, similarity=sim)
        for sym, sim in placeholders[:k]
    ]
