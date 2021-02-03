import re
import argparse
import difflib
import sys

METHOD_DECL_REGEX='(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)'

def get_test_snippet(str_test, target_name):
    cursor_start, cursor_end = None, None

    found = False
    for m in re.finditer(METHOD_DECL_REGEX, str_test):
        method_name = m.group(2)
        if method_name == target_name:
          cursor_start = m.start()
          cursor_end = m.end()
          found = True
          break

    if not found:
      return None

    snippet = str_test[cursor_start:cursor_end]
    indentation = str_test[:cursor_start].split('\n')[-1]
    snippet = indentation + snippet

    before = str_test[:cursor_start].strip().split('\n')
    for line in reversed(before):
        if line.strip().startswith('@'):
            snippet = line + '\n' + snippet
        else:
            break

    opened = None
    for c in str_test[cursor_end:]:
        if c == '}':
            opened -= 1
        elif c == '{':
            if opened is None:
                opened = 1
            else:
                opened += 1
        snippet += c
        if opened == 0:
            break
    return snippet

def insert_test(str_test, test_snippet):
    lines = str_test.split("\n")
    for i, line in enumerate(reversed(lines)):
        lineno = len(lines) - i - 1
        if line.strip() != '':
            break

    lines = lines[:lineno] + test_snippet.split("\n") + lines[lineno:]

    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=str)
    parser.add_argument("dest", type=str)
    parser.add_argument("method", type=str)
    args = parser.parse_args()

    with open(args.src, 'r') as f:
      src_test = f.read()
      new_snippet = get_test_snippet(src_test, args.method)
      assert new_snippet is not None

    with open(args.dest, 'r') as f:
      tgt_test = f.read()
      orig_snippet = get_test_snippet(tgt_test, args.method)

    if orig_snippet:
      # overwrite
      new_test = tgt_test.replace(orig_snippet, new_snippet)
    else:
      # create new test
      new_test = insert_test(tgt_test, new_snippet)

    with open(args.dest, 'w') as f:
      f.write(new_test)
