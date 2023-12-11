import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app2 import imagedetectionresult

# Konfigurasi SQLAlchemy
db_uri = 'mysql://root:@localhost/datameteranair'
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

def check_and_detect_images():
    session = Session()
    images_to_detect = session.query(imagedetectionresult).filter(imagedetectionresult.detection_result == None).all()

    for image in images_to_detect:
        image_filename = image.filename
        image_path = f'input/{image_filename}'

        if image_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            detection_api_url = 'http://127.0.0.1:5000/detect'
            try:
                response = requests.post(detection_api_url, files={'file': open(image_path, 'rb')})
                response.raise_for_status()  # Check for HTTP request errors

                detected_numbers = response.json().get('detected_numbers')

                # Simpan hasil deteksi ke database
                if detected_numbers:
                    image.detection_result = detected_numbers
                    session.commit()
                else:
                    # Hapus entry yang sudah di-deteksi
                    session.delete(image)
                    session.commit()
                   
            except requests.exceptions.RequestException as e:
                print(f"Error in API request: {e}")
            except Exception as e:
                print(f"Error during detection: {e}")

    session.close()

if __name__ == '__main__':
    while True:
        check_and_detect_images()
        print("Pemeriksaan gambar selesai. Menunggu 1 menit sebelum pemeriksaan berikutnya...")
        time.sleep(60)
