import json
from logging import Logger
from logger  import logger
import requests
from typing import Any, Dict, List
from models import Monster
from models.monster import MonsterSchema
from service.redis_client import RedisClient

class DnDAPIClient:
    """
        Description:
            A client for the DnD 5e API.
    """

    __base_url: str
    logger: Logger
    redis_client: RedisClient
    __base_url: str = 'https://www.dnd5eapi.co/api/monsters'

    def __init__(self):
        self.logger = logger

        try:
            self.redis_client = RedisClient()
        except Exception as e:
            self.logger.error(f"Initializing RedisClient failed: {e}")
        self.logger.info("DnDAPIClient initialized")

    def get_monsters(self) -> List[Monster]:
        """
        Uses lazy loading to load the monsters from the API. Stores them in the redis cache for one hour.
        Returns a list of Monster objects.
        """
        try:
            monsters_json: List[Dict[str,Any]] = self._lazy_load_monsters_list_json()
            
            return [Monster(monster) for monster in monsters_json]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting monsters: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error getting monsters: {e}")
            raise e
    
    def _lazy_load_monsters_list_json(self) -> List[Dict[str,Any]]:
        try:
            monsters_json_list = self._get_cached_monsters()

        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error retrieving monsters from cache: {e}")
            monsters_json_list = None

        if monsters_json_list is None:
            try:
                monsters_json_list = self._get_monsters_list_from_api()
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__} - Error while lazy loading monsters: {e}")
                raise e
            
            try:
                self._cache_monsters_list_json(monsters_json_list)
            except:
                self.logger.error(f"{self.__class__.__name__} - Error caching monsters json")
        
        return monsters_json_list
    
    def _get_cached_monsters(self) -> List[Dict[str,Any]] | None:
        redis_key = "json:monsters"
        cached_monsters = None
        try: 
            cached_monsters_str = self.redis_client.get_value(redis_key).decode('utf-8')

            cached_monsters = json.loads(cached_monsters_str)
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error retrieving monsters from cache: {e}")
        finally:
            return cached_monsters
        
    def _cache_monsters_list_json(self, monsters_json_list: List[Dict[str,Any]]) -> None:
        redis_key = "json:monsters"
        try:
            self.redis_client.set_value_ex(redis_key, 3600, json.dumps(monsters_json_list))
            self.logger.info(f"{self.__class__.__name__} - Cached monsters for 1 hour")
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error caching monsters: {e}")

    def _get_monsters_list_from_api(self) -> List[Dict[str,Any]]:
        try:
            response = requests.get(self.__base_url)
            response.raise_for_status()
            monsters_json_list: List[Dict[str,Any]] = response.json()['results']
            self.logger.info(f"{self.__class__.__name__} - Successfully fetched monsters from {self.url}")
            return monsters_json_list
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{self.__class__.__name__} - Error fetching monsters from {self.url}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error while fetching monsters: {e}")
            raise

    def get_monster(self, index: str) -> Dict[str, Any]:
        self.redis_client
        url = f"{self.__base_url}/{index}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            monster_json: Dict[str,Any] = response.json()
            return Monster(monster_json).to_dict()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching monster {index} from {url}: {e}")
            raise
    
    def add_monster(self, monster_data: Dict[str, Any]) -> None:
        try:
            self.redis_client.create('monster:', monster_data)
            schema = MonsterSchema()
            monster = schema.load(monster_data)
            redis_monster = {
                key: str(value) if isinstance(value, (list, dict)) else value
                for key,value in monster.items() if value is not None
            }
            self.redis_client.create('monster:', redis_monster)
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} - Error adding monster: {e}")
            raise e