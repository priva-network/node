import docker
import aioipfs
from aiohttp import ClientSession, TCPConnector
from aioipfs import AsyncIPFS
import atexit
import time
import logging

class IPFSNode:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.ipfs_client = None

        self.port = None
        self.container_image = None
        self.ipfs_data_dir = None

    async def init_config(self, config):
        self.cleanup()

        self.container_image = config.IPFS_CONTAINER_IMAGE
        self.ipfs_data_dir = config.DATA_BASE_DIR

        # Start the IPFS container
        container = self.docker_client.containers.run(
            self.container_image,
            detach=True,
            ports={
                "4001/tcp": 4001,
                "4001/udp": 4001,
                "8080/tcp": 8080,
                "5001/tcp": 5001,
            },
            volumes={self.ipfs_data_dir: {'bind': '/data/ipfs', 'mode': 'rw'}},
            name="ipfs",
        )
        # as command line
        
        # Wait for the container to start
        # Keep checking until container logs say "Daemon is ready"
        while True:
            time.sleep(1)
            logs = container.logs().decode("utf-8")
            if "Daemon is ready" in logs:
                break

        logging.debug("IPFS container started")

        # Cleanup the container on exit
        atexit.register(self.cleanup)

        # Connect to the IPFS container
        self.ipfs_client = aioipfs.AsyncIPFS(
            maddr="/ip4/0.0.0.0/tcp/5001",
            debug=True,
        )

        # this is a bootstrap peer that has all the models hosted
        await self.add_peer("/ip4/35.175.177.225/tcp/4001/ipfs/12D3KooWR2xJJ4Pm1JKFm8PbbHYMmHg8yq72dqKecijEMFK8XMJt")

    async def add_peer(self, peer_id):
        if self.ipfs_client is None:
            raise Exception("IPFS client not initialized")
        try:
            await self.ipfs_client.swarm.connect(peer_id)
            logging.debug(f"Added IPFS peer: {peer_id}")
        except Exception as e:
            logging.error(f"Failed to add IPFS peer: {e}")

    def get_client(self) -> AsyncIPFS:
        if self.ipfs_client is None:
            raise Exception("IPFS client not initialized")
        return self.ipfs_client
    
    def cleanup(self):
        try:
            self.docker_client.containers.get("ipfs").stop()
            self.docker_client.containers.get("ipfs").remove()
        except:
            pass

# Global instance of the IPFSNode
ipfs_node = IPFSNode()
