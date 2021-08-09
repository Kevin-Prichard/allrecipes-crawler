#!/usr/bin/env python3

from collections import defaultdict as dd
import logging
import os, psutil, sys
import pymongo
from pymongo import MongoClient
import re
import time


logging.basicConfig()
progressLogger = logging.getLogger(__name__)
progressLogger.addHandler(logging.StreamHandler(sys.stderr))


WORD_SPLIT_REGEX = re.compile(r"[^a-z0-9_\-']+", re.I)


class PullSomeStats:

    REPORT_FREQ = 100
    DATABASE_NAME = 'RecipeDB'
    COLL_NAME_QUEUE = 'queue'
    COLL_NAME_RECIPE = 'recipe'
    COLL_NAME_HISTORY = 'action'

    @classmethod
    def _get_mem_usage(cls):
        return psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2

    def __init__(self):
        self._mdb = MongoClient()
        self._db = self._mdb[self.DATABASE_NAME]

        # Collections
        self._queue = self._db[self.COLL_NAME_QUEUE]
        self._recipe = self._db[self.COLL_NAME_RECIPE]
        self._action = self._db[self.COLL_NAME_HISTORY]
        # self.recipe = self._mdb.RecipeDB.recipes
        self.start_mem = self._get_mem_usage()
        self.time_start = time.time()

    def titles_gen(self):
        x = self._recipe.find({
            "title": {
                "$not": {
                    "$regex": r"/johnsonville/i"
                }
            }
        },
        {"title": 1, "_id": 0})
        # x = self._recipe.find({}, {"title": 1, "_id": 0})
        # import pudb; pu.db
        return x

    def title_pop_words(self):
        wordset = dd(int)
        titles_counted = 0
        words_counted = 0
        recipe_title_iter = self.titles_gen()

        for _title in recipe_title_iter:
            title = _title.get('title', None)
            if not title:
                continue
            words = WORD_SPLIT_REGEX.split(title)
            if not words:
                progressLogger.error("Got empty word splits on: %s", title)
                continue
            for word in words:
                wordset[word.lower()] += 1
                words_counted += 1
            titles_counted += 1
            if (titles_counted / self.REPORT_FREQ ==
                    int(titles_counted / self.REPORT_FREQ)):
                wordset_count = len(wordset.keys())
                secs = time.time() - self.time_start
                progressLogger.info(
                    "Titles %d %d/sec   Words %d %d/sec   Uniques %d %d/sec",
                    titles_counted, titles_counted/secs,
                    words_counted, words_counted/secs,
                    wordset_count, wordset_count/secs,
                )
                time.sleep(0)
        self.wordset = wordset

    def word_stats_report(self):
        for word in self.wordset:
            print(f"{self.wordset[word]}\t{word}")


if __name__ == "__main__":
    stats = PullSomeStats()
    stats.title_pop_words()
    stats.word_stats_report()
