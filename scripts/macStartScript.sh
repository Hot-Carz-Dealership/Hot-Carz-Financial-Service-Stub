#!/bin/bash 
### To start up enter
### source startScript.sh

# Define file paths
VIRT_ENV="../venv/bin/activate"
FLASK_APP="../run.py"
FLASK_PORT="5001"  # new port number in order to not interfere with other backend endpoints.


echo "Starting Python Enviroment"
source "$VIRT_ENV"
sleep 2

echo "Set ENV Variables"
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP="$FLASK_APP"
echo "ENV Variables Set"

#echo "Starting Flask Server"
#flask run

echo "Starting Flask Server on port $FLASK_PORT"
flask run --port=$FLASK_PORT
