.PHONY: docker-build
docker-build:
	@docker-compose -f docker/docker-compose.yml build

.PHONY: docker-run
docker-run:
	@docker run --rm twitch_scraper