import ast
from pathlib import Path

TARGET_DIR = Path(r"C:\boatrace")
OUTPUT_PATH = TARGET_DIR / "args_extracted.txt"

def extract_args_from_file(file_path: Path):
    results = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "parse_args":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                    if inner.func.attr == "add_argument":
                        args = []
                        for a in inner.args:
                            if isinstance(a, ast.Str):
                                args.append(a.s)
                            elif isinstance(a, ast.Constant):  # Python 3.8+
                                args.append(str(a.value))
                        desc = ""
                        for kw in inner.keywords:
                            if kw.arg == "help":
                                if isinstance(kw.value, ast.Str):
                                    desc = kw.value.s
                                elif isinstance(kw.value, ast.Constant):
                                    desc = str(kw.value.value)
                        arg_line = ", ".join(args)
                        if desc:
                            results.append(f"{arg_line} : {desc}")
                        else:
                            results.append(arg_line)
    return results

def main():
    result_lines = []
    for py_file in TARGET_DIR.rglob("*.py"):
        args = extract_args_from_file(py_file)
        if args:
            result_lines.append(f"{py_file.name}")
            result_lines.append("-" * 40)
            result_lines.extend(args)
            result_lines.append("")

    OUTPUT_PATH.write_text("\n".join(result_lines), encoding="utf-8")
    print(f"[OK] 出力ファイル: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
