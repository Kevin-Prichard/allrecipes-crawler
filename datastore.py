from datetime import datetime as dt, timedelta as td
import json
import os
import secrets
from threading import Thread, Lock
from requests.packages.urllib3.util import Url
from requests.packages.urllib3.util import parse_url
import logging

import pymongo
from pymongo import MongoClient
from simple_classproperty import classproperty

mutex = Lock()
logging.basicConfig()
logger = logging.getLogger(__name__)


class EmptyQueueException(Exception):
    pass


class RecipeStore:
    _instance = None

    DATABASE_NAME = 'RecipeDB'
    COLL_NAME_QUEUE = 'queue'
    COLL_NAME_RECIPE = 'recipe'
    COLL_NAME_HISTORY = 'action'

    def __init__(self):
        # print("\n".join(str(kv) for kv in os.environ.items()))
        self.user = os.environ.get("MONGO_APP_USERNAME")
        self.passwd = os.environ.get("MONGO_APP_PASSWORD")
        self.host = os.environ.get("localhost")
        # self.conn_uri = f"mongo+srv://{self.user}:{self.passwd}@"
        # import pudb; pu.db
        self._mdb = MongoClient()
        self._ensure_existence()
        logger.info("Database start: %s", self._db_stats_report())

    @classproperty
    def instance(cls) -> 'RecipeStore':
        if cls._instance is None:
            mutex.acquire()
            try:
                # Why check twice? Multiple threads could can slip past the
                # first if, and we don't want the lock penalty on every
                if cls._instance is None:
                    cls._instance = cls()
            finally:
                mutex.release()
        return cls._instance

    @classmethod
    def _get_indices(cls, coll):
        return {index['key'].keys()[0]: index for index
                in list(coll.list_indexes())}

    def _ensure_existence(self):
        # Database
        self._db = self._mdb[self.DATABASE_NAME]

        # Collections
        self._queue = self._db[self.COLL_NAME_QUEUE]
        self._recipe = self._db[self.COLL_NAME_RECIPE]
        self._action = self._db[self.COLL_NAME_HISTORY]

        # Indices - queue
        # self._queue.ensure_index(
        #     [("domain_name", pymongo.ASCENDING),
        #      ("ts_added", pymongo.ASCENDING)],
        #       name="idx_domain", unique=True)
        # self._queue.ensure_index("ts", unique=True, name="idx_ts")
        self._queue.ensure_index([("state", pymongo.ASCENDING),
                                  ("ts", pymongo.ASCENDING)],
                                 unique=True, name="idx_ts")
        self._queue.ensure_index("uri", unique=True, name="idx_uri")

        # Indices - recipe
        self._recipe.ensure_index([("domain", pymongo.ASCENDING),
                                   ("canonical_url", pymongo.ASCENDING)],
                                  unique=True, name="idx_domain")
        # self._recipe.ensure_index("recipe_id", unique=True, name="idx_recipe_id")
        self._recipe.ensure_index("canonical_url", unique=True, name="idx_uri")

        # Indices - action
        # uri-chrono order
        self._action.ensure_index(
            [("uri", pymongo.ASCENDING),
             ("ts", pymongo.ASCENDING),
             ("act", pymongo.ASCENDING)],
            unique=True, name="idx_uri_ts")
        # Global chrono order
        self._action.ensure_index(
            [("ts", pymongo.ASCENDING),
             ("uri", pymongo.ASCENDING),
             ("act", pymongo.ASCENDING)],
            unique=True, name="idx_ts")

    def _db_stats_report(self):
        return (f"Queue# {self._queue.count()}  "
                f"Recipe# {self._recipe.count()}  "
                f"Action# {self._action.count()}")

    def have_recipe(self, recipe_uri: Url):
        found = self._recipe.find({"canonical_url": str(recipe_uri)})
        if not found or found.count() == 0:
            return False
        if found.count() > 1:
            logger.warning("Found more than one recipe for %s", recipe_uri)
        return True

    def upsert_recipe(self, recipe):
        uri = recipe['canonical_url']
        # print("upsert_recipe: %s" % uri)
        if self.have_recipe(uri):
            logger.warning("Updating existing recipe: %s" % uri)
        result = self._recipe.replace_one(
            {"canonical_url": uri}, recipe, upsert=True)
        print("upsert_recipeed: %s" % uri)
        return result

    def is_enqueued(self, recipe_uri: Url, recipe_id: int = None) -> bool:
        return self._queue.find({"uri": str(recipe_uri)}).count() > 0

    def enqueue(self, recipe_uri: Url) -> bool:
        if self.is_enqueued(recipe_uri):
            return False
        now = dt.now()
        self._queue.insert_one(
            {"uri": str(recipe_uri), "ts": now, "state": "wait"})
        self._action.insert_one(
            {"uri": str(recipe_uri), "ts": now, "act": "enqueue"})

    def dequeue(self) -> Url:
        entry = None
        now = dt.now()
        tries_left = 10
        while entry is None:
            # entry = self._queue.find_one({
            #     "$query": {"state": "wait", "ts": {"$lt": now.timestamp() + 1}},
            #     "_addSpecial": {"$orderBy": {"ts": 1}}}
            # )
            mutex.acquire(blocking=True, timeout=3)
            entries = self._queue.find({"state": "wait"})
            entries.sort("ts")
            # {"state": "wait", "ts": {"$gt": now}})
            if entries is None or entries.count() == 0:
                if tries_left > 0:
                    now += td(seconds=1)
                    tries_left -= 1
                else:
                    break
            else:
                entry = entries[0]

        if entry:
            self._queue.update_one({"uri": entry["uri"]},
                                   {"$set": {"state": "scrape"}})
            mutex.release()
            self._action.insert_one({
                "uri": str(entry['uri']), "ts": now, "act": "scrape"})
            return parse_url(entry["uri"])
        else:
            mutex.release()
            queue_size = self._queue.find({"state": "wait"}).count()
            queue_status = self._queue.aggregate([
                {"$group": {"_id": "$state", "count": {"$sum": 1}}},
            ])
            # self._action.insert_one({
            #     "uri": str(entry['recipe_uri']), "ts": now,
            #     "act": "dequeue_miss(%d)" % queue_size})
            logger.debug("dequeue_miss with known %s entries" % json.dumps(
                list(queue_status)))
            if not queue_size:
                raise EmptyQueueException("Found zero entries in queue")
            return None

    def dequeue_finish(self, recipe_uri: Url):
        now = dt.now()
        count0 = self._queue.find({"uri": str(recipe_uri)}).count()
        res = self._queue.delete_one({"uri": str(recipe_uri)})
        count1 = self._queue.find({"uri": str(recipe_uri)}).count()
        # print("DEQUEUE RESULT 0: %s, count0: %s, count1: %s",
        #       str(res.raw_result), count0, count1)
        self._action.insert_one({"uri": str(recipe_uri), "ts": now, "act":
            "finish"})
        # print("DEQUEUE RESULT 1: ")

    # def _ensure_db_exists(self):
    #     mutex.acquire()
    #     dblist = self._mdb.list_database_names()
    #     try:
    #         if self.DATABASE_NAME not in dblist:
    #             self._mdb[self.DATABASE_NAME]
    #     finally:
    #         mutex.release()

    def _create_user(self, username):
        """
        https://stackoverflow.com/questions/20117104/mongodb-root-user

        import secrets
        secrets.token_urlsafe(64)

        https://cryptography.io/en/latest/random-numbers/

        :param username:
        :return:
        """
        # self._db.
