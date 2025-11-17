import sys
from pathlib import Path

# Add ARF directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ARF.cli import swarm

if __name__ == "__main__":
    # Bypassing typer's CLI parsing to directly call the main function
    # This is a workaround for the issues with typer in this environment
    from typer.main import get_command
    import asyncio

    async def main():
        # This is a simplified version of the logic in swarm.py's main function
        # It's intended to be a temporary solution to verify the SwarmRuntime
        from ARF.pwnies.desktop_pony_swarm.runtime.orchestrator import SwarmRuntime
        runtime = SwarmRuntime()
        try:
            await runtime.connect()
            version = await runtime.get_latest_version()
            print(f"Latest version: {version}")
        finally:
            await runtime.disconnect()

    if len(sys.argv) > 1 and sys.argv[1] == "version":
        asyncio.run(main())
    else:
        print("Usage: python ARF/run_swarm_cli.py version")
