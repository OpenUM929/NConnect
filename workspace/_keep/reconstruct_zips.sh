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

has_part() {
  [ -f "$DIR/$1" ] || git -C "$DIR" cat-file -e "HEAD:./$1" 2>/dev/null
}

rebuild_one() {
  base="$1"
  # manifests written on Windows (Get-FileHash) are upper case
  expected=$(cut -d' ' -f1 "$DIR/${base}.sha256" | tr 'A-F' 'a-f')
  tmp="$DIR/${base}.rebuild.tmp"

  : > "$tmp"
  # PC2 splits with `split -d` and numbers parts from .000; others start at .001
  start=1
  has_part "${base}.000" && start=0
  i=$start
  while :; do
    n=$(printf "%03d" "$i")
    part="$DIR/${base}.${n}"
    if [ -f "$part" ]; then
      cat "$part" >> "$tmp"
    elif git -C "$DIR" cat-file -e "HEAD:./${base}.${n}" 2>/dev/null; then
      # parts hidden by sparse-checkout are read straight from git (ARTIFACT_MANAGEMENT.md 6-a-3)
      git -C "$DIR" cat-file blob "HEAD:./${base}.${n}" >> "$tmp"
    else
      break
    fi
    i=$((i + 1))
  done

  if [ "$i" -le "$start" ]; then
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
  echo "OK $base reconstructed from $((i - start)) parts (sha256 verified)"
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
  "GO2_G_A063_PC2_S12_ACTION_RATE_L2_M0P02_RESULT.zip" \
  "GO2_G_A063_PC2_S13_ACTION_RATE_L2_M0P005_RESULT.zip" \
  "GO2_G_A063_PC2_S14_P0_REPEAT_RESULT.zip" \
  "GO2_G_A066_PC2_P0_RESULT.zip" \
  "GO2_G_A066_PC2_S04_RESULT.zip" \
  "GO2_G_A066_PC2_S11_RESULT.zip" \
  "GO2_G_A066_PC2_S13_RESULT.zip" \
  "GO2_G_A066_PC2_S07_RESULT.zip" \
  "GO2_G_A064_PC2_C2_S07_LIN_VEL_Z_L2_M0P5_RESULT.zip" \
  "GO2_G_A064_PC2_C1_S07_ANG_VEL_XY_L2_M0P02_RESULT.zip" \
  "GO2_G_A064_PC2_C3_S07_ACTION_RATE_L2_M0P0075_RESULT.zip" \
  "GO2_G_A064_PC2_C6_S07_ANG_VEL_XY_L2_M0P035_RESULT.zip" \
  "GO2_G_A057_TRACK_LIN_VEL_XY_EXP_P1P4_RESULT.zip" \
  "GO2_G_A057_TRACK_LIN_VEL_XY_EXP_P1P6_RESULT.zip" \
  "GO2_G_A057_ANG_VEL_XY_L2_M0P04_RESULT.zip" \
  "GO2_G_A057_ANG_VEL_XY_L2_M0P08_RESULT.zip" \
  "GO2_A017_FULL_SUITE_RESULT.zip" \
  "GO2_DEFAULT_VS_PILOT_RESULT.zip" \
  "GO2_G_A033_CAMPAIGN_RESULT.zip" \
  "GO2_G_A043_CAMPAIGN_RESULT.zip" \
  "GO2_G_A044_RESULT.zip" \
  "GO2_G_A047_RESULT.zip" \
  "GO2_G_A048_RESULT.zip" \
  "GO2_G_A049_RESULT.zip" \
  "GO2_BASIC_MOTION_PAIR_RESULT.zip" \
  "GO2_G_A050_RESULT.zip" \
  "GO2_G_A055_RESULT.zip" \
  "GO2_PILOT_V2_BASELINE_RESULT.zip" \
  "GO2_FEET_AIR_TIME_020_RESULT.zip" \
  "GO2_G_A041_CAMPAIGN_RESULT.zip" \
  "GO2_G_A042_CAMPAIGN_RESULT.zip"
do
  rebuild_one "$base"
done