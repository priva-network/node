import requests

class PrivaAPIException(Exception):
    """Custom exception class for PrivaAPI errors."""
    pass

class PrivaAPI:
    def __init__(self):
        self.api_key = None
        self.base_url = None

    def init_config(self, config):
        self.base_url = config.PRIVA_API_BASE_URL

    def request_eth(self, address, api_key=None) -> dict:
        """
        Request ETH from the Priva Network.
        """
        if api_key is None and self.api_key is None:
            raise Exception("API Key not provided.")
        if api_key is None:
            api_key = self.api_key
        
        url = f"{self.base_url}/v1/node/request-eth"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'address': address
        }
        response = requests.post(url, headers=headers, json=data)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Attempt to extract the error message from the response JSON
            error_message = "An error occurred."
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_message = error_data['error']
            except ValueError:
                # JSON decoding failed
                pass
            # Raise a custom exception with the extracted error message
            raise PrivaAPIException(f"{error_message}") from e

        return response.json()

# Global instance of Priva API
priva_api = PrivaAPI()