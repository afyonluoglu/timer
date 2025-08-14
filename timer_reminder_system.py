from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QDateEdit, QTimeEdit, QTextEdit, QComboBox, 
                           QSpinBox, QFrame)
from PyQt5.QtCore import Qt, QDate, QTime
import datetime
import calendar

from timer_logger import record_log

class Hatirlatici:
    def __init__(self, id, tarih, saat, not_metni, yapildi=False, olusturma_zamani=None,
                 tekrarlama_tipi="yok", tekrarlama_araligi=1, son_tekrar_tarihi=None,
                 hafta_gunu=None, ertelendi=False): 
        self.id = id
        self.tarih = tarih  # datetime.date objesi
        self.saat = saat    # QTime objesi
        self.not_metni = not_metni
        self.yapildi = yapildi
        self.olusturma_zamani = olusturma_zamani or datetime.datetime.now()

        # Tekrarlama özellikleri
        self.tekrarlama_tipi = tekrarlama_tipi  # "yok", "gun", "hafta", "ay"
        self.tekrarlama_araligi = tekrarlama_araligi  # 1, 2, 3, ... (her X günde/haftada/ayda bir)
        self.son_tekrar_tarihi = son_tekrar_tarihi  # Son tekrarın yapıldığı tarih
        self.hafta_gunu = hafta_gunu  # 0=Pazartesi, 1=Salı, ..., 6=Pazar (haftalık tekrarlama için)

        # Erteleme durumu
        self.ertelendi = ertelendi 

    def get_datetime(self):
        """Hatırlatıcının tarih ve saatini datetime objesi olarak döndürür"""
        # return datetime.datetime.combine(
        #     self.tarih, 
        #     datetime.time(self.saat.hour(), self.saat.minute())
        # )
        """Hatırlatıcının tarih ve saatini birleşik bir datetime nesnesi olarak döndürür."""
        if not self.tarih or not self.saat:
            return None

        # self.saat'in türünü kontrol et ve uygun şekilde birleştir
        if isinstance(self.saat, datetime.time):
            # Eğer self.saat zaten bir datetime.time nesnesi ise, doğrudan kullan
            return datetime.datetime.combine(self.tarih, self.saat)
        elif hasattr(self.saat, 'hour') and callable(self.saat.hour):
            # Eğer QTime nesnesi ise (metodları var), datetime.time'a çevir
            time_obj = datetime.time(self.saat.hour(), self.saat.minute())
            return datetime.datetime.combine(self.tarih, time_obj)
        else:
            # Diğer beklenmedik durumlar için None döndür
            return None        
    
    def is_gecmis(self):
        """Hatırlatıcının zamanı geçmiş mi kontrol eder"""
        return self.get_datetime() < datetime.datetime.now()
    
    def get_sonraki_tekrar_tarihi(self):
        """Bir sonraki tekrar tarihini hesaplar"""
        if self.tekrarlama_tipi == "yok":
            return None
            
        # Başlangıç tarihi olarak son tekrar tarihi veya orijinal tarih
        # record_log(f"🔄 [HATIRLATICI DEBUG] son_tekrar_tarihi: {self.son_tekrar_tarihi}, tarih: {self.tarih}")
        # baslangic_tarihi = self.son_tekrar_tarihi or self.tarih
        # Mustafa: 07.07.2025 "yapılmamış hatırlatıcılar" bölümüne yanlış aktarımları engellemek için denendi:
        baslangic_tarihi = self.tarih

        if self.tekrarlama_tipi == "gun":
            sonraki_tarih = baslangic_tarihi + datetime.timedelta(days=self.tekrarlama_araligi)
            # record_log(f"🔄 [HATIRLATICI DEBUG] başlangıç tarihi: {baslangic_tarihi} sonraki tarih: {sonraki_tarih}")
        elif self.tekrarlama_tipi == "hafta":
            # Haftalık tekrarlama için
            if self.hafta_gunu is None:
                return None
            
            # Kaç hafta sonra olacağını hesapla
            hafta_sayisi = self.tekrarlama_araligi
            gun_sayisi = hafta_sayisi * 7
            
            # Başlangıç tarihinden itibaren belirtilen hafta sayısı kadar ileri git
            temp_tarih = baslangic_tarihi + datetime.timedelta(days=gun_sayisi)
            
            # Hedef haftanın gününü bul
            # temp_tarih'in haftanın hangi günü olduğunu bul
            mevcut_hafta_gunu = temp_tarih.weekday()  # 0=Pazartesi, 6=Pazar
            
            # Hedef güne ulaşmak için gereken gün farkını hesapla
            gun_farki = self.hafta_gunu - mevcut_hafta_gunu
            if gun_farki < 0:
                gun_farki += 7  # Bir sonraki haftaya geç
            
            sonraki_tarih = temp_tarih + datetime.timedelta(days=gun_farki)
            
        elif self.tekrarlama_tipi == "ay":
            # Ay ekleme için relativedelta kullanmak daha iyi olur, basit versiyonda:
            yil = baslangic_tarihi.year
            ay = baslangic_tarihi.month + self.tekrarlama_araligi
            gun = baslangic_tarihi.day
            
            # Ay overflow kontrolü
            while ay > 12:
                yil += 1
                ay -= 12
            
            # Günün o ayda geçerli olup olmadığını kontrol et
            try:
                sonraki_tarih = datetime.date(yil, ay, gun)
            except ValueError:
                # Örneğin 31 Ocak + 1 ay = 28/29 Şubat
                import calendar
                son_gun = calendar.monthrange(yil, ay)[1]
                sonraki_tarih = datetime.date(yil, ay, min(gun, son_gun))
        else:
            return None
            
        return sonraki_tarih

    def sonraki_tekrari_olustur(self):
        """Tekrarlayan hatırlatıcı için bir sonraki örneği oluşturur"""
        if self.tekrarlama_tipi == "yok":
            return None
            
        sonraki_tarih = self.get_sonraki_tekrar_tarihi()
        if not sonraki_tarih:
            return None
            
        # Yeni ID gerekecek - bu ana uygulama tarafından ayarlanacak
        yeni_hatirlatici = Hatirlatici(
            id=0,  # Ana uygulamada ayarlanacak
            tarih=sonraki_tarih,
            saat=self.saat,
            not_metni=self.not_metni,
            yapildi=False,
            tekrarlama_tipi=self.tekrarlama_tipi,
            tekrarlama_araligi=self.tekrarlama_araligi,
            son_tekrar_tarihi=self.tarih
        )
        
        return yeni_hatirlatici

    def to_dict(self):
        return {
            'id': self.id,
            'tarih': self.tarih.isoformat(),
            'saat': self.saat.toString("HH:mm"),
            'not_metni': self.not_metni,
            'yapildi': self.yapildi,
            'olusturma_zamani': self.olusturma_zamani.isoformat(),
            'tekrarlama_tipi': self.tekrarlama_tipi,
            'tekrarlama_araligi': self.tekrarlama_araligi,
            'son_tekrar_tarihi': self.son_tekrar_tarihi.isoformat() if self.son_tekrar_tarihi else None,
            'hafta_gunu': self.hafta_gunu,
            'ertelendi': self.ertelendi 
        }
    
    @classmethod
    def from_dict(cls, data):
        son_tekrar_tarihi = None
        if data.get('son_tekrar_tarihi'):
            son_tekrar_tarihi = datetime.date.fromisoformat(data['son_tekrar_tarihi'])

        return cls(
            id=data['id'],
            tarih=datetime.date.fromisoformat(data['tarih']),
            saat=QTime.fromString(data['saat'], "HH:mm"),
            not_metni=data['not_metni'],
            yapildi=data.get('yapildi', False),
            olusturma_zamani=datetime.datetime.fromisoformat(data.get('olusturma_zamani', datetime.datetime.now().isoformat())),
            tekrarlama_tipi=data.get('tekrarlama_tipi', 'yok'),
            tekrarlama_araligi=data.get('tekrarlama_araligi', 1),
            son_tekrar_tarihi=son_tekrar_tarihi,
            hafta_gunu=data.get('hafta_gunu', None),
            ertelendi=data.get('ertelendi', False)  
        )

class HatirlaticiDialog(QDialog):
    def __init__(self, parent=None, hatirlatici=None):
        super().__init__(parent)
        self.hatirlatici = hatirlatici
        self.setWindowTitle("Hatırlatıcı Ekle/Düzenle")
        self.resize(400, 300)
        self.setup_ui()
        
        if hatirlatici:
            self.load_hatirlatici()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tarih seçimi
        tarih_layout = QHBoxLayout()
        tarih_layout.addWidget(QLabel("Tarih:"))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        tarih_layout.addWidget(self.tarih_edit)
        layout.addLayout(tarih_layout)
        
        # Saat seçimi
        saat_layout = QHBoxLayout()
        saat_layout.addWidget(QLabel("Saat:"))
        
        # QTimeEdit kullan (saat:dakika formatında yazılabilir)
        self.saat_edit = QTimeEdit()
        self.saat_edit.setTime(QTime.currentTime())
        self.saat_edit.setDisplayFormat("HH:mm")
        self.saat_edit.setTimeRange(QTime(0, 0), QTime(23, 59))
        saat_layout.addWidget(self.saat_edit)

        layout.addLayout(saat_layout)        
        
        # Not metni
        layout.addWidget(QLabel("Hatırlatma Metni:"))
        self.not_edit = QTextEdit()
        self.not_edit.setMaximumHeight(150)
        layout.addWidget(self.not_edit)

        # Tekrarlama bölümü
        tekrarlama_grup = QFrame()
        tekrarlama_grup.setFrameStyle(QFrame.Box)
        tekrarlama_layout = QVBoxLayout()
        
        # Tekrarlama başlığı
        tekrarlama_baslik = QLabel("Tekrarlama:")
        tekrarlama_baslik.setStyleSheet("font-weight: bold;")
        tekrarlama_layout.addWidget(tekrarlama_baslik)
        
        # Tekrarlama tipi seçimi
        self.tekrarlama_combo = QComboBox()
        self.tekrarlama_combo.addItems(["Tekrarlanmaz", "Her X günde bir", "Her X haftada bir", "Her X ayda bir"])
        self.tekrarlama_combo.currentIndexChanged.connect(self.tekrarlama_degisti)
        tekrarlama_layout.addWidget(self.tekrarlama_combo)
        
        # Aralık seçimi
        self.aralik_widget = QFrame()
        aralik_layout = QHBoxLayout(self.aralik_widget)  # Layout'u constructor'da belirt
        
        aralik_layout.addWidget(QLabel("Aralık:"))
        self.aralik_spin = QSpinBox()
        self.aralik_spin.setMinimum(1)
        self.aralik_spin.setMaximum(999)
        self.aralik_spin.setValue(1)
        aralik_layout.addWidget(self.aralik_spin)
        
        self.aralik_label = QLabel("")
        aralik_layout.addWidget(self.aralik_label)
        aralik_layout.addStretch()
        
        self.aralik_widget.setVisible(False)
        tekrarlama_layout.addWidget(self.aralik_widget)
        
        # Başlangıçta gizle
        self.aralik_widget = QFrame()
        self.aralik_widget.setLayout(aralik_layout)
        self.aralik_widget.setVisible(False)
        tekrarlama_layout.addWidget(self.aralik_widget)
        
        # Hafta günü seçimi 
        self.hafta_gunu_widget = QFrame()
        hafta_gunu_layout = QHBoxLayout(self.hafta_gunu_widget)  # Layout'u constructor'da belirt
        
        hafta_gunu_layout.addWidget(QLabel("Haftanın Günü:"))
        self.hafta_gunu_combo = QComboBox()
        self.hafta_gunu_combo.addItems([
            "Pazartesi", "Salı", "Çarşamba", "Perşembe", 
            "Cuma", "Cumartesi", "Pazar"
        ])
        hafta_gunu_layout.addWidget(self.hafta_gunu_combo)
        hafta_gunu_layout.addStretch()
        
        self.hafta_gunu_widget.setVisible(False)
        tekrarlama_layout.addWidget(self.hafta_gunu_widget)
        
        tekrarlama_grup.setLayout(tekrarlama_layout)
        layout.addWidget(tekrarlama_grup)

        # Butonlar
        button_layout = QHBoxLayout()
        self.kaydet_btn = QPushButton("Kaydet")
        self.iptal_btn = QPushButton("İptal")
        
        self.kaydet_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.kaydet_btn)
        button_layout.addWidget(self.iptal_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def tekrarlama_degisti(self):
        """Tekrarlama seçimi değiştiğinde arayüzü günceller"""
        secim = self.tekrarlama_combo.currentIndex()
        
        if secim == 0:  # Tekrarlanmaz
            self.aralik_widget.setVisible(False)
            self.hafta_gunu_widget.setVisible(False)
        elif secim == 1:  # Her X günde bir
            self.aralik_widget.setVisible(True)
            self.hafta_gunu_widget.setVisible(False)
            self.aralik_label.setText("gün")
        elif secim == 2:  # Her X haftada bir - YENİ EKLENEN
            self.aralik_widget.setVisible(True)
            self.hafta_gunu_widget.setVisible(True)
            self.aralik_label.setText("hafta")
        elif secim == 3:  # Her X ayda bir 
            self.aralik_widget.setVisible(True)
            self.hafta_gunu_widget.setVisible(False)
            self.aralik_label.setText("ay")

    def populate_saat_combo(self):
        """30 dakikalık aralıklarla saat seçeneklerini doldur"""
        for saat in range(24):
            for dakika in [0, 10, 20, 30, 40, 50]:
                zaman = QTime(saat, dakika)
                self.saat_combo.addItem(zaman.toString("HH:mm"), zaman)
    
    def load_hatirlatici(self):
        """Mevcut hatırlatıcı bilgilerini forma yükle"""
        self.tarih_edit.setDate(QDate(self.hatirlatici.tarih))
        
        # İlgili saat değeri
        self.saat_edit.setTime(self.hatirlatici.saat)

        self.not_edit.setPlainText(self.hatirlatici.not_metni)

        # Tekrarlama ayarlarını yükle
        if self.hatirlatici.tekrarlama_tipi == "yok":
            self.tekrarlama_combo.setCurrentIndex(0)
        elif self.hatirlatici.tekrarlama_tipi == "gun":
            self.tekrarlama_combo.setCurrentIndex(1)
        elif self.hatirlatici.tekrarlama_tipi == "hafta":  
            self.tekrarlama_combo.setCurrentIndex(2)
            if self.hatirlatici.hafta_gunu is not None:
                self.hafta_gunu_combo.setCurrentIndex(self.hatirlatici.hafta_gunu)
        elif self.hatirlatici.tekrarlama_tipi == "ay":
            self.tekrarlama_combo.setCurrentIndex(3)
        
        self.aralik_spin.setValue(self.hatirlatici.tekrarlama_araligi)
        self.tekrarlama_degisti()  # Arayüzü güncelle

    def get_values(self):
        """Form değerlerini döndür"""
        # Tekrarlama tipini belirle 
        tekrarlama_map = {0: "yok", 1: "gun", 2: "hafta", 3: "ay"}
        tekrarlama_tipi = tekrarlama_map[self.tekrarlama_combo.currentIndex()]
        print(f"🔄 [HATIRLATICI DEBUG] tekrarlama_tipi: {tekrarlama_tipi}")
        
        # Hafta günü değerini al
        hafta_gunu = None
        if tekrarlama_tipi == "hafta":
            hafta_gunu = self.hafta_gunu_combo.currentIndex()  # 0=Pazartesi, 6=Pazar
        
        return {
            'tarih': self.tarih_edit.date().toPyDate(),
            'saat': self.saat_edit.time(),
            'not_metni': self.not_edit.toPlainText().strip(),
            'tekrarlama_tipi': tekrarlama_tipi,
            'tekrarlama_araligi': self.aralik_spin.value(),
            'hafta_gunu': hafta_gunu  
        }
    
class HatirlaticiBildirimDialog(QDialog):
    def __init__(self, parent, hatirlatici):
        super().__init__(parent)
        self.hatirlatici = hatirlatici
        self.setWindowTitle("Hatırlatıcı")
        self.resize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        baslik = QLabel("Hatırlatıcı Zamanı!")
        baslik.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)
        
        # Tarih ve saat
        tarih_saat = QLabel(f"Tarih: {self.hatirlatici.tarih.strftime('%d.%m.%Y')} - Saat: {self.hatirlatici.saat.toString('HH:mm')}")
        tarih_saat.setAlignment(Qt.AlignCenter)
        layout.addWidget(tarih_saat)
        
        # Not metni
        not_label = QLabel("Hatırlatma:")
        not_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(not_label)
        
        not_text = QLabel(self.hatirlatici.not_metni)
        not_text.setWordWrap(True)
        not_text.setStyleSheet("background-color: #f5f5f5; padding: 10px; border: 1px solid #ccc;")
        layout.addWidget(not_text)
        
        # Butonlar
        button_layout = QHBoxLayout()
        self.yapildi_btn = QPushButton("Yapıldı")
        self.yapilmayacak_btn = QPushButton("Bu Kez Yapılmayacak")
        self.sonra_btn = QPushButton("Daha Sonra")
        
        self.yapildi_btn.clicked.connect(self.yapildi_clicked)
        self.yapilmayacak_btn.clicked.connect(self.yapilmayacak_clicked)
        self.sonra_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.yapildi_btn)
        button_layout.addWidget(self.yapilmayacak_btn)
        button_layout.addWidget(self.sonra_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def yapildi_clicked(self):
        self.done(2)  # Özel return kodu

    def yapilmayacak_clicked(self):
        # record_log(f"'{self.hatirlatici.not_metni}' başlıklı hatırlatıcı 'bu kez yapılmayacak' olarak işaretlendi.")
        self.done(3)  # özel return kodu
