#!/usr/bin/env python3
"""Regenerate publications.html from the CV's publication database.

    cp ~/Overleaf/CV/paper.tdb data/paper.tdb && python3 tools/build_pubs.py
"""
import html
import unicodedata
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = [("Journal", "Journal Articles"), ("Conference", "Conference Papers"), ("Book", "Books, Chapters & Other")]

ACCENTS = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302", "~": "\u0303",
           "v": "\u030c", "u": "\u0306", "c": "\u0327", "=": "\u0304"}
MATH = {r"\log": "log", r"\varepsilon": "ε", r"\alpha": "α", r"\epsilon": "ε"}


def tuples(src):
    """Yield each \\tuple{...} as a dict of field -> raw LaTeX value."""
    for m in re.finditer(r"\\tuple\s*\{", src):
        i, depth, fields, key, buf = m.end(), 1, {}, None, ""
        while depth:
            ch = src[i]
            if ch == "{":
                depth += 1
                if depth == 2 and key is not None:
                    i += 1
                    continue
            elif ch == "}":
                depth -= 1
                if depth == 1 and key is not None:
                    fields[key.strip()], key, buf = buf, None, ""
                    i += 1
                    continue
            if depth == 1:
                if ch == "=":
                    key, buf = buf.strip(" \t\n,"), ""
                elif ch == "," and key is not None:
                    fields[key.strip()], key, buf = buf.strip(), None, ""
                else:
                    buf += ch
            elif depth > 0:
                buf += ch
            i += 1
        if key is not None:
            fields[key.strip()] = buf.strip()
        yield fields


def math(s):
    s = re.sub(r"(?<=[A-Za-z0-9])\\log", r" \\log", s)
    for k, v in MATH.items():
        s = s.replace(k, v)
    s = re.sub(r"\^\{?(\d)\}?", lambda m: "⁰¹²³⁴⁵⁶⁷⁸⁹"[int(m.group(1))], s)
    s = re.sub(r"\^\s*ε", "<sup>ε</sup>", s)
    return f"<i>{s.strip()}</i>"


def latex(s):
    """Convert the small LaTeX subset used in paper.tdb to HTML."""
    s = html.escape(s, quote=False)
    s = re.sub(r"\$([^$]*)\$", lambda m: math(m.group(1)), s)
    s = re.sub(r"\\([o])\{\}|\{\\(o)\}|\\(o)\b", "ø", s)
    s = s.replace(r"\i", "ı").replace("{ı}", "ı")
    s = re.sub(r"\{?\\([`'\"^~=])\{?\s*([A-Za-zı])\}?\}?",
               lambda m: m.group(2).replace("ı", "i") + ACCENTS[m.group(1)], s)
    s = re.sub(r"\{?\\([vuc])[\s{]\s*([A-Za-z])\}?\}?", lambda m: m.group(2) + ACCENTS[m.group(1)], s)
    for cmd, tag in (("emph", "em"), ("textbf", "strong"), ("textsc", "span")):
        s = re.sub(r"\\%s\{([^{}]*)\}" % cmd, rf"<{tag}>\1</{tag}>", s)
    s = re.sub(r"\{\\em\s+([^{}]*)\}", r"<em>\1</em>", s)
    s = re.sub(r"\{\\sc\s+([^{}]*)\}", r"\1", s)
    s = s.replace("~", " ").replace("--", "–").replace("``", "“").replace("''", "”")
    s = s.replace("{", "").replace("}", "").replace("\\ ", " ").replace("\\", "")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", s).strip())


def authors(s):
    s = latex(s)
    return re.sub(r"M\. (Farach-Colton|Farach)\b", r'<span class="me">M. \1</span>', s)


def render(t):
    info = latex(t.get("Info", ""))
    link = t.get("Link") or (f"https://doi.org/{t['DOI']}" if t.get("DOI") else "")
    if "Title" not in t:  # Book-style entries keep everything in Info
        body = f'<span class="pvenue plain">{info}</span>'
        if link:
            body += f' <a class="plink" href="{html.escape(link)}">link</a>'
        return f'<li>{body}</li>'
    title = latex(t["Title"])
    if link:
        title = f'<a href="{html.escape(link)}">{title}</a>'
    doi = (f' <a class="plink" href="https://doi.org/{html.escape(t["DOI"])}">doi</a>'
           if t.get("DOI") and t.get("Link") else "")
    return (f'<li><span class="ptitle">{title}</span>'
            f'<span class="pauthors">{authors(t.get("Authors", ""))}</span>'
            f'<span class="pvenue">{info}{doi}</span></li>')


def main():
    src = (ROOT / "data" / "paper.tdb").read_text()
    src = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("%"))
    entries = list(tuples(src))
    out, counts = [], {}
    for field, heading in SECTIONS:
        items = [t for t in entries if t.get(field) == "1"]
        counts[field] = len(items)
        lis = "\n".join(render(t) for t in items)
        out.append(f'<section class="year" id="{field.lower()}"><h2>{heading} '
                   f'<span class="count">({len(items)})</span></h2>\n<ol class="pubs">\n{lis}\n</ol></section>')
    page = (ROOT / "tools" / "publications.template.html").read_text()
    page = page.replace("{{COUNT}}", str(counts["Journal"] + counts["Conference"]))
    page = page.replace("{{JOURNALS}}", str(counts["Journal"])).replace("{{CONFERENCES}}", str(counts["Conference"]))
    page = page.replace("{{PUBLICATIONS}}", "\n".join(out))
    (ROOT / "publications.html").write_text(page)
    leftovers = sorted(set(re.findall(r"\\[a-zA-Z]+|[{}$]", re.sub(r"<[^>]+>", "", page.split("<main")[1].split("<script")[0]))))
    print(f"wrote publications.html: {counts}" + (f"; unconverted LaTeX: {leftovers}" if leftovers else ""))


if __name__ == "__main__":
    main()
