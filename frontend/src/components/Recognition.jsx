import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const Recognition = () => {
  const videoRef = useRef(null);
  const [result, setResult] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState('');

  // Hàm để khởi động camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Lỗi truy cập camera:", err);
      setError("Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.");
    }
  };

  useEffect(() => {
    startCamera();
  }, []);

  // Hàm chụp ảnh, gửi đi và xử lý kết quả
  const captureAndRecognize = async () => {
    if (isDetecting || !videoRef.current?.srcObject) return;

    setIsDetecting(true);
    setResult(null); // Xóa kết quả cũ

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg');

    try {
      // Thay đổi URL nếu backend của bạn chạy ở địa chỉ khác
      const response = await axios.post('http://127.0.0.1:5000/api/recognize', { image: imageData });
      setResult(response.data);
    } catch (error) {
      console.error("Lỗi khi gọi API:", error);
      setResult({ found: false, message: "Lỗi kết nối đến server backend." });
    } finally {
      setIsDetecting(false);
    }
  };


  return (
    <div className="recognition-container">
      <div className="camera-view">
        <h2>Khung hình Camera</h2>
        <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
        <button onClick={captureAndRecognize} disabled={isDetecting}>
          {isDetecting ? 'Đang xử lý...' : 'Nhận diện biển số'}
        </button>
        {error && <p className="error-message">{error}</p>}
      </div>
      <div className="result-view">
        <h2>Kết quả nhận diện</h2>
        <div className="result-box">
          {!result && <p>Chưa có dữ liệu. Hãy nhấn nút để nhận diện.</p>}
          {result && (
            <div>
              <p><strong>Trạng thái:</strong> {result.message}</p>
              {result.found && <h3>Biển số: <span className="license-plate">{result.bien_so}</span></h3>}
              {result.registered && result.nhan_vien && (
                <div className="employee-info">
                  <h4>Thông tin nhân viên:</h4>
                  <p><strong>Mã NV:</strong> {result.nhan_vien.ma_nhan_vien}</p>
                  <p><strong>Họ tên:</strong> {result.nhan_vien.ho_ten}</p>
                  <p><strong>Chức vụ:</strong> {result.nhan_vien.chuc_vu}</p>
                  <p><strong>Phòng ban:</strong> {result.nhan_vien.phong_ban}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Recognition;