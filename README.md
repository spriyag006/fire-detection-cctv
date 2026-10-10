# FireWatch
pip install -r requirements.txt
python manage.py makemigrations core && python manage.py migrate
python manage.py createsuperuser
python manage.py runserver            # daphne serves HTTP + WebSocket
# In /admin: add a Camera (source: 0, a video path, or rtsp://...) and Facilities (fire/ambulance/hospital with lat/lon + email)
python manage.py run_detector 1 --weights fire_smoke.pt   # separate terminal
# PostgreSQL: set DB_NAME, DB_USER, DB_PASSWORD, DB_HOST env vars
