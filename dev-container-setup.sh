#!/bin/bash

cd $CRAWLER_DIR
pwd
ls -l $CRAWLER_DIR/requirements.txt
pip3 install -r $CRAWLER_DIR/requirements.txt

cd $SCRAPER_DIR
pwd
ls -l $SCRAPER_DIR/requirements-dev.txt
pip3 install -r $SCRAPER_DIR/requirements-dev.txt
