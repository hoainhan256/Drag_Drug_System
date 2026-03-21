# debug_ocr.py
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image

ocr = PaddleOCR(lang="vi")
img = np.array(Image.open("image/test1.jpg").convert("RGB"))

try:
    result = ocr.ocr(img, cls=True)
except TypeError:
    result = ocr.ocr(img)

print("=== TYPE ===", type(result))
print("=== LEN ===", len(result) if result else 0)
print("=== result[0] TYPE ===", type(result[0]) if result else "empty")
print("=== result[0] ===", result[0] if result else "empty")
print("=== FULL RAW ===")
print(result)