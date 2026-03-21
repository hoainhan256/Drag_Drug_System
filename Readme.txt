Step 1: run API in folder "paddleOCR_API" with "uvicorn ocr_api:app --host 0.0.0.0 --port 8001 --reload"
Step 2: run web server in folder "drag_drug_web" with "python manage.py runserver 127.0.0.1:8000"
step 3: run Ngrok (if you want to open global server)
ex:"ngrok http --domain=falciform-paramountly-alaysia.ngrok-free.dev 8000" on my pc
