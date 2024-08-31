import json
from logging import Logger
from logger  import logger
import requests
from typing import Any, Dict, List
from models import Monster
from service.redis_client import RedisClient

class DnDAPIClient:
    """
        Description:
            A client for the DnD 5e API.
    """

    base_url: str
    logger: Logger
    redis_client: RedisClient

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logger

        try:
            self.redis_client = RedisClient()
        except Exception as e:
            self.logger.error(f"Initializing RedisClient failed: {e}")
        self.logger.info("DnDAPIClient initialized")

    def get_monsters(self) -> List[Monster]:
        url = f"{self.base_url}"
        try:
            monsters_json: List[Dict[str,Any]] = self._lazy_load_monsters()
            return [Monster(monster) for monster in monsters_json]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monsters from {url}: {e}")
            raise
    
    def _lazy_load_monsters(self) -> List[Dict[str,Any]]:
        url = f"{self.base_url}"
        redis_key = "monsters"

        if self.redis_client:
            try:
                cached_monsters = self.redis_client.get_value(redis_key)
                if cached_monsters:
                    self.logger.info("Using cached monsters")
                    return json.loads(cached_monsters)
                else:
                    self.logger.info(f"{self.__class__.__name__} - No monsters in cache")
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__} - Error retrieving monsters from cache: {e}")
        else:
            self.logger.warning(f"{self.__class__.__name__} - Redis client not initialized")
        try:
            self.logger.info(f"{self.__class__.__name__} - Fetching monsters from {url}")
            response = requests.get(url)
            response.raise_for_status()
            monsters_json_list: List[Dict[str,Any]] = response.json()['results']
            self.logger.info(f"{self.__class__.__name__} - Successfully fetched monsters from {url}")

            if self.redis_client:
                try:
                    self.redis_client.set_value_ex(redis_key, 3600, json.dumps(monsters_json_list))
                    self.logger.info(f"{self.__class__.__name__} - Cached monsters for 1 hour")
                except Exception as e:
                    self.logger.error(f"{self.__class__.__name__} - Error caching monsters: {e}")

            return monsters_json_list
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{self.__class__.__name__} - Error fetching monsters from {url}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error while lazy loading monsters: {e}")
            raise
    

    def get_monster(self, index: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{index}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            monster_json: Dict[str,Any] = response.json()
            return Monster(monster_json).to_dict()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monster {index} from {url}: {e}")
            raise
