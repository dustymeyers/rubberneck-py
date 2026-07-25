"""Compatibility launcher for local development and existing deployments."""

from rubberneck.app import PRODUCTION_COGS, bot, load_production_cogs, main

__all__ = ["PRODUCTION_COGS", "bot", "load_production_cogs", "main"]

if __name__ == "__main__":
    main()
