from ..managers.evolution_manager import EvolutionManager
import asyncio
from ..managers.replication_manager import ReplicationManager
from ..managers.neurosynchrony_manager import NeurosynchronyManager
from ..managers.version_manager import VersionManager
from ..holochain_connector import HolochainConnector


class SwarmRuntime:
    """
    The main orchestrator for the Desktop Pony Swarm.

    This class is responsible for initializing and coordinating the various
    managers that make up the swarm's functionality.
    """

    def __init__(self, conductor_url: str = "ws://localhost:8888"):
        """Initializes the SwarmRuntime and its managers."""
        self.conductor_url = conductor_url
        self.connector = None
        self.conductor_process = None
        self.evolution_manager = EvolutionManager()
        self.replication_manager = ReplicationManager()
        self.neurosynchrony_manager = NeurosynchronyManager()
        self.version_manager = VersionManager()

    async def connect(self):
        """Connects to the Holochain conductor."""
        # Start the conductor using the helper script
        self.conductor_process = await asyncio.create_subprocess_exec(
            "node",
            "ARF/tests/tryorama/start_conductor.js",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Read the conductor URL from stdout
        conductor_url_bytes = await self.conductor_process.stdout.readline()
        self.conductor_url = conductor_url_bytes.decode().strip()

        # Print stderr for debugging
        stderr_bytes = await self.conductor_process.stderr.read()
        print(stderr_bytes.decode())

        # Connect to the conductor
        self.connector = HolochainConnector(conductor_url=self.conductor_url)
        await self.connector.connect()

    async def disconnect(self):
        """
        Disconnects from the Holochain conductor and stops the conductor process.
        """
        if self.connector:
            await self.connector.disconnect()
        if self.conductor_process:
            self.conductor_process.kill()

    def start(self):
        """Starts the swarm and all its managers."""
        print("SwarmRuntime starting...")
        # In the future, this will initialize and start the managers.
        pass

    def stop(self):
        """Stops the swarm and all its managers."""
        print("SwarmRuntime stopping...")
        # In the future, this will stop the managers.
        pass

    async def get_latest_version(self):
        """Gets the latest version of the DNA from the Holochain conductor."""
        return await self.connector.call_zome(
            zome_name="coordinator",
            fn_name="get_latest_version",
            payload=None,
        )
