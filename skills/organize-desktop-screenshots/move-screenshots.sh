#!/bin/bash
# Moves screenshot files from Desktop to ~/Desktop/Screenshots/
# Handles macOS naming patterns including Unicode spaces

DESKTOP="$HOME/Desktop"
TARGET="$DESKTOP/Screenshots"

mkdir -p "$TARGET"

cd "$DESKTOP" || exit 1

# Use find to handle Unicode filenames reliably
find . -maxdepth 1 -type f \( \
  -iname "Screenshot*" -o \
  -iname "CleanShot*" -o \
  -iname "Screen Shot*" -o \
  -iname "Screen Recording*" \
\) | while read -r file; do
  basename="$(basename "$file")"
  dest="$TARGET/$basename"

  # If file already exists in target, append a number
  if [ -e "$dest" ]; then
    ext="${basename##*.}"
    name="${basename%.*}"
    counter=2
    while [ -e "$TARGET/${name}-${counter}.${ext}" ]; do
      counter=$((counter + 1))
    done
    dest="$TARGET/${name}-${counter}.${ext}"
  fi

  mv "$file" "$dest"
done
