# utils.py
# small helpers

import os

def ensure_ext(path, ext):
    if not path.lower().endswith(ext.lower()):
        return path + ext
    return path

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)