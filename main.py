from flask import Flask, request, render_template, send_file, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy #  Digunakan mengatur dan berinteraksi dengan basis data MySQL.
from io import BytesIO
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, String, LargeBinary

import subprocess
import os
import MySQLdb

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/datameteranair'
db = SQLAlchemy(app)

class imagedetectionresult(db.Model):
    __tablename__ = 'imagedetectionresult'
    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    detection_result = Column(String(255))
    image_data = Column(LargeBinary)
    timestamp = Column(String(255))

@app.route('/')
def index():
    try:
        db.session.query("1").from_statement("SELECT 1").all()
        db_connected = True
    except Exception as e:
        db_connected = False

    return render_template('index.html', result_image=None, result_message=None, db_connected=db_connected)

@app.route('/image/<path:file_path>', methods=['GET'])
def ambil_image(file_path):
    result_gambar_folder = 'Templates/image/'
    full_path = os.path.join(result_gambar_folder, file_path)

    if os.path.exists(full_path):
        return send_from_directory(result_gambar_folder, file_path)
    else:
        return "Konten tidak ditemukan"

@app.route('/show-results', methods=['GET'])
def show_results():
    results = imagedetectionresult.query.all()
    return render_template('index.html', results=results)

@app.route('/output/<image_name>', methods=['GET'])
def ambil_gambar(image_name):
    result_image_folder = 'output/exp/'
    if os.path.exists(os.path.join(result_image_folder, image_name)):
        return send_file(os.path.join(result_image_folder, image_name), as_attachment=True)
    else:
        return "Gambar tidak ditemukan"

@app.route('/detect', methods=['POST'])
def detect_image():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        image_filename = secure_filename(uploaded_file.filename)
        image_path = os.path.join('input', image_filename)
        uploaded_file.save(image_path)

        command = ['python', 'yolov5/detect.py', '--weights', 'models/best.pt', '--source', image_path, '--imgsz', '640', '--conf-thres', '0.25', '--iou-thres', '0.45']

        try:
            result_message = subprocess.run(command, cwd=os.getcwd(), capture_output=True, text=True, check=True).stdout.strip()
            detected_numbers = result_message

            detection_result = imagedetectionresult(
                filename=image_filename,
                detection_result=detected_numbers,
                image_data=None,
            )
            db.session.add(detection_result)
            db.session.commit()

            response_data = {
                "result_image": image_filename,
                "result_message": detected_numbers
            }
            return jsonify(response_data)
        except subprocess.CalledProcessError as e:
            error_message = str(e.output)
            return jsonify({"error": error_message})
        except Exception as e:
            error_message = str(e)
            return jsonify({"error": error_message})
    else:
        return jsonify({"result_image": "Belum Ada", "result_message": "Belum Ada"})

if __name__ == '__main__':
    app.run(debug=False)
