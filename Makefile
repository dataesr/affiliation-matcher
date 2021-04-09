test: unit

unit:
	@echo Running unit tests...
	APP_ENV=test python -m pytest
	@echo

notebook:
	jupyter notebook