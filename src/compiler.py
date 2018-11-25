import sys
# import backend
from ins_parse import parse
from ins_check import check
from errors import CompilerError


def main():
    c = (len(sys.argv) > 1 and sys.argv[1] == 'c')
    text = ''.join(sys.stdin.readlines())

    try:
        tree = parse(text)
        check(tree, [])
    except CompilerError as err:
        print(f'ERROR\n{err}')
        exit(1)
        return

    if c:
        # backend.compile(tree)
        pass
    else:
        print(f'OK\n{tree}\n')
        exit(0)


if __name__ == '__main__':
    main()
