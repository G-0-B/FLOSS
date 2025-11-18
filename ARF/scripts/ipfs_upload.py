# scripts/ipfs_upload.py
#!/usr/bin/env python3
"""Upload large files to IPFS"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ARF.storage.ipfs.adapter import IPFSStorageAdapter

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/ipfs_upload.py <file_path>")
        sys.exit(1)
    
    adapter = IPFSStorageAdapter()
    adapter.add_file(sys.argv[1])
