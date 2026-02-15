"""Sidecar JSON I/O for margin annotations."""

import json
import os


def get_path(filepath):
    """Return the sidecar annotation path for a markdown file."""
    return filepath + ".annotations.json"


def get_resolved_path(filepath):
    """Return the resolved archive path for a markdown file."""
    return filepath + ".annotations.resolved.json"


def read(filepath):
    """Read annotations for a file. Returns (data_dict, mtime)."""
    path = get_path(filepath)
    if os.path.exists(path):
        try:
            mtime = os.path.getmtime(path)
            with open(path) as f:
                data = json.load(f)
            return data, mtime
        except Exception:
            pass
    return {"version": 1, "annotations": []}, 0


def read_resolved(filepath):
    """Read resolved annotations archive. Returns data_dict."""
    path = get_resolved_path(filepath)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 1, "resolved": []}


def write(filepath, data):
    """Write annotations to the sidecar JSON file."""
    path = get_path(filepath)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_resolved(filepath, data):
    """Write resolved archive to the sidecar JSON file."""
    path = get_resolved_path(filepath)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
