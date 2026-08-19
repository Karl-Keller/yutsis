"""Compare every docstring against a git ref. Prose needs an oracle too."""
import ast
import subprocess
import sys
from pathlib import Path

ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
files = subprocess.run(["git", "ls-files", "*.py"], capture_output=True,
                       text=True).stdout.split()

def docs(src, name):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"<parse error>": str(e)}
    out = {"<module>": ast.get_docstring(tree)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[f"{name}:{node.name}:{node.lineno}"] = ast.get_docstring(node)
    return out

changed = 0
for f in files:
    old = subprocess.run(["git", "show", f"{ref}:{f}"], capture_output=True, text=True)
    if old.returncode:
        print(f"NEW FILE {f}")
        continue
    a = docs(old.stdout, f)
    b = docs(Path(f).read_text(), f)
    keys = {k.rsplit(":", 1)[0] for k in a} | {k.rsplit(":", 1)[0] for k in b}
    aa = {k.rsplit(":", 1)[0]: v for k, v in a.items()}
    bb = {k.rsplit(":", 1)[0]: v for k, v in b.items()}
    for k in sorted(keys):
        if aa.get(k) != bb.get(k):
            changed += 1
            print(f"DOCSTRING CHANGED  {f}  {k}")
print(f"\n{changed} docstring(s) differ from {ref}")
