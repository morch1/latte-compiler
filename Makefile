all: venv runtime

runtime: src/lib/runtime.ll
	llvm-as -o lib/runtime.bc src/lib/runtime.ll

src/lib/runtime.ll: src/lib/runtime.c
	clang -emit-llvm -S src/lib/runtime.c -o src/lib/runtime.ll

venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || python3.7 -m venv venv
	venv/bin/pip install -Ur requirements.txt
	touch venv/bin/activate
