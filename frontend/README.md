HỆ THỐNG NHẬN DIỆN BIỂN SỐ XE CÔNG TY

(License Plate Recognition System)

1. Giới thiệu

Hệ thống tự động nhận diện biển số xe từ camera giám sát hoặc webcam, đối chiếu với cơ sở dữ liệu nhân viên để xác thực quyền ra vào. Hệ thống bao gồm:

Frontend: ReactJS (Giao diện người dùng).

Backend: Python Flask (API, Xử lý ảnh OpenCV, Tesseract OCR).

Database: MySQL (Lưu trữ thông tin nhân viên, phương tiện và lịch sử).

2. Yêu cầu hệ thống (Prerequisites)

Trước khi cài đặt, đảm bảo máy tính đã cài:

Python (3.8 trở lên).

Node.js & npm.

MySQL Server (XAMPP, WAMP hoặc MySQL Installer).

Tesseract OCR Engine:

Tải và cài đặt Tesseract tại: https://www.google.com/search?q=https://github.com/UB-Mannheim/tesseract/wiki

Quan trọng: Ghi nhớ đường dẫn cài đặt (Ví dụ: C:\Program Files\Tesseract-OCR\tesseract.exe) để cấu hình trong code.

3. Hướng dẫn Cài đặt (Installation)

Bước 1: Cấu hình Cơ sở dữ liệu (MySQL)

Mở công cụ quản lý MySQL (phpMyAdmin, Workbench, HeidiSQL).

Tạo một Database mới tên là cong_ty_db.

Chạy câu lệnh SQL sau để tạo bảng:

-- Bảng Nhân viên
CREATE TABLE IF NOT EXISTS nhanvien (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ma_nhan_vien VARCHAR(20) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    chuc_vu VARCHAR(50),
    phong_ban VARCHAR(50),
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Phương tiện
CREATE TABLE IF NOT EXISTS phuongtien (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bien_so VARCHAR(20) UNIQUE NOT NULL,
    loai_xe VARCHAR(50),
    nhan_vien_id INT,
    FOREIGN KEY (nhan_vien_id) REFERENCES nhanvien(id)
);

-- Bảng Lịch sử Vào/Ra
CREATE TABLE IF NOT EXISTS lich_su_vao_ra (
    id INT PRIMARY KEY AUTO_INCREMENT,
    thoi_gian_vao DATETIME NOT NULL,
    bien_so_xe VARCHAR(20) NOT NULL,
    phuongtien_id INT,
    nhan_vien_id INT,
    FOREIGN KEY (phuongtien_id) REFERENCES phuongtien(id),
    FOREIGN KEY (nhan_vien_id) REFERENCES nhanvien(id)
);


Thêm một vài dữ liệu mẫu vào bảng nhanvien và phuongtien để test.

Bước 2: Cài đặt Backend (Python Flask)

Mở terminal tại thư mục backend.

Cài đặt các thư viện cần thiết:

pip install flask flask-cors opencv-python numpy pytesseract mysql-connector-python


Mở file recognition.py, tìm phần MYSQL_CONFIG và cập nhật thông tin đăng nhập MySQL của bạn (user, password).

Kiểm tra đường dẫn pytesseract.pytesseract.tesseract_cmd trong code xem đã đúng với nơi bạn cài Tesseract chưa.

Chạy server:

python app.py


Server sẽ chạy tại: http://127.0.0.1:5000

Bước 3: Cài đặt Frontend (ReactJS)

Mở terminal mới tại thư mục frontend.

Cài đặt các gói phụ thuộc:

npm install
# Đảm bảo đã cài axios
npm install axios


Khởi chạy ứng dụng:

npm start
