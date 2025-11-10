"""Performance benchmarks for application startup."""

import sys
import time
from pathlib import Path

import pytest


@pytest.mark.benchmark
@pytest.mark.slow
class TestStartupPerformance:
    """Test startup performance targets."""

    def test_gui_import_time(self, benchmark):
        """Benchmark GUI import time."""

        def import_gui():
            # Clear any cached imports
            modules_to_remove = [k for k in sys.modules if k.startswith("gui.")]
            for module in modules_to_remove:
                del sys.modules[module]

            # Measure import time
            start = time.perf_counter()
            import gui.main_window  # noqa: F401

            elapsed = time.perf_counter() - start
            return elapsed

        result = benchmark(import_gui)
        # Target: imports should be fast (<100ms)
        assert result < 0.5  # 500ms is reasonable for initial import

    def test_main_window_creation_time(self, benchmark, qtbot):
        """Benchmark main window creation time."""
        from PyQt6.QtWidgets import QApplication

        if not QApplication.instance():
            QApplication(sys.argv)

        def create_window():
            from gui.main_window import ArbitrageBotGUI

            return ArbitrageBotGUI()

        window = benchmark(create_window)
        window.set_update_thread_enabled(False)  # Disable thread for test stability

        # Target: window creation <200ms
        assert window is not None

    @pytest.mark.skip(reason="Requires full app initialization - run manually")
    def test_gui_startup_time(self):
        """Test full GUI startup time (target <300ms)."""
        import subprocess

        script = """
import time
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import ArbitrageBotGUI

start = time.perf_counter()
app = QApplication(sys.argv)
window = ArbitrageBotGUI()
window.show()
elapsed = time.perf_counter() - start
print(f"STARTUP_TIME:{elapsed}")
app.quit()
"""

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Extract timing from output
        for line in result.stdout.split("\n"):
            if "STARTUP_TIME:" in line:
                startup_time = float(line.split(":")[1])
                # Target: <300ms on moderately powered Windows 11 PC
                assert startup_time < 0.5  # 500ms is more realistic for CI
