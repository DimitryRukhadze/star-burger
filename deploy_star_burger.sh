#!/bin/bash

set -e
git pull
source env/bin/activate
pip install -r requirements.txt --no-cache-dir
npm ci --dev
python3 manage.py collectstatic --no-input
python3 manage.py migrate --no-input
systemctl start star_burger.target
source .env
export ROLLBAR_TOKEN
export ROLLBAR_ENV
export ROLLBAR_NAME
git_hash=$(git rev-parse --short HEAD)
comments=$(git log -1 --pretty=%B)
json=$( jo "environment=$ROLLBAR_ENV" "revision=$git_hash" "rollbar_name=$ROLLBAR_NAME" "local_username=$USER" "comment=$comments" "status=succeeded" )
curl -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d "$json"
echo "Finished Deploying!"
