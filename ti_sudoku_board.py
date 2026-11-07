"""
Sudoku hücre stilleri, tahta görselleştirmesi ve hücre etkileşimlerini yöneten Mixin modülü.
"""

import random
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class SudokuBoardMixin:
    """Sudoku tahta görselleştirmesi, hücre stilleri ve kullanıcı etkileşim mixini."""

    SABIT_RENK = "color: black; font-weight: bold;"
    KULLANICI_RENK = "color: #4169E1;"
    IPUCU_ARKAPLAN = "#2E8B57"  # Koyu yeşil (Sea Green)
    IPUCU_YAZI = "color: white; font-weight: bold;"
    HATA_ARKAPLAN = "#FFB6C1"  # Açık pembe (Light Pink)
    SECILI_ARKAPLAN = "#60EB60"  # Açık yeşil (Light Green)
    KULLANICI_ARKAPLAN = "#C4FF85"  # Açık yeşil-sarı
    NORMAL_ARKAPLAN = "white"
    VURGULU_ARKAPLAN = "#E8E8E8"  # Aynı satır/sütun/bölge için açık gri
    AYNI_SAYI_ARKAPLAN = "#FFD700"  # Aynı sayı için altın sarısı

    def normal_hucre_stili(self, satir, sutun):
        """Hücrenin temel stilini döndürür"""
        return (
            "QPushButton { "
            "background-color: white; "
            "border: 1px solid gray; "
            f"margin: {2 if satir % 3 == 0 else 0}px {2 if sutun % 3 == 0 else 0}px "
            f"{2 if satir % 3 == 2 else 0}px {2 if sutun % 3 == 2 else 0}px; "
            "padding: 0px; "
            "} "
        )

    def hucre_vurgulu_mu(self, satir, sutun):
        """Hücrenin vurgulanması gerekip gerekmediğini kontrol et"""
        if not self.secili_hucre:
            return False, False

        secili_satir, secili_sutun = self.secili_hucre
        secili_deger = self.tahta[secili_satir][secili_sutun].deger
        hucre_deger = self.tahta[satir][sutun].deger

        ayni_sayi = secili_deger != 0 and hucre_deger == secili_deger and (satir, sutun) != self.secili_hucre
        ayni_satir = satir == secili_satir
        ayni_sutun = sutun == secili_sutun
        ayni_bolge = (satir // 3 == secili_satir // 3) and (sutun // 3 == secili_sutun // 3)
        ilgili_hucre = (ayni_satir or ayni_sutun or ayni_bolge) and (satir, sutun) != self.secili_hucre

        return ayni_sayi, ilgili_hucre

    def hucre_stilini_guncelle(self, satir, sutun, secili=False):
        """Hücrenin stilini durumuna göre günceller"""
        buton = self.hucre_butonlari[satir][sutun]
        hucre = self.tahta[satir][sutun]

        margin_top = 2 if satir % 3 == 0 else 0
        margin_left = 2 if sutun % 3 == 0 else 0
        margin_bottom = 2 if satir % 3 == 2 else 0
        margin_right = 2 if sutun % 3 == 2 else 0

        ayni_sayi, ilgili_hucre = self.hucre_vurgulu_mu(satir, sutun)

        if (satir, sutun) in self.ipucu_hucreleri:
            stil = f"""
                QPushButton {{
                    background-color: {self.IPUCU_ARKAPLAN};
                    {self.IPUCU_YAZI}
                    border: {'2px solid blue' if secili else '1px solid gray'};
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif (satir, sutun) in self.hatali_hucreler:
            stil = f"""
                QPushButton {{
                    background-color: {self.HATA_ARKAPLAN};
                    {self.KULLANICI_RENK}
                    border: {'2px solid blue' if secili else '1px solid gray'};
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif secili:
            if hucre.sabit:
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                renk = self.KULLANICI_RENK
            else:
                renk = ""

            stil = f"""
                QPushButton {{
                    background-color: {self.SECILI_ARKAPLAN};
                    {renk}
                    border: 2px solid blue;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif ayni_sayi:
            if hucre.sabit:
                renk = self.SABIT_RENK
            else:
                renk = self.KULLANICI_RENK

            stil = f"""
                QPushButton {{
                    background-color: {self.AYNI_SAYI_ARKAPLAN};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif ilgili_hucre:
            if hucre.sabit:
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                renk = self.KULLANICI_RENK
            else:
                renk = ""

            stil = f"""
                QPushButton {{
                    background-color: {self.VURGULU_ARKAPLAN};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        else:
            if hucre.sabit:
                arkaplan = self.NORMAL_ARKAPLAN
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                arkaplan = self.KULLANICI_ARKAPLAN
                renk = self.KULLANICI_RENK
            else:
                arkaplan = self.NORMAL_ARKAPLAN
                renk = ""

            stil = f"""
                QPushButton {{
                    background-color: {arkaplan};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """

        buton.setStyleSheet(stil)

    def hucreyi_guncelle(self, satir, sutun):
        """Hücrenin içeriğini güncelle (sayı veya notlar)"""
        buton = self.hucre_butonlari[satir][sutun]
        hucre = self.tahta[satir][sutun]

        if hucre.deger != 0:
            buton.setText(str(hucre.deger))
            buton.setFont(QFont('Arial', 16))
        elif self.notlar[satir][sutun]:
            not_metni = ""
            for n in range(1, 10):
                if n in self.notlar[satir][sutun]:
                    not_metni += str(n)
                else:
                    not_metni += " "
                if n % 3 == 0 and n < 9:
                    not_metni += "\n"
            buton.setText(not_metni)
            buton.setFont(QFont('Arial', 8))
        else:
            buton.setText("")
            buton.setFont(QFont('Arial', 16))

    def tahtayi_guncelle(self):
        """Tahtayı görsel olarak güncelle"""
        for i in range(9):
            for j in range(9):
                hucre = self.tahta[i][j]
                buton = self.hucre_butonlari[i][j]

                if hucre.deger != 0:
                    buton.setText(str(hucre.deger))
                    if hucre.sabit:
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
                        buton.setStyleSheet("""
                            QPushButton {
                                background-color: #C4FF85; 
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

    def tum_hucreleri_guncelle(self):
        """Tüm hücrelerin stillerini güncelle (vurgulama için)"""
        for i in range(9):
            for j in range(9):
                secili = self.secili_hucre == (i, j)
                self.hucre_stilini_guncelle(i, j, secili=secili)

    def hucre_secildi(self, satir, sutun):
        """Bir hücre seçildiğinde çağrılır"""
        self.secili_hucre = (satir, sutun)
        self.tum_hucreleri_guncelle()

    def ok_tusu_hareketi(self, key):
        """Ok tuşları ile hücre hareketi"""
        if not self.secili_hucre:
            self.hucre_secildi(0, 0)
            return

        satir, sutun = self.secili_hucre

        if key == Qt.Key_Up and satir > 0:
            self.hucre_secildi(satir - 1, sutun)
        elif key == Qt.Key_Down and satir < 8:
            self.hucre_secildi(satir + 1, sutun)
        elif key == Qt.Key_Left and sutun > 0:
            self.hucre_secildi(satir, sutun - 1)
        elif key == Qt.Key_Right and sutun < 8:
            self.hucre_secildi(satir, sutun + 1)

    def gecmise_ekle(self, satir, sutun, eski_deger, yeni_deger):
        """Bir hamleyi geçmişe ekle"""
        if self.gecmis_index < len(self.gecmis) - 1:
            self.gecmis = self.gecmis[:self.gecmis_index + 1]

        self.gecmis.append((satir, sutun, eski_deger, yeni_deger))
        self.gecmis_index = len(self.gecmis) - 1

    def geri_al(self):
        """Son hamleyi geri al"""
        if not self.oyun_aktif or self.gecmis_index < 0:
            return

        satir, sutun, eski_deger, yeni_deger = self.gecmis[self.gecmis_index]
        self.gecmis_index -= 1

        self.tahta[satir][sutun].deger = eski_deger
        if eski_deger == 0:
            self.hucre_butonlari[satir][sutun].setText("")
        else:
            self.hucre_butonlari[satir][sutun].setText(str(eski_deger))

        if eski_deger == 0 or eski_deger == self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.discard((satir, sutun))
        elif eski_deger != self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.add((satir, sutun))

        self.hucre_stilini_guncelle(satir, sutun)

    def ileri_al(self):
        """Geri alınan hamleyi tekrar yap"""
        if not self.oyun_aktif or self.gecmis_index >= len(self.gecmis) - 1:
            return

        self.gecmis_index += 1
        satir, sutun, eski_deger, yeni_deger = self.gecmis[self.gecmis_index]

        self.tahta[satir][sutun].deger = yeni_deger
        if yeni_deger == 0:
            self.hucre_butonlari[satir][sutun].setText("")
        else:
            self.hucre_butonlari[satir][sutun].setText(str(yeni_deger))

        if yeni_deger == 0 or yeni_deger == self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.discard((satir, sutun))
        elif yeni_deger != self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.add((satir, sutun))

        self.hucre_stilini_guncelle(satir, sutun)

    def otomatik_kontrol(self):
        """Tüm hücreler doluysa otomatik olarak kontrol et"""
        if not self.oyun_aktif:
            return

        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    return

        self.cozumu_kontrol_et()

    def ipucu_goster(self):
        """Rastgele bir boş hücreye doğru sayıyı yerleştir. Mevcut puanı 10 puan azaltır"""
        if not self.oyun_aktif or not self.cozum_tahtasi:
            return

        if self.puan <= 10:
            QMessageBox.warning(self, "Uyarı", "Puanınız ipucu için yetersiz! (En az 10 puanınız olmalı)")
            return

        bos_hucreler = []
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    bos_hucreler.append((i, j))

        if not bos_hucreler:
            QMessageBox.information(self, "İpucu", "Tüm hücreler dolu!")
            return

        satir, sutun = random.choice(bos_hucreler)
        dogru_sayi = self.cozum_tahtasi[satir][sutun]
        self.tahta[satir][sutun].deger = dogru_sayi
        self.tahta[satir][sutun].sabit = True

        self.ipucu_hucreleri.add((satir, sutun))
        self.ipucu_sayisi += 1
        self.ipucu_label.setText(f"İpucu: {self.ipucu_sayisi}")

        buton = self.hucre_butonlari[satir][sutun]
        buton.setText(str(dogru_sayi))
        self.hucre_stilini_guncelle(satir, sutun)

        self.puan = max(0, self.puan - 10)
        self.puan_label.setText(f"Puan: {self.puan}")

    def sag_tus_menusu(self, satir, sutun):
        """Oyun panelindeki Hücreye sağ tıklama ile olası sayıları gösteren menü"""
        if not self.oyun_aktif:
            return

        if self.tahta[satir][sutun].sabit:
            return

        olasi_sayilar = self.olasi_sayilari_bul(satir, sutun)

        if not olasi_sayilar:
            QMessageBox.information(self, "Bilgi", "Bu hücreye yerleştirilebilecek uygun sayı yok!")
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #4169E1;
                font-size: 14pt;
                font-weight: bold;
            }
            QMenu::item {
                padding: 8px 25px;
                color: #4169E1;
            }
            QMenu::item:selected {
                background-color: #90EE90;
            }
        """)

        for sayi in sorted(olasi_sayilar):
            action = menu.addAction(str(sayi))
            action.triggered.connect(lambda checked, s=sayi: self.sayi_sec(satir, sutun, s))

        buton = self.hucre_butonlari[satir][sutun]
        menu.exec_(buton.mapToGlobal(buton.rect().bottomLeft()))

    def sayi_sec(self, satir, sutun, sayi):
        """Menüden seçilen sayıyı hücreye yerleştir"""
        if not self.oyun_aktif or self.tahta[satir][sutun].sabit:
            return

        self.tahta[satir][sutun].deger = sayi
        self.hucre_butonlari[satir][sutun].setText(str(sayi))

        if (satir, sutun) in self.hatali_hucreler:
            if sayi == self.cozum_tahtasi[satir][sutun]:
                self.hatali_hucreler.remove((satir, sutun))

        self.secili_hucre = (satir, sutun)
        self.hucre_stilini_guncelle(satir, sutun, secili=True)
        self.otomatik_kontrol()

    def ilgili_notlari_temizle(self, satir, sutun, sayi):
        """Aynı satır, sütun ve 3x3 bölgedeki ilgili notları temizle"""
        for j in range(9):
            self.notlar[satir][j].discard(sayi)
            self.hucreyi_guncelle(satir, j)

        for i in range(9):
            self.notlar[i][sutun].discard(sayi)
            self.hucreyi_guncelle(i, sutun)

        kutu_satir = (satir // 3) * 3
        kutu_sutun = (sutun // 3) * 3
        for i in range(kutu_satir, kutu_satir + 3):
            for j in range(kutu_sutun, kutu_sutun + 3):
                self.notlar[i][j].discard(sayi)
                self.hucreyi_guncelle(i, j)

    def tum_notlari_temizle(self):
        """Tüm notları temizle"""
        if not self.oyun_aktif:
            return

        for i in range(9):
            for j in range(9):
                self.notlar[i][j].clear()
                self.hucreyi_guncelle(i, j)

    def not_modu_degistir(self):
        """Not modunu aç/kapat"""
        self.not_modu = not self.not_modu
        self.not_modu_btn.setChecked(self.not_modu)
        self.not_modu_label.setText(f"Not: {'Açık' if self.not_modu else 'Kapalı'}")
