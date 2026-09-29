"""영상 판독용 연속 프레임 시트 (2026-09-28, 계단 영상 판독 — Codex 계획 GO2_STAIRS_REWARD_BASICS_CODEX_PLAN_20260928 §5).

영상에서 [start, stop) 프레임을 step 간격으로 뽑아(선택적으로 잘라) 격자 한 장으로 만든다.  각 칸에 시각(초)을 적는다.
판정을 하지 않는다 — 사람이 읽는 시트다.  영상은 50 fps 이므로 step 25 = 0.5 s, step 5 = 0.1 s.

    python -B tools/go2_video_contact_sheet.py <video.mp4> <out.jpg> --start 0 --stop 499 --step 25 --cols 4 --width 480
    python -B tools/go2_video_contact_sheet.py <video.mp4> <out.jpg> --start 110 --stop 210 --step 5 \\
        --crop 680 460 1180 790 --cols 4 --width 480

2026-09-28 판독에 쓴 인자는 reports/GO2_STAIRS_PROCESS_A043_A048_A050_20260927.md §7 에 적혀 있다.
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np


def sheet(video: str, out: str, start: int, stop: int, step: int, cols: int, width: int,
          crop: tuple[int, int, int, int] | None, fps: float = 50.0) -> int:
    cap = cv2.VideoCapture(video)
    tiles = []
    for frame in range(start, stop, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ok, image = cap.read()
        if not ok:
            image = np.zeros((1080, 1920, 3), np.uint8)
        if crop:
            x0, y0, x1, y1 = crop
            image = image[y0:y1, x0:x1]
        height = int(width * image.shape[0] / image.shape[1])
        image = cv2.resize(image, (width, height))
        cv2.putText(image, f"t={frame / fps:.2f}", (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        tiles.append(image)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return len(tiles)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video")
    parser.add_argument("out")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=499)
    parser.add_argument("--step", type=int, default=25)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--crop", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    args = parser.parse_args()
    n = sheet(args.video, args.out, args.start, args.stop, args.step, args.cols, args.width,
              tuple(args.crop) if args.crop else None)
    print(args.out, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
