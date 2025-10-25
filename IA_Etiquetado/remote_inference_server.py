# IA_Etiquetado/remote_inference_server.py
"""
Remote Inference Server for VisiFruit
====================================

FastAPI server that runs YOLOv8 inference on a GPU laptop/PC and serves
results over HTTP to Raspberry Pi clients. Designed for low-latency use.

Endpoints:
- GET  /health  -> { status: "ok", device: "cuda|cpu", model: "path" }
- POST /infer   -> multipart/form-data with field "image" (JPEG/PNG bytes)
                   form fields: imgsz, conf, iou, max_det, class_names_json
                   returns detections and timing metrics

Run:
  pip install ultralytics fastapi uvicorn[standard] python-multipart opencv-python
  # For CUDA PyTorch, install matching wheels for your GPU/CUDA version
  # Example (CUDA 12.x): https://pytorch.org/get-started/locally/

  python IA_Etiquetado/remote_inference_server.py --model weights/best.pt --host 0.0.0.0 --port 9000
"""

from __future__ import annotations
import argparse
import json
import time
from typing import Any, Dict, List

import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except Exception:
    ULTRALYTICS_AVAILABLE = False

app = FastAPI(title="VisiFruit Remote Inference Server", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelRunner:
    def __init__(self, model_path: str):
        if not ULTRALYTICS_AVAILABLE:
            raise RuntimeError("Ultralytics is not installed. pip install ultralytics")
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.model_path = model_path
        self.model = YOLO(model_path)
        # Move model to device (Ultralytics handles device parameter in predict, but to be explicit)
        try:
            if self.device == "cuda":
                self.model.to("cuda")
        except Exception:
            pass
        # Optional: warmup
        try:
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.model.predict(dummy, imgsz=640, conf=0.1, iou=0.1, max_det=1, device=self.device, verbose=False)
        except Exception:
            pass

    def infer(self, img: np.ndarray, imgsz: int, conf: float, iou: float, max_det: int, class_names: List[str] | None) -> Dict[str, Any]:
        start_inf = time.perf_counter()
        results = self.model.predict(
            img,
            imgsz=int(imgsz),
            conf=float(conf),
            iou=float(iou),
            max_det=int(max_det),
            device=self.device,
            verbose=False,
        )
        inf_ms = (time.perf_counter() - start_inf) * 1000.0

        dets: List[Dict[str, Any]] = []
        if results and len(results) > 0:
            r0 = results[0]
            boxes = r0.boxes
            names_map = r0.names if hasattr(r0, "names") and r0.names else {}
            for i in range(len(boxes)):
                try:
                    xyxy = boxes.xyxy[i].tolist()
                    conf_i = float(boxes.conf[i].item() if hasattr(boxes.conf[i], 'item') else boxes.conf[i])
                    cls_i = int(boxes.cls[i].item() if hasattr(boxes.cls[i], 'item') else boxes.cls[i])
                    # Prefer provided class_names to keep consistency with client config
                    if class_names and cls_i < len(class_names):
                        cls_name = class_names[cls_i]
                    else:
                        cls_name = names_map.get(cls_i, str(cls_i))
                    dets.append({
                        "class_id": cls_i,
                        "class_name": cls_name,
                        "confidence": conf_i,
                        "bbox": [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                    })
                except Exception:
                    continue
        return {"detections": dets, "inference_ms": inf_ms}


# Global model runner holder
runner: ModelRunner | None = None


@app.on_event("startup")
async def _startup_event():
    # Model is loaded in main() before uvicorn.run for CLI; keep no-op here to support other runners
    pass


@app.get("/health")
async def health() -> JSONResponse:
    device = runner.device if runner else ("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu")
    return JSONResponse({"status": "ok", "device": device, "model": runner.model_path if runner else None})


@app.post("/infer")
async def infer(
    image: UploadFile = File(...),
    imgsz: int = Form(640),
    conf: float = Form(0.5),
    iou: float = Form(0.45),
    max_det: int = Form(100),
    class_names_json: str = Form(None)
) -> JSONResponse:
    if runner is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    pre_t0 = time.perf_counter()
    data = await image.read()
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    pre_ms = (time.perf_counter() - pre_t0) * 1000.0

    # Parse class names override
    class_names = None
    if class_names_json:
        try:
            class_names = json.loads(class_names_json)
        except Exception:
            class_names = None

    # Inference
    out = runner.infer(img, imgsz=imgsz, conf=conf, iou=iou, max_det=max_det, class_names=class_names)

    # Post time (trivial here)
    total_ms = pre_ms + out.get("inference_ms", 0.0)

    resp = {
        "detections": out.get("detections", []),
        "pre_ms": pre_ms,
        "inference_ms": out.get("inference_ms", 0.0),
        "post_ms": 0.0,
        "total_ms": total_ms,
        "device": runner.device,
    }
    return JSONResponse(resp)


def main():
    parser = argparse.ArgumentParser(description="VisiFruit Remote Inference Server")
    parser.add_argument("--model", type=str, default="weights/best.pt", help="Path to YOLO model (.pt)")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    global runner
    runner = ModelRunner(args.model)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
