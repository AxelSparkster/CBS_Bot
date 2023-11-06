# CBS Bot

This bot and doesn't really do a whole lot (but that might change!!!)

A list of the, like, two things it does:
* Detects if someone mentions combo-based scoring
* Calls them out on it
* Shows the amount of time since the last time someone mentioned combo-based scoring

## Installing

You'll need to do two things to get this to work:
* Run `pip install -r requirements.txt` in the project directory
* Add your own token. (Explained in the next section.)

## Using CBS Bot

Right now, CBS Bot is automatically deployed via a CI/CD pipeline every time the main branch is updated - which affects the "official" version of the bot. 
Therefore, you'll need to do some nonsense if you want to test changes or make your own of the bot:
    * Create your own Discord bot through the Discord Developer Portal
    * Go to the Bot section and:
        * Turn "Message Content Intent" to O
        * Near the top, click Reset Token
        * Copy the token value and replace `os.environ['TOKEN']` with a string containing your actual token
    * Then, go to OAuth2 -> URL Generator and:
        * Scopes: Tick `"bot"`
        * Bot Permissions: Tick `"Send Messages"` and `"Manage Messages"`
        * Take the generated URL, go to it and then add it to whatever server you want
    * Run cbs.py

Theoretically, if you have enough Docker container knowledge, you could also throw the token into the Docker Compose file and probably do `docker compose up -d --build`, but at the current moment I need caffeine and am too lazy to figure out if what I just put in writing works, so you might just need to fuck with it a bit if I'm lying to you.

## Dependencies

* Python 3.5 or higher

Modules:
* discord.py (for discord client stuff)
* python-dotenv (duh)
* re (for regex functions - checking if the words exist in each message)
* datetime (to get last combo-based scoring mention)
* os/sys (grouping these together, these are for getting the script directory, but may change this later to something that looks more safe)
* pandas (Reading/saving CSV files, soon to be deprecated)
* unidecode (Attempt to prevent people from getting around the bot by using Unicode stuff)

## Future/Potential Upgrades

* Use MongoDB instead of a shitty CSV file 
* Restructure the project to make it cleaner
* Better detection of combo-based scoring mentions
* More features in general

## Contributing

* Non-contributors will use a [forking workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow). TL;DR, fork the repo, make a PR, and Losermanwins or I will accept it and merge it.
    * Please make sure the code builds and runs before submitting. (Please.)
* Contributors will follow a [Feature branch workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow). We'll make feature branches and merge them into `main` via PR
* `main` is protected. Losermanwins or I must approve the changes.
