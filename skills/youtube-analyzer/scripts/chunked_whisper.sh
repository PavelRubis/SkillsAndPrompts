#!/bin/bash
# chunked_whisper.sh — видео/аудио → mp3 10-мин чанки → whisper через OpenRouter с сегментами.
#
#   ./chunked_whisper.sh <media-file> [workdir]
#   ./chunked_whisper.sh --timeline [workdir]     # сводный транскрипт с абсолютными таймкодами
#
# Выход: <workdir>/audio.mp3, <workdir>/chunks/c_NN.mp3, <workdir>/seg/c_NN.json (verbose_json)
# Абсолютное время сегмента = NN * 600 + segment.start
set -euo pipefail

FF="$HOME/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffmpeg"
[ -x "$FF" ] || FF=ffmpeg
SEG=600  # длина чанка, секунды

if [ "${1:-}" = "--timeline" ]; then
  WORK="${2:-$PWD}"
  python3 - "$WORK" <<'PY'
import glob, json, os, sys
work = sys.argv[1]
rows = []
for f in sorted(glob.glob(os.path.join(work, "seg", "c_*.json"))):
    n = int(os.path.basename(f).split("c_")[1].split(".")[0])
    data = json.load(open(f))
    for s in data.get("segments") or []:
        rows.append((n * 600 + s["start"], n * 600 + s["end"], s["text"].strip()))
rows.sort()
for t0, t1, txt in rows:
    print(f"{int(t0)//60:02d}:{int(t0)%60:02d}-{int(t1)//60:02d}:{int(t1)%60:02d}  {txt}")
print(f"# segments: {len(rows)}", file=sys.stderr)
PY
  exit 0
fi

IN="${1:?usage: chunked_whisper.sh <media-file> [workdir]  |  --timeline [workdir]}"
WORK="${2:-$PWD}"
KEY="$(grep -m1 '^OPENROUTER_API_KEY=' "$HOME/.hermes/.env" | cut -d= -f2-)"
[ -n "$KEY" ] || { echo "OPENROUTER_API_KEY not found in ~/.hermes/.env" >&2; exit 1; }

mkdir -p "$WORK/chunks" "$WORK/seg"
cd "$WORK"

# 1. аудио: 24 kbps mono 16 kHz ≈ 1.8 МБ на 10 минут (лимит whisper 25 МБ на файл)
[ -s audio.mp3 ] || "$FF" -v error -y -i "$IN" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 24k audio.mp3

# 2. нарезка
ls chunks/c_*.mp3 >/dev/null 2>&1 || "$FF" -v error -y -i audio.mp3 -f segment -segment_time $SEG -c copy chunks/c_%02d.mp3

# 3. транскрибация (verbose_json обязателен — иначе нет посегментных таймкодов)
for f in chunks/c_*.mp3; do
  n="$(basename "$f" .mp3 | sed 's/^c_//')"
  out="seg/c_$n.json"
  [ -s "$out" ] && continue
  curl -sS --max-time 900 https://openrouter.ai/api/v1/audio/transcriptions \
    -H "Authorization: Bearer $KEY" \
    -H "HTTP-Referer: https://hermes-agent.nousresearch.com" \
    -H "X-Title: Hermes" \
    -F "file=@$f" \
    -F "model=openai/whisper-large-v3-turbo" \
    -F "response_format=verbose_json" \
    -o "$out"
  echo "$out $(wc -c < "$out") bytes"
done

echo "готово: $WORK/seg/*.json; сводка — $0 --timeline $WORK"
