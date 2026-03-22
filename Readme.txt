Step 1: run API in folder "paddleOCR_API" with "uvicorn ocr_api:app --host 0.0.0.0 --port 8001 --reload"
Step 2: run web server in folder "drag_drug_web" with "python manage.py runserver 127.0.0.1:8000" after run sync_chroma.py and import_to_mongodb.py, import_chuyen_luan_chroma.py
step 3: run Ngrok (if you want to open global server)
ex:"ngrok http --domain=falciform-paramountly-alaysia.ngrok-free.dev 8000" on my pc

Link GitHub: https://github.com/hoainhan256/Drag_Drug_System.git
Link Video: https://drive.google.com/drive/folders/1BkpBBBKPNgnfjL0anYXAU6czmYoze4xC?usp=sharing