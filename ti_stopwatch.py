"""
Kronometre yönetimi, arayüz bileşenleri ve tur işlemlerini sağlayan Mixin modülü.
"""

from PyQt5.QtWidgets import (
    QInputDialog, QLineEdit, QFrame, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QMenu
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from ti_models import Kronometre
from dialog_classes import ClickableFrame
from timer_logger import record_log
from timer_helpers import show_toast


class KronometreMixin:
    """Kronometre oluşturma, kontrol etme ve arayüz etkileşimlerini yöneten Mixin sınıfı."""

    def yeni_kronometre_baslat(self):
        """Yeni kronometre başlatmak için isim soran dialog açar"""
        isim, ok = QInputDialog.getText(
            self, 
            "Yeni Kronometre",
            "Kronometre için bir isim girin:",
            QLineEdit.Normal,
            f"Kronometre {self.kronometre_id_sayaci + 1}"
        )

        if ok and isim.strip():
            self.kronometre_id_sayaci += 1
            yeni_kronometre = Kronometre(
                id=self.kronometre_id_sayaci,
                isim=isim.strip()
            )
            self.aktif_kronometreler.append(yeni_kronometre)
            self.kronometre_widget_olustur(yeni_kronometre)
            self.ayarlari_kaydet()
            record_log(f"⏱️ Yeni kronometre başlatıldı: {yeni_kronometre.isim}")
            show_toast(self, 'Yeni Kronometre', f"{yeni_kronometre.isim} başlatıldı", 5000)

    def kronometre_widget_olustur(self, kronometre):
        """Kronometre için widget oluşturur"""
        kronometre_cerceve = ClickableFrame(f"kronometre_{kronometre.id}")
        kronometre_cerceve.setObjectName(f"kronometre_{kronometre.id}")
        kronometre_cerceve.setFrameStyle(QFrame.Box | QFrame.Raised)
        kronometre_cerceve.setLineWidth(1)
        kronometre_cerceve.setFixedHeight(55)  # Kronometre satırının sabit yüksekliği

        kronometre_cerceve.setContextMenuPolicy(Qt.CustomContextMenu)
        kronometre_cerceve.customContextMenuRequested.connect(
            lambda pos, k_id=kronometre.id: self.kronometre_sag_tik_menu(pos, k_id)
        )

        if kronometre.calisma_durumu:
            kronometre_cerceve.setStyleSheet(f"""
                #kronometre_{kronometre.id} {{
                    background-color: #e8f5e9;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                }}
                QLabel {{
                    border: none;
                }}
            """)
        else:
            kronometre_cerceve.setStyleSheet(f"""
                #kronometre_{kronometre.id} {{
                    background-color: #fff8e1;
                    border: 1px solid #ff9800;
                    border-radius: 4px;
                }}
                QLabel {{
                    border: none;
                }}
            """)

        kronometre_duzen = QHBoxLayout()
        kronometre_duzen.setContentsMargins(6, 2, 6, 2)
        kronometre_duzen.setSpacing(6)

        ikon_label = QLabel("⏱️")
        ikon_label.setStyleSheet("font-size: 18px; border: none;")
        ikon_label.setObjectName(f"krono_ikon_{kronometre.id}")
        kronometre_duzen.addWidget(ikon_label)

        isim_label = QLabel(kronometre.isim)
        isim_label.setMinimumWidth(150)
        isim_label.setObjectName(f"krono_isim_{kronometre.id}")
        isim_label.setFont(QFont("Arial", 10, QFont.Bold))
        kronometre_duzen.addWidget(isim_label)

        sure_label = QLabel(kronometre.get_formatted_time())
        sure_label.setObjectName(f"krono_sure_{kronometre.id}")
        sure_label.setAlignment(Qt.AlignCenter)
        sure_label.setFont(QFont("Consolas", 14, QFont.Bold))
        sure_label.setStyleSheet("color: #2e7d32;")
        kronometre_duzen.addWidget(sure_label)

        tur_label = QLabel("")
        tur_label.setObjectName(f"krono_tur_{kronometre.id}")
        tur_label.setMinimumWidth(80)
        if kronometre.turlar:
            son_tur = kronometre.turlar[-1]
            tur_label.setText(f"Tur {son_tur[0]}")
        kronometre_duzen.addWidget(tur_label)

        tur_dugme = QPushButton("🏁 Tur")
        tur_dugme.setObjectName(f"krono_tur_btn_{kronometre.id}")
        tur_dugme.clicked.connect(lambda checked, k_id=kronometre.id: self.kronometre_tur_ekle(k_id))
        tur_dugme.setToolTip("Tur ekle")
        kronometre_duzen.addWidget(tur_dugme)

        durum_metni = "⏸️ Duraklat" if kronometre.calisma_durumu else "▶️ Devam"
        durdur_dugme = QPushButton(durum_metni)
        durdur_dugme.setObjectName(f"krono_durdur_{kronometre.id}")
        durdur_dugme.clicked.connect(lambda checked, k_id=kronometre.id: self.kronometre_durdur_devam(k_id))
        kronometre_duzen.addWidget(durdur_dugme)

        kapat_dugme = QPushButton("❌ Kapat")
        kapat_dugme.setObjectName(f"krono_kapat_{kronometre.id}")
        kapat_dugme.clicked.connect(lambda checked, k_id=kronometre.id: self.kronometre_kapat(k_id))
        kapat_dugme.setStyleSheet("background-color: #ffcdd2;")
        kronometre_duzen.addWidget(kapat_dugme)

        kronometre_cerceve.setLayout(kronometre_duzen)
        self.aktif_zamanlayicilar_alan.addWidget(kronometre_cerceve)

    def kronometre_durdur_devam(self, kronometre_id):
        """Kronometreyi durdurur veya devam ettirir"""
        for kronometre in self.aktif_kronometreler:
            if kronometre.id == kronometre_id:
                kronometre.calisma_durumu = not kronometre.calisma_durumu

                cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
                if cerceve:
                    durdur_dugme = cerceve.findChild(QPushButton, f"krono_durdur_{kronometre_id}")
                    if durdur_dugme:
                        if kronometre.calisma_durumu:
                            durdur_dugme.setText("⏸️ Duraklat")
                            cerceve.setStyleSheet(f"""
                                #kronometre_{kronometre_id} {{
                                    background-color: #e8f5e9;
                                    border: 1px solid #4caf50;
                                    border-radius: 4px;
                                }}
                                QLabel {{
                                    border: none;
                                }}
                            """)
                        else:
                            durdur_dugme.setText("▶️ Devam")
                            cerceve.setStyleSheet(f"""
                                #kronometre_{kronometre_id} {{
                                    background-color: #fff8e1;
                                    border: 1px solid #ff9800;
                                    border-radius: 4px;
                                }}
                                QLabel {{
                                    border: none;
                                }}
                            """)

                durum = "devam ediyor" if kronometre.calisma_durumu else "duraklatıldı"
                record_log(f"⏱️ Kronometre '{kronometre.isim}' {durum}")
                self.ayarlari_kaydet()
                break

    def kronometre_kapat(self, kronometre_id):
        """Kronometreyi kapatır"""
        for i, kronometre in enumerate(self.aktif_kronometreler):
            if kronometre.id == kronometre_id:
                cevap = QMessageBox.question(
                    self,
                    "Kronometreyi Kapat",
                    f"'{kronometre.isim}' kronometresini kapatmak istiyor musunuz?\n\nGeçen süre: {kronometre.get_formatted_time()}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if cevap == QMessageBox.Yes:
                    cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
                    if cerceve:
                        self.aktif_zamanlayicilar_alan.removeWidget(cerceve)
                        cerceve.deleteLater()

                    self.aktif_kronometreler.pop(i)
                    record_log(f"⏱️ Kronometre '{kronometre.isim}' kapatıldı (Süre: {kronometre.get_formatted_time()})")
                    self.ayarlari_kaydet()
                break

    def kronometre_tur_ekle(self, kronometre_id):
        """Kronometreye tur ekler"""
        for kronometre in self.aktif_kronometreler:
            if kronometre.id == kronometre_id:
                tur_no, toplam_sure, tur_suresi = kronometre.tur_ekle()

                cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
                if cerceve:
                    tur_label = cerceve.findChild(QLabel, f"krono_tur_{kronometre_id}")
                    if tur_label:
                        tur_label.setText(f"Tur {tur_no}")

                tur_sure_str = f"{tur_suresi // 3600:02d}:{(tur_suresi % 3600) // 60:02d}:{tur_suresi % 60:02d}"
                record_log(f"🏁 Kronometre '{kronometre.isim}' - Tur {tur_no}: {tur_sure_str}")
                show_toast(self, f"Tur {tur_no}", f"{kronometre.isim}: {tur_sure_str}", 3000)
                self.ayarlari_kaydet()
                break

    def kronometre_sag_tik_menu(self, position, kronometre_id):
        """Kronometre için sağ tık context menüsü"""
        kronometre = None
        for k in self.aktif_kronometreler:
            if k.id == kronometre_id:
                kronometre = k
                break

        if not kronometre:
            return

        menu = QMenu(self)

        tur_action = menu.addAction("🏁 Tur Ekle")

        if kronometre.turlar:
            turlar_menu = menu.addMenu("📋 Turları Göster")
            for tur in kronometre.turlar:
                tur_no, toplam, tur_suresi = tur
                tur_str = f"{tur_suresi // 3600:02d}:{(tur_suresi % 3600) // 60:02d}:{tur_suresi % 60:02d}"
                toplam_str = f"{toplam // 3600:02d}:{(toplam % 3600) // 60:02d}:{toplam % 60:02d}"
                turlar_menu.addAction(f"Tur {tur_no}: {tur_str} (Toplam: {toplam_str})")

        menu.addSeparator()

        sifirla_action = menu.addAction("🔄 Sıfırla")
        isim_action = menu.addAction("✏️ İsmi Değiştir")

        menu.addSeparator()

        if kronometre.calisma_durumu:
            durdur_action = menu.addAction("⏸️ Duraklat")
        else:
            durdur_action = menu.addAction("▶️ Devam Et")

        kapat_action = menu.addAction("❌ Kronometreyi Kapat")

        cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
        if cerceve:
            action = menu.exec_(cerceve.mapToGlobal(position))

            if action == tur_action:
                self.kronometre_tur_ekle(kronometre_id)
            elif action == sifirla_action:
                self.kronometre_sifirla(kronometre_id)
            elif action == isim_action:
                self.kronometre_isim_degistir(kronometre_id)
            elif action == durdur_action:
                self.kronometre_durdur_devam(kronometre_id)
            elif action == kapat_action:
                self.kronometre_kapat(kronometre_id)

    def kronometre_sifirla(self, kronometre_id):
        """Kronometreyi sıfırlar"""
        for kronometre in self.aktif_kronometreler:
            if kronometre.id == kronometre_id:
                cevap = QMessageBox.question(
                    self,
                    "Kronometreyi Sıfırla",
                    f"'{kronometre.isim}' kronometresini sıfırlamak istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if cevap == QMessageBox.Yes:
                    kronometre.sifirla()

                    cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
                    if cerceve:
                        sure_label = cerceve.findChild(QLabel, f"krono_sure_{kronometre_id}")
                        if sure_label:
                            sure_label.setText(kronometre.get_formatted_time())
                        tur_label = cerceve.findChild(QLabel, f"krono_tur_{kronometre_id}")
                        if tur_label:
                            tur_label.setText("")

                    record_log(f"🔄 Kronometre '{kronometre.isim}' sıfırlandı")
                    self.ayarlari_kaydet()
                break

    def kronometre_isim_degistir(self, kronometre_id):
        """Kronometre ismini değiştirir"""
        for kronometre in self.aktif_kronometreler:
            if kronometre.id == kronometre_id:
                yeni_isim, ok = QInputDialog.getText(
                    self,
                    "İsim Değiştir",
                    "Yeni isim girin:",
                    QLineEdit.Normal,
                    kronometre.isim
                )

                if ok and yeni_isim.strip():
                    eski_isim = kronometre.isim
                    kronometre.isim = yeni_isim.strip()

                    cerceve = self.findChild(QFrame, f"kronometre_{kronometre_id}")
                    if cerceve:
                        isim_label = cerceve.findChild(QLabel, f"krono_isim_{kronometre_id}")
                        if isim_label:
                            isim_label.setText(kronometre.isim)

                    record_log(f"✏️ Kronometre ismi değiştirildi: '{eski_isim}' -> '{kronometre.isim}'")
                    self.ayarlari_kaydet()
                break
