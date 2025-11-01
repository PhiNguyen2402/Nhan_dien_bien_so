import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// =================================================================
// KHỐI 1: BÊN TRÁI (LOGIC NHẬN DIỆN)
// Component con cho phần Camera
// =================================================================
const CameraView = ({ onScanResult, onScanStart, isDetecting, error }) => {
  const videoRef = useRef(null);
  const [localError, setLocalError] = useState(''); // Lỗi camera cục bộ

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
      setLocalError("Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.");
    }
  };

  useEffect(() => {
    startCamera();
    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const captureAndRecognize = async () => {
    if (isDetecting || !videoRef.current?.srcObject) return;

    onScanStart(); // Báo cho App (cha) là bắt đầu quét

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg');

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/recognize', { image: imageData });
      onScanResult(response.data); // Gửi kết quả lên App (cha)
    } catch (error) {
      console.error("Lỗi khi gọi API:", error);
      onScanResult({ found: false, message: "Lỗi kết nối đến server backend." }); // Gửi lỗi lên App (cha)
    }
  };

  const displayError = error || localError; // Hiển thị lỗi API hoặc lỗi camera

  return (
    // Sử dụng class CSS "camera-view" của bạn
    <div className="camera-view">
      <h2>Khung hình Camera</h2>
      <div className="video-container"> {/* Bọc video-feed trong container */}
        <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
      </div>
      <button onClick={captureAndRecognize} disabled={isDetecting || !!displayError} className="capture-btn">
        {isDetecting ? 'Đang xử lý...' : 'Nhận diện biển số'}
      </button>
      {displayError && <p className="error-message">{displayError}</p>}
    </div>
  );
};

// =================================================================
// KHỐI 2: BÊN PHẢI - TRÊN (KẾT QUẢ QUÉT)
// =================================================================
const ScanResult = ({ scanData }) => {
  const result = scanData; // Dùng state được truyền từ App (cha)

  return (
    // Sử dụng class CSS "result-box" của bạn
    <div className="result-box">
      <h2>Kết quả nhận diện</h2> {/* Thêm H2 cho result-box */}
      {!result && <p>Chưa có dữ liệu. Hãy nhấn nút để nhận diện.</p>}
      {result && (
        <div>
          {/* Sửa đổi: Sử dụng các class status */}
          <p className={result.found ? (result.registered ? 'status-success' : 'status-pending') : 'error-message'}>
            <strong>Trạng thái:</strong> {result.message}
          </p>
          {result.found ? (
            <>
              <h3>Biển số: <span className="license-plate">{result.bien_so}</span></h3>
              {result.registered && result.nhan_vien && (
                <div className="employee-info">
                  <h4>Thông tin nhân viên:</h4> {/* Đổi từ h3 thành h4 */}
                  <p><strong>Mã NV:</strong> {result.nhan_vien.ma_nhan_vien}</p>
                  <p><strong>Họ tên:</strong> {result.nhan_vien.ho_ten}</p>
                  <p><strong>Chức vụ:</strong> {result.nhan_vien.chuc_vu}</p>
                  <p><strong>Phòng ban:</strong> {result.nhan_vien.phong_ban}</p>
                </div>
              )}
            </>
          ) : (
            // Bỏ 'not-found' vì đã có 'error-message'
            null
          )}
        </div>
      )}
    </div>
  );
};

// =================================================================
// KHỐI 3: BÊN PHẢI - DƯỚI (LỊCH SỬ - PHẦN BỔ SUNG)
// =================================================================
const LogHistory = ({ history }) => {
  return (
    // Sử dụng class CSS "history-box"
    <div className="history-box">
      <h2>Lịch sử vào ra</h2>
      <div className="history-list"> {/* Div này dùng để cuộn */}
        {history.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '10px' }}>Chưa có dữ liệu vào ra.</p>
        ) : (
          // Chuyển <ul> sang <table>
          <table className="history-table"> {/* Thêm class để bạn có thể style table này */}
            <thead>
              <tr>
                <th>Biển số</th>
                <th>Họ tên</th>
                <th>Chức vụ</th>
                <th>Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {history.map((log, index) => (
                <tr key={index}>
                  <td>
                    <span className={log.registered ? 'plate-registered' : 'plate-guest'}>
                      {log.bien_so}
                    </span>
                  </td>
                  <td>
                    {/* Lấy họ tên từ object nhan_vien */}
                    {log.nhan_vien ? log.nhan_vien.ho_ten : 'Khách'}
                  </td>
                  <td>
                    {/* Lấy chức vụ từ object nhan_vien */}
                    {log.nhan_vien ? log.nhan_vien.chuc_vu : 'N/A'}
                  </td>
                  <td>
                    <span className="time">{log.time}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};


// Component Recognition (Cha) quản lý state và layout
// =================================================================
const Recognition = () => {
  // Nâng state (trạng thái) lên component cha
  const [currentScan, setCurrentScan] = useState(null);
  const [logHistory, setLogHistory] = useState([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [apiError, setApiError] = useState('');

  // Hàm này được CameraView gọi khi bắt đầu quét
  const handleScanStart = () => {
    setIsDetecting(true);
    setCurrentScan(null);
    setApiError('');
  };

  // Hàm này được CameraView gọi khi có kết quả
  const handleScanResult = (result) => {
    setCurrentScan(result);
    setIsDetecting(false); // Quét xong

    // Nếu tìm thấy, thêm vào lịch sử
    if (result && result.found) {
      // --- SỬA ĐỔI: Lưu toàn bộ object 'nhan_vien' ---
      const newLogEntry = {
        bien_so: result.bien_so,
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        registered: result.registered,
        nhan_vien: result.nhan_vien || null // Lưu cả object nhân viên
      };
      // ---------------------------------------------
      setLogHistory(prevHistory => [newLogEntry, ...prevHistory]);
    }

    // Xử lý lỗi
    if (result && !result.found && result.message.includes("Lỗi")) {
      setApiError(result.message);
    }
  };

  return (
    // Layout 2 CỘT (Trái / Phải)
    // Sử dụng class CSS "recognition-container" của bạn
    <div className="recognition-container">

      {/* CỘT TRÁI: CAMERA */}
      <CameraView
        onScanResult={handleScanResult}
        onScanStart={handleScanStart}
        isDetecting={isDetecting}
        error={apiError}
      />

      {/* CỘT PHẢI: THÔNG TIN */}
      {/* Sử dụng class CSS "result-view" của bạn */}
      <div className="result-view">

        {/* PHẦN TRÊN: KẾT QUẢ */}
        <ScanResult scanData={currentScan} />

        {/* PHẦN DƯỚI: LỊCH SỬ (Bổ sung) */}
        <LogHistory history={logHistory} />

      </div>
    </div>
  );
};

export default Recognition;
