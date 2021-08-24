#!/usr/bin/env python3

import os, sys  # , json, time
from crawl_coordinator import CrawlCoordinator
from datastore import RecipeStore

sys.path.append(os.path.join(os.getcwd(), "build/lib/recipe_scrapers"))

from recipe_scrapers import scrape_me
from recipe_scrapers import AllRecipes
from requests.packages.urllib3.util import Url


def main():
    # cProfile.run('CrawlCoordinator([AllRecipes]).start()')
    coordinator = CrawlCoordinator(
        [AllRecipes], lambda uri: True, lambda uri: True)
    coordinator.start_crawl()

    # a = scrape_me("https://www.allrecipes.com/recipe/12345/jeff-davis-pie-i/",
    #               proxies={"http": "http://127.0.0.1:3128",
    #                        "https": "http://127.0.0.1:3128"})
    # import pudb; pu.db
    """
    rs = RecipeStore.instance
    # import pudb; pu.db
    u1 = "https://www.allrecipes.com/recipe/12345/jeff-davis-pie-i/"
    u2 = "https://www.allrecipes.com/recipe/12346/jeff-davis-pie-i/"
    rs.enqueue(u1)
    rs.enqueue(u2)
    d2 = rs.dequeue()
    d1 = rs.dequeue()
    """

    """
    uris = [
        "https://www.allrecipes.com/recipe/6786/crazay-bagels/",
        "https://www.allrecipes.com/recipe/6902/indian-naan-i/",
        "https://www.allrecipes.com/recipe/6908/butterscotch-buns/",
        "https://www.allrecipes.com/recipe/6909/jam-filled-buns/",
        "https://www.allrecipes.com/recipe/6910/kolaches-i/",
        "https://www.allrecipes.com/recipe/6911/sour-cream-and-onion-bread/",
        "https://www.allrecipes.com/recipe/6912/orange-loaf/",
        "https://www.allrecipes.com/recipe/6913/cranberry-orange-loaf/",
        "https://www.allrecipes.com/recipe/6914/cranberry-loaf/",
        "https://www.allrecipes.com/recipe/6915/zucchini-bread-iv/",
        "https://www.allrecipes.com/recipe/6916/croissants/",
        "https://www.allrecipes.com/recipe/6917/portuguese-cornbread/",
        "https://www.allrecipes.com/recipe/6918/portuguese-fried-bread/",
        "https://www.allrecipes.com/recipe/6919/bannock/",
        "https://www.allrecipes.com/recipe/6920/orange-cinnamon-sticks/",
        "https://www.allrecipes.com/recipe/6921/quick-banana-bread/",
        "https://www.allrecipes.com/recipe/6922/fake-sourdough-biscuits/",
        "https://www.allrecipes.com/recipe/6923/monkey-bread-iii/",
        "https://www.allrecipes.com/recipe/6924/monkey-bread-iv/",
        "https://www.allrecipes.com/recipe/6925/monkey-bread-v/",
        "https://www.allrecipes.com/recipe/6926/bruces-honey-sesame-bread/",
        "https://www.allrecipes.com/recipe/6927/beaten-biscuits/",
        "https://www.allrecipes.com/recipe/6928/bagels-ii/",
        "https://www.allrecipes.com/recipe/6929/flower-pot-challah-bread/",
        "https://www.allrecipes.com/recipe/6930/date-orange-bread/",
        "https://www.allrecipes.com/recipe/6931/luxury-loaf/",
        "https://www.allrecipes.com/recipe/6932/orange-pumpkin-loaf/",
        "https://www.allrecipes.com/recipe/6933/pumpkin-tea-bread/",
        "https://www.allrecipes.com/recipe/6934/cinnamon-bread-i/",
        "https://www.allrecipes.com/recipe/6935/cherry-spice-loaf/",
        "https://www.allrecipes.com/recipe/6936/raisin-bread-i/",
        "https://www.allrecipes.com/recipe/6937/pineapple-bread/",
        "https://www.allrecipes.com/recipe/6938/fruit-and-nut-loaf/",
        "https://www.allrecipes.com/recipe/6939/fruit-bread-i/",
        "https://www.allrecipes.com/recipe/6940/fruit-bread-ii/",
        "https://www.allrecipes.com/recipe/6941/zucchini-coconut-loaf/",
        "https://www.allrecipes.com/recipe/6942/favorite-nut-bread/",
        "https://www.allrecipes.com/recipe/6943/cottage-cheese-loaf/",
        "https://www.allrecipes.com/recipe/6944/pumpkin-loaf/",
        "https://www.allrecipes.com/recipe/6945/fancy-crescents/",
        "https://www.allrecipes.com/recipe/6946/blueberry-scones/",
        "https://www.allrecipes.com/recipe/6947/english-muffins/",
        "https://www.allrecipes.com/recipe/6948/cinnamon-sour-cream-biscuits/",
        "https://www.allrecipes.com/recipe/6949/fruit-loaf/",
        "https://www.allrecipes.com/recipe/6950/sophies-zucchini-bread/",
        "https://www.allrecipes.com/recipe/6951/abbys-super-zucchini-loaf/",
        "https://www.allrecipes.com/recipe/6952/butter-tart-muffins/",
        "https://www.allrecipes.com/recipe/6953/hot-water-cornbread/",
        "https://www.allrecipes.com/recipe/6954/maple-twists/",
        "https://www.allrecipes.com/recipe/6955/mama-ds-italian-bread/",
        "https://www.allrecipes.com/recipe/6956/pepperoni-filled-bread/",
        "https://www.allrecipes.com/recipe/6957/banana-chip-muffins-i/",
        "https://www.allrecipes.com/recipe/6958/cinnamon-buns/",
        "https://www.allrecipes.com/recipe/6959/mustard-wheat-rye-sandwich-bread/",
        "https://www.allrecipes.com/recipe/6960/dr-michaels-yeasted-cornbread/",
        "https://www.allrecipes.com/recipe/6961/the-best-pizza-crust/",
        "https://www.allrecipes.com/recipe/6962/seven-grain-bread-i/",
        "https://www.allrecipes.com/recipe/6963/good-100-whole-wheat-bread/",
        "https://www.allrecipes.com/recipe/6964/persimmon-bread-ii/",
        "https://www.allrecipes.com/recipe/6965/peanut-butter-sandwich-loaf/",
        "https://www.allrecipes.com/recipe/6966/soft-pretzels-ii/",
        "https://www.allrecipes.com/recipe/6967/mincemeat-quick-bread/",
        "https://www.allrecipes.com/recipe/6968/poppy-seed-rolls/",
        "https://www.allrecipes.com/recipe/6969/peach-bread/",
        "https://www.allrecipes.com/recipe/6970/butterfly-buns/",
        "https://www.allrecipes.com/recipe/6971/honey-of-an-oatmeal-bread/",
        "https://www.allrecipes.com/recipe/6972/buttermilk-bread-ii/",
        "https://www.allrecipes.com/recipe/6973/poppy-seed-loaf/",
        "https://www.allrecipes.com/recipe/6974/irish-bannock/",
        "https://www.allrecipes.com/recipe/6975/swedish-limpu-bread/",
        "https://www.allrecipes.com/recipe/6976/hot-water-cornmeal-bread/",
        "https://www.allrecipes.com/recipe/6977/cracklin-bread-i/",
    ]
    for recipe_uri in uris:
        r = scrape_me(recipe_uri)
        x = r.to_dict(unitized=True, uri=str(recipe_uri))
        print(r)
    """

    """
    rs = RecipeStore.instance
    # import pudb; pu.db
    u1 = "https://www.allrecipes.com/recipe/12345/jeff-davis-pie-i/"
    u2 = "https://www.allrecipes.com/recipe/12346/jeff-davis-pie-i/"
    rs.enqueue(u1)
    rs.enqueue(u2)
    d2 = rs.dequeue()
    d1 = rs.dequeue()
    """

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
