import os
import json
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout, QAction, QMessageBox, # QAction ve QMessageBox eklendi
    QInputDialog, QDialog, QListWidget, QListWidgetItem, QGroupBox # Diğer potansiyel eksik widget'lar eklendi
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer, Qt


class SudokuHucre:
    def __init__(self):
        self.deger = 0  # 0 boş hücreyi temsil eder
        self.sabit = False  # Başlangıçta verilen sayılar için
        self.notlar = set()  # Oyuncunun aldığı notlar

class SudokuOyunu(QMainWindow):
    # Renk tanımlamaları
    SABIT_RENK = "color: red; font-weight: bold;"
    KULLANICI_RENK = "color: blue;"
    IPUCU_RENK = "background-color: #90EE90; color: red; font-weight: bold;"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sudoku")
        self.resize(600, 700)
        
        # Oyun değişkenleri
        self.secili_hucre = None
        self.baslangic_zamani = None
        self.zorluk = "Kolay"  # Varsayılan zorluk
        self.puan = 0
        self.oyun_aktif = False
        self.cozum_tahtasi = None  # İpucu için çözüm tahtası
        
        # Merkezi widget
        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        ana_duzen = QVBoxLayout(merkez_widget)
        
        # Üst bilgi alanı
        ust_duzen = QHBoxLayout()
        
        # Zorluk seçici
        self.zorluk_combo = QComboBox()
        self.zorluk_combo.addItems(["Kolay", "Orta", "Zor"])
        self.zorluk_combo.currentTextChanged.connect(self.zorluk_degisti)
        ust_duzen.addWidget(QLabel("Zorluk:"))
        ust_duzen.addWidget(self.zorluk_combo)
        
        # Süre göstergesi
        self.sure_label = QLabel("Süre: 00:00")
        ust_duzen.addWidget(self.sure_label)
        
        # Puan göstergesi
        self.puan_label = QLabel("Puan: 0")
        ust_duzen.addWidget(self.puan_label)
        
        # Yeni değişkenler ekle
        self.silme_hakki = 5
        self.toplam_puan = 0  # Toplam puan için yeni değişken
        
        # Silme hakkı göstergesi
        self.silme_hakki_label = QLabel(f"Silme Hakkı: {self.silme_hakki}")
        ust_duzen.addWidget(self.silme_hakki_label)
        
        # Toplam puan göstergesi
        self.toplam_puan_label = QLabel("Toplam Puan: 0")
        ust_duzen.addWidget(self.toplam_puan_label)
        
        ana_duzen.addLayout(ust_duzen)
        
        # Sudoku ızgarası
        self.izgara = QGridLayout()
        self.izgara.setSpacing(1)
        self.hucre_butonlari = []
        
        # 9x9 ızgarayı oluştur
        for i in range(9):
            satir = []
            for j in range(9):
                buton = QPushButton()
                buton.setFixedSize(50, 50)
                buton.setFont(QFont('Arial', 16))
                buton.clicked.connect(lambda checked, s=i, k=j: self.hucre_secildi(s, k))
                self.izgara.addWidget(buton, i, j)
                satir.append(buton)
            self.hucre_butonlari.append(satir)
        
        # 3x3'lük bölgeleri belirginleştir
        for i in range(9):
            for j in range(9):
                self.hucre_butonlari[i][j].setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1px solid gray;
                        margin: %dpx %dpx %dpx %dpx;
                    }
                """ % (
                    2 if i % 3 == 0 else 0,
                    2 if j % 3 == 0 else 0,
                    2 if i % 3 == 2 else 0,
                    2 if j % 3 == 2 else 0
                ))
        
        ana_duzen.addLayout(self.izgara)
        
        # Alt butonlar
        alt_duzen = QHBoxLayout()
        
        yeni_oyun_btn = QPushButton("Yeni Oyun")
        yeni_oyun_btn.clicked.connect(self.yeni_oyun)
        alt_duzen.addWidget(yeni_oyun_btn)
        
        kontrol_btn = QPushButton("Kontrol Et")
        kontrol_btn.clicked.connect(self.cozumu_kontrol_et)
        alt_duzen.addWidget(kontrol_btn)
        
        # İpucu butonu ekle
        ipucu_btn = QPushButton("İpucu")
        ipucu_btn.clicked.connect(self.ipucu_goster)
        alt_duzen.addWidget(ipucu_btn)
        
        ana_duzen.addLayout(alt_duzen)
        
        # Menü oluştur
        self.menu_olustur()
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.sure_guncelle)
        
        # Oyun tahtası
        self.tahta = [[SudokuHucre() for _ in range(9)] for _ in range(9)]
        
        # Başlangıçta yeni oyun başlat
        self.yeni_oyun()
        
        # Klavye kısayolları için focus policy
        self.setFocusPolicy(Qt.StrongFocus)
    
    def menu_olustur(self):
        menubar = self.menuBar()
        
        # Oyun menüsü
        oyun_menu = menubar.addMenu('Oyun')
        
        yeni_oyun = QAction('Yeni Oyun', self)
        yeni_oyun.setShortcut('F2')
        yeni_oyun.triggered.connect(self.yeni_oyun)
        oyun_menu.addAction(yeni_oyun)
        
        puan_tablosu = QAction('Puan Tablosu', self)
        puan_tablosu.triggered.connect(self.puan_tablosunu_goster)
        oyun_menu.addAction(puan_tablosu)
        
        # Yardım menüsü
        yardim_menu = menubar.addMenu('Yardım')
        
        nasil_oynanir = QAction('Nasıl Oynanır?', self)
        nasil_oynanir.triggered.connect(self.yardim_goster)
        yardim_menu.addAction(nasil_oynanir)
    
    def keyPressEvent(self, event):
        if not self.secili_hucre or not self.oyun_aktif:
            return
        
        satir, sutun = self.secili_hucre
        
        if event.key() in [Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5,
                          Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9]:
            # Sayı girişi
            if not self.tahta[satir][sutun].sabit:
                sayi = int(event.text())
                self.tahta[satir][sutun].deger = sayi
                self.hucre_butonlari[satir][sutun].setText(str(sayi))
                temel_stil = self.normal_hucre_stili(satir, sutun)
                self.hucre_butonlari[satir][sutun].setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #4169E1;
                        border: 1px solid gray;
                        margin: %dpx %dpx %dpx %dpx;
                    }
                """ % (
                    2 if satir % 3 == 0 else 0,
                    2 if sutun % 3 == 0 else 0,
                    2 if satir % 3 == 2 else 0,
                    2 if sutun % 3 == 2 else 0
                ))
        
        elif event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Hücreyi temizle
            if not self.tahta[satir][sutun].sabit and self.tahta[satir][sutun].deger != 0:
                if self.silme_hakki > 0:
                    self.silme_hakki -= 1
                    self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
                    self.tahta[satir][sutun].deger = 0
                    self.hucre_butonlari[satir][sutun].setText("")
                    self.hucre_butonlari[satir][sutun].setStyleSheet(
                        self.normal_hucre_stili(satir, sutun)
                    )
                    
                    # Silme hakkı bittiyse oyunu bitir
                    if self.silme_hakki == 0:
                        self.oyun_bitti("Silme hakkınız bitti!")
                else:
                    QMessageBox.warning(self, "Uyarı", "Silme hakkınız kalmadı!")

    def hucre_secildi(self, satir, sutun):
        """Bir hücre seçildiğinde çağrılır"""
        # Önceki seçili hücrenin stilini temizle
        if self.secili_hucre:
            eski_satir, eski_sutun = self.secili_hucre
            eski_hucre = self.tahta[eski_satir][eski_sutun]
            eski_etiket = self.hucre_butonlari[eski_satir][eski_sutun]
            
            if eski_hucre.deger != 0:
                if eski_hucre.sabit:
                    eski_etiket.setStyleSheet(
                        self.normal_hucre_stili(eski_satir, eski_sutun) + 
                        "color: red; font-weight: bold;"
                    )
                else:
                    eski_etiket.setStyleSheet(
                        self.normal_hucre_stili(eski_satir, eski_sutun) + 
                        "color: blue;"
                    )
            else:
                eski_etiket.setStyleSheet(self.normal_hucre_stili(eski_satir, eski_sutun))
        
        # Yeni hücreyi seç ve belirgin yap
        self.secili_hucre = (satir, sutun)
        self.hucre_butonlari[satir][sutun].setStyleSheet(
            self.normal_hucre_stili(satir, sutun) + 
            "background-color: lightblue; border: 2px solid blue;"
        )
    
    def normal_hucre_stili(self, satir, sutun):
        """Hücrenin temel stilini döndürür"""
        return (
            "QLabel { "
            "background-color: white; "
            "border: 1px solid gray; "
            f"margin: {2 if satir % 3 == 0 else 0}px {2 if sutun % 3 == 0 else 0}px "
            f"{2 if satir % 3 == 2 else 0}px {2 if sutun % 3 == 2 else 0}px; "
            "padding: 0px; "
            "} "
        )
    
    def yeni_oyun(self, puan_sifirla=True):
        """Yeni oyun başlat"""
        # Oyun tahtasını temizle
        for i in range(9):
            for j in range(9):
                self.tahta[i][j] = SudokuHucre()
                self.hucre_butonlari[i][j].setText("")
                self.hucre_butonlari[i][j].setStyleSheet(self.normal_hucre_stili(i, j))
        
        # Yeni oyun oluştur
        self.tahta = self.sudoku_olustur(self.zorluk)
        
        # Tahtayı göster
        self.tahtayi_guncelle()
        
        # Süreyi başlat (15 dakika = 900 saniye)
        self.baslangic_zamani = datetime.datetime.now()
        self.kalan_sure = 900  # 15 dakika
        self.timer.start(1000)  # Her saniye güncelle
        self.oyun_aktif = True
        
        # Puanı ayarla
        if puan_sifirla:
            self.puan = 500  # Başlangıç puanı 250 olarak değiştirildi
            self.toplam_puan = 0
            self.toplam_puan_label.setText("Toplam Puan: 0")
            self.silme_hakki = 5
            self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
        else:
            self.puan = 500  # Yeni oyun için başlangıç puanı 250
        
        self.puan_label.setText(f"Puan: {self.puan}")
    
    def sudoku_olustur(self, zorluk):
        """Sudoku tahtası oluştur ve çözümünü sakla"""
        tahta = [[SudokuHucre() for _ in range(9)] for _ in range(9)]
        
        # Yeni ve rastgele bir Sudoku tahtası oluştur
        bos_tahta = [[0 for _ in range(9)] for _ in range(9)]
        self.cozum_tahtasi = self.sudoku_coz(bos_tahta)  # Önce tam çözülmüş bir tahta oluştur
        
        # Zorluk seviyesine göre rakam sayısını belirle
        if zorluk == "Kolay":
            silinecek_sayi = 40  # 41 rakam görünür
        elif zorluk == "Orta":
            silinecek_sayi = 50  # 31 rakam görünür
        else:  # Zor
            silinecek_sayi = 60  # 21 rakam görünür
        
        # Rastgele hücreleri boşalt
        import random
        dolu_hucreler = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(dolu_hucreler)
        
        baslangic_tahtasi = [row[:] for row in self.cozum_tahtasi]
        for i, j in dolu_hucreler[:silinecek_sayi]:
            baslangic_tahtasi[i][j] = 0
        
        # Tahtayı ayarla
        for i in range(9):
            for j in range(9):
                tahta[i][j].deger = baslangic_tahtasi[i][j]
                if baslangic_tahtasi[i][j] != 0:
                    tahta[i][j].sabit = True
        
        return tahta
    
    def sudoku_coz(self, tahta):
        """Sudoku çözme algoritması"""
        bos = self.bos_hucre_bul(tahta)
        if not bos:
            return tahta
        
        satir, sutun = bos
        sayilar = list(range(1, 10))
        import random
        random.shuffle(sayilar)  # Rastgele çözüm için sayıları karıştır
        
        for sayi in sayilar:
            if self.sayi_uygun_mu(tahta, sayi, (satir, sutun)):
                tahta[satir][sutun] = sayi
                
                if self.sudoku_coz(tahta):
                    return tahta
                
                tahta[satir][sutun] = 0
        
        return False
    
    def bos_hucre_bul(self, tahta):
        """Boş hücre bul"""
        for i in range(9):
            for j in range(9):
                if tahta[i][j] == 0:
                    return (i, j)
        return None
    
    def sayi_uygun_mu(self, tahta, sayi, pos):
        """Sayının belirtilen konuma uygun olup olmadığını kontrol et"""
        # Satır kontrolü
        for j in range(9):
            if tahta[pos[0]][j] == sayi and pos[1] != j:
                return False
        
        # Sütun kontrolü
        for i in range(9):
            if tahta[i][pos[1]] == sayi and pos[0] != i:
                return False
        
        # 3x3 kutu kontrolü
        kutu_x = pos[1] // 3
        kutu_y = pos[0] // 3
        
        for i in range(kutu_y * 3, kutu_y * 3 + 3):
            for j in range(kutu_x * 3, kutu_x * 3 + 3):
                if tahta[i][j] == sayi and (i, j) != pos:
                    return False
        
        return True
    
    def tahtayi_guncelle(self):
        """Tahtayı görsel olarak güncelle"""
        for i in range(9):
            for j in range(9):
                hucre = self.tahta[i][j]
                buton = self.hucre_butonlari[i][j]
                
                if hucre.deger != 0:
                    buton.setText(str(hucre.deger))
                    if hucre.sabit:
                        # Başlangıçta verilen sayılar siyah renkte
                        buton.setStyleSheet("""
                            QPushButton {
                                background-color: white;
                                color: black;
                                font-weight: bold;
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
                    else:
                        # Kullanıcının girdiği sayılar açık mavi
                        buton.setStyleSheet("""
                            QPushButton {
                                background-color: white;
                                color: #4169E1;  /* Royal Blue */
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
                else:
                    buton.setText("")
                    buton.setStyleSheet("""
                        QPushButton {
                            background-color: white;
                            border: 1px solid gray;
                            margin: %dpx %dpx %dpx %dpx;
                        }
                    """ % (
                        2 if i % 3 == 0 else 0,
                        2 if j % 3 == 0 else 0,
                        2 if i % 3 == 2 else 0,
                        2 if j % 3 == 2 else 0
                    ))
    
    def sure_guncelle(self):
        if self.baslangic_zamani and self.oyun_aktif:
            gecen_sure = datetime.datetime.now() - self.baslangic_zamani
            dakika = gecen_sure.seconds // 60
            saniye = gecen_sure.seconds % 60
            self.sure_label.setText(f"Süre: {dakika:02d}:{saniye:02d}")
            
            # Her 30 saniyede bir puan düşür
            if gecen_sure.seconds > 0 and gecen_sure.seconds % 30 == 0:
                self.puan = max(0, self.puan - 1)  # Puan 0'ın altına düşmeyecek
                self.puan_label.setText(f"Puan: {self.puan}")
    
    def cozumu_kontrol_et(self):
        """Mevcut durumu kontrol et"""
        bos_hucre_var = False
        hatali_hucreler = []
        
        # Önce kullanıcının girdiği sayıları kontrol et
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    bos_hucre_var = True
                elif not self.tahta[i][j].sabit:  # Sadece kullanıcının girdiği sayıları kontrol et
                    if self.tahta[i][j].deger != self.cozum_tahtasi[i][j]:
                        hatali_hucreler.append((i, j))
        
        if hatali_hucreler:
            # Hatalı hücreleri işaretle
            for satir, sutun in hatali_hucreler:
                self.hucre_butonlari[satir][sutun].setStyleSheet("""
                    QPushButton {
                        background-color: #ffcccc;
                        color: #4169E1;
                        border: 1px solid gray;
                        margin: %dpx %dpx %dpx %dpx;
                    }
                """ % (
                    2 if satir % 3 == 0 else 0,
                    2 if sutun % 3 == 0 else 0,
                    2 if satir % 3 == 2 else 0,
                    2 if sutun % 3 == 2 else 0
                ))
            
            # Hata mesajı göster
            hata_konumlari = ", ".join([f"({s+1},{k+1})" for s, k in hatali_hucreler])
            QMessageBox.warning(
                self, 
                "Hatalı Sayılar", 
                f"Şu konumlardaki sayılar hatalı:\n{hata_konumlari}\n\n" +
                "(Hatalı hücreler kırmızı arka planla işaretlendi)"
            )
            
            # 2 saniye sonra hatalı hücrelerin arka planını normale döndür
            QTimer.singleShot(2000, self.hatalilari_temizle)
            return
        
        if bos_hucre_var:
            QMessageBox.information(self, "Kontrol", "Henüz tüm hücreler doldurulmamış!")
            return
        
        # Tüm hücreler dolu ve doğruysa
        gecen_sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        self.toplam_puan += self.puan
        self.toplam_puan_label.setText(f"Toplam Puan: {self.toplam_puan}")
        
        cevap = QMessageBox.question(
            self,
            "Tebrikler!",
            f"Sudoku'yu başarıyla çözdünüz!\nPuan: {self.puan}\nYeni oyuna devam etmek ister misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if cevap == QMessageBox.Yes:
            self.silme_hakki = 5
            self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
            self.yeni_oyun(puan_sifirla=False)
        else:
            self.oyun_bitti("Tebrikler! Oyunu başarıyla tamamladınız.")

    def hatalilari_temizle(self):
        """Hatalı hücrelerin arka planını normale döndür"""
        for i in range(9):
            for j in range(9):
                if not self.tahta[i][j].sabit:
                    if self.tahta[i][j].deger != 0:
                        self.hucre_butonlari[i][j].setStyleSheet("""
                            QPushButton {
                                background-color: white;
                                color: #4169E1;
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
                    else:
                        self.hucre_butonlari[i][j].setStyleSheet("""
                            QPushButton {
                                background-color: white;
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
    
    def zorluk_degisti(self, yeni_zorluk):
        if self.oyun_aktif:
            cevap = QMessageBox.question(
                self,
                "Yeni Oyun",
                "Aktif oyun var. Yeni oyun başlatmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if cevap == QMessageBox.Yes:
                self.zorluk = yeni_zorluk
                self.yeni_oyun()
            else:
                # Zorluk değişikliğini geri al
                self.zorluk_combo.setCurrentText(self.zorluk)
    
    def puan_tablosunu_goster(self):
        """Puan tablosunu göster"""
        try:
            # Puan tablosu dosyası
            puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_puanlar.json")
            
            # Mevcut puanları yükle
            puanlar = {"Kolay": [], "Orta": [], "Zor": []}
            if os.path.exists(puan_dosyasi):
                with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                    puanlar = json.load(f)
            
            # Puan tablosu penceresi
            dialog = QDialog(self)
            dialog.setWindowTitle("Puan Tablosu")
            dialog.setModal(True)
            dialog.resize(400, 500)
            
            # Düzen
            duzen = QVBoxLayout()
            
            # Zorluk seviyeleri için sekmeler
            for zorluk in ["Kolay", "Orta", "Zor"]:
                # Grup kutusu
                grup = QGroupBox(zorluk)
                grup_duzen = QVBoxLayout()
                
                # Puan listesi
                liste = QListWidget()
                zorluk_puanlari = sorted(puanlar.get(zorluk, []), 
                                       key=lambda x: (-x['puan'], x['sure']))  # Puana göre sırala
                
                for i, kayit in enumerate(zorluk_puanlari[:10], 1):  # İlk 10
                    sure = kayit['sure']  # saniye cinsinden
                    dakika = sure // 60
                    saniye = sure % 60
                    item = QListWidgetItem(
                        f"{i}. {kayit['isim']} - {kayit['puan']} puan "
                        f"(Süre: {dakika:02d}:{saniye:02d})"
                    )
                    liste.addItem(item)
                
                grup_duzen.addWidget(liste)
                grup.setLayout(grup_duzen)
                duzen.addWidget(grup)
            
            # Kapat düğmesi
            kapat_btn = QPushButton("Kapat")
            kapat_btn.clicked.connect(dialog.close)
            duzen.addWidget(kapat_btn)
            
            dialog.setLayout(duzen)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Puan tablosu gösterilirken hata oluştu: {str(e)}")
    
    def yardim_goster(self):
        yardim_metni = """
        <h2>Sudoku Nasıl Oynanır?</h2>
        <p>Sudoku, 9x9'luk bir ızgarada oynanan bir bulmaca oyunudur.</p>
        
        <h3>Kurallar:</h3>
        <ul>
            <li>Her satırda 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
            <li>Her sütunda 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
            <li>Her 3x3'lük bölgede 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
        </ul>
        
        <h3>Puan Sistemi:</h3>
        <ul>
            <li>Her oyun 500 puanla başlar</li>
            <li>Her 30 saniyede 1 puan düşer</li>
            <li>Her ipucu kullanımı 10 puan düşürür</li>
            <li>Oyuncunun 5 silme hakkı vardır</li>
            <li>Silme hakkı biterse oyun sonlanır</li>
            <li>Başarılı oyun bitiminde puanlar toplanır ve yeni oyuna devam edilebilir</li>
        </ul>
        
        <h3>Klavye Kontrolleri:</h3>
        <ul>
            <li>1-9: Sayı girmek için</li>
            <li>Delete/Backspace: Hücreyi silmek için (silme hakkı kullanılır)</li>
            <li>Ok tuşları: Hücreler arası hareket için</li>
            <li>F2: Yeni oyun başlatmak için</li>
        </ul>
        
        <h3>Fare Kontrolleri:</h3>
        <ul>
            <li>Sol tık: Hücre seçmek için</li>
            <li>Sayı girişi: Seçili hücreye klavyeden sayı girin</li>
        </ul>
        
        <h3>Renkler:</h3>
        <ul>
            <li>Kırmızı sayılar: Bilgisayar tarafından yerleştirilen veya ipucu ile doldurulan sayılar</li>
            <li>Mavi sayılar: Oyuncu tarafından girilen sayılar</li>
            <li>Yeşil arka plan: İpucu ile doldurulan hücreler</li>
        </ul>
        """
        
        QMessageBox.information(self, "Nasıl Oynanır?", yardim_metni)
    
    def ipucu_goster(self):
        """Rastgele bir boş hücreye doğru sayıyı yerleştir"""
        if not self.oyun_aktif or not self.cozum_tahtasi:
            return
        
        if self.puan <= 10:
            QMessageBox.warning(self, "Uyarı", "Puanınız ipucu için yetersiz!")
            return
        
        # Boş hücreleri bul
        bos_hucreler = []
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    bos_hucreler.append((i, j))
        
        if not bos_hucreler:
            QMessageBox.information(self, "İpucu", "Tüm hücreler dolu!")
            return
        
        # Rastgele bir boş hücre seç
        import random
        satir, sutun = random.choice(bos_hucreler)
        
        # Doğru sayıyı yerleştir
        dogru_sayi = self.cozum_tahtasi[satir][sutun]
        self.tahta[satir][sutun].deger = dogru_sayi
        self.tahta[satir][sutun].sabit = True
        
        # Hücreyi güncelle ve ipucu rengini ayarla
        buton = self.hucre_butonlari[satir][sutun]
        buton.setText(str(dogru_sayi))
        buton.setStyleSheet("""
            QPushButton {
                background-color: #90EE90;
                color: red;
                font-weight: bold;
                border: 1px solid gray;
                margin: %dpx %dpx %dpx %dpx;
            }
        """ % (
            2 if satir % 3 == 0 else 0,
            2 if sutun % 3 == 0 else 0,
            2 if satir % 3 == 2 else 0,
            2 if sutun % 3 == 2 else 0
        ))
        
        # Puanı güncelle
        self.puan = max(0, self.puan - 10)
        self.puan_label.setText(f"Puan: {self.puan}")

    def oyun_bitti(self, mesaj):
        """Oyunu bitir ve puan tablosuna girip giremediğini kontrol et"""
        self.oyun_aktif = False
        self.timer.stop()
        
        # İsim iste
        isim, ok = QInputDialog.getText(self, "Oyun Bitti!", 
            f"{mesaj}\nToplam Puanınız: {self.toplam_puan}\nİsminizi girin:")
        
        if ok and isim:
            self.puan_kaydet(isim, self.toplam_puan)
            self.puan_tablosunu_goster()

    def puan_kaydet(self, isim, puan):
        """Puanı kaydet"""
        puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  "sudoku_puanlar.json")
        
        puanlar = {"Kolay": [], "Orta": [], "Zor": []}
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)
        
        # Yeni puanı ekle
        puanlar[self.zorluk].append({
            'isim': isim,
            'puan': puan,
            'sure': int((datetime.datetime.now() - self.baslangic_zamani).total_seconds()),
            'tarih': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Puanları kaydet
        with open(puan_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(puanlar, f, ensure_ascii=False, indent=2)
