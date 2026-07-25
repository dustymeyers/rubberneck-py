# rubberneck-py
rebuilding the rubberneck discord bot but with python and connected to dnd 5e api

I want to create a DnD 5e supporting discord bot which can make requests to dnd5eapi.co. I expect to create the main bot which will use different modules for accessing information about monsters, spells, rules, etc.

## commands

- `/rule name` looks up a rule section from the 2014 D&D 5e SRD. Begin typing
  to see matching rules such as **Cover**, **Resting**, or **Making an Attack**.
  API responses are fetched asynchronously and cached in memory for one hour.
- `/rules lookup term` searches both rule sections and conditions.
- `/rules search text` searches inside locally indexed rule and condition
  descriptions. Queries require at least three characters and return up to 20
  ranked results in one paginated response.
- `/monsters` browses the available 2014 SRD monsters.
- `/monster name` looks up a monster with cached autocomplete.

All production commands use bounded in-process caching. Redis is not required
to install, start, or run the bot.

`/rule` remains available as a compatibility alias while the unified `/rules`
commands evolve.

When `GUILD_ID` is set in `.env`, the `/rules` group is registered directly to
that development server so new commands and subcommands appear immediately.
Without `GUILD_ID`, the group is registered globally and Discord may take time
to propagate a newly created command.

## requirements

Some kind of IDE that is able to run python. I suggest Visual Studio Code (VSC).

[Python 3.12.4](https://www.python.org/downloads/release/python-3124/)

See the requirements.txt for a list of python library dependencies.

## setup

1. Create a virtual environment.

```shell
    python -m venv venv
```

2. Activate the virtual environment. VSC terminals will activate the virtual environment if you point the interpreter to the virtual environment, otherwise use the following command. 

*Windows*
```shell
    venv\Scripts\activate
```

*macOS/Linux*
```shell
    source venv/bin/activate
```

3. Install runtime dependencies.

```shell
    pip install -r requirements.txt
```

For development and tests, install the development set instead:

```shell
    pip install -r requirements-dev.txt
```

4. (Optional) - Remove password requirement for sudo commands. From the Linux shell, do the following:

```shell
    cd /etc/sudoers.d
    sudo sh
    echo "%sudo ALL=(ALL) NOPASSWD: /usr/sbin/service redis-server *" >> allowed-services
    sudo chmod 0440 allowed-services
    exit
```

## running in debug mode with VSC

1. Start up the redis server

    - Windows:
        1. In your command line run `wsl` to log into your ubuntu instance.
        2. Run `sudo service redis-server start`

2. *(Optional)* Setup your `launch.json`, if you don't already have one. 

*Example*:
- *Note*: you'll need to get a discord bot token for testing. For steps on how to get the `DISCORD_BOT_TOKEN`, follow guide from [pycord](https://docs.pycord.dev/en/stable/discord.html)

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Bot",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "env": {
                "DISCORD_BOT_TOKEN": ""
            }
        }
    ]
}
```

3. Press the play button for "Debug Bot" selection, or hit `F5` if you've already got it selected.

### running tests

```shell
pytest
```

### formatting and linting

```shell
ruff format .
ruff check .
```

### running in production

From the repository root, run the application package:

```shell
python -m rubberneck
```

`python main.py` remains as a compatibility launcher. Application code lives in
the `rubberneck` package: `rubberneck.cogs` contains Discord presentation and
commands, while `rubberneck.services` contains API, catalog, search, and
relationship logic.
