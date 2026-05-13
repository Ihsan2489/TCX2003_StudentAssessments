python3 -m venv .venv
source .venv/bin/activate

pip install flask
pip install mysql-connector-python

# run app
flask --app flask_app run --debug