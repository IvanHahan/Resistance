import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def abs_path(path):
    return os.path.join(ROOT_DIR, path)
