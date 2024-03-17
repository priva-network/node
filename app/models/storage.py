from app.chain import model_registry
from aioipfs import AsyncIPFS
import logging
import os
import shutil

class ModelStorage:
    def __init__(self):
        self.ipfs_client = None
        self.model_storage_base_path = None
        self.supported_models = None

    def init(self, config, ipfs_client: AsyncIPFS):
        self.model_storage_base_path = os.path.join(config.DATA_BASE_DIR, "models")
        self.ipfs_client = ipfs_client
        os.makedirs(self.model_storage_base_path, exist_ok=True)

        self.supported_models = config.SUPPORTED_MODELS

    def get_supported_models(self):
        return self.supported_models

    def _parse_model_dir(self, model_name: str) -> str:
        lower_model_name = model_name.lower()
        return os.path.join(self.model_storage_base_path, lower_model_name)

    async def _download_model(self, ipfs_hash: str, target_dir: str) -> str:
        logging.debug(f"Downloading model from IPFS: {ipfs_hash}")
        os.makedirs(target_dir, exist_ok=True)
        await self.ipfs_client.core.get(ipfs_hash, dstdir=target_dir)
        # move it from the subdirectory (/<ipfs_hash>) to the target directory
        for filename in os.listdir(os.path.join(target_dir, ipfs_hash)):
            shutil.move(os.path.join(target_dir, ipfs_hash, filename), os.path.join(target_dir, filename))
        os.rmdir(os.path.join(target_dir, ipfs_hash))
        return target_dir

    async def _estimate_ipfs_content_size(self, ipfs_hash: str) -> int:
        """
        Estimate the size of content on IPFS by its hash.

        :param ipfs_hash: The IPFS hash of the content to estimate size for.
        :return: The estimated size in bytes.
        """
        logging.debug(f"Estimating IPFS content size: {ipfs_hash}")
        try:
            stats = await self.ipfs_client.object.stat(ipfs_hash)
            logging.debug(f"IPFS content stats: {stats}")
            if not stats or 'CumulativeSize' not in stats:
                return 0
            return stats['CumulativeSize']
        except Exception as e:
            logging.error(f"Failed to estimate IPFS content size: {e}")
            return 0
        
    def _has_enough_space(self, target_dir: str, required_space: int) -> bool:
        _, _, free = shutil.disk_usage(target_dir)
        return free >= required_space
    
    def _delete_older_models(self, required_space: int) -> bool:
        model_dirs = [os.path.join(self.model_storage_base_path, d) for d in os.listdir(self.model_storage_base_path) if os.path.isdir(os.path.join(self.model_storage_base_path, d))]
        model_dirs.sort(key=lambda x: os.path.getmtime(x))

        for model_dir in model_dirs:
            if self._has_enough_space(self.model_storage_base_path, required_space):
                return True  # Enough space has been freed
            logging.debug(f"Deleting model to free space: {model_dir}")
            shutil.rmtree(model_dir)
        
        return self._has_enough_space(self.model_storage_base_path, required_space)
    
    async def is_model_downloaded(self, model_name: str) -> bool:
        lower_model_name = model_name.lower()
        model_dir = self._parse_model_dir(lower_model_name)
        return os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "config.json"))

    async def get_model_dir(self, model_name: str) -> str:
        lower_model_name = model_name.lower()
        # Check if the model is already downloaded
        model_dir = self._parse_model_dir(lower_model_name)
        if os.path.exists(model_dir):
            # check if directory has a config.json file
            if os.path.exists(os.path.join(model_dir, "config.json")):
                return model_dir
            else:
                logging.warning(f"Model directory {model_dir} does not contain a config.json file. Redownloading the model.")
                shutil.rmtree(model_dir)
        
        # Otherwise download the model from IPFS
        model_details = model_registry.get_model_details(model_name)
        ipfs_hash = model_details.ipfs_hash

        logging.debug(f"Retrieved model IPFS hash from chain: {ipfs_hash}")

        # Estimate the size of the model
        required_space = await self._estimate_ipfs_content_size(ipfs_hash)
        
        if not self._has_enough_space(self.model_storage_base_path, required_space):
            if not self._delete_older_models(required_space):
                raise Exception("Not enough space to download the model, even after cleaning old models.")
            
        logging.debug(f"Enough space to download the model: {required_space} bytes")

        model_path = await self._download_model(ipfs_hash, model_dir)
        return model_path
    
# Global instance of the ModelStorage
model_storage = ModelStorage()
