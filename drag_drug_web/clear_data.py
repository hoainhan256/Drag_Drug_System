# Xoá toàn bộ dữ liệu trong database
import mongoengine
from home.models import DrugMonograph, DrugInteraction

# 1. Kết nối DB
mongoengine.connect(db='drag_drug', host='localhost', port=27017)

# 2. Xóa sạch dữ liệu trong 2 Collection
print("--- Đang dọn dẹp Database ---")
DrugMonograph.objects.delete()      # Xóa toàn bộ chuyên luận
DrugInteraction.objects.delete()    # Xóa toàn bộ tương tác
print("✅ Đã xóa sạch! Bây giờ bạn có thể chạy lại file import.")