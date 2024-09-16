CURRENT_VERSION=$(shell cat project/__init__.py | cut -d "'" -f 2)
DOCKER_IMAGE_NAME=dataesr/affiliation-matcher
GHCR_IMAGE_NAME=ghcr.io/$(DOCKER_IMAGE_NAME)

test: unit

unit: start
	@echo Running unit tests...
	APP_ENV=test venv/bin/python -m pytest
	@echo End of unit tests

start: stop
	@echo Affiliation matcher starting...
	docker compose up -d
	@echo Affiliation matcher started http://localhost:5004

stop:
	@echo Affiliation matcher stopping...
	docker compose down
	@echo Affiliation matcher stopped

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo End of dependencies installation

client-build:
	@echo Building client files
	cd project/client && npm install && npm run build

docker-build:
	@echo Building a new docker image
	docker build -t $(GHCR_IMAGE_NAME):$(CURRENT_VERSION) -t $(GHCR_IMAGE_NAME):latest .
	@echo Docker image built

docker-push:
	@echo Pushing a new docker image
	docker push -a $(GHCR_IMAGE_NAME)
	@echo Docker image pushed

python-build:
	@echo Building a python package
	venv/bin/python setup.py sdist
	@echo Python package built

load:
	@echo Load all data into ES
	curl http://localhost:5004/load
	@echo Affiliation matcher is now populated

release:
	echo "__version__ = '$(VERSION)'" > project/__init__.py
	cd project/client && npm version
	make client-build
	git commit -am '[release] version $(VERSION)'
	git tag $(VERSION)
	@echo If everything is OK, you can push with tags i.e. git push origin master --tags
