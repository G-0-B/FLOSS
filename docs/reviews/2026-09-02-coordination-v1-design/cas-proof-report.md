# git update-ref CAS race proof — Windows / NTFS

**Date:** 2026-09-02  
**Host:** Windows 11 10.0.22631.6199, NTFS on `C:`  
**Repo:** `C:/~shit/FLOSS` (standalone repo, `.git` at `C:/~shit/FLOSS/.git`, NOT shared common-dir worktree)  
**Git:** `git version 2.54.0.windows.1` (`C:/Program Files/Git/cmd/git.exe`)  
**Ref namespace:** `refs/agent-claims/cas-test` (loose ref, cleaned after)  
**Verdict:** **PASS — CAS is atomic. Exactly 1/8 wins, 7/8 blocked on every run.**

---

## 1. Environment

```
$ git --version
git version 2.54.0.windows.1

$ git -C "C:/~shit/FLOSS" rev-parse --git-dir
.git  ->  C:/~shit/FLOSS/.git  (no commondir; FLOSS is its own repo)

$ df -T "C:/~shit/FLOSS"
Filesystem  Type  1K-blocks       Used  Available Use%  Mounted on
C:          ntfs  1973163004  1615484408  357678596  82%  /c

$ git config --list | grep core
core.autocrlf=true
core.fscache=true
core.symlinks=false  (FLOSS) / true (system)
core.filemode=false
core.logallrefupdates=true
core.repositoryformatversion=0
```

Filesystem is NTFS. Git `core.fscache=true`. No packed-refs entry for `refs/agent-claims/*` before or after (loose refs only).

---

## 2. Tests performed

Python via `C:/Python313/python.exe` (`PYTHONPATH` cleared) spawned 8 concurrent `subprocess.Popen` on the native `C:/Program Files/Git/cmd/git.exe`. Each racer: `git update-ref refs/agent-claims/cas-test <new_sha> <expected_old_sha>`.

Blob SHAs created with `git hash-object -w --stdin` (real objects, so `update-ref` object-existence check passes).

### 2a. Single create/delete cycle + lock file behavior

```
ZERO=0000000000000000000000000000000000000000
initial_sha=7df80b0dde2edcb84db8b74c990085aaf736e388  (blob)

# create with ZERO expected — must succeed when ref absent
$ git update-ref refs/agent-claims/cas-test <initial_sha> 000...0
rc=0

$ git rev-parse refs/agent-claims/cas-test
7df80b0dde2edcb84db8b74c990085aaf736e388

$ git for-each-ref refs/agent-claims/cas-test
7df80b0dde2edcb84db8b74c990085aaf736e388 blob  refs/agent-claims/cas-test

# lock file does NOT linger
$ glob .git/**/*.lock -> []
$ cat .git/refs/agent-claims/cas-test -> "7df80b0d...\n"  size 41
$ ls .git/refs/agent-claims/cas-test.lock -> not exists

# second create with ZERO when already exists — must fail
$ git update-ref refs/agent-claims/cas-test <other_sha> 000...0
rc=128  fatal: update_ref failed for ref 'refs/agent-claims/cas-test':
        cannot lock ref 'refs/agent-claims/cas-test': reference already exists

# delete with correct old — must succeed
$ git update-ref -d refs/agent-claims/cas-test <initial_sha>
rc=0

$ git show-ref refs/agent-claims/cas-test
rc=1  (deleted)

# manual lock-file contention
$ echo "manual lock" > .git/refs/agent-claims/cas-test-lockcheck.lock
$ git update-ref refs/agent-claims/cas-test-lockcheck <sha2> <sha1>
rc=128  fatal: update_ref failed ... Unable to create '...cas-test-lockcheck.lock':
        File exists.  Another git process seems to be running...
$ rm .git/refs/agent-claims/cas-test-lockcheck.lock
$ git update-ref refs/agent-claims/cas-test-lockcheck <sha2> <sha1>
rc=0  (succeeds after lock removed)
$ glob .git/**/*.lock -> []   # no stale locks

# cleanup verified
$ git show-ref refs/agent-claims/cas-test-lockcheck  -> rc=1
$ ls .git/refs/agent-claims/ -> empty dir (pruned to empty, not deleted)
```

Behavior: `update-ref` uses `*.lock` file next to the loose ref. Lock is created atomically via `CreateFile` semantics, held only for the write, removed on success. Stale lock blocks with `File exists`. `reference already exists` vs `is at <sha> but expected <old>` are distinct errors.

### 2b. 8-way concurrent CAS race

Setup (repeated twice, same result):

```
# recreate initial
$ git update-ref refs/agent-claims/cas-test <initial_sha> 000...0  # rc=0

# 8 distinct blobs as race targets
racer 0: 9eaed538b14e602415ddf37aab4634db8298270d
racer 1: 9be04e80f1d8f7d773fa19a6a936386cd65efe39
racer 2: 9192e6d7568e9563e2b5e7fe038f734cbea39a8b
racer 3: e1acd0c5bd766b095a3c4ad385083fb6176bab6d
racer 4: bf062bd2deee81d9405d31bd97beb373f26fc681
racer 5: 93bcc8052b5d94541733cfe2784384a46e5264ef
racer 6: 6502f47998cbe820f041726533762b4f395eb648
racer 7: 33e81644aa4e647d956b4b9ad9bbbfb8c16807e8

# python: 8x Popen(["C:/Program Files/Git/cmd/git.exe","-C","C:/~shit/FLOSS",
#                   "update-ref", REF, new_sha, initial_sha]) concurrently
```

**Run 1 (2026-09-02, elapsed 0.079s):**

```
racer 0 new=9eaed538 rc=0   WIN
racer 1 new=9be04e80 rc=128 BLOCKED  fatal: ... is at 9eaed538... but expected 7df80b0d...
racer 2 new=9192e6d7 rc=128 BLOCKED  (same)
racer 3 new=e1acd0c5 rc=128 BLOCKED
racer 4 new=bf062bd2 rc=128 BLOCKED
racer 5 new=93bcc805 rc=128 BLOCKED
racer 6 new=6502f479 rc=128 BLOCKED
racer 7 new=33e81644 rc=128 BLOCKED

WINS=1 LOSSES=7  CAS ATOMICITY VERIFIED: exactly 1 winner
final ref value: 9eaed538b14e602415ddf37aab4634db8298270d  (racer 0)
```

**Run 2 (elapsed 0.082s, fresh SHAs, same pattern):**

```
WINS=1 LOSSES=7  winner racer 0 -> ce88d1615f91a251d244f2101689a5a8bc77bf78
all 7 losers: rc=128  "is at ce88d161... but expected 7460c9c1..."
```

Post-race stale-CAS check (consistent):

```
$ git update-ref refs/agent-claims/cas-test <any> 7df80b0d...  (stale old)
rc=128  fatal: ... is at 9eaed538... but expected 7df80b0d...

$ glob .git/**/*.lock -> []
$ git update-ref -d refs/agent-claims/cas-test <final_sha>  -> rc=0, show-ref rc=1
```

No reflog surprise: `git reflog show refs/agent-claims/cas-test` empty (ref was deleted; `core.logAllRefUpdates` logs but file pruned on delete — expected for ephemeral refs).

---

## 3. Evidence envelope

**Commands executed (verbatim):**

```bash
git --version
"C:/Program Files/Git/cmd/git.exe" --version
git -C "C:/~shit/FLOSS" rev-parse --git-dir
git -C "C:/~shit/FLOSS" worktree list
df -T "C:/~shit/FLOSS"
git -C "C:/~shit/FLOSS" for-each-ref refs/agent-claims/
# python proof scripts:
#   C:/Users/kalis/AppData/Local/Temp/cas_proof.py   (8-way race + create/delete)
#   C:/Users/kalis/AppData/Local/Temp/cas_lock_test.py (manual lock contention)
env -u PYTHONPATH "C:/Python313/python.exe" "C:/Users/kalis/AppData/Local/Temp/cas_proof.py"
env -u PYTHONPATH "C:/Python313/python.exe" "C:/Users/kalis/AppData/Local/Temp/cas_lock_test.py"
```

**Key outputs (truncated, full logs in terminal history):**

- Create with ZERO: `rc=0`; second create with ZERO: `rc=128 reference already exists`; delete: `rc=0`.
- 8-way race: `WINS=1 LOSSES=7` both runs, losers `rc=128 ... is at <winner> but expected <initial>`, winner `rc=0`.
- Lock file: no `*.lock` left after any operation; manual `.lock` causes `File exists` failure, removed → success.

**Artifacts left:** none. `refs/agent-claims/cas-test` and `cas-test-lockcheck` deleted, blobs remain in `objects/` (harmless, unreferenced). No packed-refs entry.

---

## 4. Verdict

- [V] `git update-ref <ref> <new> <old>` CAS works on Windows 11 / NTFS / `git 2.54.0.windows.1`.
- [V] Concurrent 8-way race is linearizable: exactly 1 winner, 7 blocked with `is at <winner> but expected <old>`.
- [V] Lock file is `refs/agent-claims/<name>.lock`, held only during write, no stale locks.
- [V] Single create (`old=ZERO`) / delete cycle behaves per spec.
- [V] `refs/agent-claims/*` is safe for file-based CAS / claim coordination in this repo.

**Recommendation:** use `git update-ref refs/agent-claims/<claim> <new> 000...0` to create (fail if exists) and `git update-ref refs/agent-claims/<claim> <new> <expected_old>` to CAS-update. Blocked callers get `rc=128` — retry with fresh `rev-parse`.
