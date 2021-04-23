test: unit

unit:
	@echo Running unit tests...
	APP_ENV=test python -m pytest
	@echo End of unit tests

notebook:
	jupyter notebook

start:
	@echo Matcher starting...
	docker-compose up -d
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
	docker build -t dataesr/matcher:$(VERSION) -t dataesr/matcher:latest .
	@echo Docker image built

docker-push:
	@echo Pushing a new docker image
	docker push dataesr/matcher:$(VERSION)
	docker push dataesr/matcher:latest
	@echo Docker image pushed

python-build:
	@echo Building a python package
	python setup.py sdist
	@echo Python package built

init:
	@echo Populate data into matcher
	curl http://localhost:5004/init
	@echo Matcher is now populated