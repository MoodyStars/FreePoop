# utils.py
# small helpers for FreePoop project

import os
import tempfile
import requests

def ensure_ext(path, ext):
    if not path.lower().endswith(ext.lower()):
        return path + ext
    return path

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def download_url_placeholder(url):
    """
    Placeholder downloader: attempts to download a URL to a local temp file.
    - If the URL points to a file (direct link), it will be saved and returned.
    - For more advanced downloads (YouTube/Internet Archive), replace this with yt-dlp or a proper downloader.
    """
    # basic sanity
    if not url.startswith("http"):
        raise ValueError("Not a valid URL")
    # make a local temp file
    tmpdir = tempfile.mkdtemp(prefix="freepoop_dl_")
    filename = os.path.basename(url.split("?")[0]) or "online_item"
    local = os.path.join(tmpdir, filename)
    try:
        # stream download
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        with open(local, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
        return local
    except Exception as e:
        # cleanup and re-raise
        try:
            os.remove(local)
        except Exception:
            pass
        raise