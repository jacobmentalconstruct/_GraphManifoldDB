"""
deterministic_embedder.tokenizer_trainer
---------------------------------------

This module implements a minimal, fully deterministic Byte‑Pair Encoding (BPE)
tokeniser trainer.  The goal of this implementation is to provide a reproducible
method for generating a vocabulary and merge rules from an input text corpus
without relying on external dependencies such as HuggingFace's `tokenizers`.

The algorithm is intentionally conservative: it operates at the character
level, appending a special end‑of‑word symbol (``</w>``) to each word before
applying merges.  At each iteration the most frequent adjacent symbol pair is
identified and collapsed into a new symbol until the target vocabulary size
is reached or no more merges can be performed.

The resulting vocabulary and merge sequence are written to a JSON file.  This
JSON file may be consumed by other modules within the deterministic embedder
pipeline for encoding text into token identifiers.

Note: This trainer is not optimised for very large corpora.  For research
purposes and moderate corpora sizes it performs adequately.  If scaling to
hundreds of millions of tokens is required then a more specialised C/Rust
implementation or the HuggingFace ``tokenizers`` library is recommended.

Usage example::

    from deterministic_embedder.tokenizer_trainer import BPETokenizerTrainer

    trainer = BPETokenizerTrainer(vocab_size=10000)
    trainer.train(corpus_dir="data/corpus", output_path="tokenizer.json")

The JSON file will contain keys ``vocab``, ``merges`` and ``end_of_word``.

This file has no side effects at import time and is safe to include as
a reusable module.  It contains only one class, so it adheres to the
"single concern" rule.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class BPETokenizerTrainer:
    """A simple deterministic Byte‑Pair Encoding trainer.

    This class encapsulates the logic necessary to train a BPE model.  It
    consumes a directory of plain text files, tokenises them at the
    character level, and iteratively merges the most frequent adjacent
    symbol pairs until the desired vocabulary size is achieved.

    Parameters
    ----------
    vocab_size: int
        The maximum size of the resulting vocabulary.  This includes the
        initial set of single characters and the special end‑of‑word symbol.
    end_of_word_symbol: str, optional
        A unique string appended to the end of every word.  Defaults to
        ``"</w>"``.  This marker helps the tokenizer distinguish between
        sequences that span word boundaries.
    """

    vocab_size: int = 30000
    end_of_word_symbol: str = "</w>"
    _vocab: Dict[str, int] = field(init=False, default_factory=dict)
    _merges: List[Tuple[str, str]] = field(init=False, default_factory=list)

    def _read_corpus(self, corpus_dir: str) -> List[Tuple[str, ...]]:
        """Read all text files from a directory into a list of words.

        Each word is represented as a tuple of symbols (characters) with
        the ``end_of_word_symbol`` appended.  Non‑text files are ignored.

        Parameters
        ----------
        corpus_dir: str
            Path to a directory containing ``.txt`` files.

        Returns
        -------
        words: List[Tuple[str, ...]]
            A list of words represented as tuples of symbols.
        """
        words: List[Tuple[str, ...]] = []
        for root, _, files in os.walk(corpus_dir):
            for fname in files:
                if not fname.lower().endswith(".txt"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            for word in line.strip().split():
                                # Represent each word as a sequence of characters with an end‑of‑word marker
                                symbols = list(word) + [self.end_of_word_symbol]
                                words.append(tuple(symbols))
                except OSError:
                    # Skip files that cannot be read
                    continue
        return words

    def _init_vocab(self, words: List[Tuple[str, ...]]) -> None:
        """Initialise the vocabulary with individual symbols.

        Parameters
        ----------
        words: List[Tuple[str, ...]]
            The corpus represented as tuples of symbols.
        """
        vocab: Dict[str, int] = {}
        # Reserve ID 0 for unknown tokens if needed in future
        next_id = 0
        for word in words:
            for symbol in word:
                if symbol not in vocab:
                    vocab[symbol] = next_id
                    next_id += 1
        self._vocab = vocab

    @staticmethod
    def _get_pair_frequencies(words: List[Tuple[str, ...]]) -> Dict[Tuple[str, str], int]:
        """Compute the frequency of each adjacent symbol pair in the corpus.

        Parameters
        ----------
        words: List[Tuple[str, ...]]
            The corpus represented as tuples of symbols.

        Returns
        -------
        Dict[Tuple[str, str], int]
            A mapping from symbol pairs to their frequency of occurrence.
        """
        pairs: Dict[Tuple[str, str], int] = defaultdict(int)
        for word in words:
            # Record each adjacent pair
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += 1
        return pairs

    @staticmethod
    def _merge_pair(pair: Tuple[str, str], words: List[Tuple[str, ...]]) -> List[Tuple[str, ...]]:
        """Merge the specified pair of symbols throughout the corpus.

        Parameters
        ----------
        pair: Tuple[str, str]
            The symbol pair to merge (A, B).
        words: List[Tuple[str, ...]]
            The corpus represented as tuples of symbols.

        Returns
        -------
        new_words: List[Tuple[str, ...]]
            The corpus with all occurrences of the specified pair merged.
        """
        a, b = pair
        merged_token = a + b
        new_words: List[Tuple[str, ...]] = []
        for word in words:
            i = 0
            new_word: List[str] = []
            while i < len(word):
                if i < len(word) - 1 and word[i] == a and word[i + 1] == b:
                    # Merge the pair into a single symbol
                    new_word.append(merged_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_words.append(tuple(new_word))
        return new_words

    def train(self, corpus_dir: str, output_path: str) -> None:
        """Train a BPE tokenizer on a directory of text files.

        This procedure reads all ``.txt`` files from ``corpus_dir``, builds
        an initial vocabulary of single symbols, and iteratively merges the
        most frequent adjacent symbol pair until the desired vocabulary size
        is met.  The vocabulary and merge list are then serialized to
        ``output_path`` as JSON.

        Parameters
        ----------
        corpus_dir: str
            Path to the directory containing training text files.
        output_path: str
            Path to the output JSON file.
        """
        words = self._read_corpus(corpus_dir)
        # Initialise vocabulary with single symbols
        self._init_vocab(words)
        # Perform merges until vocab_size is reached
        while len(self._vocab) < self.vocab_size:
            pair_freq = self._get_pair_frequencies(words)
            if not pair_freq:
                break  # no more pairs to merge
            # Select the pair with the highest frequency
            best_pair = max(pair_freq, key=pair_freq.get)
            # Merge the pair throughout the corpus
            words = self._merge_pair(best_pair, words)
            # Record the merge for future encoding
            self._merges.append(best_pair)
            # Add the new token to the vocabulary if it's not already present
            new_token = best_pair[0] + best_pair[1]
            if new_token not in self._vocab:
                self._vocab[new_token] = len(self._vocab)
        # Serialize the vocabulary and merges to JSON
        tokenizer_spec = {
            "vocab": self._vocab,
            "merges": self._merges,
            "end_of_word": self.end_of_word_symbol,
        }
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tokenizer_spec, f, ensure_ascii=False, indent=2)

    @property
    def vocab(self) -> Dict[str, int]:
        """Return the learned vocabulary mapping."""
        return self._vocab

    @property
    def merges(self) -> List[Tuple[str, str]]:
        """Return the list of merges in the order they were applied."""
        return self._merges
