# scripts/ipfs_download.py
#!/usr/bin/env python3
"""Download all large files from IPFS manifest"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ARF.storage.ipfs.adapter import IPFSStorageAdapter

if __name__ == "__main__":
    adapter = IPFSStorageAdapter()
    adapter.download_all()
