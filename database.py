import bson
import logging
import os
import pymongo
import urllib.parse

# MongoDB related junk
MONGO_CLIENT = pymongo.MongoClient((f'mongodb://{urllib.parse.quote_plus(os.getenv("MONGODB_USERNAME"))}' +
                                    f':{urllib.parse.quote_plus(os.getenv("MONGODB_PASSWORD"))}' +
                                    f'@mongo:27017/{os.getenv("MONGODB_DATABASE")}?authSource=admin'))
CBS_DATABASE = MONGO_CLIENT["cbs-database"]
MESSAGE_COLLECTION = CBS_DATABASE["message-collection"]
SETTINGS_COLLECTION = CBS_DATABASE["settings-collection"]


def has_guild_settings(guild_id: int):
    number_guild_settings = len(list(SETTINGS_COLLECTION.find({"guild_id": bson.int64.Int64(guild_id)})))
    return number_guild_settings > 0


def insert_default_guild_settings(guild_id: int):
    default_settings = {"guild_id": guild_id, "message_enabled": True}
    SETTINGS_COLLECTION.insert_one(default_settings)
    logging.warning(f"Settings did not exist for {guild_id}, inserted default values.")
