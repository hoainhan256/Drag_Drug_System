import json
import mongoengine
from home.models import DrugMonograph, DrugInteraction # Sửa 'myapp' thành tên app django của bạn

# Kết nối MongoDB
mongoengine.connect(db='drag_drug', host='localhost', port=27017)

def import_drug_monographs(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    count = 0
    for item in data:
        for key_name, info in item.items():
            # Kiểm tra xem đã tồn tại chưa để tránh lỗi duplicate
            if not DrugMonograph.objects(key_name=key_name).first():
                DrugMonograph(
                    key_name=key_name,
                    ten_hoat_chat=info.get('ten_hoat_chat', ''),
                    ten_chung_quoc_te=info.get('ten_chung_quoc_te', ''),
                    ma_atc=info.get('ma_atc', ''),
                    ten_thuong_mai=info.get('ten_thuong_mai', ''),
                    chong_chi_dinh=info.get('chong_chi_dinh', ''),
                    than_trong=info.get('than_trong', ''),
                    tuong_tac_thuoc=info.get('tuong_tac_thuoc', ''),
                    cac_truong_hop_cu_the=info.get('cac_truong_hop_cu_the', {})
                ).save()
                count += 1
    print(f"✅ Đã import thành công {count} chuyên luận thuốc.")

def import_drug_interactions(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    count = 0
    for item in data:
        if not DrugInteraction.objects(interaction_id=item['id']).first():
            DrugInteraction(
                interaction_id=item['id'],
                hoat_chat_1=item.get('hoat_chat_1', ''),
                hoat_chat_2=item.get('hoat_chat_2', ''),
                co_che=item.get('co_che', ''),
                hau_qua=item.get('hau_qua', ''),
                xu_tri=item.get('xu_tri', ''),
                text_for_embedding=item.get('text_for_embedding', ''),
                metadata_info=item.get('metadata', {})
            ).save()
            count += 1
    print(f"✅ Đã import thành công {count} tương tác thuốc.")

if __name__ == "__main__":
    print("Bắt đầu import dữ liệu vào MongoDB...")
    import_drug_monographs('database_duoc_thu_final.json')
    import_drug_interactions('data_tuong_tac_rag.json')