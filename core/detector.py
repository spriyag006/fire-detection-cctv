"""core/detector.py - YOLOX FireDetector + TemporalVerifier (complete file, just replace the old one)."""
from collections import deque

import torch
from django.conf import settings
from yolox.data.data_augment import ValTransform
from yolox.exp import get_exp
from yolox.utils import postprocess


class FireDetector:
    NAMES = ["smoke", "fire"]          # same order as YOLO class ids (0 smoke, 1 fire)

    def __init__(self, ckpt, conf=0.25, nms=0.45):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.exp = get_exp(settings.YOLOX_EXP, None)
        self.model = self.exp.get_model()
        self.model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=False)["model"])
        self.model.to(self.device).eval()
        self.pre, self.conf, self.nms = ValTransform(legacy=False), conf, nms

    @torch.no_grad()
    def detect(self, frame):
        """Returns list of (label, conf, (x1, y1, x2, y2))."""
        h, w = frame.shape[:2]
        size = self.exp.test_size
        ratio = min(size[0] / h, size[1] / w)
        img, _ = self.pre(frame, None, size)
        x = torch.from_numpy(img).unsqueeze(0).float().to(self.device)
        out = postprocess(self.model(x), self.exp.num_classes, self.conf, self.nms,
                          class_agnostic=True)[0]
        if out is None:
            return []
        res = []
        for r in out.cpu():
            box = tuple((r[:4] / ratio).int().tolist())
            res.append((self.NAMES[int(r[6])], float(r[4] * r[5]), box))
        return res


class TemporalVerifier:
    """Confirms fire only if >= FIRE_MIN_HITS of the last FIRE_WINDOW frames had a confident fire box."""

    def __init__(self):
        self.hist = deque(maxlen=settings.FIRE_WINDOW)

    def update(self, detections):
        hit = any(l == "fire" and c >= settings.FIRE_CONF for l, c, _ in detections)
        self.hist.append(hit)
        return len(self.hist) == self.hist.maxlen and sum(self.hist) >= settings.FIRE_MIN_HITS
