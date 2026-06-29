#!/usr/bin/env python3
"""Extract JK × instrument matrix from purchase method registries."""

import re
from pathlib import Path

BASE = Path("/Users/anton_tsoy/Desktop/Обсидиан/9. Застройщики/Способы покупок")

FILES = {
    "Т": BASE / "Траншевая ипотека/Условия траншевой ипотеки.md",
    "С": BASE / "Субсидированная ипотека/Условия субсидированной ипотеки.md",
    "К": BASE / "Сниженный платеж от Совкомбанка/Условия сниженного платежа.md",
    "Р": BASE / "Рассрочка/Условия рассрочек.md",
}

SKIP_PATTERNS = re.compile(
    r"нет рассрочки|все объекты по дду|объекты дду$",
    re.I,
)

CANONICAL = {
    "жк зорге. премьер": "ЖК Зорге.Премьер",
    "жк зорге.премьер": "ЖК Зорге.Премьер",
    "жк урбан мартен": "ЖК Урбан Мартен / Урбан Тау",
    "жк урбан тау": "ЖК Урбан Мартен / Урбан Тау",
    "жк урбан мартен жк урбан тау": "ЖК Урбан Мартен / Урбан Тау",
    "жк свои берег жк 8 марта": "ЖК Свой берег / 8 Марта / Цветы Башкирии",
    "жк 8 марта": "ЖК Свой берег / 8 Марта / Цветы Башкирии",
    "жк свой берег": "ЖК Свой берег / 8 Марта / Цветы Башкирии",
    "жк цветы башкирии": "ЖК Свой берег / 8 Марта / Цветы Башкирии",
    "жк новаленд": "ЖК Novaland / Новаленд",
    "жк novaland": "ЖК Novaland / Новаленд",
    "жк паруса": "ЖК Паруса",
    "жк паруса. заречьестрой": "ЖК Паруса. ЗаречьеСтрой",
    "жк первый остров": "ЖК Первый Остров",
}


def canonical(name: str) -> str:
    key = re.sub(r"\s+", " ", name.strip().lower())
    key = re.sub(r"\s*\(.*$", "", key)
    return CANONICAL.get(key, name.strip())


def clean_jk_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    name = re.sub(r"\s*\(.*$", "", name).strip()
    return canonical(name)


def extract_jk_names(cell: str) -> list[str]:
    cell = re.sub(r"<br\s*/?>", " ", cell, flags=re.I)
    cell = re.sub(r"\*+", "", cell)
    parts = re.split(r"(?=ЖК\s)", cell, flags=re.I)
    names: list[str] = []
    for part in parts:
        part = part.strip()
        if not part.upper().startswith("ЖК"):
            continue
        m = re.match(r"(ЖК\s+.+?)(?:\s*/\s*|$)", part, re.I)
        raw = m.group(1) if m else part
        names.append(clean_jk_name(raw))
    return [n for n in dict.fromkeys(names) if n and len(n) > 3]


def parse_tables(path: Path, jk_col: int) -> set[str]:
    found: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-+", line):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) <= jk_col:
            continue
        cell = cols[jk_col]
        if SKIP_PATTERNS.search(cell) or cell in ("—", "-", ""):
            continue
        for name in extract_jk_names(cell):
            found.add(name)
    return found


def main() -> str:
    data: dict[str, dict[str, bool]] = {}
    for code, path in FILES.items():
        jk_col = 1 if code == "К" else 0
        for jk in parse_tables(path, jk_col):
            data.setdefault(jk, {"Т": False, "С": False, "К": False, "Р": False})
            data[jk][code] = True

    rows = sorted(data.items(), key=lambda x: (-sum(x[1].values()), x[0]))
    all4 = [jk for jk, f in rows if all(f.values())]

    lines = [
        "## 📊 Матрица ЖК × инструменты покупки",
        "",
        "Сводка по реестрам каталога. **Т** — [[Условия траншевой ипотеки|траншевая ипотека]], "
        "**С** — [[Условия субсидированной ипотеки|субсидированная ипотека]], "
        "**К** — [[Сниженный платеж от Совкомбанка/Условия сниженного платежа|сниженный платёж Совкомбанка]], "
        "**Р** — [[Условия рассрочек|рассрочка]]. "
        "✅ — инструмент есть в соответствующем реестре.",
        "",
    ]

    if all4:
        lines.extend([
            "### Объекты со всеми 4 инструментами",
            "",
            ", ".join(f"**{jk}**" for jk in all4) + ".",
            "",
        ])

    lines.extend([
        "| Жилой комплекс | Т | С | К | Р |",
        "| :--- | :-: | :-: | :-: | :-: |",
    ])
    for jk, flags in rows:
        mark = ["✅" if flags[c] else "—" for c in "ТСКР"]
        lines.append(f"| {jk} | {mark[0]} | {mark[1]} | {mark[2]} | {mark[3]} |")

    lines.extend([
        "",
        f"*Объектов в матрице: {len(rows)}. Со всеми 4 инструментами: {len(all4)}. Обновлено: 22.06.2026.*",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(main())
