import logging
import multiprocessing.dummy as mp
import random
import re
import threading

from pymongo import MongoClient
from requests.packages.urllib3.util import Url
import sys
import time
from typing import List, Callable
from threading import Thread, Lock
from simple_classproperty import classproperty

mutex = Lock()

from datastore import RecipeStore, EmptyQueueException
import json
from recipe_scrapers import scrape_me
from recipe_scrapers._abstract import AbstractScraper
import requests_cache
from requests_cache.backends.sqlite import DbCache
# from requests_cache.backends.mongo import MongoCache

# https://www.madelyneriksen.com/blog/simple-concurrency-python-multiprocessing

THREADS_DISCOVERY_HTTP_CLIENT = 4
THREADS_FETCH_HTTP_DOC = 4

logging.basicConfig()
logger = logging.getLogger(__name__)


class CrawlCoordinator:

    def __init__(self,
                 scraper_classes: List[type(AbstractScraper)],
                 should_process_recipe: Callable[[Url], None],
                 process_recipe: Callable[[Url], bool],
                 ):
        self._should_process_recipe = should_process_recipe
        self.scraper_classes = scraper_classes
        self.store = RecipeStore.instance
        # https://requests-cache.readthedocs.io/
        # mongo_conn = MongoClient()
        # mongo_http_cache = MongoCache(db_name='http_cache', connection=mongo_conn)

        sqlite_cache = DbCache(db_path='./requests_cache.sqlite')
        requests_cache.install_cache(
            cache_name='http_cache',
            backend=sqlite_cache,
            expire_after=-1,
            allowable_codes=(200, 301)
        )

        # requests_cache.install_cache('demo_cache')

        # self.requests_session = requests_cache.CachedSession(
        #     backend=sqlite_cache, expire_after=-1)

    def start(self):
        thread_scrape = Thread(target=self._run_scrape)
        thread_scrape.start()

        thread_discovery = Thread(target=self._run_discovery)
        thread_discovery.start()
        # thread_discovery.setDaemon(True)


        thread_discovery.join()
        thread_scrape.join()

    def _run_scrape(self):

        with mp.Pool(THREADS_FETCH_HTTP_DOC) as scrape_pool:
            scrape_iterator = scrape_pool.imap_unordered(
                self._scrape, self._scrape_target_generator()
            )
            try:
                while True:
                    result = next(scrape_iterator)
                    # print(result)
            except StopIteration:
                print("_run_scrape: done scraping")

    def _scrape(self, recipe_uri: Url):
        # print("Recipe scrape: %s" % str(recipe_uri))
        if self.store.have_recipe(recipe_uri):
            logger.warning("Skipping2 %s" % str(recipe_uri))
            return
        recipe = scrape_me(str(recipe_uri))
        d = recipe.to_dict(unitized=True, uri=str(recipe_uri))
        if d['canonical_url'] != str(recipe_uri):
            raise ValueError(
                "Found unmatching uri, d['canonical_url'] != str(recipe_uri) "
                f"-> %s '{d['canonical_url']}' != '{str(recipe_uri)}'")
        d['domain'] = recipe_uri.hostname
        # print("Recipe scraped: %s (%d)" % (recipe_uri, len(json.dumps(d))))
        result = self.store.upsert_recipe(d)
        self.store.dequeue_finish(recipe_uri)
        # print("Recipe upsert result: %s" % str(result.raw_result))

    def _scrape_target_generator(self):
        while True:
            try:
                recipe_uri = self.store.dequeue()
                if recipe_uri:
                    yield recipe_uri
                else:
                    time.sleep(0.1)
            except EmptyQueueException:
                time.sleep(0.1)

    def _run_discovery(self):
        # site_explorers = [RecipeSiteUrlIterator(klass)
        #                   for klass in self.scraper_classes]
        # sites_completed = 0
        urls_counted = 0

        with mp.Pool(
                THREADS_FETCH_HTTP_DOC * len(self.scraper_classes)) as dpool:
            RECIPE_ID_REGEX = re.compile(r".*/recipe/(\d+)/[a-z0-9_\-.]+/?$",
                                         re.I)
            found_ids = []
            site_iterator = dpool.imap_unordered(
                self.discovery_runner,
                self.scraper_classes)

            try:
                while True:
                    print("_start_discovery ...1")
                    permalink_block = next(site_iterator)
                    print("_start_discovery ...1 ", str(permalink_block))
                    while True:
                        # print("_start_discovery ...2")
                        recipe_permalink = next(permalink_block)
                        if not recipe_permalink:
                            print("_run_discovery: recipe_permalink is None, "
                                  "continueing")
                            continue
                        # print("_run_discovery: recipe_permalink type: %s" %
                        #       str(type(recipe_permalink)))
                        # mutex.acquire()
                        try:
                            recipe_id = RECIPE_ID_REGEX.match(
                                str(recipe_permalink)).groups()[0]
                            self.store.enqueue(recipe_permalink)
                            # recipe = scrape_me(str(recipe_permalink))
                            # recipe_dumpus = json.dumps(recipe.to_dict())
                            # print(f"Fetched JSON: {recipe_permalink}")
                            found_ids.append(int(recipe_id))
                            urls_counted += 1
                            # print("_start_discovery ...3 " +
                            #       str(an_item) + "    " + str(urls_counted))
                            if urls_counted / 10 == int(urls_counted / 10):
                                # sys.stderr.write(
                                fmt = ("Status: urls_counted: "
                                       "%s -- %s -- th:%s -- %s")
                                stat = self.store._queue.aggregate([
                                    {"$group": {"_id": "$state",
                                                "count": {"$sum": 1}}}])
                                print(fmt % (
                                    str(urls_counted),
                                    str(sorted(list(stat),
                                               key=lambda a: a['_id'])),
                                    str(threading.active_count()),
                                    recipe_permalink,
                                ))
                        except Exception as eeee:
                            print("Exceptioni encountered: %s" %
                                  str(recipe_permalink), eeee)
                        # finally:
                            # mutex.release()
            except StopIteration as ee:
                print("_start_discovery: StopIteration")
                    # print("_start_discovery 4 "+str(item))
                    # except StopIteration:

                # found_ids = sorted(found_ids)
                # for i in range(0, 9999):
                #     if found_ids[i] != i + 1:
                #         import pudb; pu.db
                return

    def discovery_runner(self, scraper_class):
        # def choose(recipe_id: int, uri: str):
        #     return False

        yield from scraper_class.site_urls(
            # self.requests_session,
            should_exclude_recipe=lambda uri: self.store.is_enqueued(uri) or
                                              self.store.have_recipe(uri),
            recipe_check_threads=THREADS_DISCOVERY_HTTP_CLIENT,
        )

        # print("discovery_runner startup")
        # site_iter = scraper_class.site_iterator(None, 1, 10000)
        # print("discovery_runner site_iter: "+str(site_iter))
        """
        try:
            while True:
                # print("d-r...")
                recipe_url = next(site_iter)
                # print("d-r: ... recipe_url = " + str(recipe_url))
                yield recipe_url
        except StopIteration:
            print("discovery_runner StopIteration")
            return
        """
