#!/usr/bin/env bash
# mux.sh FRAMES_DIR MUSIC.wav OUT.mp4 — 30 fps H.264 + AAC, two-pass loudnorm to -14 LUFS / -1.5 dBTP
set -e
FF=${FFMPEG:-ffmpeg}   # set FFMPEG to use another build
J=$($FF -hide_banner -nostats -i "$2" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
$FF -v error -y -framerate 30 -i "$1/f%04d.jpg" -i "$2" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -profile:v high -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$3"
echo "wrote $3"
