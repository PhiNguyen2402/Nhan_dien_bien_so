from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2
from config import Config
from models import db, NhanVien, PhuongTien
from recognition import recognize_plate_from_image

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

@app.route('/api/recognize', methods=['POST'])
def recognize():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'Không có ảnh'}), 400

    # Giải mã ảnh base64
    image_data = base64.b64decode(data['image'].split(',')[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Gọi hàm nhận diện
    plate_text = recognize_plate_from_image(img)

    if not plate_text:
        return jsonify({'found': False, 'message': 'Không nhận diện được biển số.'})

    # Truy vấn database
    phuong_tien = PhuongTien.query.filter_by(bien_so=plate_text).first()

    if not phuong_tien or not phuong_tien.nhan_vien:
        return jsonify({
            'found': True,
            'bien_so': plate_text,
            'registered': False,
            'message': f'Biển số {plate_text} không được đăng ký cho nhân viên nào.'
        })

    # Trả về thông tin nhân viên
    nhan_vien_info = phuong_tien.nhan_vien.to_dict()
    return jsonify({
        'found': True,
        'bien_so': plate_text,
        'registered': True,
        'nhan_vien': nhan_vien_info
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)