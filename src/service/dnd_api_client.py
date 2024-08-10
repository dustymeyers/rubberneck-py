from logging import Logger
import requests
from typing import Any, Dict, List
from models import Monster

class DnDAPIClient:
    """
        Description:
            A client for the DnD 5e API.
    """

    base_url: str
    logger: Logger

    def __init__(self, base_url: str, logger: Logger):
        self.base_url = base_url
        self.logger = logger
        self.logger.info("DnDAPIClient initialized")

    def get_monsters(self) -> List[Monster]:
        url = f"{self.base_url}/monsters"
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.logger.info(f"Successfully fetched monsters from {url}")
            monsters_json: List[Dict[str,Any]] = response.json()['results']
            return [Monster(monster) for monster in monsters_json]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monsters from {url}: {e}")
            raise

    def get_monster(self, index: str) -> Dict[str, Any]:
        url = f"{self.base_url}/monsters/{index}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            monster_json: Dict[str,Any] = response.json()
            return Monster(monster_json).to_dict()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monster {index} from {url}: {e}")
            raise
