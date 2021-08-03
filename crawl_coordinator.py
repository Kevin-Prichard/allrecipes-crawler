import multiprocessing.dummy as mp
import random
import re
import requests
import sys
from typing import List
from threading import Thread, Lock

mutex = Lock()

from datastore import RecipeStore
import json
from recipe_scrapers import scrape_me
from recipe_scrapers._abstract import AbstractScraper


# https://www.madelyneriksen.com/blog/simple-concurrency-python-multiprocessing

class CrawlCoordinator:
    DISCOVERY_CLIENT_THREADS = 4
    DISCOVERY_SINK_THREADS = 1

    def __init__(self, scraper_classes: List[type(AbstractScraper)]):
        self.scraper_classes = scraper_classes
        self.store = RecipeStore()

    def start(self):
        self._start_discovery()

    def _start_discovery(self):
        # site_explorers = [RecipeSiteUrlIterator(klass)
        #                   for klass in self.scraper_classes]
        # sites_completed = 0
        urls_counted = 0

        with mp.Pool(4*len(self.scraper_classes)) as dpool:
            RECIPE_ID_REGEX = re.compile(r".*/recipe/(\d+)/[a-z0-9_\-.]+/?$",
                                         re.I)
            found_ids = []
            site_iterator = dpool.imap_unordered(
                CrawlCoordinator.discovery_runner,
                self.scraper_classes)

            try:
                while True:
                    print("_start_discovery ...1")
                    item = next(site_iterator)
                    print("_start_discovery ...1 ", str(item))
                    while True:
                        # print("_start_discovery ...2")
                        a_recipe_uri = next(item)
                        if not a_recipe_uri:
                            continue
                        recipe_id = RECIPE_ID_REGEX.match(a_recipe_uri).groups()[0]
                        mutex.acquire()
                        try:
                            recipe = scrape_me(a_recipe_uri)
                            # r = requests.get(a_recipe_uri)
                            # if r.ok:
                            #     print(f"{a_recipe_uri} - {len(r.text)}")
                            recipe_dumpus = json.dumps(recipe.to_dict())
                            print(f"{a_recipe_uri} - {recipe_dumpus}\n\n")
                            found_ids.append(int(recipe_id))
                            urls_counted += 1
                            # print("_start_discovery ...3 " +
                            #       str(an_item) + "    " + str(urls_counted))
                            if urls_counted / 100 == int(urls_counted / 100):
                                # sys.stderr.write(
                                print("urls_counted: " + str(urls_counted))
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
        def choose(x):
            return True
            # yes = random.random() > 0.6666
            # return yes

        yield from scraper_class.site_iterator(choose, 1, 10000)

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
