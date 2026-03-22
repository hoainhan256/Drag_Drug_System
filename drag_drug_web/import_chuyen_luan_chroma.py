import json
import chromadb
import unicodedata
import re
from chromadb.utils import embedding_functions

def clean_text(text):
    """Hàm tiền xử lý làm phẳng chữ: Bỏ dấu, bỏ ký tự đặc biệt, in thường"""
    if not text: return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def import_monographs_to_chroma(json_path):
    # 1. Khởi tạo kết nối ChromaDB
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="drug_monographs",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # 2. Đọc dữ liệu từ file JSON chuyên luận
    print(f"Đang đọc file dữ liệu: {json_path} ...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc file JSON: {e}")
        return

    # Sử dụng Dictionary để map: { "tên_đã_clean": "TÊN_CHUYÊN_LUẬN_GỐC" }
    # Điều này giúp khi search trúng tên thương mại, nó vẫn trả về Tên gốc để query Mongo
    unique_drugs_map = {}

    # 3. Trích xuất và phân tách dữ liệu
    for item in data:
        # Trong file này, mỗi item là một dict có 1 key duy nhất là Tên hoạt chất gốc (vd: "ABACAVIR")
        for main_key, info in item.items():
            
            # Danh sách tạm chứa tất cả các tên thô cần xử lý của chuyên luận này
            raw_names_to_process = []
            
            # a. Lấy key chính gốc
            raw_names_to_process.append(main_key)
            
            # b. Lấy ten_hoat_chat (Ngăn cách bởi dấu phẩy)
            ten_hoat_chat = info.get('ten_hoat_chat', '')
            if ten_hoat_chat:
                raw_names_to_process.extend(ten_hoat_chat.split(','))
                
            # c. Lấy ten_chung_quoc_te (Ngăn cách bởi dấu phẩy)
            ten_chung_quoc_te = info.get('ten_chung_quoc_te', '')
            if ten_chung_quoc_te:
                raw_names_to_process.extend(ten_chung_quoc_te.split(','))
                
            # d. Lấy ten_thuong_mai (Ngăn cách bởi dấu chấm phẩy)
            ten_thuong_mai = info.get('ten_thuong_mai', '')
            if ten_thuong_mai:
                raw_names_to_process.extend(ten_thuong_mai.split(';'))

            # Xử lý làm sạch toàn bộ danh sách tên vừa thu thập được
            for raw_name in raw_names_to_process:
                cleaned_name = clean_text(raw_name)
                
                # Chỉ lấy những tên có ý nghĩa (độ dài >= 2)
                if len(cleaned_name) >= 2:
                    # Map tên biến thể này về key gốc (main_key)
                    # Việc dùng dict sẽ tự động loại bỏ trùng lặp nếu có 2 tên giống hệt nhau
                    if cleaned_name not in unique_drugs_map:
                        unique_drugs_map[cleaned_name] = main_key.strip().upper()

    print(f"✅ [DEBUG] Đã trích xuất và phân tách thành {len(unique_drugs_map)} tên gọi khác nhau (bao gồm tên thương mại, tên quốc tế...).")

    if len(unique_drugs_map) == 0:
        print("❌ LỖI: Không trích xuất được tên nào. Hãy kiểm tra lại file JSON.")
        return

    # 4. Chuẩn bị Batch để nạp vào Vector DB
    new_documents = []
    new_metadatas = []
    new_ids = []

    # Duyệt qua các item trong Dictionary
    for i, (cleaned_name, original_key) in enumerate(unique_drugs_map.items()):
        new_documents.append(cleaned_name)
        new_metadatas.append({"hoat_chat": original_key}) # Lưu tên gốc để Web có thể truy vấn MongoDB
        
        # ID phải là string duy nhất không chứa khoảng trắng lạ
        safe_id = f"mono_{i}_{cleaned_name.replace(' ', '_')}" 
        new_ids.append(safe_id)

    # Nạp dữ liệu theo lô (batch) để tránh quá tải RAM nếu file quá lớn
    batch_size = 5000
    total_batches = (len(new_documents) // batch_size) + 1

    print(f" Bắt đầu nạp {len(new_documents)} vectors vào ChromaDB (chia làm {total_batches} đợt)...")
    
    for i in range(0, len(new_documents), batch_size):
        end_idx = min(i + batch_size, len(new_documents))
        
        # Dùng UPSERT: Tự động ghi đè nếu trùng ID, thêm mới nếu chưa có
        collection.upsert(
            documents=new_documents[i:end_idx],
            metadatas=new_metadatas[i:end_idx],
            ids=new_ids[i:end_idx]
        )
        print(f"   -> Đã nạp đợt { (i // batch_size) + 1 }/{ total_batches } ({end_idx}/{len(new_documents)} items)")

    print("✅ HOÀN TẤT! Đã import toàn bộ dữ liệu chuyên luận vào ChromaDB thành công.")

if __name__ == "__main__":
    # LƯU Ý: VUI LÒNG TẮT SERVER DJANGO TRƯỚC KHI CHẠY FILE NÀY
    import_monographs_to_chroma('database_duoc_thu_final.json')