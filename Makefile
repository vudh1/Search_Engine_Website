export FLASK_APP=web_launch.py
export FLASK_ENV=development
export FLASK_RUN_HOST=localhost
export FLASK_RUN_PORT=8000

run:
	python3 -m flask run

