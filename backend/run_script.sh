#!/bin/bash

# Activate the virtual environment
source /home/ubuntu/building_bids_data_scraper/cron_venv/bin/activate

# Run the Python script using the absolute path to the virtual environment's Python interpreter
/home/ubuntu/building_bids_data_scraper/cron_venv/bin/python /home/ubuntu/building_bids_data_scraper/backend/auction_script.py
