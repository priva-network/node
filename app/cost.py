import requests
from cachetools import cached, TTLCache

ONE_ETH_IN_WEI = 10**18

@cached(cache=TTLCache(maxsize=1024, ttl=300))
def get_usd_to_eth_conversion_rate():
    # Using the CoinGecko API for cryptocurrency data
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        eth_price_in_usd = data['ethereum']['usd']
        return eth_price_in_usd
    except requests.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return None

class CostCalculator:
    def __init__(self):
        self.usd_cost_per_1000_tokens_map = None

    def init_config(self, config):
        self.usd_cost_per_1000_tokens_map = config.USD_COST_PER_1000_TOKENS

    def calculate_cost(self, tokens_used, model=None, currency="USD"):
        if tokens_used is None or tokens_used <= 0:
            return 0

        usd_cost_per_1000_tokens = None
        if model is None:
            usd_cost_per_1000_tokens = self.usd_cost_per_1000_tokens_map.get('default')
        else:
            usd_cost_per_1000_tokens = self.usd_cost_per_1000_tokens_map.get(model)
            if usd_cost_per_1000_tokens is None:
                usd_cost_per_1000_tokens = self.usd_cost_per_1000_tokens_map.get('default')
        
        usd_cost = (tokens_used / 1000) * usd_cost_per_1000_tokens

        if currency == "USD":
            return usd_cost
        
        if currency == "ETH":
            eth_to_usd_rate = get_usd_to_eth_conversion_rate()
            if eth_to_usd_rate is not None:
                return usd_cost / eth_to_usd_rate
            return None
        
        if currency == "ETH_WEI":
            eth_to_usd_rate = get_usd_to_eth_conversion_rate()
            if eth_to_usd_rate is not None:
                eth_cost = usd_cost / eth_to_usd_rate
                return int(eth_cost * ONE_ETH_IN_WEI)
            return None

    
# Create a global instance of the cost calculator
cost_calculator = CostCalculator()
