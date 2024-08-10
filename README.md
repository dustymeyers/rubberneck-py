# rubberneck-py
rebuilding the rubberneck discord bot but with python and connected to dnd 5e api

I want to create a DnD 5e supporting discord bot which can make requests to dnd5eapi.co. I expect to create the main bot which will use different modules for accessing information about monsters, spells, rules, etc.

# requirements

# setup

# run

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