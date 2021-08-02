import multiprocessing.dummy as mp
import re
import requests
import sys
from typing import List
from threading import Thread, Lock

mutex = Lock()

from datastore import RecipeStore

# from recipe_scrapers import scrape_me
from recipe_scrapers._abstract import AbstractScraper


# https://www.madelyneriksen.com/blog/simple-concurrency-python-multiprocessing

class CrawlCoordinator:
    DISCOVERY_CLIENT_THREADS = 4
    DISCOVERY_SINK_THREADS = 1

    def __init__(self, scraper_classes: List[type(AbstractScraper)]):
        self.scraper_classes = scraper_classes
        self.store = RecipeStore()

    def start(self):
        # import pudb; pu.db
        url_gen = self._start_discovery() <- isn\'t a generator
        try:
            while True:
                print("start...")
                url = next(url_gen)  <- NoneType is not an iterator
                print("CrawlCoordinator.start: " + url)
        except StopIteration:
            import pudb; pu.db
            print("Finished URL discovery")
            return

    def _start_discovery(self):
        # site_explorers = [RecipeSiteUrlIterator(klass)
        #                   for klass in self.scraper_classes]
        # sites_completed = 0
        urls_counted = 0

        with mp.Pool(4*len(self.scraper_classes)) as dpool:
            RECIPE_ID_REGEX = re.compile(r".*[^/]+/(\d+)$")
            found_ids = []
            site_iterator = dpool.imap_unordered(
                CrawlCoordinator.discovery_runner,
                self.scraper_classes)

            try:
                while True:
                    # print("_start_discovery ...1")
                    item = next(site_iterator)
                    while True:
                        # print("_start_discovery ...2")
                        an_item = next(item)
                        recipe_id = RECIPE_ID_REGEX.match(an_item).groups()[0]
                        mutex.acquire()
                        try:
                            found_ids.append(int(recipe_id))
                            urls_counted += 1
                            # print("_start_discovery ...3 " +
                            #       str(an_item) + "    " + str(urls_counted))
                            if urls_counted / 100 == int(urls_counted / 100):
                                sys.stderr.write(
                                    "urls_counted: " + str(urls_counted) + "\n")
                        finally:
                            mutex.release()
            except StopIteration as ee:
                print("_start_discovery: StopIteration")
                    # print("_start_discovery 4 "+str(item))
                    # except StopIteration:

                found_ids = sorted(found_ids)
                for i in range(0, 9999):
                    if found_ids[i] != i + 1:
                        import pudb; pu.db
                return


    @classmethod
    def discovery_runner(cls, scraper_class):
        # import pudb; pu.db
        # print("discovery_runner startup")
        site_iter = scraper_class.site_iterator(None, 1, 10000)
        # print("discovery_runner site_iter: "+str(site_iter))
        try:
            while True:
                # print("d-r...")
                recipe_url = next(site_iter)
                # print("d-r: ... recipe_url = " + str(recipe_url))
                yield recipe_url
        except StopIteration:
            print("discovery_runner StopIteration")
            return
