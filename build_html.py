#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""電子鬼譚_桃太郎.md を読書用の単一HTMLへ変換する。"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "電子鬼譚_桃太郎.md"
OUT = ROOT / "index.html"

SERIES = "NEO-TOKYO / CYBER FOLKTALE"
BRAND = "MOMO"

# 装飾的な区切り文字（場面転換に使う）
BREAK_CHARS = "*＊・·•—―─＝="


def parse_markdown(text):
    blocks = []
    para = []
    quote = []

    def flush_para():
        nonlocal para
        if para:
            blocks.append(("p", "".join(para)))
            para = []

    def flush_quote():
        nonlocal quote
        if quote:
            blocks.append(("quote", quote[:]))
            quote = []

    def flush_all():
        flush_para()
        flush_quote()

    def is_scene_break(s):
        if s == "---":
            return True
        core = s.replace("　", "").replace(" ", "")
        if not core:
            return False
        if not all(ch in BREAK_CHARS for ch in core):
            return False
        # 中点・アスタリスク系を含む装飾線のみを区切りとみなす（純粋なダッシュは本文扱い）
        return any(ch in "*＊・·•" for ch in core)

    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_all()
            continue
        if s.startswith("# "):
            flush_all()
            blocks.append(("h1", s[2:].strip()))
            continue
        if s.startswith("## "):
            flush_all()
            blocks.append(("h2", s[3:].strip()))
            continue
        if s.startswith("### "):
            flush_all()
            blocks.append(("h3", s[4:].strip()))
            continue
        if is_scene_break(s):
            flush_all()
            blocks.append(("hr", None))
            continue
        if s.startswith(">"):
            flush_para()
            quote.append(s.lstrip(">").strip())
            continue
        flush_quote()
        para.append(s)

    flush_all()
    return blocks


def inline(text):
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def title_parts(title):
    """「EN ── JP」形式を分割。区切りはダッシュ系の連続（──／—— 等）。"""
    parts = re.split(r"\s*[─—–―]{2,}\s*", title, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title, ""


def render_block(block, section_id=None):
    typ, payload = block
    if typ == "h1":
        en, jp = title_parts(payload)
        jp_html = f'<span class="ttl-jp">{inline(jp)}</span>' if jp else ""
        return (
            f'<div class="series">{html.escape(SERIES)}</div>'
            '<h1 class="title">'
            f'<span class="ttl-en">{inline(en)}</span>{jp_html}'
            "</h1>"
        )
    if typ == "h2":
        sid = f' id="{section_id}"' if section_id else ""
        return f"<h2{sid}>{inline(payload)}</h2>"
    if typ == "h3":
        return f"<h3>{inline(payload)}</h3>"
    if typ == "p":
        return f"<p>{inline(payload)}</p>"
    if typ == "quote":
        body = "".join(f"<p>{inline(line)}</p>" for line in payload)
        return f"<blockquote>{body}</blockquote>"
    if typ == "hr":
        return '<hr class="scene">'
    return ""


def build():
    blocks = parse_markdown(SRC.read_text(encoding="utf-8"))
    page_title = BRAND
    sections = []
    nav = []
    h2_count = 0
    rendered = []

    for block in blocks:
        typ, payload = block
        if typ == "h1":
            en, jp = title_parts(payload)
            page_title = f"{jp}｜{en}" if jp else en
            rendered.append(render_block(block))
        elif typ == "h2":
            h2_count += 1
            sid = f"chapter-{h2_count:02d}"
            sections.append((sid, payload))
            nav.append(f'<a href="#{sid}">{html.escape(payload)}</a>')
            rendered.append(render_block(block, sid))
        else:
            rendered.append(render_block(block))

    body = "\n".join(rendered)
    nav_html = "\n".join(nav)
    doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title)}</title>
<link rel="stylesheet" href="reader.css">
</head>
<body>
<header class="bar" id="bar">
  <button id="barToggle" type="button" aria-label="メニュー" aria-expanded="false">☰</button>
  <span class="nm">{html.escape(BRAND)}</span>
  <nav>{nav_html}</nav>
  <button id="fontDec" type="button" aria-label="文字を小さく">A-</button>
  <button id="fontInc" type="button" aria-label="文字を大きく">A+</button>
  <button id="themeBtn" type="button" aria-label="テーマ切替">paper</button>
  <button id="bmBtn" type="button" aria-label="しおり">bookmark</button>
</header>
<main id="scroll" class="scroll">
  <article class="book">
{body}
  </article>
</main>
<aside class="progress" aria-hidden="true">
  <div class="track"></div>
  <div class="ticks" id="ticks"></div>
  <div class="fill" id="fill"></div>
  <div class="pct" id="pct">0%</div>
</aside>
<a class="resume" id="resume" href="#">前回の続き <small class="pct">--%</small></a>
<script src="reader.js"></script>
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT} ({len(sections)} sections)")


if __name__ == "__main__":
    build()
