import sys
from pathlib import Path

# Import the vmc_ubbink modules standalone (vigor.py / direct.py don't depend on HA),
# bypassing the package __init__.py (which pulls in homeassistant).
_PKG = Path(__file__).resolve().parent.parent / "custom_components" / "vmc_ubbink"
sys.path.insert(0, str(_PKG))
