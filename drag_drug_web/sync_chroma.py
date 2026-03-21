import json
import chromadb
from chromadb.utils import embedding_functions

def sync_interactions_to_chroma(json_path):
    # 1. Khởi tạo kết nối ChromaDB (Giống hệt vector_service.py)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="drug_monographs",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # 2. Đọc dữ liệu từ file tương tác
    print("Đang đọc file dữ liệu tương tác...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Tập hợp (set) để lưu tên hoạt chất đã tách, tự động loại bỏ trùng lặp nội bộ
    unique_drugs = set()

    # 3. Tiền xử lý: Tách chuỗi bằng '/' và ','
    for item in data:
        for key in ['hoat_chat_1', 'hoat_chat_2']:
            raw_string = item.get(key, '')
            # Đổi ',' thành '/' để gộp chung logic tách
            clean_string = raw_string.replace(',', '/')
            parts = clean_string.split('/')
            
            for part in parts:
                drug_name = part.strip()
                if drug_name:
                    unique_drugs.add(drug_name)

    # 4. Kiểm tra sự tồn tại trong ChromaDB
    existing_data = collection.get()
    existing_ids = set(existing_data['ids'])

    new_documents = []
    new_metadatas = []
    new_ids = []

    # 5. Lọc ra các hoạt chất CHƯA CÓ
    for drug in unique_drugs:
        drug_id = drug.lower()  # ID trong ChromaDB quy ước là chữ thường
        if drug_id not in existing_ids:
            new_documents.append(drug.lower())
            new_metadatas.append({"hoat_chat": drug}) # Lưu metadata là tên gốc viết hoa
            new_ids.append(drug_id)

    # 6. Nạp vào Vector DB
    if new_ids:
        print(f"Phát hiện {len(new_ids)} hoạt chất MỚI chưa có trong Vector DB.")
        print("Đang nạp dữ liệu...")
        collection.add(
            documents=new_documents,
            metadatas=new_metadatas,
            ids=new_ids
        )
        print("✅ Đã cập nhật xong Vector DB!")
    else:
        print("✅ Không có hoạt chất nào mới. Vector DB đã chứa đầy đủ.")

if __name__ == "__main__":
    sync_interactions_to_chroma('database_duoc_thu_final.json')