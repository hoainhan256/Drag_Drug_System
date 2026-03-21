import json
import requests
import io
from PIL import Image
from itertools import combinations
from mongoengine import Q
from django.shortcuts import render
from django.http import JsonResponse
from .vector_service import DrugVectorDB
from .models import DrugMonograph, DrugInteraction

vector_db = DrugVectorDB()

def index(request):
    return render(request, 'home/home.html')

def process_drug_image(request):
    if request.method == 'POST':
        user_text = request.POST.get('user_text', '').strip()
        image_files = request.FILES.getlist('images')

        all_input_texts = []
        
        if user_text:
            all_input_texts.append(user_text)

        for image_file in image_files:
            image_file.seek(0) 
            try:
                # ==========================================
                # BẮT ĐẦU MODULE XỬ LÝ & TIỀN NÉN ẢNH
                # ==========================================
                img = Image.open(image_file)
                
                # Chuyển đổi sang RGB nếu ảnh có kênh alpha (PNG) để an toàn lưu chuẩn JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Giới hạn kích thước cạnh dài nhất (1600px là mức tối ưu cho chữ nhỏ)
                max_dimension = 1600
                if max(img.size) > max_dimension:
                    # thumbnail() sẽ tự động giữ nguyên tỷ lệ khung hình (aspect ratio)
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Lưu ảnh đã xử lý vào bộ nhớ đệm RAM (không lưu ra ổ cứng)
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=90)
                img_io.seek(0)
                
                # Đóng gói lại thành định dạng file để gửi qua API
                file_name = image_file.name.rsplit('.', 1)[0] + '.jpg'
                files = {'file': (file_name, img_io.read(), 'image/jpeg')}
                # ==========================================

                print(f"Đang gửi ảnh {file_name} cho OCR xử lý (đã tối ưu)...")
                response = requests.post("http://127.0.0.1:8001/predict", files=files, timeout=60)
                
                if response.status_code == 200:
                    ocr_data = response.json()
                    for item in ocr_data.get('lines', []):
                        all_input_texts.append(item['text'])
            except Exception as e:
                print(f"Lỗi OCR hoặc xử lý ảnh: {e}")

        print(f"Dữ liệu gửi vào Vector DB: {all_input_texts}")

        if not all_input_texts:
            return JsonResponse({"status": "error", "message": "Không nhận diện được nội dung nào."})

        try:
            matched_drugs = vector_db.search_drug(all_input_texts)
            
            if not matched_drugs:
                return JsonResponse({"status": "error", "message": "Không tìm thấy hoạt chất nào khớp với thông tin bạn cung cấp."})
            
            final_results = []
            valid_hoat_chats = []

            for match in matched_drugs:
                if match['confidence'] >= 60:
                    hoat_chat_name = match.get('matched_hoat_chat') 
                    if not hoat_chat_name:
                        continue
                        
                    if hoat_chat_name not in valid_hoat_chats:
                        valid_hoat_chats.append(hoat_chat_name)
                        
                    drug_info = DrugMonograph.objects(key_name__iexact=hoat_chat_name).first()
                    
                    if drug_info:
                        final_results.append({
                            "hoat_chat": hoat_chat_name,
                            "confidence": match['confidence'],
                            "has_monograph": True,
                            "details": {
                                "ten_hoat_chat": drug_info.ten_hoat_chat,
                                "chong_chi_dinh": drug_info.chong_chi_dinh,
                                "than_trong": drug_info.than_trong,
                                "tuong_tac_thuoc": drug_info.tuong_tac_thuoc,
                                "cac_truong_hop_cu_the": drug_info.cac_truong_hop_cu_the 
                            }
                        })
                    else:
                        print(f"[THÔNG BÁO] Nhận diện được '{hoat_chat_name}', nhưng chất này không có chuyên luận (chỉ dùng để check tương tác).")
                        final_results.append({
                            "hoat_chat": hoat_chat_name,
                            "confidence": match['confidence'],
                            "has_monograph": False, 
                            "details": None
                        })

            # ===== BẮT ĐẦU XỬ LÝ TƯƠNG TÁC THUỐC =====
            interactions = []
            if len(valid_hoat_chats) >= 2:
                pairs = list(combinations(valid_hoat_chats, 2))
                print(f"[DEBUG] Đang kiểm tra tương tác cho các cặp: {pairs}")
                
                for hc1, hc2 in pairs:
                    interaction = DrugInteraction.objects(
                        (Q(hoat_chat_1__icontains=hc1) & Q(hoat_chat_2__icontains=hc2)) | 
                        (Q(hoat_chat_1__icontains=hc2) & Q(hoat_chat_2__icontains=hc1))
                    ).first()
                    
                    if interaction:
                        is_exist = any(i['thuoc_1'] == interaction.hoat_chat_1 and i['thuoc_2'] == interaction.hoat_chat_2 for i in interactions)
                        if not is_exist:
                            interactions.append({
                                "thuoc_1": interaction.hoat_chat_1,
                                "thuoc_2": interaction.hoat_chat_2,
                                "hau_qua": interaction.hau_qua,
                                "co_che": interaction.co_che,
                                "xu_tri": interaction.xu_tri
                            })
            # =========================================

            return JsonResponse({
                "status": "success", 
                "results": final_results,
                "interactions": interactions
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {str(e)}"})
            
    return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})