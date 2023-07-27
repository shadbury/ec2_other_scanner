# Makefile for AWS EBS Volumes Analysis Tool

# Variables
PYTHON = python
VENV_NAME = venv
REQUIREMENTS = requirements.txt
ACTIVATE_VENV = $(VENV_NAME)/bin/activate
ifeq ($(OS),Windows_NT)
	ACTIVATE_VENV = $(VENV_NAME)/Scripts/activate
endif

# Targets
.PHONY: install run clean

# Create a virtual environment and install dependencies
install:
	$(PYTHON) -m venv $(VENV_NAME)
	. $(ACTIVATE_VENV) && pip install -r $(REQUIREMENTS)

# Run the app with AWS profile and optional region arguments
run:
	. $(ACTIVATE_VENV) && $(PYTHON) app.py $(PROFILE) $(REGION)

# Clean up the virtual environment
clean:
	rm -rf $(VENV_NAME)

