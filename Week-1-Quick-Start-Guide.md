# Week 1 Quick-Start: IPFS Integration Implementation

## 🎯 Goal
Build core IPFS + Holochain infrastructure that allows uploading and verifying large files.

**Success Metric**: Upload a 500MB test file, verify it in CI, download and verify hash ✅

---

## 📅 Day-by-Day Breakdown

### Day 1: Holochain DNA Setup

#### Morning: Create Integrity Zome
```bash
cd your-arf-repo
hc scaffold dna file-artifacts
cd dnas/file-artifacts

# Create integrity zome
hc scaffold zome integrity file_artifacts_integrity --integrity
```

#### Create Entry Types (`zomes/integrity/file_artifacts_integrity/src/lib.rs`)
```rust
use hdi::prelude::*;

#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct FileArtifact {
    pub filename: String,
    pub description: String,
    pub ipfs_cid: String,
    pub size_bytes: u64,
    pub sha256: String,
    pub blake3: String,
    pub artifact_type: String,  // Start simple: "model", "dataset", "media"
    pub uploader: AgentPubKey,
    pub uploaded_at: Timestamp,
    pub license: String,
    pub gateways: Vec<String>,
    pub pinning_services: Vec<String>,
}

#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct PinningProof {
    pub file_cid: String,
    pub service: String,
    pub proof_data: String,
    pub timestamp: Timestamp,
}
```

#### Afternoon: Validation Rules
```rust
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store_entry) => match store_entry {
            OpEntry::CreateEntry { app_entry, .. } => match app_entry {
                EntryTypes::FileArtifact(artifact) => {
                    // RULE 1: License must be FOSS
                    let valid_licenses = vec![
                        "MIT", "Apache-2.0", "GPL-3.0", 
                        "BSD-3-Clause", "MPL-2.0", "CC-BY-4.0"
                    ];
                    if !valid_licenses.contains(&artifact.license.as_str()) {
                        return Ok(ValidateCallbackResult::Invalid(
                            format!("License '{}' not FOSS-approved", artifact.license)
                        ));
                    }
                    
                    // RULE 2: CID format
                    if !artifact.ipfs_cid.starts_with("Qm") && 
                       !artifact.ipfs_cid.starts_with("bafy") {
                        return Ok(ValidateCallbackResult::Invalid(
                            "Invalid IPFS CID format".into()
                        ));
                    }
                    
                    // RULE 3: SHA256 format
                    if artifact.sha256.len() != 64 {
                        return Ok(ValidateCallbackResult::Invalid(
                            "SHA256 must be 64 hex chars".into()
                        ));
                    }
                    
                    // RULE 4: At least 1 pinning service (relax to 1 for Week 1)
                    if artifact.pinning_services.is_empty() {
                        return Ok(ValidateCallbackResult::Invalid(
                            "Requires at least 1 pinning proof".into()
                        ));
                    }
                    
                    Ok(ValidateCallbackResult::Valid)
                }
                _ => Ok(ValidateCallbackResult::Valid),
            },
            _ => Ok(ValidateCallbackResult::Valid),
        },
        _ => Ok(ValidateCallbackResult::Valid),
    }
}
```

**Evening: Test validation rules**
```bash
hc sandbox generate workdir/
hc sandbox run -p 8888 workdir/
# Run tests in another terminal
cargo test --package file_artifacts_integrity
```

---

### Day 2: Coordinator Zome

#### Morning: Create Coordinator
```bash
hc scaffold zome coordinator file_artifacts_coordinator
```

#### Implement Basic Operations (`zomes/coordinator/file_artifacts_coordinator/src/lib.rs`)
```rust
use hdk::prelude::*;
use file_artifacts_integrity::*;

#[hdk_extern]
pub fn publish_file_artifact(input: FileArtifact) -> ExternResult<ActionHash> {
    // Simple version: just create entry
    let artifact_hash = create_entry(&EntryTypes::FileArtifact(input.clone()))?;
    
    // Add to global index
    let path = Path::from("all_artifacts");
    create_link(
        path.path_entry_hash()?,
        artifact_hash.clone(),
        LinkTypes::ArtifactIndex,
        ()
    )?;
    
    Ok(artifact_hash)
}

#[hdk_extern]
pub fn get_artifact(hash: ActionHash) -> ExternResult<Option<FileArtifact>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(record) => {
            let artifact: FileArtifact = record
                .entry()
                .to_app_option()?
                .ok_or(wasm_error!(WasmErrorInner::Guest(
                    "Entry not found".into()
                )))?;
            Ok(Some(artifact))
        }
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn get_artifact_by_cid(cid: String) -> ExternResult<Option<FileArtifact>> {
    // For Week 1, iterate all artifacts (optimize later)
    let path = Path::from("all_artifacts");
    let links = get_links(path.path_entry_hash()?, LinkTypes::ArtifactIndex, None)?;
    
    for link in links {
        if let Some(artifact) = get_artifact(ActionHash::from(link.target))? {
            if artifact.ipfs_cid == cid {
                return Ok(Some(artifact));
            }
        }
    }
    Ok(None)
}

#[hdk_extern]
pub fn list_artifacts() -> ExternResult<Vec<FileArtifact>> {
    let path = Path::from("all_artifacts");
    let links = get_links(path.path_entry_hash()?, LinkTypes::ArtifactIndex, None)?;
    
    let mut artifacts = vec![];
    for link in links {
        if let Some(artifact) = get_artifact(ActionHash::from(link.target))? {
            artifacts.push(artifact);
        }
    }
    Ok(artifacts)
}
```

**Afternoon: Build and test**
```bash
hc dna pack workdir/dna
hc app pack workdir/
# Test in tryorama
```

---

### Day 3: CLI Upload Tool

#### Create `tools/arf-ipfs-upload`
```bash
#!/bin/bash
set -euo pipefail

# Usage: arf-ipfs-upload <file> <description> [license]
FILE="$1"
DESCRIPTION="$2"
LICENSE="${3:-MIT}"

echo "🔐 Uploading $FILE to IPFS..."

# 1. Calculate hashes
echo "  Computing hashes..."
SHA256=$(sha256sum "$FILE" | cut -d' ' -f1)
BLAKE3=$(b3sum "$FILE" 2>/dev/null || echo "BLAKE3_NOT_AVAILABLE")

# 2. Upload to IPFS
echo "  Uploading to IPFS..."
if ! command -v ipfs &> /dev/null; then
    echo "Error: ipfs command not found. Install IPFS: https://ipfs.io"
    exit 1
fi

CID=$(ipfs add --quieter --pin=true "$FILE")
echo "  ✓ CID: $CID"

# 3. Get pinning info
PINNING_SERVICES='["personal_node"]'  # Week 1: just local node
if ipfs id &>/dev/null; then
    PEER_ID=$(ipfs id -f="<id>")
    echo "  ✓ Pinned to personal node: $PEER_ID"
fi

# 4. Get gateways
GATEWAYS=(
    "https://ipfs.io/ipfs/$CID"
    "https://dweb.link/ipfs/$CID"
    "https://w3s.link/ipfs/$CID"
)

# 5. Create pointer file
POINTER_FILE="large_files/$(basename $FILE).ipfs"
mkdir -p large_files

cat > "$POINTER_FILE" <<EOF
{
  "filename": "$(basename $FILE)",
  "description": "$DESCRIPTION",
  "ipfs_cid": "$CID",
  "size_bytes": $(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE"),
  "sha256": "$SHA256",
  "blake3": "$BLAKE3",
  "artifact_type": "$(guess_type $FILE)",
  "uploaded_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "license": "$LICENSE",
  "gateways": $(printf '%s\n' "${GATEWAYS[@]}" | jq -R . | jq -s .),
  "pinning_services": $PINNING_SERVICES
}
EOF

echo ""
echo "✅ Upload complete!"
echo "   Pointer: $POINTER_FILE"
echo "   CID: $CID"
echo "   SHA256: $SHA256"
echo ""
echo "Next steps:"
echo "  1. git add $POINTER_FILE"
echo "  2. git commit -m 'Add $(basename $FILE) via IPFS'"
echo "  3. Optionally pin to additional services (Pinata, web3.storage)"
```

#### Helper function
```bash
guess_type() {
    case "$1" in
        *.bin|*.h5|*.ckpt|*.pt|*.pth|*.safetensors) echo "model" ;;
        *.csv|*.parquet|*.arrow) echo "dataset" ;;
        *.mp4|*.avi|*.mov|*.png|*.jpg) echo "media" ;;
        *.md|*.pdf|*.txt) echo "documentation" ;;
        *) echo "other" ;;
    esac
}
```

**Make executable**:
```bash
chmod +x tools/arf-ipfs-upload
```

---

### Day 4: CLI Download Tool

#### Create `tools/arf-ipfs-download`
```bash
#!/bin/bash
set -euo pipefail

POINTER="$1"

if [ ! -f "$POINTER" ]; then
    echo "Error: Pointer file not found: $POINTER"
    exit 1
fi

echo "📥 Downloading file from IPFS..."

# 1. Parse pointer
CID=$(jq -r '.ipfs_cid' "$POINTER")
FILENAME=$(jq -r '.filename' "$POINTER")
SHA256=$(jq -r '.sha256' "$POINTER")
GATEWAYS=($(jq -r '.gateways[]' "$POINTER"))

echo "  CID: $CID"
echo "  Filename: $FILENAME"

# 2. Try local IPFS daemon first (fastest)
if command -v ipfs &>/dev/null && ipfs id &>/dev/null; then
    echo "  Trying local IPFS daemon..."
    if ipfs get "$CID" -o "$FILENAME" 2>/dev/null; then
        echo "  ✓ Downloaded via local IPFS"
    fi
fi

# 3. Fallback to gateways
if [ ! -f "$FILENAME" ]; then
    echo "  Trying gateways..."
    for GATEWAY in "${GATEWAYS[@]}"; do
        echo "    Trying: $GATEWAY"
        if curl -fL -o "$FILENAME" "$GATEWAY" 2>/dev/null; then
            echo "  ✓ Downloaded via gateway"
            break
        fi
    done
fi

# 4. Verify hash
if [ ! -f "$FILENAME" ]; then
    echo "✗ Download failed from all sources"
    exit 1
fi

echo "  Verifying integrity..."
ACTUAL_SHA256=$(sha256sum "$FILENAME" | cut -d' ' -f1)

if [ "$ACTUAL_SHA256" = "$SHA256" ]; then
    echo "✅ File verified and downloaded: $FILENAME"
else
    echo "✗ SHA256 mismatch!"
    echo "  Expected: $SHA256"
    echo "  Got:      $ACTUAL_SHA256"
    rm "$FILENAME"
    exit 1
fi
```

**Make executable**:
```bash
chmod +x tools/arf-ipfs-download
```

---

### Day 5: Git Integration + Testing

#### Morning: Git Setup

**Update `.gitignore`**:
```
# Ignore large binaries
large_files/*.bin
large_files/*.h5
large_files/*.ckpt
large_files/*.safetensors
large_files/*.tar.gz

# Track pointer files
!large_files/*.ipfs
```

**Create pre-commit hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Validate IPFS pointer files

for pointer in large_files/*.ipfs; do
    [ -f "$pointer" ] || continue
    
    # Validate JSON
    if ! jq empty "$pointer" 2>/dev/null; then
        echo "Error: Invalid JSON in $pointer"
        exit 1
    fi
    
    # Check required fields
    for field in ipfs_cid sha256 filename license; do
        if ! jq -e ".$field" "$pointer" >/dev/null; then
            echo "Error: Missing field '$field' in $pointer"
            exit 1
        fi
    done
    
    # Validate license
    LICENSE=$(jq -r '.license' "$pointer")
    VALID="MIT Apache-2.0 GPL-3.0 BSD-3-Clause MPL-2.0 CC-BY-4.0"
    if ! echo "$VALID" | grep -q "$LICENSE"; then
        echo "Error: Invalid license '$LICENSE' in $pointer"
        exit 1
    fi
    
    echo "✓ $pointer validated"
done

exit 0
```

```bash
chmod +x .git/hooks/pre-commit
```

#### Afternoon: CI Setup

**Create `.github/workflows/verify-ipfs-pointers.yml`**:
```yaml
name: Verify IPFS Pointers

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y jq
      
      - name: Verify pointer files
        run: |
          for pointer in large_files/*.ipfs; do
            [ -f "$pointer" ] || continue
            
            echo "Verifying: $pointer"
            
            # Validate JSON
            jq empty "$pointer" || exit 1
            
            # Check required fields
            jq -e '.ipfs_cid' "$pointer" >/dev/null || exit 1
            jq -e '.sha256' "$pointer" >/dev/null || exit 1
            jq -e '.filename' "$pointer" >/dev/null || exit 1
            jq -e '.license' "$pointer" >/dev/null || exit 1
            
            # Validate license
            LICENSE=$(jq -r '.license' "$pointer")
            case "$LICENSE" in
              MIT|Apache-2.0|GPL-3.0|BSD-3-Clause|MPL-2.0|CC-BY-4.0)
                echo "  ✓ Valid license: $LICENSE"
                ;;
              *)
                echo "  ✗ Invalid license: $LICENSE"
                exit 1
                ;;
            esac
            
            echo "  ✓ $pointer verified"
          done
      
      - name: Test IPFS availability
        run: |
          for pointer in large_files/*.ipfs; do
            [ -f "$pointer" ] || continue
            
            CID=$(jq -r '.ipfs_cid' "$pointer")
            echo "Checking availability: $CID"
            
            # Try HEAD request to gateway (don't download full file)
            if curl -I -f "https://ipfs.io/ipfs/$CID" 2>/dev/null | grep -q "200 OK"; then
              echo "  ✓ Available on ipfs.io"
            else
              echo "  ⚠️  Not immediately available (may need time to propagate)"
            fi
          done
```

#### Evening: End-to-End Test

```bash
# 1. Create test file
dd if=/dev/urandom of=test.bin bs=1M count=500  # 500MB test file

# 2. Upload
./tools/arf-ipfs-upload test.bin "Test file for IPFS integration" MIT

# 3. Verify pointer created
ls -lh large_files/test.bin.ipfs
cat large_files/test.bin.ipfs

# 4. Commit
git add large_files/test.bin.ipfs
git commit -m "Add test file via IPFS"

# 5. Download (simulate new user)
rm test.bin
./tools/arf-ipfs-download large_files/test.bin.ipfs

# 6. Verify file restored
ls -lh test.bin
# Should show: test.bin (500MB)

# 7. Push to GitHub
git push

# 8. Verify CI passes
# Check GitHub Actions tab
```

---

## ✅ Week 1 Success Checklist

- [ ] Holochain DNA created with integrity zome
- [ ] Validation rules enforce license + CID format
- [ ] Coordinator zome can publish/get artifacts
- [ ] CLI upload tool works (`arf-ipfs-upload`)
- [ ] CLI download tool works (`arf-ipfs-download`)
- [ ] Git ignores binaries, tracks pointers
- [ ] Pre-commit hook validates pointers
- [ ] CI workflow verifies all pointers
- [ ] End-to-end test passes (upload → commit → download)
- [ ] Documentation in README.md

---

## 🚨 Troubleshooting

### IPFS daemon not running
```bash
# Start IPFS daemon
ipfs daemon &

# Or install if missing
curl -o ipfs.tar.gz https://dist.ipfs.io/go-ipfs/latest/go-ipfs_linux-amd64.tar.gz
tar -xvzf ipfs.tar.gz
cd go-ipfs
sudo bash install.sh
ipfs init
ipfs daemon
```

### Git hook not executing
```bash
# Ensure executable
chmod +x .git/hooks/pre-commit

# Test manually
./.git/hooks/pre-commit
```

### Holochain build errors
```bash
# Update Holochain CLI
cargo install holochain_cli --locked

# Clean build
cargo clean
hc dna pack workdir/dna
```

### CID not resolving
```bash
# Wait 1-2 minutes for DHT propagation
sleep 120

# Try different gateway
curl -I https://dweb.link/ipfs/$CID
```

---

## 📚 Resources

- [IPFS Documentation](https://docs.ipfs.io)
- [Holochain Developer Portal](https://developer.holochain.org)
- [Final ADR Document](/mnt/user-data/outputs/ADR-N-IPFS-Integration-VVS.md)
- [Evolution Summary](/mnt/user-data/outputs/IPFS-Integration-Evolution-Summary.md)

---

## 🎯 Week 2 Preview

After Week 1 completes:
- Add knowledge graph integration (artifact triples)
- Implement semantic validation
- Add multi-service pinning (Pinata, web3.storage)
- Begin budget accounting implementation

---

**Ready to start? Begin with Day 1, Morning!** 🚀
