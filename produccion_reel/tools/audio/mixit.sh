#!/bin/bash
# usage: mixit.sh music.wav voice.wav out.wav
ffmpeg -v error -y -i "$1" -i "$2" -filter_complex "[0]volume=0.42[m];[1]asplit=3[v1][v2][v3];[m][v2]sidechaincompress=threshold=0.012:ratio=12:attack=30:release=380:knee=4[md];[md]asplit[md1][md2];[md1][v1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[o];[md2]anull[mo];[v3]anull[vo]" -map "[o]" -ar 44100 "$3" -map "[mo]" "${3%.wav}_music.wav" -map "[vo]" "${3%.wav}_voice.wav"
for f in "${3%.wav}_voice.wav" "${3%.wav}_music.wav"; do echo -n "$(basename $f): "; ffmpeg -hide_banner -i "$f" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1; done
