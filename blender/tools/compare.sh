#!/usr/bin/env bash
# Side-by-side VIDEO | MODEL image.  Usage: compare.sh <video_frame.jpg> <render.png> <out.jpg>
set -e
ffmpeg -nostdin -v error -y -i "$1" -i "$2" -filter_complex \
 "[0]scale=960:540,drawtext=text='VIDEO':x=10:y=10:fontsize=28:fontcolor=yellow:box=1:boxcolor=black[a];[1]scale=960:540,drawtext=text='MODEL':x=10:y=10:fontsize=28:fontcolor=yellow:box=1:boxcolor=black[b];[a][b]hstack" "$3"
