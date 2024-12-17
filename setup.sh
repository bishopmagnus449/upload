#!/bin/bash

# Install Python 3 and pip
sudo apt update
sudo apt install -y python3 python3-pip

# Install Linux dependencies for the modules
sudo apt install -y libjpeg-dev zlib1g-dev wkhtmltopdf

# Install Python modules from requirements.txt
pip3 install -r requirements.txt