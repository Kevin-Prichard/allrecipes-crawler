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
