"""
ocr_api.py — PaddleOCR FastAPI Service (PaddleOCR v3 / PaddleX OCRResult)
--------------------------------------------------------------------------
Cài đặt:
    pip install fastapi uvicorn paddlepaddle paddleocr python-multipart pillow

Chạy:
    uvicorn ocr_api:app --host 0.0.0.0 --port 8001 --reload
"""

import io
import logging
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from PIL import Image

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocr_api")

ocr_engine: PaddleOCR | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_engine
    logger.info("Đang tải mô hình PaddleOCR...")
    ocr_engine = PaddleOCR(lang="vi", det_limit_side_len=1600)
    logger.info("Tải mô hình thành công.")
    yield
    ocr_engine = None


app = FastAPI(
    title="PharmaScan OCR API",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def parse_ocr_result(result) -> list:
    """
    PaddleOCR v3 trả về: list chứa 1 OCRResult object (dict-like) với:
        result[0]['rec_texts']  — list các chuỗi văn bản
        result[0]['rec_scores'] — list các điểm confidence tương ứng
        result[0]['rec_polys']  — list tọa độ bounding box

    PaddleOCR v2 trả về: [ [ [box, (text, score)], ... ] ]
    """
    lines = []
    if not result:
        return lines

    page = result[0]  # Luôn lấy trang đầu tiên

    # ── PaddleOCR v3: OCRResult object (hoặc dict) có key rec_texts ──
    if hasattr(page, 'get') or isinstance(page, dict):
        rec_texts  = page.get("rec_texts",  [])
        rec_scores = page.get("rec_scores", [])
        rec_polys  = page.get("rec_polys",  [])

        for i, text in enumerate(rec_texts):
            score = rec_scores[i] if i < len(rec_scores) else 0.0
            box   = rec_polys[i].tolist() if i < len(rec_polys) else []
            lines.append({
                "text":       text,
                "confidence": round(float(score), 4),
                "box":        box,
            })

    # ── PaddleOCR v2: list of [box, (text, score)] ──
    elif isinstance(page, list):
        for item in page:
            if not item:
                continue
            box, (text, score) = item
            lines.append({
                "text":       text,
                "confidence": round(float(score), 4),
                "box":        box,
            })

    return lines


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # 1. Kiểm tra định dạng
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Định dạng không hỗ trợ: '{file.content_type}'. Chấp nhận: JPEG, PNG, WEBP, BMP, TIFF.",
        )

    # 2. Đọc & kiểm tra kích thước
    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File quá lớn. Giới hạn 10 MB.")

    # 3. Decode ảnh → numpy array
    try:
        image     = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        img_array = np.array(image)
    except Exception as exc:
        logger.error("Lỗi đọc ảnh: %s", exc)
        raise HTTPException(status_code=400, detail="Không thể đọc ảnh. File có thể bị hỏng.")

    # 4. Chạy OCR (v3 không dùng cls=True nữa)
    try:
        try:
            result = ocr_engine.ocr(img_array, cls=True)
        except TypeError:
            result = ocr_engine.ocr(img_array)
    except Exception as exc:
        logger.error("Lỗi OCR: %s", exc)
        raise HTTPException(status_code=500, detail="Lỗi xử lý OCR phía máy chủ.")

    # 5. Parse kết quả
    lines = parse_ocr_result(result)
    count = len(lines)
    avg_confidence = (
        round(sum(l["confidence"] for l in lines) / count, 4) if count > 0 else 0.0
    )
    full_text = "\n".join(l["text"] for l in lines)

    logger.info("OCR xong: %d dòng, confidence TB=%.3f", count, avg_confidence)

    return {
        "text":       full_text,
        "lines":      lines,
        "line_count": count,
        "confidence": avg_confidence,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": ocr_engine is not None}