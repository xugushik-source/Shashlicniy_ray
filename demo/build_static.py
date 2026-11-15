"""Build the static hosted demo from the portable demo export."""
from pathlib import Path
import shutil
from export_preview import export
ROOT=Path(__file__).resolve().parents[1]
export()
shutil.copytree(ROOT/'demo-preview',ROOT/'dist',dirs_exist_ok=True)
(ROOT/'dist/README.txt').unlink(missing_ok=True)
print('Static Site build: dist/index.html and media/')
