from app.chain import model_registry
from aioipfs import AsyncIPFS
import requests
import logging
import os
import shutil

class ModelStorage:
    def __init__(self):
        self.ipfs_client = None
        self.model_storage_base_path = None
        self.supported_models = None

        self.ipfs_gateway_url = "https://ipfs.usescholar.org/ipfs"

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
    
    def _download_file_with_stream(self, url: str, target_dir: str, filename: str):
        import time
        file_path = os.path.join(target_dir, filename)
        start_download = time.time()
        last_progress_time = start_download
        progress_timeout = 1800  # 30 minutes

        # files can be quite large so we opt to stream the download
        with requests.get(url, stream=True) as r:
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if time.time() - last_progress_time > progress_timeout:
                        raise Exception("Download timed out due to inactivity.")
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        last_progress_time = time.time()

    def _download_file_in_chunks(
            self, url: str, target_dir: str, filename: str,
            total_size: int, chunk_size: int = 10*1024*1024
        ):
        from tqdm import tqdm

        # the urllib prints a lot of debug logs for each chunk download
        # which is unncessary and annoying so let's suppress it.
        logger = logging.getLogger("urllib3.connectionpool")
        original_level = logger.getEffectiveLevel()
        logger.setLevel(logging.WARNING)

        target_path = os.path.join(target_dir, filename)

        # Initialize progress bar
        pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc=filename)

        with open(target_path, 'wb') as f:
            for start in range(0, total_size, chunk_size):
                end = min(start + chunk_size - 1, total_size - 1)

                # Implement retries for this chunk
                attempts = 0
                max_attempts = 5
                while attempts < max_attempts:
                    try:
                        # Specify the range of bytes to download
                        headers = {'Range': f'bytes={start}-{end}'}
                        response = requests.get(url, headers=headers, stream=True)
                        response.raise_for_status()  # Check for HTTP errors
                        
                        f.write(response.content)
                        pbar.update(len(response.content))
                        break  # Chunk downloaded successfully
                    except requests.RequestException as e:
                        attempts += 1
                        logging.error(f"Failed to download chunk: {e}, attempt {attempts}/{max_attempts}, retrying...")
                        if attempts == max_attempts:
                            pbar.close()
                            raise Exception(f"Failed to download chunk after {max_attempts} attempts.")
                        
        pbar.close()
        logger.setLevel(original_level)  # Reset the logging level
    
    def _download_file_from_gateway(
        self, ipfs_hash: str, target_dir: str, filename: str,
        chunk_size: int = 10*1024*1024 # 10MB
    ) -> str:
        url = f"{self.ipfs_gateway_url}/{ipfs_hash}"

        # get file size
        response = requests.head(url)
        if response.status_code != 200:
            raise Exception(f"Failed to download file from IPFS gateway: {response.status_code}")
        file_size = int(response.headers.get('Content-Length', 0))
        logging.debug(f"File size for url {url}: {file_size}")

        if file_size > chunk_size:
            self._download_file_in_chunks(url, target_dir, filename, file_size, chunk_size)
        else:
            self._download_file_with_stream(url, target_dir, filename)

    async def _download_model(self, ipfs_hash: str, target_dir: str) -> str:
        logging.info(f"Downloading model from IPFS Hash: {ipfs_hash}")
        os.makedirs(target_dir, exist_ok=True)

        def progress_callback(*args, **kwargs):
            logging.debug(f"IPFS download progress: {args}, {kwargs}")

        def cleanup_failed_download():
            logging.error("Cleaning up failed download...")
            shutil.rmtree(target_dir)

        ls_result = await self.ipfs_client.ls(ipfs_hash)
        ipfs_files = []
        for obj in ls_result['Objects']:
            for link in obj['Links']:
                ipfs_files.append(link['Name'])

        logging.debug(f"IPFS files in {ipfs_hash}: {ipfs_files}")

        try:
            await self.ipfs_client.core.get(ipfs_hash, dstdir=target_dir, progress_callback=progress_callback)
            # move it from the subdirectory (/<ipfs_hash>) to the target directory
            for filename in os.listdir(os.path.join(target_dir, ipfs_hash)):
                shutil.move(os.path.join(target_dir, ipfs_hash, filename), os.path.join(target_dir, filename))
            os.rmdir(os.path.join(target_dir, ipfs_hash))

            logging.debug(f"Model downloaded to: {target_dir}")
        except Exception as e:
            logging.warn(f"Failed to directly download model from IPFS, attempting individual files: {e}")

            succeeded_files = []
            failed_files = []

            # Download each file individually
            for obj in ls_result['Objects']:
                for link in obj['Links']:
                    try:
                        file_hash = link['Hash']
                        file_name = link['Name']
                        await self.ipfs_client.core.get(file_hash, dstdir=target_dir, progress_callback=progress_callback)
                        # move it from the subdirectory (/<file_hash>) to the target directory
                        shutil.move(os.path.join(target_dir, file_hash), os.path.join(target_dir, file_name))
                        logging.info(f"Downloaded file {file_name} to {target_dir} from IPFS Node")
                        succeeded_files.append(file_name)
                    except Exception as e:
                        logging.error(f"Failed to download file {file_name}: {e}")
                        failed_files.append({
                            "name": file_name,
                            "hash": file_hash
                        })

            if len(failed_files) > 0:
                logging.warn(f"Failed to download {len(failed_files)} files from IPFS Node, trying to download from HTTPS gateway")
                # try to download failed files directly from a gateway using HTTP
                for file in failed_files:
                    try:
                        filename = file['name']
                        file_hash = file['hash']
                        self._download_file_from_gateway(file_hash, target_dir, filename)
                        succeeded_files.append(filename)
                        logging.info(f"Downloaded file {filename} to {os.path.join(target_dir, filename)} from IPFS gateway")
                    except Exception as e:
                        logging.error(f"Failed to download file {filename} from IPFS gateway: {e}")
                        cleanup_failed_download()
                        raise Exception(f"Failed to complete download of model from IPFS: {e}")

            if len(succeeded_files) == 0:
                cleanup_failed_download()
                raise Exception("Failed to download any files from IPFS")

        # make sure that the files in the ipfs_hash exist in the target_dir
        logging.info("Verifying all files were successfully downloaded...")
        for file in ipfs_files:
            if not os.path.exists(os.path.join(target_dir, file)):
                cleanup_failed_download()
                raise Exception(f"Failed to download file {file} from IPFS")

        logging.info("All files successfully downloaded")

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
        if os.path.exists(model_dir):
            # check if directory has a config.json file
            if os.path.exists(os.path.join(model_dir, "config.json")):
                return True
            else:
                logging.debug(f"Model directory {model_dir} does not contain a config.json file. Redownloading the model.")
                shutil.rmtree(model_dir)
        return False
    
    async def download_model(self, model_name: str) -> str:
        lower_model_name = model_name.lower()
        model_dir = self._parse_model_dir(lower_model_name)
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

    async def get_model_dir(self, model_name: str, download_if_not_saved: bool = False) -> str:
        lower_model_name = model_name.lower()
        # Check if the model is already downloaded
        is_downloaded = await self.is_model_downloaded(model_name)
        if is_downloaded:
            return self._parse_model_dir(lower_model_name)

        if not download_if_not_saved:
            raise Exception(f"Model {model_name} not downloaded")
        
        # Otherwise download the model from IPFS
        model_path = await self.download_model(model_name)
        return model_path
    
# Global instance of the ModelStorage
model_storage = ModelStorage()

