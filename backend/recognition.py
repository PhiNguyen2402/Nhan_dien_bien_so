import cv2
import numpy as np
import re
import pytesseract

try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception as e:
    print("Lỗi: Không tìm thấy Tesseract. Hãy chắc chắn bạn đã cài đặt Tesseract OCR và cập nhật đúng đường dẫn.")
    print(e)

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