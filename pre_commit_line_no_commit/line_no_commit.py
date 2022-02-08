import argparse
import collections
import os
import sys
import re


CR = '\r'
LF = '\n'
CRLF = '\r\n'
NO_COMMIT_COMMENT_REGEX_COMPILED = re.compile(r"#\s*no[-]{0,1}commit\s*$")


def find_newline(source):
    counter = collections.defaultdict(int)
    for line in source:
        if line.endswith(CRLF):
            counter[CRLF] += 1
        elif line.endswith(CR):
            counter[CR] += 1
        elif line.endswith(LF):
            counter[LF] += 1
    return (sorted(counter, key=counter.get, reverse=True) or [LF])[0]


class ExitCodes(object):
    """Possible exit codes."""
    ok = 0
    error = 1
    interrupted = 2
    check_failed = 3


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filenames', nargs='*',
        help='Filenames pre-commit believes are changed',
    )
    parser.add_argument('-c', '--check', action='store_true',
        help='only check and report incorrectly formatted files'
    )

    args = parser.parse_args(argv)

    try:
        return remove_no_commit_lines(args.filenames, args)
    except KeyboardInterrupt:
        return ExitCodes.interrupted


def find_py_files(filenames):
    def not_hidden(filename):
        return not filename.startswith('.')

    def is_python_file(filename):
        return os.path.isfile(filename) and filename.endswith('.py')

    for name in sorted(filenames):
        if not_hidden(name) and is_python_file(name):
            yield name

def format_code(source):
    new_code_lines = []
    file_corrected = False

    code_lines = source.splitlines()
    new_line = find_newline(code_lines)
    
    for line in code_lines:
        if not NO_COMMIT_COMMENT_REGEX_COMPILED.search(line):
            new_code_lines.append(line)
        else:
            file_corrected = True


    return f"{new_line}".join(new_code_lines), file_corrected


def format_file(filename, args):
    with open(filename) as fi:
        source = fi.read()

        formatted_source, file_corrected = format_code(source)

        if source != formatted_source and file_corrected:
            if args.check:
                return ExitCodes.check_failed

            with open(filename, mode='w') as fo:
                fo.write(formatted_source)

    return ExitCodes.ok

def remove_no_commit_lines(filenames, args):
    outcomes = collections.Counter()

    for filename in find_py_files(filenames):
        try:
            result = format_file(filename, args)
            outcomes[result] += 1
        except Exception:
            outcomes[ExitCodes.error] += 1

    return_codes = [
        ExitCodes.error,
        ExitCodes.check_failed,
        ExitCodes.ok,
    ]

    for code in return_codes:
        if outcomes[code]:
            return code



if __name__ == '__main__':
    sys.exit(main())
