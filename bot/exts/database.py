from typing import Mapping, Any

import bson
import logging
import os
import pymongo
import urllib.parse

from bot.resources.models import MatchType

# MongoDB related junk
MONGO_CLIENT = pymongo.MongoClient((f'mongodb://{urllib.parse.quote_plus(str(os.getenv("MONGODB_USERNAME")))}' +
                                    f':{urllib.parse.quote_plus(str(os.getenv("MONGODB_PASSWORD")))}' +
                                    f'@mongo:27017/{str(os.getenv("MONGODB_DATABASE"))}?authSource=admin'))
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


def insert_match_data(match_data: dict[str, str | Any]):
    MESSAGE_COLLECTION.insert_one(match_data)


def get_last_match(match_type: MatchType, guild_id: int) -> Mapping[str, Any]:
    return (MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(guild_id),
                                     "match_type": str(match_type)})
            .sort({"created_at": -1}).limit(1).next())


def get_number_match_mentions(match_type: MatchType, guild_id: int):
    return len(list(MESSAGE_COLLECTION.find({"guild_id": bson.int64.Int64(guild_id),
                                             "match_type": str(match_type)})))


def set_bot_messages_ability(messages_enabled: bool, guild_id: int):
    SETTINGS_COLLECTION.update_one({"guild_id": bson.int64.Int64(guild_id)},
                                   {"$set": {"message_enabled": messages_enabled}})
