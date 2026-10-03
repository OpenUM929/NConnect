#!/bin/sh
# Reconstruct >100MB result archives from their .zip.001.. parts.
#
# GitHub enforces a hard 100 MB per-file limit, so these archives are stored
# split into 95 MB parts. Parts are concatenated in numeric order and verified
# against the recorded .sha256 manifest before replacing the original.
#
# To add another archive: split it into 95 MB parts as <name>.001.., keep its
# .sha256 manifest, gitignore the original, and add its base name to the list
# below. See ARTIFACT_MANAGEMENT.md 6-a.
set -e
DIR=$(cd "$(dirname "$0")" && pwd)

rebuild_one() {
  base="$1"
  expected=$(cut -d' ' -f1 "$DIR/${base}.sha256")
  tmp="$DIR/${base}.rebuild.tmp"

  : > "$tmp"
  i=1
  while :; do
    n=$(printf "%03d" "$i")
    part="$DIR/${base}.${n}"
    [ -f "$part" ] || break
    cat "$part" >> "$tmp"
    i=$((i + 1))
  done

  if [ "$i" -le 1 ]; then
    echo "no parts found for $base" >&2
    rm -f "$tmp"
    return 1
  fi

  actual=$(sha256sum "$tmp" | cut -d' ' -f1)
  if [ "$actual" != "$expected" ]; then
    echo "MISMATCH $base: expected $expected got $actual" >&2
    rm -f "$tmp"
    return 1
  fi

  mv -f "$tmp" "$DIR/${base}"
  echo "OK $base reconstructed from $((i - 1)) parts (sha256 verified)"
}

for base in \
  "GO2_G_A057_TRACK_LIN_VEL_XY_EXP_P1P2_RESULT.zip" \
  "GO2_G_A058_A048_SEED42_RESULT.zip" \
  "GO2_G_A058_A043_SEED43_RESULT.zip" \
  "GO2_CHAIN01_BASELINE_RESULT.zip" \
  "GO2_G_A028_RESULT.zip"
do
  rebuild_one "$base"
done