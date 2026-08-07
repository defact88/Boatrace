# fan_old_layout_tester.py
# 旧FANレイアウトでの固定長切り出し確認用
# レイアウト: C:\boatrace\tmp\fan_data_layout_old.txt
# 入力:       C:\boatrace\tmp\fan1304_part.txt

from pathlib import Path

LAYOUT = r"C:\boatrace\tmp\fan_data_layout_old.txt"
SAMPLE = r"C:\boatrace\tmp\fan1304_part.txt"  # サンプル部分ファイル

def load_layout(path):
    names, offs = [], []
    pos = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "\t" not in line:
                continue
            name, wtxt = line.split("\t", 1)
            w = int(wtxt.strip())
            names.append(name.strip())
            offs.append((pos, w))
            pos += w
    return names, offs, pos  # pos は総バイト幅

def decode_line(line_bytes, names, offs):
    out = {}
    for name, (pos, w) in zip(names, offs):
        raw = line_bytes[pos:pos+w]
        out[name] = raw.decode("cp932", errors="ignore")
    return out

def main():
    names, offs, total_w = load_layout(LAYOUT)
    print(f"[LAYOUT] cols={len(names)} total_width={total_w}")

    with open(SAMPLE, "rb") as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip(b"\r\n")
            print(f"\n[LINE {i}] bytes={len(line)}  (expect≈{total_w})")
            obj = decode_line(line, names, offs)

            # 代表項目だけ表示（必要なら増やしてください）
            for k in ("登番","氏名漢字","氏名カナ","級","年号","生年月日","勝率","複勝率","平均スタートタイミング","年","期","登録期"):
                v = obj.get(k, "")
                print(f"  {k}: {v!r}")

            # 先頭数項目の幅チェック（ズレ検出用）
            print("-- head hex --")
            hnames = names[:6]
            for name, (pos, w) in zip(hnames, offs[:6]):
                seg = line[pos:pos+w]
                print(f"  {pos:04d}+{w:02d} {name:<16} head={seg[:8].hex(' ')}")

            if i >= 3:  # 行数が多い場合は最初の数人だけ
                break

if __name__ == "__main__":
    main()
