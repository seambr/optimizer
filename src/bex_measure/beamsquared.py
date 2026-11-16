from __future__ import annotations

import os
import sys
from pathlib import Path


class BeamSquared:
    

    def __init__(
        self,
        install_dir: str | Path = r"C:\Program Files\Spiricon\BeamSquared",
        show_gui: bool = True,
    ) -> None:
        self.install_dir = Path(install_dir)
        self.show_gui = show_gui
        self._app = None

    def initialize(self) -> BeamSquared:

        if self._app is not None:
            return self

        folder = self.install_dir.resolve()
        filenames = (
            "Spiricon.Interfaces.ConsoleService.dll",
            "Spiricon.TreePattern.dll",
            "M2.Automation.dll",
        )
        for filename in filenames:
            if not (folder / filename).is_file():
                raise FileNotFoundError(folder / filename)

        from pythonnet import load

        load("netfx")
        import clr

        
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))

        previous_directory = Path.cwd()
        try:
            os.chdir(folder)
            for filename in filenames:
                clr.AddReference(str(folder / filename))
            from M2.Automation import AutomatedBeamSquared

            self._app = AutomatedBeamSquared(self.show_gui)
        finally:
            os.chdir(previous_directory)
        return self

    def _require_app(self):
        if self._app is None:
            raise RuntimeError("Call initialize() before using BeamSquared.")
        return self._app

    def start_live(self) -> None:
        """Enable live"""
        self._require_app().Capture.LiveMode = True

    def stop_live(self) -> None:
        """Disable live"""
        self._require_app().Capture.LiveMode = False

    def get_centroid(self) -> tuple[float, float]:
        """Return latest centroid (x, y), unconverted; may repeat a prior frame."""
        results = self._require_app().QuantitativeResults
        return float(results.CentroidX), float(results.CentroidY)

    def close(self) -> None:

        if self._app is not None:
            self._app.Instance.Shutdown()
            self._app = None

    def __enter__(self) -> BeamSquared:
        return self.initialize()

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            self.close()
        except Exception as shutdown_error:
            if exc_value is None:
                raise
            # Preserve the original failure while reporting a cleanup failure.
            import warnings

            warnings.warn(f"BeamSquared shutdown also failed: {shutdown_error}")
        return False
