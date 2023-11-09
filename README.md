# WORK IN PROGRESS DO NOT USE

A visualisation builder that uses python panels to visualise a dataset on DAFNI. This is purely intended as a base example repository.

docker build -t panels-app .

docker run  --env-file ./.env -p 3000:3000 panels-app

python panels-app.py