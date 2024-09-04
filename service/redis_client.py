from logger import logger
from logging import Logger
import redis
from redis.exceptions import ConnectionError
from redis.commands.json.path import Path
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
from functools import wraps

class RedisClient:
    _instance = None
    _host: str 
    _port: int 
    _r: redis.Redis = None 
    _logger: Logger

    def __new__(cls):
        if cls._instance is None:
            try:
                cls._instance = super(RedisClient, cls).__new__(cls)
                cls._instance._init()
            except Exception as e:
                raise e
        return cls._instance
    
    def _init(self):
        try:
            self._logger = logger
            self._host = "localhost"
            self._port = 6379
            self._connect()

        except Exception as e:
            raise e

    def _connect(self):
        try:
            if self.ping():
                self.logger.debug(f"{self.__class__.__name__} - Already connected to Redis")
                pass
            else:
                self._r = redis.Redis(host=self._host, port=self._port)
                self._logger.info(f"{self.__class__.__name__} - Successfully connected to Redis")
        except ConnectionError as e:
            self._logger.error(f"{self.__class__.__name__} - Error connecting to Redis: {e}")
            raise e

    def ping(self) -> bool:
        try:
            if self._r is None:
                return False
            else:
                return self._r.ping()
        except ConnectionError as e:
            self._logger.error(f"{self.__class__.__name__} - Error pinging Redis: {e}")
            return False
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__} - Error pinging Redis: {e}")
            raise e
    
    def _ensure_connection(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.ping():
                self._connect()
            return func(self, *args, **kwargs)
        return wrapper
    
    @_ensure_connection
    def set_value(self, key, value):
        return self._r.set(key, value)
    
    @_ensure_connection
    def set_value_ex(self, key, time, value):
        return self._r.setex(key, time, value)
    
    @_ensure_connection
    def get_value(self, key):
        return self._r.get(key)

    @_ensure_connection
    def delete_value(self, key):
        return self._r.delete(key)
    
    @_ensure_connection
    def exists(self, key):
        return self._r.exists(key)

    @_ensure_connection
    def create(self, key_prefix, data):
        return self._r.ft().create(key_prefix, data)