import builtins
import importlib


def test_production_packages_do_not_import_redis(monkeypatch):
    original_import = builtins.__import__

    def reject_redis(name, *args, **kwargs):
        if name == "redis" or name.startswith("redis."):
            raise AssertionError("Production package imported optional Redis code")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_redis)

    import cogs
    import service

    importlib.reload(cogs)
    importlib.reload(service)
