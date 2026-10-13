# convert_args_summary_to_csv.py

from pathlib import Path
import csv

IN_PATH = Path(r"C:\boatrace\Management_GUI\args_summary.txt")
OUT_PATH = Path(r"C:\boatrace\Management_GUI\args_table.csv")

lines = IN_PATH.read_text(encoding="utf-8").splitlines()
entries = []
current_file = None

for line in lines:
    line = line.strip()
    if line.startswith("[") and line.endswith("]"):
        current_file = line[1:-1]
    elif line and not line.startswith("="):
        if ":" in line:
            arg_part = line.split(":")[0].strip()
        else:
            arg_part = line.strip()
        for arg in map(str.strip, arg_part.split(",")):
            if arg:
                entries.append((current_file, arg))

# CSV出力
with OUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["ファイル名", "引数"])
    writer.writerows(entries)

OUT_PATH.name
