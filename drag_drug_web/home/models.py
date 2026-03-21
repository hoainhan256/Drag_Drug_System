# home/models.py
from mongoengine import Document, StringField, DictField

class DrugMonograph(Document):
    # Khai báo tên collection và tạo Index cho trường tìm kiếm chính
    meta = {
        'collection': 'drug_monographs', 
        'indexes': ['key_name']
    }
    
    key_name = StringField(required=True, unique=True)
    ten_hoat_chat = StringField()
    ten_chung_quoc_te = StringField()
    ma_atc = StringField()
    ten_thuong_mai = StringField()
    chong_chi_dinh = StringField()
    than_trong = StringField()
    tuong_tac_thuoc = StringField()
    cac_truong_hop_cu_the = DictField() # MongoDB sinh ra để lưu cái này!

class DrugInteraction(Document):
    meta = {
        'collection': 'drug_interactions', 
        'indexes': ['hoat_chat_1', 'hoat_chat_2'] # Index để sau này query tương tác nhanh
    }
    
    interaction_id = StringField(unique=True)
    hoat_chat_1 = StringField()
    hoat_chat_2 = StringField()
    co_che = StringField()
    hau_qua = StringField()
    xu_tri = StringField()
    text_for_embedding = StringField()
    metadata_info = DictField()