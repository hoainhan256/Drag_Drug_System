import re
import unicodedata
from chromadb.utils import embedding_functions
import chromadb

import difflib
class DrugVectorDB:
    def __init__(self):
        # Sử dụng SentenceTransformer hỗ trợ cả tiếng Anh/Việt
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="drug_monographs",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"} 
        )

    def clean_text(self, text):
        """Tiền xử lý văn bản cực mạnh"""
        if not text: return ""
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.strip()

    def index_data(self, json_path):
        import json
        import os
        
        if not os.path.exists(json_path):
            print(f"LỖI: Không tìm thấy file {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []
        metadatas = []
        ids = []
        counter = 0

        for item in data:
            for key_name, info in item.items():
                raw_names = [
                    key_name,
                    info.get('ten_hoat_chat'),
                    info.get('ten_chung_quoc_te'),
                    info.get('ten_thuong_mai')
                ]
                names_to_index = set(filter(None, raw_names))

                for name in names_to_index:
                    cleaned_name = self.clean_text(name)
                    if len(cleaned_name) < 2: 
                        continue
                    
                    documents.append(cleaned_name)
                    metadatas.append({"hoat_chat": key_name.strip().upper()})
                    ids.append(f"id_{counter}")
                    counter += 1

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            print(f"Thành công! Đã nạp {counter} biến thể tên.")


    def search_drug(self, text_list, n_results=1):
        import difflib
        
        all_queries = []
        for raw_text in text_list:
            cleaned_phrase = self.clean_text(raw_text)
            if not cleaned_phrase: continue
            
            # 1. Lấy nguyên cụm gốc (Rất quan trọng cho từ ghép)
            all_queries.append(cleaned_phrase)
            
            # 2. Tách từ đơn
            words = cleaned_phrase.split()
            
            # 3. KỸ THUẬT N-GRAM: Ghép các từ đứng cạnh nhau
            # Ví dụ: "magnesi", "sulfat" -> "magnesi sulfat"
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    bigram = f"{words[i]} {words[i+1]}"
                    all_queries.append(bigram)

            # Vẫn giữ từ đơn để đề phòng (nhưng filter kỹ hơn)
            for w in words:
                if len(w) > 3 and not w.isdigit():
                    all_queries.append(w)
        
        unique_queries = list(set(all_queries))
        if not unique_queries: return []

        print(f"\n[DEBUG] Queries (đã gồm từ ghép): {unique_queries}")

        results = self.collection.query(
            query_texts=unique_queries,
            n_results=n_results,
            include=["metadatas", "distances", "documents"] 
        )

        final_matches = []
        for i in range(len(results['documents'])):
            query_item = unique_queries[i]
            for j in range(len(results['documents'][i])):
                dist = results['distances'][i][j]
                meta = results['metadatas'][i][j]
                doc_matched = results['documents'][i][j]
                
                if not meta: continue
                hoat_chat = meta['hoat_chat']
                vector_conf = max(0, 100 - (dist * 100))
                
                # Tính toán độ khớp mặt chữ
                string_ratio = difflib.SequenceMatcher(None, query_item, doc_matched).ratio()
                
                # LOGIC ƯU TIÊN TỪ GHÉP:
                # Nếu query là từ ghép (có dấu cách) và khớp hoàn toàn với DB
                is_perfect_match = (query_item == doc_matched)
                is_substring = (doc_matched in query_item) or (query_item in doc_matched)

                # Điều kiện:
                # 1. Vector score phải cao (>75)
                # 2. Nếu là từ ghép thì ưu tiên hàng đầu, nếu là từ đơn thì string_ratio phải cực cao (>85%)
                if vector_conf > 75:
                    if is_perfect_match or (is_substring and len(query_item) > 8):
                        # Thưởng điểm cho từ ghép nhưng giới hạn tối đa 100
                        actual_conf = min(100.0, vector_conf + 5) 
                        final_matches.append({
                            "matched_hoat_chat": hoat_chat, 
                            "confidence": actual_conf
                        })
                    elif string_ratio > 0.8:
                        # Từ đơn khớp tốt
                        actual_conf = min(100.0, (vector_conf + string_ratio * 100) / 2)
                        final_matches.append({
                            "matched_hoat_chat": hoat_chat, 
                            "confidence": actual_conf
                        })

        # Sắp xếp và lấy kết quả tốt nhất
        unique_results = {}
        for res in final_matches:
            name = res['matched_hoat_chat']
            if name not in unique_results or res['confidence'] > unique_results[name]['confidence']:
                unique_results[name] = res

        return sorted(unique_results.values(), key=lambda x: x['confidence'], reverse=True)