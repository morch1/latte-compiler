import sys
import frontend.parser as par
import frontend.checker
import backend.llvm_translator
import errors

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
        llvm = program.translate()
        print(llvm)
    else:
        print(f'OK\n', file=sys.stderr)
        print(program)

    exit(0)


if __name__ == '__main__':
    main()
