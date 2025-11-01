import cv2
import numpy as np
import re
import pytesseract
import mysql.connector  # <<< THÊM MỚI: Thư viện MySQL
import datetime         # <<< THÊM MỚI: Thư viện thời gian

# =======================================================
# KHỐI 1: CẤU HÌNH
# =======================================================

# --- Cấu hình Tesseract ---
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception as e:
    print("Lỗi: Không tìm thấy Tesseract. Hãy chắc chắn bạn đã cài đặt Tesseract OCR và cập nhật đúng đường dẫn.")
    print(e)

# --- Cấu hình CSDL MySQL ---
# !!! QUAN TRỌNG: Hãy điền thông tin CSDL của bạn vào đây
MYSQL_CONFIG = {
    'host': 'localhost',        # Hoặc IP/Domain của server
    'user': 'root',    # Tên người dùng MySQL (ví dụ: 'root')
    'password': 'tanphi1040',  # Mật khẩu của bạn
    'database': 'cong_ty_db' # Tên CSDL (Schema) bạn đã tạo
}

# =======================================================
# KHỐI 2: XỬ LÝ ẢNH VÀ OCR (Code gốc của bạn)
# =======================================================

def find_license_plate(image):
    """
    Sử dụng OpenCV để tìm vùng ảnh có khả năng là biển số xe.
    Trả về vùng ảnh đã được cắt và một flag cho biết loại biển (dài hay vuông).
    """
    if image is None:
        return None, None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(bfilter, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

    location = None
    plate_type = None # Sẽ là 'long' hoặc 'square'
    
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            (x, y, w, h) = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            if aspect_ratio > 2.5 and aspect_ratio < 5.0:
                location = approx
                plate_type = 'long' # Biển dài
                break
            elif aspect_ratio > 1.2 and aspect_ratio < 2.2:
                location = approx
                plate_type = 'square' # Biển vuông
                break
    
    if location is None:
        print("Không tìm thấy contour nào phù hợp với biển số.")
        return None, None

    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [location], 0, 255, -1)
    
    (x_coords, y_coords) = np.where(mask == 255)
    (x1, y1) = (np.min(x_coords), np.min(y_coords))
    (x2, y2) = (np.max(x_coords), np.max(y_coords))
    padding = 5
    cropped_image = gray[max(0, x1-padding):min(x2+padding, gray.shape[0]), max(0, y1-padding):min(y2+padding, gray.shape[1])]

    return cropped_image, plate_type

def ocr_from_plate(plate_image, plate_type):
    """
    Sử dụng Pytesseract để đọc ký tự, với logic được tối ưu cho từng loại biển.
    """
    try:
        # Nếu là biển vuông (2 dòng)
        if plate_type == 'square' and plate_image is not None:
            height, width = plate_image.shape
            
            # Cắt đôi ảnh
            top_half = plate_image[0:height//2, :]
            bottom_half = plate_image[height//2:, :]

            # Cấu hình cho đọc một dòng văn bản
            config_single_line = r'--oem 3 --psm 7 -l vie+eng'
            
            # Đọc riêng từng nửa
            top_text = pytesseract.image_to_string(top_half, config=config_single_line)
            bottom_text = pytesseract.image_to_string(bottom_half, config=config_single_line)
            
            return f"{top_text.strip()} {bottom_text.strip()}" # Ghép kết quả

        # Nếu là biển dài (1 dòng) hoặc không xác định được loại
        else:
            config = r'--oem 3 --psm 7 -l vie+eng'
            return pytesseract.image_to_string(plate_image, config=config).strip()

    except Exception as e:
        print(f"Lỗi trong quá trình OCR: {e}")
        return ""

def clean_plate_text(text):
    """Dọn dẹp và chuẩn hóa chuỗi biển số."""
    text = text.upper()
    # Loại bỏ các ký tự nhiễu nhưng giữ lại chữ, số
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def recognize_plate_from_image(image_np):
    """Hàm chính điều phối việc nhận diện."""
    try:
        # Bước 1: Tìm biển số và xác định loại biển (dài hay vuông)
        plate_region, plate_type = find_license_plate(image_np)
        
        if plate_region is None or plate_region.size == 0:
            print("Không phát hiện được vùng biển số, thử OCR toàn bộ ảnh...")
            plate_region = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            plate_type = 'unknown' # Không xác định

        # Bước 2: Đọc ký tự từ vùng ảnh với logic phù hợp
        raw_text = ocr_from_plate(plate_region, plate_type)
        
        # Bước 3: Dọn dẹp và chuẩn hóa text
        plate_text = clean_plate_text(raw_text)
        
        return plate_text
    except Exception as e:
        print(f"Lỗi trong quá trình nhận diện: {e}")
        return None

# =======================================================
# KHỐI 3: XỬ LÝ CSDL MYSQL (PHẦN ĐÃ SỬA/THÊM)
# =======================================================

# --- HÀM SỬA ĐỔI ---
def find_vehicle_info(plate_text):
    """
    Truy vấn CSDL MySQL để tìm thông tin xe VÀ thông tin nhân viên.
    Trả về: (phuongtien_id, nhan_vien_id, nhan_vien_info_dict)
    """
    if not plate_text:
        return None, None, None # Trả về 3 giá trị
    
    conn = None # Khởi tạo conn
    try:
        # Kết nối đến server MySQL bằng cấu hình ở Khối 1
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print(">>> Kết nối CSDL (find_vehicle_info) thành công.") # Log kết nối
        
        # Dùng dictionary=True để lấy kết quả dạng dict
        cursor = conn.cursor(dictionary=True) 
        
        # 1. Truy vấn vào bảng phuongtien
        cursor.execute("SELECT id, nhan_vien_id FROM phuongtien WHERE bien_so = %s", (plate_text,))
        result = cursor.fetchone() 
        
        if result:
            phuongtien_id = result['id']
            nhan_vien_id = result['nhan_vien_id']
            
            # 2. Nếu tìm thấy nhan_vien_id, lấy thêm thông tin nhân viên
            if nhan_vien_id:
                # (Giả định các cột của bạn là ho_ten, chuc_vu, ma_nhan_vien)
                cursor.execute("SELECT ho_ten, chuc_vu, ma_nhan_vien, phong_ban FROM nhanvien WHERE id = %s", (nhan_vien_id,))
                nhan_vien_info = cursor.fetchone() # Lấy thông tin nhân viên
                
                if nhan_vien_info:
                    # Trả về đầy đủ thông tin
                    return phuongtien_id, nhan_vien_id, nhan_vien_info
            
            # Nếu xe có trong CSDL nhưng không gán cho nhân viên nào
            return phuongtien_id, None, None
            
        else:
            # Không tìm thấy xe này trong CSDL (xe khách)
            return None, None, None
            
    except mysql.connector.Error as e:
        print(f"Lỗi khi truy vấn MySQL: {e}")
        return None, None, None
    finally:
        # Đảm bảo luôn đóng kết nối
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- HÀM NÀY GIỮ NGUYÊN ---
def log_entry_time(plate_text, phuongtien_id, nhan_vien_id):
    """
    Lưu thông tin vào bảng lich_su_vao_ra trên MySQL.
    Hàm này CHỈ ĐƯỢC GỌI KHI ĐÃ XÁC NHẬN LÀ NHÂN VIÊN.
    """
    conn = None # Khởi tạo conn
    try:
        current_time = datetime.datetime.now()
        
        # Kết nối đến server MySQL
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print(">>> Kết nối CSDL (log_entry_time) thành công.") # Log kết nối
        
        cursor = conn.cursor()
        
        # (Giả định bạn đã tạo bảng 'lich_su_vao_ra' như đã trao đổi)
        sql_insert = """
            INSERT INTO lich_su_vao_ra 
            (thoi_gian_vao, bien_so_xe, phuongtien_id, nhan_vien_id) 
            VALUES (%s, %s, %s, %s)
        """
        values = (current_time, plate_text, phuongtien_id, nhan_vien_id)
        
        cursor.execute(sql_insert, values)
        conn.commit() # Xác nhận lưu thay đổi
        
        # Log đã lưu
        print(f"ĐÃ LƯU: Xe nhân viên (BSX: {plate_text}) vào cổng lúc {current_time}")
            
    except mysql.connector.Error as e:
        print(f"Lỗi khi lưu log vào MySQL: {e}")
    finally:
        # Đảm bảo luôn đóng kết nối
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# =======================================================
# KHỐI 4: HÀM ĐIỀU PHỐI CHÍNH (LOGIC MỚI THEO YÊU CẦU)
# =======================================================

# --- HÀM SỬA ĐỔI ---
def process_vehicle_entry(image_path_or_np_array):
    """
    Hàm chính điều phối toàn bộ quy trình:
    1. Đọc ảnh.
    2. Nhận diện biển số.
    3. Tra cứu thông tin.
    4. Ghi log (CHỈ KHI LÀ NHÂN VIÊN).
    Trả về: (plate_text, phuongtien_id, nhan_vien_id, nhan_vien_info)
    """
    
    # 1. Đọc ảnh
    if isinstance(image_path_or_np_array, str):
        img = cv2.imread(image_path_or_np_array)
        if img is None:
            print(f"Lỗi: không thể đọc ảnh từ {image_path_or_np_array}")
            return None
    else:
        img = image_path_or_np_array

    # 2. Nhận diện biển số (dùng hàm gốc của bạn)
    plate_text = recognize_plate_from_image(img)
    
    if not plate_text:
        print("KHÔNG NHẬN DIỆN ĐƯỢC BIỂN SỐ.")
        return None # Trả về None nếu không nhận diện được

    print(f"Nhận diện được biển số: {plate_text}")

    # 3. Tra cứu thông tin (dùng hàm MySQL mới, nhận 3 giá trị)
    phuongtien_id, nhan_vien_id, nhan_vien_info = find_vehicle_info(plate_text)
    
    # 4. GHI LOG (LOGIC MỚI THEO YÊU CẦU)
    if nhan_vien_id:
        # TÌM THẤY NHÂN VIÊN:
        # Hàm này sẽ log cả xe của nhân viên (có id) và xe khách (id là None)
        log_entry_time(plate_text, phuongtien_id, nhan_vien_id)
    else:
        # KHÔNG TÌM THẤY:
        # Chỉ thông báo và KHÔNG LƯU
        print(f"BIỂN CHƯA ĐĂNG KÝ: Biển {plate_text} không thuộc nhân viên nào. Không lưu vào CSDL.")
    
    # Trả về kết quả để có thể hiển thị lên giao diện
    # nhan_vien_info sẽ là dict (nếu tìm thấy) hoặc None (nếu là khách)
    return plate_text, phuongtien_id, nhan_vien_id, nhan_vien_info