import datetime
import json
import logging
import multiprocessing.dummy as mp
import re
import threading

from requests.packages.urllib3.util import Url
import sys
import time
from typing import List, Callable
from threading import Thread, Lock

from datastore import RecipeStore, EmptyQueueException
from recipe_scrapers import scrape_me
from recipe_scrapers._abstract import AbstractScraper
import requests_cache
from requests_cache.backends.sqlite import DbCache

mutex = Lock()


THREADS_DISCOVERY_HTTP_CLIENT = 1
THREADS_FETCH_HTTP_DOC = 1

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
)
rootLogger = logging.getLogger()

logPath = "./logs"
fileName = datetime.datetime.now().strftime("crawler_%Y%m%d-%H%M%S")
fileHandler = logging.FileHandler(f"{logPath}/{fileName}.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
logger = rootLogger

sys.setrecursionlimit(250)

SPAM_RECIPE_TITLES = [
    # As of 2021-8-8 there are over 36,410 spammy-looking recipes on
    # this site, all having commercial food brandname "Johnsonville" in the
    # title.
    re.compile(r".*johnsonville.*", re.I),
]


class CrawlCoordinator:
    def __init__(
        self,
        scraper_classes: List[type(AbstractScraper)],
        should_process_recipe: Callable[[Url], bool],
        process_recipe: Callable[[Url], bool],
    ):
        self._should_process_recipe = should_process_recipe
        self.scrapers = scraper_classes
        self.store = RecipeStore.instance
        logger.info("Database start: %s", self.store._db_stats_report())
        self.store.setLogger(logger)

        # https://requests-cache.readthedocs.io/
        sqlite_cache = DbCache(db_path="./requests_cache.sqlite")
        requests_cache.install_cache(
            cache_name="http_cache",
            backend=sqlite_cache,
            expire_after=-1,  # never expire
            allowable_codes=(200, 301, 404),  # cache responses for these codes
        )

    def start_crawl(self):
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
                self._scrape_one, self._scrape_target_generator()
            )
            try:
                while True:
                    next(scrape_iterator)
            except StopIteration:
                print("_run_scrape: done scraping")

    def _scrape_one(self, recipe_uri: Url):
        if self.store.have_recipe(recipe_uri):
            logger.warning("Skipping2 %s", str(recipe_uri))
            return
        tries_left = 10
        recipe = None
        while tries_left > 0:
            try:
                recipe = scrape_me(str(recipe_uri))
                if recipe and recipe.title():
                    title = recipe.title()
                    for pat in SPAM_RECIPE_TITLES:
                        if pat.match(title):
                            recipe = None
                            break
                break
            except BaseException as efef:
                logger.error("Error in scrape_me: %s", efef)
                tries_left -= 1
                time.sleep(3)

        if recipe is not None:
            d = recipe.to_dict(unitized=True, uri=str(recipe_uri))
            if d["canonical_url"] != str(recipe_uri):
                logger.error(
                    "Found unmatching uri, d['canonical_url'] != recipe_uri "
                    f"-> %s '{d['canonical_url']}' != '{str(recipe_uri)}'"
                )
            d["domain"] = recipe_uri.hostname
            logger.debug(
                "Recipe scraped: %s (%d)", recipe_uri, len(json.dumps(d))
            )
            result = self.store.upsert_recipe(d)
            self.store.dequeue_finish(recipe_uri)
            logger.debug("Recipe upsert result: %s", str(result.raw_result))

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
        urls_counted = 0
        logging_fmt = "Status: urls_counted: " "%s -- %s -- th:%s -- %s"

        with mp.Pool(THREADS_FETCH_HTTP_DOC * len(self.scrapers)) as dpool:
            site_iterator = dpool.imap_unordered(
                self.discovery_runner, self.scrapers
            )

            try:
                while True:
                    logger.debug("_start_discovery 1")
                    permalink_block = next(site_iterator)
                    logger.debug("_start_discovery 1 ", str(permalink_block))
                    while True:
                        recipe_uri = next(permalink_block)
                        if not recipe_uri:
                            logger.debug(
                                "_run_discovery: recipe_uri is "
                                "None, continueing"
                            )
                            continue
                        logger.debug(
                            "_run_discovery: recipe_uri type: %s",
                            str(type(recipe_uri)),
                        )
                        try:
                            self.store.enqueue(recipe_uri)
                            urls_counted += 1
                            if urls_counted / 10 == int(urls_counted / 10):
                                stat = list(
                                    self.store._queue.aggregate(
                                        [
                                            {
                                                "$group": {
                                                    "_id": "$state",
                                                    "count": {"$sum": 1},
                                                }
                                            }
                                        ]
                                    )
                                )
                                logger.debug(
                                    logging_fmt,
                                    str(urls_counted),
                                    str(sorted(stat, key=lambda a: a["_id"])),
                                    str(threading.active_count()),
                                    recipe_uri,
                                )
                        except Exception as eeee:
                            logger.exception(
                                "Exc _run_discovery: %s", str(recipe_uri), eeee
                            )
            except StopIteration:
                logger.debug("_start_discovery: StopIteration")

                logger.debug("dpool.close() 0")
                dpool.close()
                logger.debug("dpool.close() 1")
                logger.debug("dpool.join() 0")
                dpool.join()
                logger.debug("dpool.join() 1")

    def discovery_runner(self, scraper_class):
        yield from scraper_class.sitemap_iter(
            recipe_check_fn=lambda uri, rid: self.store.is_enqueued(uri)
            or self.store.have_recipe(uri),
            threadcount=THREADS_DISCOVERY_HTTP_CLIENT,
        )
