FROM python:3.8 AS base

ENV DOCKER_BUILDKIT 0
ENV COMPOSE_DOCKER_CLI_BUILD 0

ENV PARENT_DIR /opt/app-root/src
ENV CRAWLER_DIR $PARENT_DIR/recipe-crawler
ENV SCRAPER_DIR $PARENT_DIR/recipe-scrapers

ENV CRAWLER_GIT_REPO https://github.com/Kevin-Prichard/recipes-crawler
ENV CRAWLER_GIT_BRANCH master
ENV SCRAPER_GIT_REPO https://github.com/Kevin-Prichard/recipe-scrapers
ENV SCRAPER_GIT_BRANCH develop_add-allrecipes-extended_nutritients

RUN mkdir -p $PARENT_DIR

FROM base as dev
ENTRYPOINT $CRAWLER_DIR/dev-container-setup.sh
#ENTRYPOINT $CRAWLER_DIR/crawler_start.sh
#VOLUME [ "/opt/app-root/src/recipe-crawler", "/opt/app-root/src/recipe-scrapers" ]


#FROM base as prod
#
#WORKDIR $PARENT_DIR
#RUN git clone -b $CRAWLER_GIT_BRANCH $CRAWLER_GIT_REPO
##WORKDIR $CRAWLER_DIR
#WORKDIR recipe-crawler
#RUN pwd 1>&2
#RUN ls -l $PARENT_DIR >> /tmp/allcrawl_src.log
#RUN ls -l $CRAWLER_DIR >> /tmp/allcrawl_app.log
##RUN pip3 install -r $CRAWLER_DIR/requirements.txt
#
#RUN git clone -b $SCRAPER_GIT_BRANCH $SCRAPER_GIT_REPO
#WORKDIR $SCRAPER_DIR
#RUN pwd
#RUN ls -l $PARENT_DIR >> /tmp/allcrawl_src.log
#RUN ls -l $SCRAPER_DIR >> /tmp/scraper_app.log
##RUN pip3 install -r $SCRAPER_DIR/requirements-dev.txt
##RUN python3 setup.py install
