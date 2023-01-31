.DEFAULT_GOAL := help
.PHONY: help build
help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[%a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

docker_file=./docker-compose.yml

OS := $(shell uname)

init:
    build run ## build docker, containers and install all dependencies (composer install).

build: # Build all containers
	docker-compose -f ${docker_file} rm -vsf
	docker-compose -f ${docker_file} down -v --remove-orphans
	docker-compose -f ${docker_file} build

run: ## Start all containers (in background)
	docker-compose -f ${docker_file} up -d

stop: ## Stop all started for development containers .
	docker-compose -f ${docker_file} stop

clear: ## Clear all containers and all data
	docker volume prune --force
	docker system prune -a --force
	docker system prune --force
	docker rmi $(docker images -a -q) --force
	docker images purge


