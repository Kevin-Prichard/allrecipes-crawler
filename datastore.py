import os
from threading import Thread, Lock

from pymongo import MongoClient

mutex = Lock()


class RecipeStore:
    _instance = None

    def __init__(self):
        # print("\n".join(str(kv) for kv in os.environ.items()))
        self.user = os.environ.get("MONGO_APP_USERNAME")
        self.passwd = os.environ.get("MONGO_APP_PASSWORD")
        self.host = os.environ.get("mongo")
        self.conn_uri = f"mongo+srv://{self.user}:{self.passwd}@"
        self.mdb = MongoClient()

    @classmethod
    def instance(cls):
        mutex.acquire()
        try:
            if cls._instance is None:
                cls._instance = RecipeStore()
        finally:
            mutex.release()
