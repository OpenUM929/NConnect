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
  "GO2_G_A028_RESULT.zip" \
  "GO2_G_A060_PC2_A048_SEED42_RESULT.zip" \
  "GO2_G_A060_PC2_ANG_VEL_XY_L2_M0P08_RESULT.zip" \
  "GO2_G_A060_PC2_TRACK_LIN_VEL_XY_EXP_P1P4_RESULT.zip" \
  "GO2_G_A061_PC2_N3_DOF_TORQUES_L2_M1E_4_RESULT.zip" \
  "GO2_G_A062_PC2_Q0_LIN_VEL_Z_L2_M1P5_RESULT.zip" \
  "GO2_G_A062_PC2_Q1_TRACK_ANG_VEL_Z_EXP_P1P0_RESULT.zip" \
  "GO2_G_A062_PC2_Q2_ANG_VEL_XY_L2_M0P06_RESULT.zip" \
  "GO2_G_A062_PC2_P5_DOF_ACC_L2_M1P25E_7_RESULT.zip" \
  "GO2_G_A062_PC2_P6_DOF_ACC_L2_M6P25E_8_RESULT.zip" \
  "GO2_G_A062_PC2_P4_DOF_TORQUES_L2_M5E_5_RESULT.zip" \
  "GO2_G_A063_PC2_S01_LIN_VEL_Z_L2_M5_RESULT.zip" \
  "GO2_G_A063_PC2_S02_LIN_VEL_Z_L2_M3_RESULT.zip" \
  "GO2_G_A063_PC2_S03_LIN_VEL_Z_L2_M2_RESULT.zip" \
  "GO2_G_A063_PC2_S04_LIN_VEL_Z_L2_M0P5_RESULT.zip" \
  "GO2_G_A063_PC2_S05_FEET_AIR_TIME_P0P01_RESULT.zip" \
  "GO2_G_A063_PC2_S06_FEET_AIR_TIME_P0P1_RESULT.zip" \
  "GO2_G_A063_PC2_S07_FEET_AIR_TIME_P0P35_RESULT.zip" \
  "GO2_G_A063_PC2_S08_FEET_AIR_TIME_P0P5_RESULT.zip" \
  "GO2_G_A063_PC2_S09_ANG_VEL_XY_L2_M0P3_RESULT.zip" \
  "GO2_G_A063_PC2_S10_ANG_VEL_XY_L2_M0P15_RESULT.zip" \
  "GO2_G_A063_PC2_S11_ANG_VEL_XY_L2_M0P02_RESULT.zip" \
  "GO2_G_A063_PC2_S12_ACTION_RATE_L2_M0P02_RESULT.zip"
do
  rebuild_one "$base"
done