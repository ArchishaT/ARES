"""
Frame preprocessing utilities shared by upload and simulated-camera paths.
"""
from __future__ import annotations

import numpy as np
import cv2


def bytes_to_frame(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image data.")
    return frame


def resize_max_dim(frame: np.ndarray, max_dim: int = 640) -> np.ndarray:
    h, w = frame.shape[:2]
    scale = max_dim / max(h, w)
    if scale >= 1:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)))


def render_simulated_frame(env, robot, width: int = 480, height: int = 320) -> np.ndarray:
    """Renders a synthetic top-down 'camera' frame from the current
    simulation state, so the Vision page has something live to detect
    even without an uploaded image. Obstacles are drawn as colored
    markers so the color-based detector has real signal to find."""
    frame = np.full((height, width, 3), (30, 28, 26), dtype=np.uint8)
    sx = width / env.width_m
    sy = height / env.height_m

    palette = [(60, 60, 220), (60, 200, 60), (220, 150, 40), (40, 210, 230)]
    for i, obs in enumerate(env.obstacles[:12]):
        px, py = int(obs.x * sx), int(obs.y * sy)
        color = palette[i % len(palette)]
        cv2.circle(frame, (px, py), max(4, int(obs.radius * sx)), color, -1)

    rx, ry = int(robot.x * sx), int(robot.y * sy)
    cv2.circle(frame, (rx, ry), 6, (240, 240, 240), 2)
    return frame
