#!/bin/bash

# Activate environment
source /env/bin/activate

git_repo_url="https://github.com/CentralValleyModeling/recon-cap.git"

# Clone the repo into a subfolder
echo "cloning repo $1"
git clone -b production "$git_repo_url" "code"

# Run app
echo "$PWD"
ls

echo "cd to code"
cd "code"|| exit
ls

echo "Running the application..."
export FLASK_DEBUG=1
flask run -h 0.0.0.0 -p 80
