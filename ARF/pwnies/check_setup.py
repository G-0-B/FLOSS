"""
Diagnostic script to check Desktop Pony Swarm setup.

Run this to diagnose import issues.
"""

import sys
import os
from pathlib import Path


def check_setup():
    """Check if Desktop Pony Swarm is properly set up."""

    print("=" * 80)
    print("🔍 DESKTOP PONY SWARM - Setup Diagnostic")
    print("=" * 80)

    # Check 1: Python version
    print("\n1️⃣ Python Version")
    print(f"   Version: {sys.version}")
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 9:
        print("   ✅ Python >= 3.9")
    else:
        print(f"   ❌ Python {major}.{minor} is too old (need >= 3.9)")
        return False

    # Check 2: Current directory
    print("\n2️⃣ Current Directory")
    cwd = Path.cwd()
    print(f"   {cwd}")

    # Check 3: Project structure
    print("\n3️⃣ Project Structure")
    expected_files = [
        "desktop_pony_swarm/__init__.py",
        "desktop_pony_swarm/core/__init__.py",
        "desktop_pony_swarm/core/swarm.py",
        "desktop_pony_swarm/core/pony_agent.py",
        "desktop_pony_swarm/core/horde_client.py",
        "desktop_pony_swarm/core/embedding.py",
        "run_swarm.py",
        "embedding_frames_of_scale.py",
    ]

    all_exist = True
    for file_path in expected_files:
        full_path = cwd / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (NOT FOUND)")
            all_exist = False

    if not all_exist:
        print("\n   ⚠️  Some files are missing. Are you in the correct directory?")
        print(f"   Expected directory: C:\\crap\\ARF\\ or /mnt/project/")
        print(f"   Current directory:  {cwd}")
        return False

    # Check 4: Python path
    print("\n4️⃣ Python Path")
    print(f"   Total paths: {len(sys.path)}")
    for i, path in enumerate(sys.path[:5]):
        print(f"   [{i}] {path}")
    if len(sys.path) > 5:
        print(f"   ... and {len(sys.path) - 5} more")

    # Check 5: Can find desktop_pony_swarm?
    print("\n5️⃣ Module Search")
    found = False
    for path in sys.path:
        potential = Path(path) / "desktop_pony_swarm"
        if potential.exists() and potential.is_dir():
            print(f"   ✅ Found desktop_pony_swarm at: {potential}")
            found = True
            break

    if not found:
        print(f"   ❌ desktop_pony_swarm not in Python path")
        print(f"\n   💡 FIX: Add project root to PYTHONPATH")
        print(f"      Windows: set PYTHONPATH={cwd}")
        print(f"      Linux:   export PYTHONPATH={cwd}")
        return False

    # Check 6: Try importing
    print("\n6️⃣ Import Test")

    # Add current directory to path if not already there
    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))
        print(f"   Added {cwd} to path")

    try:
        from desktop_pony_swarm import PonySwarm

        print("   ✅ desktop_pony_swarm.PonySwarm imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

    try:
        from desktop_pony_swarm.core.swarm import PonySwarm as PS

        print("   ✅ desktop_pony_swarm.core.swarm imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

    try:
        from embedding_frames_of_scale import MultiScaleEmbedding

        print("   ✅ embedding_frames_of_scale imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        print(f"   💡 Make sure embedding_frames_of_scale.py is in: {cwd}")
        return False

    # Check 7: Dependencies
    print("\n7️⃣ Dependencies")
    required = ["aiohttp", "numpy"]
    all_installed = True
    for module in required:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (not installed)")
            all_installed = False

    if not all_installed:
        print("\n   💡 FIX: Install dependencies")
        print("      pip install -r requirements_swarm.txt")
        return False

    # Success!
    print("\n" + "=" * 80)
    print("✅ ALL CHECKS PASSED - Setup is correct!")
    print("=" * 80)
    print("\n🚀 Ready to run:")
    print("   python run_swarm.py              # Interactive mode")
    print("   python run_swarm.py demo          # Demo mode")
    print("\n📝 Or install for easier use:")
    print("   pip install -e .")
    print("   pony-swarm                        # Can then use command")
    print()
    return True


if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)
