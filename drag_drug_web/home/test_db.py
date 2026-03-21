from home.vector_service import DrugVectorDB

db = DrugVectorDB()
# Thử tìm một từ khóa bị sai chính tả nhẹ xem Vector DB có nhận ra không
results = db.search_drug(["Abacavirr", "Glucobay 50"])

for r in results:
    print(f"OCR: {r['original_ocr']} => Khớp với: {r['matched_hoat_chat']} (Độ tin cậy: {r['confidence']:.2f})")