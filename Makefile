DOCKER_IMAGE_NAME=dataesr/matcher-affiliation
CURRENT_VERSION=$(shell cat matcher/__init__.py | cut -d "'" -f 2)

test: unit

unit:
	@echo Running unit tests...
	APP_ENV=test python3 -m pytest
	@echo End of unit tests

start:
	@echo Matcher starting...
	docker-compose up --build
	@echo Matcher started http://localhost:5004

stop:
	@echo Matcher stopping...
	docker-compose down
	@echo Matcher stopped

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo End of dependencies installation

docker-build:
	@echo Building a new docker image
	docker build -t ghcr.io/$(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t ghcr.io/$(DOCKER_IMAGE_NAME):latest .
	@echo Docker image built

docker-push:
	@echo Pushing a new docker image
	docker push ghcr.io/$(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)
	docker push ghcr.io/$(DOCKER_IMAGE_NAME):latest
	@echo Docker image pushed

python-build:
	@echo Building a python package
	python setup.py sdist
	@echo Python package built

load:
	@echo Load all data into ES
	curl http://localhost:5004/load
	@echo Matcher is now populated

release:
	echo "__version__ = '$(VERSION)'" > matcher/__init__.py
	git commit -am '[release] version $(VERSION)'
	git tag $(VERSION)
	@echo If everything is OK, you can push with tags i.e. git push origin master --tags
