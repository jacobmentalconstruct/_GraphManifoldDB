"""
Graph Manifold — Application Entry Point

This is the single entry point for the application. It creates a
RuntimeController and calls bootstrap() to initialize the scaffold.

Usage:
    pip install -e .           (install as editable package, once)
    python -m src.app          (module invocation — preferred)
    python src/app.py          (direct script — requires editable install)

Rules:
    - No UI startup
    - No legacy path hacks or sys.path surgery
    - No old backend code
    - Imports only new scaffold modules
"""

from src.core.runtime.runtime_controller import RuntimeController
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def main() -> int:
    """Bootstrap the Graph Manifold scaffold and run."""
    logger.info("Graph Manifold — starting bootstrap")
    controller = RuntimeController()
    controller.bootstrap()
    logger.info("Graph Manifold — scaffold ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
