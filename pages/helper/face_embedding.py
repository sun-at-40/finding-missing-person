"""Face-identity embeddings (OpenCV YuNet detector + SFace recognizer).

MediaPipe landmarks describe face geometry/pose, not identity, so they cannot
reliably tell whether two photos show the same person. SFace embeddings can.
"""

import os
import urllib.request
from functools import lru_cache

import cv2
import numpy as np

_MODEL_DIR = "models"
_BASE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models"
_DET_FILE = "face_detection_yunet_2023mar.onnx"
_REC_FILE = "face_recognition_sface_2021dec.onnx"
_DET_URL = f"{_BASE_URL}/face_detection_yunet/{_DET_FILE}"
_REC_URL = f"{_BASE_URL}/face_recognition_sface/{_REC_FILE}"

# Cosine similarity at or above this means "same person" (SFace's published value).
SAME_PERSON_THRESHOLD = 0.363


def _ensure(path: str, url: str) -> str:
    if not os.path.exists(path):
        os.makedirs(_MODEL_DIR, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


@lru_cache(maxsize=1)
def _recognizer():
    path = _ensure(os.path.join(_MODEL_DIR, _REC_FILE), _REC_URL)
    return cv2.FaceRecognizerSF.create(path, "")


def _detect(bgr: np.ndarray):
    path = _ensure(os.path.join(_MODEL_DIR, _DET_FILE), _DET_URL)
    h, w = bgr.shape[:2]
    detector = cv2.FaceDetectorYN.create(path, "", (w, h), 0.7)
    _, faces = detector.detect(bgr)
    return [] if faces is None else list(faces)


def _to_bgr(rgb: np.ndarray) -> np.ndarray:
    if rgb.ndim == 2:
        rgb = np.stack([rgb] * 3, axis=-1)
    return cv2.cvtColor(np.ascontiguousarray(rgb[:, :, :3], dtype=np.uint8), cv2.COLOR_RGB2BGR)


def embed_face(rgb: np.ndarray, bbox=None, near=None):
    """Return a unit-length identity embedding, or None if no face is found.

    bbox: (x_min, y_min, x_max, y_max) pixels; only that region is searched.
    near: (x, y) pixel point; with several faces, pick the one closest to it
          (otherwise the largest face is used).
    """
    bgr = _to_bgr(rgb)
    if bbox is not None:
        x0, y0, x1, y1 = bbox
        bgr = bgr[y0:y1, x0:x1]
        if near is not None:
            near = (near[0] - x0, near[1] - y0)
    if bgr.size == 0:
        return None

    faces = _detect(bgr)
    if not faces:
        return None
    if near is not None:
        face = min(
            faces,
            key=lambda f: (f[0] + f[2] / 2 - near[0]) ** 2
            + (f[1] + f[3] / 2 - near[1]) ** 2,
        )
    else:
        face = max(faces, key=lambda f: f[2] * f[3])

    rec = _recognizer()
    feature = rec.feature(rec.alignCrop(bgr, face)).ravel().astype(np.float32)
    norm = np.linalg.norm(feature)
    return feature / norm if norm else None


@lru_cache(maxsize=256)
def _stored_embedding(path: str, mtime: float, near):
    rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    pt = None if near is None else (near[0] * rgb.shape[1], near[1] * rgb.shape[0])
    return embed_face(rgb, near=pt)


def stored_case_embedding(case_id: str, landmarks=None):
    """Embedding of a registered case's saved photo (None if unavailable).

    landmarks (flattened x,y,z, normalised) locate the registered face when the
    saved photo contains several people.
    """
    path = f"./resources/{case_id}.jpg"
    if not os.path.exists(path):
        return None
    near = None
    if landmarks is not None:
        pts = np.asarray(landmarks, dtype=float).reshape(-1, 3)
        near = (float(pts[:, 0].mean()), float(pts[:, 1].mean()))
    return _stored_embedding(path, os.path.getmtime(path), near)


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))
