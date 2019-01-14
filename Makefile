all: venv runtime

runtime: lib/runtime.ll
	llvm-as -o lib/runtime.bc lib/runtime.ll

lib/runtime.ll: src/lib/runtime.c
	mkdir -p lib
	clang -emit-llvm -S src/lib/runtime.c -o lib/runtime.ll

venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || python3.7 -m venv venv
	venv/bin/pip install -Ur requirements.txt
	touch venv/bin/activate
