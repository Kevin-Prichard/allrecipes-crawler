#!/bin/bash

cd $CRAWLER_DIR
pwd
ls -l $CRAWLER_DIR/
python3 $CRAWLER_DIR/do_thing.py /opt/app-root/src/allrecipes-crawler/docker-compose.yaml-23-skidoo ABC
