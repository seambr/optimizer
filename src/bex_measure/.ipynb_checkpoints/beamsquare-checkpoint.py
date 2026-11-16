
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



from beamsquared import BeamSquared
import time

bs = BeamSquared()
bs.initialize()

try:
    bs.start_live()
    time.sleep(1)  # Give acquisition time to begin

    for _ in range(100):
        x, y = bs.get_centroid()
        print(f"X: {x:.3f}, Y: {y:.3f}")
        time.sleep(0.1)

finally:
    bs.close()  # Also runs if the loop errors or is interrupted