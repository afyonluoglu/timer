import os
import json
import datetime
import random # random modülü eklendi
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QAction, QInputDialog, QDialog, # QAction, QInputDialog, QDialog eklendi
    QListWidget, QListWidgetItem, QMessageBox # QListWidget, QListWidgetItem, QMessageBox eklendi
)
from PyQt5.QtGui import QColor, QPainter # QColor ve QPainter eklendi
from PyQt5.QtCore import Qt, QTimer # Qt ve QTimer eklendi


class TetrisBlok:
    # Sınıf değişkenleri olarak tanımla
    SEKILLER = {
        'I': [[1, 1, 1, 1]],
        'J': [[1, 0, 0], [1, 1, 1]],
        'L': [[0, 0, 1], [1, 1, 1]],
        'O': [[1, 1], [1, 1]],
        'S': [[0, 1, 1], [1, 1, 0]],
        'T': [[0, 1, 0], [1, 1, 1]],
        'Z': [[1, 1, 0], [0, 1, 1]]
    }
    
    RENKLER = {
        'I': QColor(0, 255, 255),  # Cyan
        'J': QColor(0, 0, 255),    # Blue
        'L': QColor(255, 165, 0),  # Orange
        'O': QColor(255, 255, 0),  # Yellow
        'S': QColor(0, 255, 0),    # Green
        'T': QColor(255, 0, 255),  # Magenta
        'Z': QColor(255, 0, 0)     # Red
    }

    def __init__(self, sekil_id):
        self.sekil_id = sekil_id
        self.sekil = self.SEKILLER[sekil_id]
        self.renk = self.RENKLER[sekil_id]
        self.x = 3
        self.y = 0

class TetrisOyunu(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tetris")
        self.resize(600, 800)
        
        # Oyun değişkenleri
        self.IZGARA_GENISLIK = 10
        self.IZGARA_YUKSEKLIK = 20
        self.HUCRE_BOYUT = 30
        self.puan = 0
        self.joker = 0
        self.oyun_aktif = False
        self.beklemede = False
        
        # Oyun tahtası
        self.tahta = [[0] * self.IZGARA_GENISLIK for _ in range(self.IZGARA_YUKSEKLIK)]
        self.mevcut_blok = None
        
        # Merkezi widget
        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        ana_duzen = QVBoxLayout(merkez_widget)
        
        # Üst bilgi alanı
        ust_duzen = QHBoxLayout()
        
        # Puan göstergesi
        self.puan_label = QLabel("Puan: 0")
        self.puan_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        ust_duzen.addWidget(self.puan_label)
        
        # Joker göstergesi
        self.joker_label = QLabel("Joker: 0")
        self.joker_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        ust_duzen.addWidget(self.joker_label)
        
        ana_duzen.addLayout(ust_duzen)
        
        # Oyun alanı
        class TetrisAlan(QFrame):
            def paintEvent(self_frame, event):
                painter = QPainter(self_frame)
                
                # Arka planı siyah yap
                painter.fillRect(event.rect(), QColor(0, 0, 0))
                
                # Sabit blokları çiz
                for y in range(self.IZGARA_YUKSEKLIK):
                    for x in range(self.IZGARA_GENISLIK):
                        if self.tahta[y][x]:
                            renk = TetrisBlok.RENKLER[self.tahta[y][x]]
                            painter.fillRect(
                                x * self.HUCRE_BOYUT,
                                y * self.HUCRE_BOYUT,
                                self.HUCRE_BOYUT - 1,
                                self.HUCRE_BOYUT - 1,
                                renk
                            )
                
                # Mevcut bloğu çiz
                if self.mevcut_blok:
                    for y, satir in enumerate(self.mevcut_blok.sekil):
                        for x, hucre in enumerate(satir):
                            if hucre:
                                painter.fillRect(
                                    (self.mevcut_blok.x + x) * self.HUCRE_BOYUT,
                                    (self.mevcut_blok.y + y) * self.HUCRE_BOYUT,
                                    self.HUCRE_BOYUT - 1,
                                    self.HUCRE_BOYUT - 1,
                                    self.mevcut_blok.renk
                                )
                
                # Izgara çizgilerini çiz
                painter.setPen(QColor(40, 40, 40))  # Koyu gri
                for x in range(self.IZGARA_GENISLIK + 1):
                    painter.drawLine(
                        x * self.HUCRE_BOYUT, 0,
                        x * self.HUCRE_BOYUT, self.IZGARA_YUKSEKLIK * self.HUCRE_BOYUT
                    )
                for y in range(self.IZGARA_YUKSEKLIK + 1):
                    painter.drawLine(
                        0, y * self.HUCRE_BOYUT,
                        self.IZGARA_GENISLIK * self.HUCRE_BOYUT, y * self.HUCRE_BOYUT
                    )
        
        self.oyun_alani = TetrisAlan(self)
        self.oyun_alani.setFixedSize(
            self.IZGARA_GENISLIK * self.HUCRE_BOYUT,
            self.IZGARA_YUKSEKLIK * self.HUCRE_BOYUT
        )
        self.oyun_alani.setFrameStyle(QFrame.Box | QFrame.Raised)
        ana_duzen.addWidget(self.oyun_alani, alignment=Qt.AlignCenter)
        
        # Alt butonlar
        alt_duzen = QHBoxLayout()
        
        self.baslat_dugme = QPushButton("Başlat")
        self.baslat_dugme.clicked.connect(self.oyunu_baslat)
        alt_duzen.addWidget(self.baslat_dugme)
        
        self.duraklat_dugme = QPushButton("Duraklat")
        self.duraklat_dugme.clicked.connect(self.oyunu_duraklat)
        self.duraklat_dugme.setEnabled(False)
        alt_duzen.addWidget(self.duraklat_dugme)
        
        ana_duzen.addLayout(alt_duzen)
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.oyun_dongusu)
        self.timer.setInterval(500)  # 500ms = 0.5 saniye
        
        # Klavye odağı
        self.setFocusPolicy(Qt.StrongFocus)

    def menu_olustur(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Oyun menüsü
        oyun_menu = menubar.addMenu('Oyun')
        
        yeni_oyun = QAction('Yeni Oyun', self)
        yeni_oyun.setShortcut('F2')
        yeni_oyun.triggered.connect(self.oyunu_baslat)
        oyun_menu.addAction(yeni_oyun)
        
        puan_tablosu = QAction('Puan Tablosu', self)
        puan_tablosu.triggered.connect(self.puan_tablosunu_goster)
        oyun_menu.addAction(puan_tablosu)
        
        # Yardım menüsü
        yardim_menu = menubar.addMenu('Yardım')
        
        nasil_oynanir = QAction('Nasıl Oynanır?', self)
        nasil_oynanir.triggered.connect(self.yardim_goster)
        yardim_menu.addAction(nasil_oynanir)

    def oyunu_baslat(self):
        """Yeni oyun başlat"""
        # Tahtayı temizle
        self.tahta = [[0] * self.IZGARA_GENISLIK for _ in range(self.IZGARA_YUKSEKLIK)]
        
        # Oyun değişkenlerini sıfırla
        self.puan = 0
        self.joker = 0
        self.puan_label.setText(f"Puan: {self.puan}")
        self.joker_label.setText(f"Joker: {self.joker}")
        
        # Yeni blok oluştur
        self.yeni_blok_olustur()
        
        # Oyunu aktif et
        self.oyun_aktif = True
        self.beklemede = False
        
        # Timer'ı başlat
        self.timer.start()
        
        # Butonları güncelle
        self.baslat_dugme.setEnabled(False)
        self.duraklat_dugme.setEnabled(True)

    def oyunu_duraklat(self):
        """Oyunu duraklat/devam ettir"""
        if not self.oyun_aktif:
            return
        
        if self.beklemede:
            # Oyuna devam et
            self.timer.start()
            self.beklemede = False
            self.duraklat_dugme.setText("Duraklat")
        else:
            # Oyunu duraklat
            self.timer.stop()
            self.beklemede = True
            self.duraklat_dugme.setText("Devam Et")

    def oyun_dongusu(self):
        """Ana oyun döngüsü"""
        if not self.oyun_aktif or self.beklemede:
            return
        
        if self.mevcut_blok:
            # Bloğu aşağı hareket ettir
            if self.blok_hareket_ettir(0, 1):
                self.oyun_alani.update()
            else:
                # Blok en aşağıya ulaştı
                self.blogu_sabitle()
                self.tamamlanan_satirlari_kontrol_et()
                self.yeni_blok_olustur()
                
                # Oyun bitti mi kontrol et
                if not self.hareket_mumkun_mu(self.mevcut_blok):
                    self.oyun_bitti()

    def yeni_blok_olustur(self):
        """Yeni bir blok oluştur"""
        import random
        sekiller = list(TetrisBlok.SEKILLER.keys())
        self.mevcut_blok = TetrisBlok(random.choice(sekiller))
        
        # Yeni blok hareket edebiliyor mu?
        if not self.hareket_mumkun_mu(self.mevcut_blok):
            self.oyun_bitti()

    def blok_hareket_ettir(self, dx, dy):
        """Bloğu hareket ettir"""
        if not self.mevcut_blok:
            return False
        
        eski_x = self.mevcut_blok.x
        eski_y = self.mevcut_blok.y
        
        self.mevcut_blok.x += dx
        self.mevcut_blok.y += dy
        
        if not self.hareket_mumkun_mu(self.mevcut_blok):
            self.mevcut_blok.x = eski_x
            self.mevcut_blok.y = eski_y
            return False
        
        return True

    def hareket_mumkun_mu(self, blok):
        """Bloğun hareketi mümkün mü kontrol et"""
        for y, satir in enumerate(blok.sekil):
            for x, hucre in enumerate(satir):
                if hucre:
                    yeni_y = blok.y + y
                    yeni_x = blok.x + x
                    
                    if (yeni_x < 0 or yeni_x >= self.IZGARA_GENISLIK or
                        yeni_y >= self.IZGARA_YUKSEKLIK or
                        (yeni_y >= 0 and self.tahta[yeni_y][yeni_x])):
                        return False
        return True

    def blogu_sabitle(self):
        """Mevcut bloğu tahtaya sabitle"""
        if not self.mevcut_blok:
            return
        
        for y, satir in enumerate(self.mevcut_blok.sekil):
            for x, hucre in enumerate(satir):
                if hucre:
                    tahta_y = self.mevcut_blok.y + y
                    tahta_x = self.mevcut_blok.x + x
                    if 0 <= tahta_y < self.IZGARA_YUKSEKLIK:
                        self.tahta[tahta_y][tahta_x] = self.mevcut_blok.sekil_id

    def tamamlanan_satirlari_kontrol_et(self):
        """Tamamlanan satırları kontrol et ve temizle"""
        tamamlanan_satirlar = 0
        y = self.IZGARA_YUKSEKLIK - 1
        
        while y >= 0:
            if all(self.tahta[y]):
                # Satır tamamlandı
                tamamlanan_satirlar += 1
                # Üstteki satırları aşağı kaydır
                for ust_y in range(y, 0, -1):
                    self.tahta[ust_y] = self.tahta[ust_y - 1][:]
                # En üst satırı boşalt
                self.tahta[0] = [0] * self.IZGARA_GENISLIK
            else:
                y -= 1
        
        # Puan hesapla
        if tamamlanan_satirlar > 0:
            self.puan += tamamlanan_satirlar * 100
            self.puan_label.setText(f"Puan: {self.puan}")
            
            # Her 50 puanda bir joker ver
            yeni_jokerler = self.puan // 50 - (self.puan - tamamlanan_satirlar * 100) // 50
            if yeni_jokerler > 0:
                self.joker += yeni_jokerler
                self.joker_label.setText(f"Joker: {self.joker}")

    def keyPressEvent(self, event):
        """Klavye kontrollerini işle"""
        if not self.oyun_aktif or not self.mevcut_blok or self.beklemede:
            return
        
        key = event.key()
        
        if key == Qt.Key_Left:
            self.blok_hareket_ettir(-1, 0)
        elif key == Qt.Key_Right:
            self.blok_hareket_ettir(1, 0)
        elif key == Qt.Key_Down:
            self.blok_hareket_ettir(0, 1)
        elif key == Qt.Key_Up:
            self.blok_dondur()
        elif key == Qt.Key_Space:
            self.blok_dusur()
        elif key == Qt.Key_P:
            self.oyunu_duraklat()
        elif key == Qt.Key_1:
            self.joker_kullan()
        elif key == Qt.Key_2:
            self.blok_degistir()
        
        self.oyun_alani.update()

    def blok_dondur(self):
        """Mevcut bloğu saat yönünde döndür"""
        if not self.mevcut_blok:
            return
        
        # Bloğun orijinal konumunu sakla
        eski_sekil = [satir[:] for satir in self.mevcut_blok.sekil]
        
        # Bloğu döndür
        self.mevcut_blok.sekil = list(zip(*reversed(self.mevcut_blok.sekil)))
        
        # Eğer dönüş mümkün değilse geri al
        if not self.hareket_mumkun_mu(self.mevcut_blok):
            self.mevcut_blok.sekil = eski_sekil

    def blok_dusur(self):
        """Bloğu en aşağıya düşür"""
        if not self.mevcut_blok:
            return
        
        while self.blok_hareket_ettir(0, 1):
            pass

    def joker_kullan(self):
        """Joker kullanarak en alttaki tamamlanmamış satırı sil"""
        if self.joker <= 0:
            return
        
        # En alttaki tamamlanmamış satırı bul
        for y in range(self.IZGARA_YUKSEKLIK - 1, -1, -1):
            if not all(self.tahta[y]) and any(self.tahta[y]):
                # Üstteki satırları aşağı kaydır
                for ust_y in range(y, 0, -1):
                    self.tahta[ust_y] = self.tahta[ust_y - 1][:]
                # En üst satırı boşalt
                self.tahta[0] = [0] * self.IZGARA_GENISLIK
                
                # Joker sayısını azalt
                self.joker -= 1
                self.joker_label.setText(f"Joker: {self.joker}")
                break

    def blok_degistir(self):
        """Mevcut bloğu rastgele başka bir blokla değiştir"""
        if not self.mevcut_blok:
            return
        
        # Mevcut konumu ve yüksekliği sakla
        x = self.mevcut_blok.x
        y = self.mevcut_blok.y
        
        # Yeni blok oluştur
        import random
        yeni_sekil = random.choice([s for s in TetrisBlok.SEKILLER.keys() 
                                   if s != self.mevcut_blok.sekil_id])
        yeni_blok = TetrisBlok(yeni_sekil)
        yeni_blok.x = x
        yeni_blok.y = y
        
        # Eğer yeni blok bu konuma yerleştirilebilirse değiştir
        if self.hareket_mumkun_mu(yeni_blok):
            self.mevcut_blok = yeni_blok

    def oyun_bitti(self):
        """Oyun bittiğinde çağrılır"""
        self.oyun_aktif = False
        self.timer.stop()
        self.baslat_dugme.setEnabled(True)
        self.duraklat_dugme.setEnabled(False)
        
        # İsim iste ve puan tablosuna kaydet
        isim, ok = QInputDialog.getText(
            self, 
            "Oyun Bitti!", 
            f"Oyun bitti!\nPuanınız: {self.puan}\nİsminizi girin:"
        )
        
        if ok and isim:
            self.puan_kaydet(isim)
            self.puan_tablosunu_goster()

    def puan_kaydet(self, isim):
        """Puanı kaydet"""
        puan_dosyasi = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "tetris_puanlar.json"
        )
        
        puanlar = []
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)
        
        # Yeni puanı ekle
        puanlar.append({
            'isim': isim,
            'puan': self.puan,
            'tarih': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Puanları sırala ve en yüksek 10 puanı sakla
        puanlar.sort(key=lambda x: x['puan'], reverse=True)
        puanlar = puanlar[:10]
        
        # Puanları kaydet
        with open(puan_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(puanlar, f, ensure_ascii=False, indent=2)

    def puan_tablosunu_goster(self):
        """Puan tablosunu göster"""
        try:
            # Puan tablosu dosyası
            puan_dosyasi = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "tetris_puanlar.json"
            )
            
            # Mevcut puanları yükle
            puanlar = []
            if os.path.exists(puan_dosyasi):
                with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                    puanlar = json.load(f)
            
            # Puan tablosu penceresi
            dialog = QDialog(self)
            dialog.setWindowTitle("Tetris Puan Tablosu")
            dialog.setModal(True)
            dialog.resize(400, 500)
            
            # Düzen
            duzen = QVBoxLayout()
            
            # Puan listesi
            liste = QListWidget()
            for i, kayit in enumerate(puanlar, 1):
                item = QListWidgetItem(
                    f"{i}. {kayit['isim']} - {kayit['puan']} puan "
                    f"(Tarih: {kayit['tarih']})"
                )
                liste.addItem(item)
            
            duzen.addWidget(liste)
            
            # Kapat düğmesi
            kapat_btn = QPushButton("Kapat")
            kapat_btn.clicked.connect(dialog.close)
            duzen.addWidget(kapat_btn)
            
            dialog.setLayout(duzen)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Puan tablosu gösterilirken hata oluştu: {str(e)}")

    def yardim_goster(self):
        """Yardım penceresini göster"""
        yardim_metni = """
        <h2>Tetris Nasıl Oynanır?</h2>
        
        <h3>Oyun Kuralları:</h3>
        <ul>
            <li>Farklı şekillerdeki bloklar yukarıdan aşağıya düşer</li>
            <li>Blokları yönlendirerek tam satırlar oluşturmaya çalışın</li>
            <li>Tamamlanan satırlar silinir ve puan kazanırsınız</li>
            <li>Bloklar üst sınıra ulaştığında oyun biter</li>
        </ul>
        
        <h3>Kontroller:</h3>
        <ul>
            <li>← → : Bloğu sağa/sola hareket ettir</li>
            <li>↑ : Bloğu döndür</li>
            <li>↓ : Bloğu hızlı düşür</li>
            <li>Boşluk : Bloğu anında düşür</li>
            <li>P : Oyunu duraklat/devam et</li>
            <li>1 : Joker kullan (tamamlanmamış satırı sil)</li>
            <li>2 : Mevcut bloğu değiştir</li>
        </ul>
        
        <h3>Puan Sistemi:</h3>
        <ul>
            <li>Her tamamlanan satır: 100 puan</li>
            <li>Her 50 puanda bir joker kazanılır</li>
            <li>Joker kullanarak tamamlanmamış satırları silebilirsiniz</li>
        </ul>
        """
        
        QMessageBox.information(self, "Nasıl Oynanır?", yardim_metni)
