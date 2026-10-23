#!/bin/bash
# 日本語 Markdown から PDF を作る。
#
#   docs/build-pdf.sh docs/jen-v4-usage.md docs/jen-v4-usage.pdf
#
# 作る前に natural-japanese の lint を通す。指摘が残っていたら PDF を作らない。
# 日本語の文章は、書いた本人（AI を含む）が自分の癖に気づけない。検出を機械に任せる。
#   https://github.com/coji/natural-japanese
#
# この経路が日本語 PDF を作る唯一の手順なので、ここで止めれば
# 「natural-japanese を使って書く」が約束ではなく機構になる。
#
# 必要なもの（開発時のみ。プラグイン本体の AXIOM-0 とは無関係）:
#   pandoc / libreoffice / zip / unzip
#   python3.10+ と sudachipy + sudachidict_core（lint の形態素解析に使う）
#   natural-japanese の clone（NJ_DIR で場所を指定、既定は ~/natural-japanese）

set -euo pipefail

SRC="${1:?使い方: build-pdf.sh <入力.md> <出力.pdf>}"
OUT="${2:?使い方: build-pdf.sh <入力.md> <出力.pdf>}"
NJ_DIR="${NJ_DIR:-$HOME/natural-japanese}"
LINT="$NJ_DIR/skills/natural-japanese/scripts/lint.py"
PY="${NJ_PYTHON:-python3}"

# ---- 1. 日本語の lint（指摘が残っていたら作らない） ----------------------
if [ ! -f "$LINT" ]; then
  cat >&2 <<EOF
natural-japanese が見つからない: $LINT

  git clone https://github.com/coji/natural-japanese "$NJ_DIR"

別の場所にあるなら NJ_DIR で指定する。
日本語 PDF は lint を通してから作る決まりなので、ここで止める。
EOF
  exit 1
fi

if ! "$PY" -c "import sudachipy" 2>/dev/null; then
  cat >&2 <<EOF
lint に sudachipy が要る（形態素解析）。

  pip install sudachipy sudachidict_core

別の python に入っているなら NJ_PYTHON で指定する（例: NJ_PYTHON=python3.13）。
EOF
  exit 1
fi

echo "— lint: $SRC"
if ! "$PY" "$LINT" --genre tech "$SRC" > /tmp/nj-lint.$$ 2>&1; then
  sed -n '1,40p' /tmp/nj-lint.$$ >&2; rm -f /tmp/nj-lint.$$
  echo "lint が失敗した。PDF は作らない。" >&2; exit 1
fi
if ! grep -q "^検出なし。" /tmp/nj-lint.$$; then
  sed -n '1,60p' /tmp/nj-lint.$$ >&2
  rm -f /tmp/nj-lint.$$
  echo >&2
  echo "指摘が残っている。直してから作り直す。" >&2
  echo "（事実や確信の度合いは変えない。言い回しだけを直す）" >&2
  exit 1
fi
sed -n '1,3p' /tmp/nj-lint.$$; rm -f /tmp/nj-lint.$$

# ---- 2. Markdown -> docx -> A4 -> PDF -------------------------------------
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
pandoc "$SRC" -o "$W/doc.docx" --toc --toc-depth=1

( cd "$W" && mkdir x && cd x && unzip -q ../doc.docx
  python3 - <<'PYEOF'
import pathlib
p = pathlib.Path("word/document.xml"); s = p.read_text(encoding="utf-8")
# pandoc は空の sectPr を置く。そこへ A4 と余白 2cm を入れる。
# 入れないと LibreOffice が locale 既定の Letter で出す。
assert "<w:sectPr />" in s, "空の sectPr が無い（pandoc の出力形式が変わった可能性）"
p.write_text(s.replace("<w:sectPr />",
  '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
  '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
  'w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>', 1), encoding="utf-8")
PYEOF
  zip -q -r ../a4.docx . )

soffice --headless --convert-to pdf --outdir "$W" "$W/a4.docx" >/dev/null 2>&1
cp "$W/a4.pdf" "$OUT"
echo "— できた: $OUT ($(pdfinfo "$OUT" | awk '/^Pages:/{print $2}')ページ A4)"
