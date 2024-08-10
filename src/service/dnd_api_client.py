import logging
import requests
from typing import Any, Dict, List

class DnDAPIClient:

    base_url: str
    logger: logging.Logger
    
    def __init__(self, base_url: str, logger: logging.Logger):
        self.base_url = base_url
        self.logger = logger
        self.logger.info("DnDAPIClient initialized")

    def get_monsters(self) -> List[Dict[str,Any]]:
        url = f"{self.base_url}/monsters"
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.logger.info(f"Successfully fetched monsters from {url}")
            return response.json()['results']
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monsters from {url}: {e}")
            raise

    def get_monster(self, index: str) -> Dict[str, Any]:
        url = f"{self.base_url}/monsters/{index}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monster {index} from {url}: {e}")
            raise
