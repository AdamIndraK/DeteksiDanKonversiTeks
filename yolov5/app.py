import os
import sys
import cv2
import torch
from flask import Flask, request, jsonify
from pathlib import Path

# Impor fungsi yang dibutuhkan dari detect.py
from detect import select_device, DetectMultiBackend, non_max_suppression, scale_boxes, xyxy2xywh

# Buat instance Flask
app = Flask(__name__)

# Definisikan path model dan data
MODEL_PATH = Path('best.pt')  # Ganti dengan path model Anda
DATA_PATH = Path('data.yaml')  # Ganti dengan path dataset.yaml Anda

# Load model
device = select_device('0')  # Ganti dengan device yang sesuai
model = DetectMultiBackend(MODEL_PATH, device=device, dnn=False, data=DATA_PATH)
model.eval()

# Route API untuk deteksi
@app.route('/detect', methods=['POST'])
def detect():
    try:
        # Ambil gambar dari request
        file = request.files['image']
        if not file:
            return jsonify({'error': 'No image provided'}), 400

        # Baca gambar sebagai numpy array
        img = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_COLOR)

        # Lakukan deteksi pada gambar
        with torch.no_grad():
            img_tensor = torch.from_numpy(img).to(device)
            img_tensor = img_tensor.float() / 255.0
            img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)

            # Lakukan deteksi
            pred = model(img_tensor)

            # Lakukan non-maximum suppression
            pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)

        # Proses hasil deteksi
        results = []
        for det in pred[0]:
            xyxy = det[:4].cpu().numpy()
            xywh = xyxy2xywh(torch.tensor(xyxy).view(1, 4)).view(-1).tolist()
            label = int(det[5].item())
            confidence = float(det[4].item())

            results.append({
                'label': label,
                'confidence': confidence,
                'bounding_box': xywh
            })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)