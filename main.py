import asyncio
import nest_asyncio
from webdrivermanager import ChromeDriverManager

from bot.cbs import main

if __name__ == '__main__':
    # This line is needed since asyncio by itself has trouble running main() due to the event
    # listener being too busy and causes a "asyncio.run() cannot be called from a running event loop"
    # error.
    nest_asyncio.apply()

    # Machines may not have the binaries to run Selenium; they must be downloaded before the bot runs
    # or else the bot may become unstable for commands that need it.
    cdm = ChromeDriverManager()
    cdm.download_and_install()

    asyncio.run(main())
