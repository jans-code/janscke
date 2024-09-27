# janscke
## jans-codewars-kata-exporter

---

I was looking for a way of exporting my kata solutions from codewars, nothing worked without hiccups so here is my own spin of [lucasbflopes/codewars-kata-exporter](https://github.com/lucasbflopes/codewars-kata-exporter).

---

### How to install
- you will need python, pip and chrome installed
- you must provide your codewars username and password (if you registered on codewars with github, use password forgotten function on login to set a password)
- clone this repo
- recommended: create and activate a virtual environment
- On Linux:
```
	python -m venv .venv
	source .venv/Scripts/activate
```
- On Windows:
```
	python -m venv .venv
	.venv/Scripts/activate
```
- install requirements
```
	pip install -r requirements.txt
```
- run the application
```
	python janscke.py
```
- provide username and password when asked
- other options can be skipped and set to default by pressing enter
- after the application finished your katas will be saved in the default location (`solutions` folder) or a folder you chose in the beginning.