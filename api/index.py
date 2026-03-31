import sys
from pathlib import Path

# Ensure the parent directory is in the path for imports
api_dir = Path(__file__).parent.resolve()
root_dir = api_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from web_run import create_app

app = create_app()

