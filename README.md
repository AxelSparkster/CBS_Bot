# CBS Bot

This bot doesn't really do a whole lot (but that might change!!!)

A list of the, like, three things it does:
* Detects if someone mentions combo-based scoring
* Calls them out on it
* Shows the amount of time since the last time someone mentioned combo-based scoring

## Installing

You'll need to do two things to get this to work:
* Run `pip install -r requirements.txt` in the project directory
* Add your own token (explained in the next section)
* Make a .env file
* Run the Docker process

## Using CBS Bot

Right now, CBS Bot is automatically deployed via a CI/CD pipeline every time the main branch is updated - which affects the "official" version of the bot. 

Therefore, you'll need to do some nonsense if you want to test changes or set up your own of the bot:

* Create your own Discord bot through the Discord Developer Portal
   * Go to the `Bot` section and:
       * Turn "Message Content Intent" to ON
       * Near the top, click `Reset Token`
       * Copy the token value and replace `os.environ['TOKEN']` with a string containing your actual token
   * Then, go to OAuth2 -> URL Generator and:
       * Scopes: Tick `"bot"`
       * Bot Permissions: Tick `"Send Messages"` and `"Manage Messages"`
       * Take the generated URL, go to it and then add it to whatever server you want
   * Go to Google CSE to get the API key and Project CX ID
       * You can get those here:
           * API key: https://console.developers.google.com/apis/credentials
           * Project CX: https://cse.google.com/cse/all 
   * Create a .env file with these properties:
       * MONGODB_USERNAME=\<something\>
       * MONGODB_PASSWORD=\<something\>
       * MONGODB_DATABASE=\<something\>
       * GIS_API_KEY=\<something\>
       * GIS_PROJECT_CX=\<something\>
   * Do `docker compose up -d --build`, but at the current moment I need caffeine and am too lazy to figure out if what I just put in writing works, so you might just need to fuck with it a bit.

## Dependencies

* Python 3.5 or higher

Modules:
* `datetime` (to get last combo-based scoring mention)
* `discord.py` (for discord client stuff)
* `os` (to get script directory - might find a different/safer option later)
* `json` (to get random possum image from google CSE)
* `pymongo` (for dealing with MongoDB databased)
* `random` (to help get random possum image)
* `re` (for regex functions - checking if the words exist in each message)
* `sys` (to get script directory - might find a different/safer option later)
* `discord.ext` (Extended discord.py library)
* `pytz` (Fixes timezone nonsense when loading data back from MongoDB)
* `unidecode` (Attempt to prevent people from getting around the bot by using Unicode stuff)

## Future/Potential Upgrades

* Restructure the project to make it cleaner
* Better detection of combo-based scoring mentions
* More features in general

## Contributing

* Non-contributors will use a [forking workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow). TL;DR, fork the repo, make a PR, and Losermanwins or I will accept it and merge it
    * Please make sure the code builds and runs before submitting (please)
* Contributors will follow a [feature branch workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow). We'll make feature branches and merge them into `main` via PR
* The `main` branch is protected. Losermanwins or I must approve changes before any updates to this branch
