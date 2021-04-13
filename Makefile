test: unit

unit:
	@echo Running unit tests...
	APP_ENV=test python -m pytest
	@echo End of unit tests

notebook:
	jupyter notebook

start:
	@echo Starting app...
	docker-compose up -d
	@echo App started

stop:
	@echo Stopping app...
	docker-compose down
	@echo App stopped

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo End of dependencies installation

docker-build:
	@echo Building a new docker image
	docker build -t dataesr/matcher .
	@echo Docker image built

python-build:
	@echo Building a python package
	python setup.py sdist
	@echo Python package built

init:
	@echo Populate data into app
	curl http://localhost:5004/init
	@echo App is now populated