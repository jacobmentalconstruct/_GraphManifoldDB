"""
Scaffold Smoke Test — verify the scaffold boots without crashing.

This test confirms that:
    - RuntimeController can be instantiated
    - bootstrap() completes without error
    - The application entry point main() returns cleanly
"""

from src.core.runtime.runtime_controller import RuntimeController
from src.app import main


def test_runtime_controller_bootstrap() -> None:
    """RuntimeController.bootstrap() should complete without error."""
    controller = RuntimeController()
    controller.bootstrap()


def test_app_main_returns_zero() -> None:
    """main() should return 0 indicating clean startup."""
    result = main()
    assert result == 0, f"main() returned {result}, expected 0"
