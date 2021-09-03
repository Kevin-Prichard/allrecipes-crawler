#!/usr/bin/env python3

from crawl_coordinator import CrawlCoordinator

from recipe_scrapers import AllRecipes


def main():
    # cProfile.run('CrawlCoordinator([AllRecipes]).start()')
    coordinator = CrawlCoordinator(
        [AllRecipes], lambda uri: True, lambda uri: True
    )
    coordinator.start_crawl()


if __name__ == "__main__":
    main()
