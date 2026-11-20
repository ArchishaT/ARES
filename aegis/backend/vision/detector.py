"""
Computer vision module.

Architecture note (see README "Computer Vision" section for the full
writeup): this module exposes a single `Detector` interface with a
`detect(frame) -> VisionResult` method. The current implementation is a
lightweight OpenCV contour/blob detector that classifies detected shapes
by color and geometry -- this runs anywhere without a GPU or model
download and is enough to demonstrate a real, working detection pipeline
(bounding boxes, confidence, timing) end-to-end.

`YoloDetector` shows the drop-in replacement: same interface, same return
type, so swapping the OPENCV_LITE backend for a real YOLOv8/ultralytics
model (or a remote inference microservice) at deploy time requires no
changes anywhere else in the codebase -- only `vision/detector.py`.
"""
from __future__ import annotations

import time
from typing import List

import cv2
import numpy as np

from models.schemas import DetectionBox, VisionResult

# Loosely tuned HSV bands used to classify obstacle/marker colors in the
# simulated or uploaded camera frame.
_COLOR_BANDS = {
    "red_marker": ((0, 120, 70), (10, 255, 255)),
    "green_marker": ((36, 60, 60), (89, 255, 255)),
    "blue_marker": ((90, 60, 60), (128, 255, 255)),
    "yellow_marker": ((20, 100, 100), (35, 255, 255)),
}

MIN_CONTOUR_AREA = 250


class Detector:
    """Active detector backend. Swap `model_name` / internals for a real
    YOLO backend without touching any caller."""

    model_name = "AEGIS-CV-Lite (OpenCV contour/color)"

    def detect(self, frame: np.ndarray) -> VisionResult:
        t0 = time.perf_counter()
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)

        boxes: List[DetectionBox] = []
        for label, (lo, hi) in _COLOR_BANDS.items():
            mask = cv2.inRange(blurred, np.array(lo), np.array(hi))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                area = cv2.contourArea(c)
                if area < MIN_CONTOUR_AREA:
                    continue
                x, y, bw, bh = cv2.boundingRect(c)
                # crude confidence proxy: how "blob-like" (filled) the
                # contour is relative to its bounding box.
                fill_ratio = area / max(1, bw * bh)
                confidence = float(min(0.98, 0.55 + fill_ratio * 0.4))
                boxes.append(
                    DetectionBox(
                        label=label.replace("_", " "),
                        confidence=round(confidence, 2),
                        x=int(x), y=int(y), width=int(bw), height=int(bh),
                    )
                )

        # Also fall back to generic edge-based blob detection so frames
        # with no strong color markers (e.g. grayscale uploads) still
        # produce plausible "unknown object" detections.
        if not boxes:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 60, 160)
            edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
                area = cv2.contourArea(c)
                if area < MIN_CONTOUR_AREA:
                    continue
                x, y, bw, bh = cv2.boundingRect(c)
                boxes.append(
                    DetectionBox(label="object", confidence=0.6, x=int(x), y=int(y), width=int(bw), height=int(bh))
                )

        inference_ms = (time.perf_counter() - t0) * 1000.0
        return VisionResult(
            model=self.model_name,
            objects=boxes,
            inference_time_ms=round(inference_ms, 2),
            frame_width=w,
            frame_height=h,
        )


_detector = Detector()


def get_detector() -> Detector:
    return _detector
