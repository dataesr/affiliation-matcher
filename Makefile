test: unit

unit:
	@echo Running unit tests...
	APP_ENV=test python -m pytest
	@echo

notebook:
	jupyter notebook

start:
	@echo Starting app...
	docker-compose up -d
	@echo

stop:
	@echo Stopping app...
	docker-compose down
	@echo

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo