from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class NhanVien(db.Model):
    __tablename__ = 'nhanvien'
    id = db.Column(db.Integer, primary_key=True)
    ma_nhan_vien = db.Column(db.String(50), unique=True, nullable=False)
    ho_ten = db.Column(db.String(100), nullable=False)
    chuc_vu = db.Column(db.String(100))
    phong_ban = db.Column(db.String(100))
    phuong_tien = db.relationship('PhuongTien', backref='nhan_vien', uselist=False)

    def to_dict(self):
        return {
            'ma_nhan_vien': self.ma_nhan_vien,
            'ho_ten': self.ho_ten,
            'chuc_vu': self.chuc_vu,
            'phong_ban': self.phong_ban
        }

class PhuongTien(db.Model):
    __tablename__ = 'phuongtien'
    id = db.Column(db.Integer, primary_key=True)
    bien_so = db.Column(db.String(20), unique=True, nullable=False)
    loai_xe = db.Column(db.String(50))
    mau_sac = db.Column(db.String(50))
    nhan_vien_id = db.Column(db.Integer, db.ForeignKey('nhanvien.id'))