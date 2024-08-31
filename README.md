# rubberneck-py
rebuilding the rubberneck discord bot but with python and connected to dnd 5e api

I want to create a DnD 5e supporting discord bot which can make requests to dnd5eapi.co. I expect to create the main bot which will use different modules for accessing information about monsters, spells, rules, etc.

## requirements

Some kind of IDE that is able to run python. I suggest Visual Studio Code (VSC).

[Python 3.12.4](https://www.python.org/downloads/release/python-3124/)

[Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)


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

3. Install the dependencies.

```shell
    pip install-r requirements.txt
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

4. To stop the redis-server,
    - if using wsl, use the command `sudo service redis-server stop`
    
### running in production 
1. *cd* into the working directory, and execute main.py.

```shell
    python main.py
```

2. The rest of the production plan doesn't exist yet since there has not been a full release.



- dnd_discord_bot/
    - bot/
        - __init__.py
        - main.py
    - modules/
        - __init__.py
        - monsters.py
        - spells.py
        - rules.py
    - data/
        - (optional: store data files)
    - requirements.txt
    - .gitignore

Here's a brief explanation of each directory:

bot/: This directory contains the main files for your Discord bot.
__init__.py: Makes the bot directory a Python package.
main.py: Contains the code for setting up the Discord bot, handling events, and integrating modules.
modules/: This directory contains separate modules for different functionalities like monsters, spells, and rules.
__init__.py: Makes the modules directory a Python package.
monsters.py, spells.py, rules.py: Modules for accessing information about monsters, spells, rules, etc. from the DnD 5e API.
data/: You can store any data files or resources that your bot might need here.
requirements.txt: A file that lists the Python dependencies your project needs. You can generate this file using pip freeze > requirements.txt.
.gitignore: A file that specifies which files and directories to ignore when using version control with Git.