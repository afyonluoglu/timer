"""
Zamanlayıcı uygulamasının ana görsel bileşenlerini, panellerini ve kısayollarını inşa eden Mixin modülü.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QScrollArea, QWidget, QSplitter, QListWidget, QAbstractItemView,
    QShortcut, QFrame
)
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import Qt


class UIBuilderMixin:
    """Zamanlayıcı ana penceresinin panellerini ve görsel bileşenlerini kuran Mixin sınıfı."""

    def kisayol_tuslari_ayarla(self):
        """Klavye kısayollarını ayarla"""
        self.favori_kisayol = QShortcut(QKeySequence("F"), self)
        self.favori_kisayol.activated.connect(self.favorileri_goster)

        self.gecmis_kisayol = QShortcut(QKeySequence("G"), self)
        self.gecmis_kisayol.activated.connect(self.gecmisi_goster)

        self.kapat_kisayol = QShortcut(QKeySequence("Escape"), self)
        self.kapat_kisayol.activated.connect(self.panelleri_kapat)

    def panelleri_kapat(self):
        """ESC tuşu ile açık panelleri kapat"""
        if self.gecmis_listesi_widget.isVisible():
            self.gecmisi_goster()
        elif self.favori_listesi_widget.isVisible():
            self.favorileri_goster()

    def arayuzu_olustur(self):
        """Ana arayüz düzenini ve alt bileşenleri kurar"""
        ana_duzen = QVBoxLayout()

        aktif_baslik_duzen = QHBoxLayout()

        aktif_baslik = QLabel("Aktif Sayaçlar:")
        aktif_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        aktif_baslik_duzen.addWidget(aktif_baslik)

        aktif_baslik_duzen.addStretch()

        self.baslat_dugme = QPushButton("⏱️ Yeni Zamanlayıcı")
        self.baslat_dugme.setFont(QFont("Arial", 11, QFont.Bold))
        self.baslat_dugme.setFixedHeight(40) 
        self.baslat_dugme.setStyleSheet("""
            QPushButton {
                background-color: #172668;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #75d6ff;
                color: #004285;
            }
        """)
        self.baslat_dugme.clicked.connect(self.yeni_zamanlayici_baslat)
        self.baslat_dugme.setCursor(Qt.PointingHandCursor)
        aktif_baslik_duzen.addWidget(self.baslat_dugme)

        self.kronometre_dugme = QPushButton("⏱️ Yeni Kronometre")
        self.kronometre_dugme.setFont(QFont("Arial", 11, QFont.Bold))
        self.kronometre_dugme.setFixedHeight(40)
        self.kronometre_dugme.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81c784;
                color: #1b5e20;
            }
        """)
        self.kronometre_dugme.clicked.connect(self.yeni_kronometre_baslat)
        self.kronometre_dugme.setCursor(Qt.PointingHandCursor)
        aktif_baslik_duzen.addWidget(self.kronometre_dugme)

        aktif_baslik_duzen.addStretch()

        self.saat_label = QLabel()
        self.saat_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.saat_label.setStyleSheet("color: #8d0000ff;") 
        self.saat_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        aktif_baslik_duzen.addWidget(self.saat_label)

        aktif_baslik_widget = QWidget()
        aktif_baslik_widget.setLayout(aktif_baslik_duzen)
        aktif_baslik_widget.setFixedHeight(50)

        ana_duzen.addWidget(aktif_baslik_widget)

        self.aktif_zamanlayicilar_alan = QVBoxLayout()
        self.aktif_zamanlayicilar_alan.setAlignment(Qt.AlignTop)  

        scroll_cerceve = QFrame()
        scroll_cerceve.setLayout(self.aktif_zamanlayicilar_alan)

        self.scroll_alan = QScrollArea()
        self.scroll_alan.setWidgetResizable(True)
        self.scroll_alan.setWidget(scroll_cerceve)
        self.scroll_alan.setMinimumHeight(150)
        self.scroll_alan.setMaximumHeight(220)
        ana_duzen.addWidget(self.scroll_alan)

        hatirlatici_duzen = QVBoxLayout()

        hatirlatici_baslik_duzen = QHBoxLayout()
        hatirlatici_baslik = QLabel("Hatırlatıcılar:")
        hatirlatici_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        hatirlatici_baslik_duzen.addWidget(hatirlatici_baslik)

        self.yeni_hatirlatici_btn = QPushButton("📅 Yeni Hatırlatıcı")
        self.yeni_hatirlatici_btn.clicked.connect(self.hatirlatici_manager.yeni_hatirlatici_ekle)
        self.yeni_hatirlatici_btn.setCursor(Qt.PointingHandCursor)
        hatirlatici_baslik_duzen.addWidget(self.yeni_hatirlatici_btn)

        hatirlatici_duzen.addLayout(hatirlatici_baslik_duzen)

        self.hatirlatici_splitter = QSplitter(Qt.Horizontal)

        sol_widget = QWidget()
        sol_duzen = QVBoxLayout()
        sol_duzen.addWidget(QLabel("Tüm Hatırlatıcılar:"))
        self.tum_hatirlaticilar_list = QListWidget()
        self.tum_hatirlaticilar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tum_hatirlaticilar_list.customContextMenuRequested.connect(self.hatirlatici_manager.hatirlatici_sag_tik_menu)
        self.tum_hatirlaticilar_list.setStyleSheet("""
            QListWidget {
                background-color: #e8f5e8;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #00a534;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #00561b;
                color: rgb(255,255,255);
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #00561b;
                color: #ffff99;
            }
        """)
        sol_duzen.addWidget(self.tum_hatirlaticilar_list)
        sol_widget.setLayout(sol_duzen)

        sag_widget = QWidget()
        sag_duzen = QVBoxLayout()
        sag_duzen.addWidget(QLabel("Yapılmamış Hatırlatıcılar:"))
        self.gecmis_hatirlaticilar_list = QListWidget()
        self.gecmis_hatirlaticilar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.gecmis_hatirlaticilar_list.customContextMenuRequested.connect(self.hatirlatici_manager.gecmis_hatirlatici_sag_tik_menu)
        self.gecmis_hatirlaticilar_list.setStyleSheet("""
            QListWidget {
                background-color: #fff2f2;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #d32f2f;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #b71c1c;
                color: rgb(255,255,255);
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #9a0007;
                color: #ffff99;
            }
        """)
        sag_duzen.addWidget(self.gecmis_hatirlaticilar_list)
        sag_widget.setLayout(sag_duzen)

        self.hatirlatici_splitter.addWidget(sol_widget)
        self.hatirlatici_splitter.addWidget(sag_widget)
        self.hatirlatici_splitter.setSizes([700, 300])

        self.hatirlatici_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #6392FF;
                width: 2px;
                border: 1px solid #aaaaaa;
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background-color: #999999;
            }
        """)
        self.hatirlatici_splitter.splitterMoved.connect(self.splitter_pozisyonu_kaydet)

        hatirlatici_duzen.addWidget(self.hatirlatici_splitter)

        dogal_dil_duzen = QHBoxLayout()
        self.natural_input = QLineEdit()
        self.natural_input.setPlaceholderText("Doğal dilde hatırlatıcı girin: örn. 'Her gün/hafta/ay saat 12:30'da ara öğün yap   5 dakika/saat/gün sonra Youtube seyret'")
        dogal_dil_duzen.addWidget(self.natural_input)

        self.natural_input_btn = QPushButton("✨ NLP ile Hatırlatıcı Oluştur")
        self.natural_input_btn.clicked.connect(self.natural_language_timer)
        dogal_dil_duzen.addWidget(self.natural_input_btn)

        hatirlatici_duzen.addLayout(dogal_dil_duzen)

        hatirlatici_widget = QWidget()
        hatirlatici_widget.setLayout(hatirlatici_duzen)

        gecmis_duzen = QVBoxLayout()

        gecmis_baslik_duzen = QHBoxLayout()
        gecmis_baslik = QLabel("Zamanlayıcı Geçmişi:")
        gecmis_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        gecmis_baslik_duzen.addWidget(gecmis_baslik)

        self.gecmis_dugme = QPushButton("GEÇMİŞİ GİZLE")
        self.gecmis_dugme.clicked.connect(self.gecmisi_goster)
        gecmis_baslik_duzen.addWidget(self.gecmis_dugme)

        self.sil_dugme = QPushButton("Seçilen Geçmişi Sil")
        self.sil_dugme.clicked.connect(self.secilen_gecmisi_sil)
        self.sil_dugme.setEnabled(False)
        gecmis_baslik_duzen.addWidget(self.sil_dugme)

        gecmis_duzen.addLayout(gecmis_baslik_duzen)

        self.gecmis_listesi_widget = QListWidget()
        self.gecmis_listesi_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.gecmis_listesi_widget.setVisible(True)
        self.gecmis_listesi_widget.itemSelectionChanged.connect(self.gecmis_secimi_degisti)
        self.gecmis_listesi_widget.itemDoubleClicked.connect(self.gecmis_zamanlayici_baslat)
        self.gecmis_listesi_widget.setStyleSheet("""
            QListWidget {
                background-color: #ccebff;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #004c80;
                color: rgb(255,255,255);
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #005599;
                color: #ffff99;
            }
        """)
        gecmis_duzen.addWidget(self.gecmis_listesi_widget)

        self.gecmis_listesi_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.gecmis_listesi_widget.customContextMenuRequested.connect(self.gecmis_sag_tik_menu)

        gecmis_widget = QWidget()
        gecmis_widget.setLayout(gecmis_duzen)

        self.ana_bolum_splitter = QSplitter(Qt.Vertical)
        self.ana_bolum_splitter.addWidget(hatirlatici_widget)
        self.ana_bolum_splitter.addWidget(gecmis_widget)
        self.ana_bolum_splitter.setSizes([420, 180])

        self.ana_bolum_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #6392FF;
                height: 2px;
                border: 1px solid #666666;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #950505;
            }
        """)
        self.ana_bolum_splitter.splitterMoved.connect(self.splitter_pozisyonu_kaydet)

        ana_duzen.addWidget(self.ana_bolum_splitter)

        favori_duzen = QVBoxLayout()

        favori_baslik_duzen = QHBoxLayout()
        favori_baslik = QLabel("Favori Zamanlayıcılar:")
        favori_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        favori_baslik_duzen.addWidget(favori_baslik)

        self.favori_dugme = QPushButton("FAVORİLERİ GİZLE")
        self.favori_dugme.clicked.connect(self.favorileri_goster)
        favori_baslik_duzen.addWidget(self.favori_dugme)

        self.favori_sil_dugme = QPushButton("Seçilen Favorileri Sil")
        self.favori_sil_dugme.clicked.connect(self.secilen_favorileri_sil)
        self.favori_sil_dugme.setEnabled(False)
        favori_baslik_duzen.addWidget(self.favori_sil_dugme)

        favori_duzen.addLayout(favori_baslik_duzen)

        self.favori_listesi_widget = QListWidget()
        self.favori_listesi_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.favori_listesi_widget.setVisible(True)
        self.favori_listesi_widget.itemSelectionChanged.connect(self.favori_secimi_degisti)
        self.favori_listesi_widget.itemDoubleClicked.connect(self.favori_zamanlayici_baslat)
        self.favori_listesi_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favori_listesi_widget.customContextMenuRequested.connect(self.favori_sag_tik_menu)
        self.favori_listesi_widget.setMaximumHeight(220)
        self.favori_listesi_widget.setStyleSheet("""
            QListWidget {
                background-color: #ccffdc;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #00a534;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #00561b;
                color: rgb(255,255,255);
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #00561b;
                color: #ffff99;
            }
        """)

        favori_duzen.addWidget(self.favori_listesi_widget)
        ana_duzen.addLayout(favori_duzen)

        self.setLayout(ana_duzen)

