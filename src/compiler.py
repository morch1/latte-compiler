import sys
import frontend.parser as par
import errors
from backend.llvm.translator import translate_program
from backend.llvm.optimizer import optimize_program

def main():
    c = (len(sys.argv) > 1 and sys.argv[1] == 'c')
    text = ''.join(sys.stdin.readlines())

    try:
        program = par.parse(text)
        program.check()
    except errors.CompilerError as err:
        print(f'ERROR\n{err}\n', file=sys.stderr)
        exit(1)
        return

    if c:
        noopts = (len(sys.argv) > 2 and sys.argv[2] == 'noopts')
        llvm = translate_program(program)
        if not noopts:
            optimize_program(llvm)
        print(llvm)
    else:
        print(f'OK\n', file=sys.stderr)
        print(program)

    exit(0)


if __name__ == '__main__':
    main()
