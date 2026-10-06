# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup

_LABELS = (
    ("time_lap", ("一周", "半周", "1周")),
    ("time_turning", ("まわり足", "回り足")),
    ("time_acceleration", ("直線",)),
)

_NUM = re.compile(r"^\d+(?:\.\d+)?$")


def _to_float(s):
    s = (s or "").strip()
    return float(s) if _NUM.match(s) else None


def _span(tag, name):
    try:
        return max(1, int(tag.get(name, 1)))
    except ValueError:
        return 1

def _header_columns(table):

    rows = table.find("thead").find_all("tr") if table.find("thead") else []
    if not rows:
        rows = [tr for tr in table.find_all("tr") if tr.find("th") and not tr.find("td")]
    grid = {}  # (r, c) -> text
    for r, tr in enumerate(rows):
        c = 0
        for th in tr.find_all(["th", "td"], recursive=False):
            while (r, c) in grid:
                c += 1
            text = th.get_text("", strip=True)
            for dr in range(_span(th, "rowspan")):
                for dc in range(_span(th, "colspan")):
                    grid[(r + dr, c + dc)] = text
            c += _span(th, "colspan")
    ncols = max((c for _, c in grid), default=-1) + 1
    cols = {}
    for c in range(ncols):
        for r in range(len(rows) - 1, -1, -1):  # 下の行(葉)優先
            t = grid.get((r, c), "")
            hit = next((f for f, keys in _LABELS if any(k == t for k in keys)), None)
            if hit:
                cols[c] = hit
                break
    return cols


def _find_table(soup):
    for t in soup.find_all("table"):
        heads = " ".join(th.get_text("", strip=True) for th in t.find_all("th"))
        if ("まわり足" in heads or "回り足" in heads) and ("一周" in heads or "半周" in heads):
            return t
    return None


def parse_table_style(html):
    soup = BeautifulSoup(html, "lxml")
    table = _find_table(soup)
    if table is None:
        return {}
    cols = _header_columns(table)
    if not cols:
        return {}
    out = {}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue
        first = tds[0].get_text("", strip=True)
        if not first.isdigit() or not 1 <= int(first) <= 6:
            continue
        # colspan 展開した行内インデックスで列対応
        cells, c = {}, 0
        for td in tds:
            for _ in range(_span(td, "colspan")):
                cells[c] = td.get_text("", strip=True)
                c += 1
        rec = {f: None for f, _ in _LABELS}
        for ci, field in cols.items():
            rec[field] = _to_float(cells.get(ci))
        out[int(first)] = rec
    return out