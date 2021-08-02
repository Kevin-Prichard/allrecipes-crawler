#!/usr/bin/env python3

import os, sys  # , json, time
from crawl_coordinator import CrawlCoordinator

sys.path.append(os.path.join(os.getcwd(), "build/lib/recipe_scrapers"))

# from recipe_scrapers import scrape_me
from recipe_scrapers import AllRecipes


def main():
    # cProfile.run('CrawlCoordinator([AllRecipes]).start()')
    coordinator = CrawlCoordinator([AllRecipes])
    coordinator.start()


if __name__ == "__main__":
    main()


"""
via: https://hub.docker.com/_/mongo/

docker pull mongo

EXTERNAL_MONGO_DATA_DIR=/Users/kev/projs/allrecipes-mongo
INTERNAL_MONGO_DATA_DIR=/data/db

$ docker run --name kevs-mongo -v \
  $EXTERNAL_MONGO_DATA_DIR:$INTERNAL_MONGO_DATA_DIR -d mongo
8ea6723c2a2640ccbba6134a12f38f7746156ef1cab4474767651ee26ec5dfc1

$ docker exec -it 8ea6723c2a26 bash  # get shell in that container
$ ls -l $INTERNAL_MONGO_DATA_DIR
abc
$ ls -l $$EXTERNAL_MONGO_DATA_DIR
abc

abc == abc
"""
