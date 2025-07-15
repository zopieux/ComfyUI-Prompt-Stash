import json
import datetime
from typing import Tuple
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

# Exposed by Comfy.
import folder_paths

lock = Lock()

# Track pause status for each node instance
status_by_id = {}
# Store edited text during pause
edited_text_by_id = {}


def _get_stash_path() -> Path:
    user = Path(folder_paths.get_user_directory())
    default = user / "default"
    directory = default / "prompt-stash"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "data.json"


def _open():
    path = _get_stash_path()
    try:
        f = path.open("r+")
        f.seek(0)
        return f
    except FileNotFoundError:
        return path.open("w")


@contextmanager
def _stash():
    with lock, _open() as f:
        try:
            data = json.load(f)
        except IOError:
            data = {}
        yield data
        f.truncate(0)
        f.seek(0)
        json.dump(data, f)


def load_prompts() -> dict:
    with _stash() as data:
        return data


def save_prompt(key: str, prompt: str, **kwargs) -> dict:
    with _stash() as data:
        data[key] = {
            "prompt": prompt,
            "saved": datetime.datetime.now().isoformat(),
            **kwargs,
        }
        return data


def delete_prompt(key: str) -> Tuple[bool, dict]:
    with _stash() as data:
        try:
            del data[key]
            ok = True
        except KeyError:
            ok = False
        return (ok, data)
