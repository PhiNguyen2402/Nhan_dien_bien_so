from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2

# --- SỬA Ở ĐÂY ---
# 1. Import hàm "nhạc trưởng" (Khối 4) từ file của bạn
try:
    # (Giả định file logic của bạn tên là recognition.py)
    from recognition import process_vehicle_entry
except ImportError:
    print("LỖI: Không tìm thấy file 'recognition.py'.")
    print("Hãy chắc chắn file chứa code logic CSDL của bạn tên là 'recognition.py'")
    process_vehicle_entry = None 

app = Flask(__name__)
CORS(app)

@app.route('/api/recognize', methods=['POST'])
def recognize():
    if not process_vehicle_entry:
         return jsonify({'error': 'Lỗi server: Không tải được mô-đun nhận diện.'}), 500

    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'Không có ảnh'}), 400

    # Giải mã ảnh base64
    try:
        image_data = base64.b64decode(data['image'].split(',')[1])
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Không thể giải mã ảnh")
    except Exception as e:
        print(f"Lỗi giải mã ảnh base64: {e}")
        return jsonify({'error': 'Dữ liệu ảnh không hợp lệ'}), 400

    # --- SỬA Ở ĐÂY ---
    # 3. Gọi hàm "nhạc trưởng" (Khối 4)
    print("--- Flask Server: Đang gọi process_vehicle_entry ---")
    result = process_vehicle_entry(img)
    print("--- Flask Server: Đã thực thi xong process_vehicle_entry ---")
    # --------------------

    # 4. Xử lý kết quả trả về từ hàm mới
    if not result:
        # Trường hợp này là "KHÔNG NHẬN DIỆN ĐƯỢC BIỂN SỐ."
        return jsonify({
            'found': False, 
            'registered': False,
            'message': 'Không nhận diện được biển số.'
        })

    # --- SỬA Ở ĐÂY ---
    # 5. Unpack 4 giá trị (thay vì 3)
    plate_text, phuongtien_id, nhan_vien_id, nhan_vien_info = result
    # ------------------
    
    if not nhan_vien_id:
        # Trường hợp "BIỂN CHƯA ĐĂNG KÝ" (xe khách)
        return jsonify({
            'found': True,
            'bien_so': plate_text,
            'registered': False,
            'message': f'Biển số {plate_text} chưa được đăng ký.'
        })

    # Trường hợp "ĐÃ LƯU" (xe nhân viên)
    # --- SỬA Ở ĐÂY ---
    # Trả về thêm đối tượng 'nhan_vien' chứa thông tin chi tiết
    return jsonify({
        'found': True,
        'bien_so': plate_text,
        'registered': True,
        'message': f'Đã ghi nhận xe nhân viên: {nhan_vien_info.get("ho_ten")}', # Cập nhật message
        'nhan_vien': nhan_vien_info # <-- THÔNG TIN CHI TIẾT ĐỂ HIỂN THỊ
    })
    # ------------------

if __name__ == '__main__':
    # Chạy server ở port 5000
    app.run(debug=True, port=5000)

