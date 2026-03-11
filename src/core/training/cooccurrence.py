"""
Co-occurrence Counter — sliding-window token pair statistics.

Ownership: src/core/training/cooccurrence.py
    Owns sliding-window co-occurrence counting over token ID streams.
    Pure statistics: receives pre-tokenised streams, returns counts.
    Does NOT own tokenisation logic — callers encode text before passing
    streams here.

Responsibilities:
    - Slide a fixed-width window over a token ID stream
    - Count unordered (min, max) token pairs within each window
    - Count individual token frequencies
    - Aggregate counts across multiple streams

Design constraints:
    - No side effects at import time
    - Stdlib only (no numpy, no scipy)
    - Single ownership: does not own BPE encoding or NPMI calculation
    - Pairs are canonicalised as (min_id, max_id) for symmetry

# Extracted from: _STUFF-TO-INTEGRATE/deterministic_embedder/cooccurrence_graph.py :: sliding_window_cooccurrence, compute_counts
# Scope: sliding window statistics only
# Rewritten per EXTRACTION_RULES.md — not verbatim copy
# Architecture change: BPETokenizer class dropped (violated single-ownership);
#   compute_counts() now accepts pre-tokenised streams instead of tokenizer path + corpus dir
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Tuple


# ── Core counting functions ──────────────────────────────────────────

def sliding_window_cooccurrence(
    token_stream: Iterable[int],
    window_size: int = 5,
) -> Tuple[Dict[Tuple[int, int], int], Dict[int, int]]:
    """Compute pair co-occurrence counts from a single token ID stream.

    Slides a window of `window_size` over the stream.  For every new
    token, each token already in the window is paired with it.  Pairs
    are stored canonically as (min_id, max_id) for symmetry.

    Parameters
    ----------
    token_stream : Iterable[int]
        Sequence of integer token IDs for one text unit (e.g. one line).
    window_size : int
        Number of tokens to keep in the sliding window (default 5).

    Returns
    -------
    pair_counts : Dict[Tuple[int, int], int]
        Unordered token pair → co-occurrence count within this stream.
    token_counts : Dict[int, int]
        Token ID → frequency within this stream.
    """
    window: deque[int] = deque(maxlen=window_size)
    pair_counts: Dict[Tuple[int, int], int] = defaultdict(int)
    token_counts: Dict[int, int] = defaultdict(int)

    for token in token_stream:
        token_counts[token] += 1
        for seen in window:
            if seen == token:
                continue
            pair = (min(seen, token), max(seen, token))
            pair_counts[pair] += 1
        window.append(token)

    return dict(pair_counts), dict(token_counts)


def compute_counts(
    token_streams: Iterable[List[int]],
    window_size: int = 5,
) -> Tuple[Dict[Tuple[int, int], int], Dict[int, int]]:
    """Aggregate co-occurrence counts over many pre-tokenised streams.

    Calls sliding_window_cooccurrence on each stream and accumulates the
    results into a single global pair_counts and token_counts mapping.

    Parameters
    ----------
    token_streams : Iterable[List[int]]
        One list of token IDs per text unit (sentence, line, document).
        Callers are responsible for encoding text into token IDs before
        passing streams to this function.
    window_size : int
        Sliding window size forwarded to sliding_window_cooccurrence.

    Returns
    -------
    pair_counts : Dict[Tuple[int, int], int]
        Global unordered pair co-occurrence counts.
    token_counts : Dict[int, int]
        Global individual token frequency counts.
    """
    total_pairs: Dict[Tuple[int, int], int] = defaultdict(int)
    total_tokens: Dict[int, int] = defaultdict(int)

    for stream in token_streams:
        line_pairs, line_tokens = sliding_window_cooccurrence(stream, window_size)
        for pair, cnt in line_pairs.items():
            total_pairs[pair] += cnt
        for tok, cnt in line_tokens.items():
            total_tokens[tok] += cnt

    return dict(total_pairs), dict(total_tokens)
