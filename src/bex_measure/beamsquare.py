
from __future__ import annotations
import clr
import time
from pathlib import Path

# Location of the BeamSquared installation
BSQ_DIR = Path(r"C:\Program Files\Spiricon\BeamSquared")


clr.AddReference(str(BSQ_DIR / "M2.Automation.dll"))

from M2.Automation import AutomatedBeamSquared


beam = AutomatedBeamSquared(True)


beam.Capture.LiveMode = True



def get_beam_centroid() -> tuple[float, float]:
    # Presumably in units [um]?
    results = beam.QuantitativeResults
    x = results.CentroidX
    y = results.CentroidY
    return x, y

