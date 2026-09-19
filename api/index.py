import sys
from pathlib import Path

# Añadir la carpeta manager al path para importar main
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir / "manager"))

from main import app