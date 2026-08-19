#!/usr/bin/env python3
"""Download all large files from IPFS manifest"""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
IPFSStorageAdapter = import_module("ARF.storage.ipfs.adapter").IPFSStorageAdapter

if __name__ == "__main__":
    adapter = IPFSStorageAdapter()
    adapter.download_all()
