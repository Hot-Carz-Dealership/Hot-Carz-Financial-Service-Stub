#!/bin/bash 
### To start up enter
### source startScript.sh

# Define file paths
VIRT_ENV="../venv/bin/activate"
FLASK_APP="../run.py"


echo "Starting Python Enviroment"
source "$VIRT_ENV"
sleep 2

echo "Set ENV Variables"
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP="$FLASK_APP"
echo "ENV Variables Set"

echo "Starting Flask Server"
flask run