#!/bin/bash
# Markdown -> docx -> (A4化) -> PDF。pandoc と libreoffice を使う。
set -e
SRC="$1"; OUT="$2"
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
pandoc "$SRC" -o "$W/doc.docx" --toc --toc-depth=1
( cd "$W" && mkdir x && cd x && unzip -q ../doc.docx
  python3 - <<'PY'
import pathlib
p = pathlib.Path("word/document.xml"); s = p.read_text(encoding="utf-8")
assert "<w:sectPr />" in s, "空の sectPr が無い（pandoc の出力形式が変わった可能性）"
p.write_text(s.replace("<w:sectPr />",
  '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
  '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
  'w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>', 1), encoding="utf-8")
PY
  zip -q -r ../a4.docx . )
soffice --headless --convert-to pdf --outdir "$W" "$W/a4.docx" >/dev/null 2>&1
cp "$W/a4.pdf" "$OUT"
