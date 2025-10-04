from pathlib import Path
import sys

DEV = not getattr(sys, "frozen", False)


RUTA_BASE = Path(__file__).resolve().parent
