"""BPE-SVD Embedder Demo — Command-Line Interface.

Usage:
    python -m embedder_demo.cli tokenize  "hello world"
    python -m embedder_demo.cli chunk     "hello world" --budget 10
    python -m embedder_demo.cli embed     "hello world" --budget 10
    python -m embedder_demo.cli reverse   "hello world" --budget 10 --top-k 5
    python -m embedder_demo.cli pipeline  "hello world" --budget 10
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from embedder_demo import core


# ── Formatters ───────────────────────────────────────────────────────

BLUE = "\033[94m"
PURPLE = "\033[95m"
GREEN = "\033[92m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _header(title: str):
    print(f"\n{BLUE}{BOLD}{'=' * 60}{RESET}")
    print(f"{BLUE}{BOLD}  {title}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 60}{RESET}")


def _kv(key: str, value: str):
    print(f"  {DIM}{key:>14s}{RESET}  {value}")


def _tokens_line(symbols: List[str]):
    parts = []
    for s in symbols:
        colour = PURPLE if s == "</w>" else BLUE
        parts.append(f"{colour}[{s}]{RESET}")
    print(f"  {' '.join(parts)}")


def _vector_line(vector: List[float], label: str = ""):
    vals = "  ".join(f"{v:+.4f}" for v in vector[:12])
    suffix = "  ..." if len(vector) > 12 else ""
    prefix = f"  {DIM}{label:>12s}{RESET}  " if label else "  "
    print(f"{prefix}[{vals}{suffix}]")


# ── Commands ─────────────────────────────────────────────────────────

def cmd_tokenize(args: argparse.Namespace):
    result = core.tokenize(args.text)

    _header("Tokenize")
    _kv("input", args.text[:72] + ("..." if len(args.text) > 72 else ""))
    _kv("token count", str(len(result.symbols)))
    _kv("token IDs", str(result.token_ids))
    print()
    _tokens_line(result.symbols)
    print()

    if args.json:
        _dump_json({
            "symbols": result.symbols,
            "token_ids": result.token_ids,
        })


def cmd_chunk(args: argparse.Namespace):
    result = core.chunk(args.text, args.budget)

    _header(f"Chunk  (budget={args.budget})")
    _kv("total tokens", str(result.total_tokens))
    _kv("hunks", str(len(result.hunks)))
    print()

    for hunk in result.hunks:
        print(f"  {GREEN}{BOLD}Hunk {hunk.index}{RESET}"
              f"  {DIM}({hunk.token_count} tokens){RESET}")
        _tokens_line(hunk.symbols)
        print()

    if args.json:
        _dump_json({
            "total_tokens": result.total_tokens,
            "hunks": [
                {
                    "index": h.index,
                    "symbols": h.symbols,
                    "token_ids": h.token_ids,
                    "token_count": h.token_count,
                }
                for h in result.hunks
            ],
        })


def cmd_embed(args: argparse.Namespace):
    chunk_result = core.chunk(args.text, args.budget)

    _header(f"Embed  ({len(chunk_result.hunks)} hunks)")

    embed_results = []
    for hunk in chunk_result.hunks:
        res = core.embed_hunk(hunk)
        embed_results.append(res)

        print(f"  {GREEN}{BOLD}Hunk {res.hunk_index}{RESET}"
              f"  {DIM}→ {res.dimensions}d vector{RESET}")
        _tokens_line(res.symbols)
        _vector_line(res.vector, label="embedding")
        print()

    if args.json:
        _dump_json({
            "embeddings": [
                {
                    "hunk_index": r.hunk_index,
                    "dimensions": r.dimensions,
                    "vector": r.vector,
                    "symbols": r.symbols,
                }
                for r in embed_results
            ],
        })


def cmd_reverse(args: argparse.Namespace):
    chunk_result = core.chunk(args.text, args.budget)

    _header(f"Reverse  (top-{args.top_k} nearest)")

    for hunk in chunk_result.hunks:
        emb = core.embed_hunk(hunk)
        nearest = core.reverse_vector(emb.vector, k=args.top_k)

        print(f"  {GREEN}{BOLD}Hunk {emb.hunk_index}{RESET}"
              f"  {DIM}nearest tokens:{RESET}")

        for nt in nearest:
            bar = "#" * int(nt.similarity * 20)
            print(f"    {BLUE}[{nt.symbol:>10s}]{RESET}"
                  f"  {PURPLE}{bar:<20s}{RESET}"
                  f"  {DIM}cos={nt.similarity:+.4f}{RESET}")
        print()

    if args.json:
        _dump_json({"note": "reverse results in JSON not yet implemented"})


def cmd_pipeline(args: argparse.Namespace):
    """Run the full pipeline: tokenize → chunk → embed → reverse."""
    _header("Full Pipeline")

    # Tokenize
    tok = core.tokenize(args.text)
    _kv("tokens", str(len(tok.symbols)))
    _tokens_line(tok.symbols)
    print()

    # Chunk
    ch = core.chunk(args.text, args.budget)
    _kv("hunks", str(len(ch.hunks)))
    print()

    # Embed + Reverse
    for hunk in ch.hunks:
        emb = core.embed_hunk(hunk)
        nearest = core.reverse_vector(emb.vector, k=args.top_k)

        print(f"  {GREEN}{BOLD}Hunk {emb.hunk_index}{RESET}")
        _tokens_line(emb.symbols)
        _vector_line(emb.vector, label="vector")

        print(f"    {DIM}nearest:{RESET}")
        for nt in nearest:
            bar = "#" * int(nt.similarity * 20)
            print(f"      {BLUE}[{nt.symbol:>10s}]{RESET}"
                  f"  {PURPLE}{bar:<20s}{RESET}"
                  f"  {DIM}cos={nt.similarity:+.4f}{RESET}")
        print()


# ── Helpers ──────────────────────────────────────────────────────────

def _dump_json(data: dict):
    print(f"\n{DIM}--- JSON ---{RESET}")
    print(json.dumps(data, indent=2))


# ── Argument parser ──────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="embedder_demo",
        description="BPE-SVD Deterministic Embedder — CLI Demo",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared arguments
    def _add_common(p: argparse.ArgumentParser):
        p.add_argument("text", help="Input text to process")
        p.add_argument("--json", action="store_true", help="Also print JSON output")

    def _add_budget(p: argparse.ArgumentParser):
        p.add_argument("--budget", type=int, default=10, help="Token budget per hunk (default: 10)")

    def _add_topk(p: argparse.ArgumentParser):
        p.add_argument("--top-k", type=int, default=5, help="Number of nearest tokens (default: 5)")

    # tokenize
    p_tok = sub.add_parser("tokenize", help="Text → BPE tokens")
    _add_common(p_tok)

    # chunk
    p_chunk = sub.add_parser("chunk", help="Text → budget-bounded hunks")
    _add_common(p_chunk)
    _add_budget(p_chunk)

    # embed
    p_embed = sub.add_parser("embed", help="Text → hunks → vectors")
    _add_common(p_embed)
    _add_budget(p_embed)

    # reverse
    p_rev = sub.add_parser("reverse", help="Text → hunks → vectors → nearest tokens")
    _add_common(p_rev)
    _add_budget(p_rev)
    _add_topk(p_rev)

    # pipeline (all at once)
    p_all = sub.add_parser("pipeline", help="Run full pipeline end-to-end")
    _add_common(p_all)
    _add_budget(p_all)
    _add_topk(p_all)

    return parser


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "tokenize": cmd_tokenize,
        "chunk": cmd_chunk,
        "embed": cmd_embed,
        "reverse": cmd_reverse,
        "pipeline": cmd_pipeline,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
