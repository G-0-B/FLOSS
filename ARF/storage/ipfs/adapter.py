# ARF/storage/ipfs/adapter.py
from ipfshttpclient import connect
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

class IPFSStorageAdapter:
    """
    IPFS storage layer for FLOSS large files.
    Implements the Layer 0 Content Storage from MemeGraph Protocol v0.2
    """
    
    def __init__(self, ipfs_host="/ip4/127.0.0.1/tcp/5001"):
        self.client = connect(ipfs_host)
        self.manifest_path = Path(".ipfs/large_files.yaml")
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                return yaml.safe_load(f) or {"files": []}
        return {"files": []}
    
    def _save_manifest(self):
        self.manifest_path.parent.mkdir(exist_ok=True)
        with open(self.manifest_path, 'w') as f:
            yaml.dump(self.manifest, f, default_flow_style=False)
    
    def add_file(self, file_path: str, pin: bool = True) -> str:
        """
        Add large file to IPFS with SHA-256 integrity tracking.
        Returns IPFS CID.
        """
        path = Path(file_path)
        
        # Compute content hash (stable SHA-256 per your architecture)
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        
        # Add to IPFS
        result = self.client.add(str(path), pin=pin)
        cid = result['Hash']
        
        # Update manifest
        self.manifest['files'].append({
            'name': path.name,
            'path': str(path),
            'ipfs_cid': cid,
            'sha256': sha256,
            'size_bytes': path.stat().st_size,
            'uploaded_at': datetime.utcnow().isoformat(),
        })
        
        self._save_manifest()
        
        print(f"✅ {path.name} → {cid}")
        return cid
    
    def get_file(self, cid: str, output_path: str):
        """Retrieve file from IPFS with integrity verification"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download from IPFS
        self.client.get(cid, target=str(path))
        
        # Verify against manifest
        for file_info in self.manifest['files']:
            if file_info['ipfs_cid'] == cid:
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                expected_hash = file_info['sha256']
                
                if actual_hash != expected_hash:
                    path.unlink()
                    raise ValueError(f"Hash mismatch! Expected {expected_hash}, got {actual_hash}")
                
                print(f"✅ {path.name} verified")
                return
    
    def download_all(self):
        """Download all files from manifest"""
        for file_info in self.manifest['files']:
            path = Path(file_info['path'])
            
            if path.exists():
                print(f"⏭️  {path.name} exists, skipping")
                continue
            
            print(f"📥 Downloading {path.name}...")
            self.get_file(file_info['ipfs_cid'], str(path))
