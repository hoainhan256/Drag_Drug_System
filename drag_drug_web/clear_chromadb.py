import chromadb

# 1. Kết nối tới thư mục chứa ChromaDB của bạn
# Đảm bảo đường dẫn path="./chroma_db" trỏ đúng vào thư mục db của bạn
client = chromadb.PersistentClient(path="./chroma_db")

print("--- Đang dọn dẹp ChromaDB ---")

# Tên collection bạn đã định nghĩa trong DrugVectorDB là "drug_monographs"
collection_name = "drug_monographs"

try:
    # 2. Lệnh này sẽ xóa hoàn toàn collection và tất cả vector bên trong
    client.delete_collection(name=collection_name)
    print(f"✅ Đã xóa sạch collection '{collection_name}' trong ChromaDB!")
except ValueError:
    # Nếu collection chưa tồn tại (hoặc đã bị xóa), nó sẽ văng lỗi ValueError
    print(f"⚠️ Collection '{collection_name}' không tồn tại hoặc đã được làm sạch từ trước.")

print("✅ Đã dọn dẹp xong! Bây giờ bạn có thể chạy lại file import.")