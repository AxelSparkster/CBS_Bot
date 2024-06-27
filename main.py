import asyncio
import nest_asyncio

from bot.cbs import main

if __name__ == '__main__':
    # This line is needed since asyncio by itself has trouble running main() due to the event
    # listener being too busy and causes a "asyncio.run() cannot be called from a running event loop"
    # error.
    nest_asyncio.apply()

    asyncio.run(main())
