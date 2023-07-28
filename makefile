# Makefile for AWS EBS Volumes Analysis Tool

# Variables
PYTHON = python3
VENV_NAME = venv
REQUIREMENTS_DEV = requirements-dev.txt
ifeq ($(OS),Windows_NT)
ACTIVATE_VENV = $(VENV_NAME)/Scripts/activate
else
ACTIVATE_VENV = $(VENV_NAME)/bin/activate
endif

# Targets
.PHONY: install run clean

# Create a virtual environment and install dependencies
check: install
	. $(ACTIVATE_VENV) && { black --diff .; flake8 --ignore=E501 app.py logs reports scanner; pylint --output-format colorized --disable=C app.py logs reports scanner; }

install:
	$(PYTHON) -m venv $(VENV_NAME)
	. $(ACTIVATE_VENV) && pip install -r $(REQUIREMENTS_DEV)

# Run the app with AWS profile and optional region arguments
run: install
	. $(ACTIVATE_VENV) && $(PYTHON) app.py $(PROFILE) $(REGION)

# Clean up the virtual environment
clean:
	rm -rf $(VENV_NAME)
