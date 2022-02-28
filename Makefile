.PHONY: docker-build
docker-build:
	@docker-compose -f docker/docker-compose.yml build

.PHONY: docker-run
docker-run:
	@docker run --rm twitch_scraper

.PHONY: docker-build-local
docker-build-local:
	@docker-compose -f local/docker-compose.yml build

.PHONY: docker-run-local
docker-run-local:
	@docker-compose -f local/docker-compose.yml up -d

.PHONY: docker-down-local
docker-down-local:
	@docker-compose -f local/docker-compose.yml down

.PHONY: bump-patch
bump-patch:
	@bump2version patch
	@git push --tags
	@git push

.PHONY: bump-minor
bump-minor:
	@bump2version minor
	@git push --tags
	@git push

.PHONY: bump-major
bump-major:
	@bump2version major
	@git push --tags
	@git push