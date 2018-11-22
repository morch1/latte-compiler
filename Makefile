venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || python3.7 -m venv venv
	venv/bin/pip install -Ur requirements.txt
	touch venv/bin/activate
