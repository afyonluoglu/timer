"""
Sudoku skor tablosu, skor kaydı ve yardım pencerelerini yöneten modül.
"""

import os
import json
import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt
from ti_sudoku_engine import MAX_SCORES_PER_DIFFICULTY


def get_puan_dosyasi(dosya_yolu=None):
    if dosya_yolu:
        return dosya_yolu
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_puanlar.json")


def skor_tablosuna_girebilir_mi_kontrol(zorluk, yeni_puan, dosya_yolu=None):
    """Yeni puanın skor tablosuna girip girmeyeceğini kontrol et"""
    try:
        puan_dosyasi = get_puan_dosyasi(dosya_yolu)
        puanlar = {"Kolay": [], "Orta": [], "Zor": []}
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)

        zorluk_puanlari = puanlar.get(zorluk, [])

        if len(zorluk_puanlari) < MAX_SCORES_PER_DIFFICULTY:
            return True

        en_dusuk_skor = min(zorluk_puanlari, key=lambda x: x['puan'])
        return yeni_puan > en_dusuk_skor['puan']

    except Exception:
        return True


def puan_kaydet(zorluk, isim, puan, sure=0, ipucu_sayisi=0, silme_sayisi=0,
                kontrol_sayisi=0, hata_sayisi=0, oynanan_oyun_sayisi=0, dosya_yolu=None):
    """Puanı kaydet ve en iyi MAX_SCORES_PER_DIFFICULTY skoru tut"""
    puan_dosyasi = get_puan_dosyasi(dosya_yolu)

    puanlar = {"Kolay": [], "Orta": [], "Zor": []}
    if os.path.exists(puan_dosyasi):
        with open(puan_dosyasi, 'r', encoding='utf-8') as f:
            puanlar = json.load(f)

    if zorluk not in puanlar:
        puanlar[zorluk] = []

    puanlar[zorluk].append({
        'isim': isim,
        'puan': puan,
        'sure': sure,
        'ipucu': ipucu_sayisi,
        'silme': silme_sayisi,
        'kontrol': kontrol_sayisi,
        'hata': hata_sayisi,
        'oyun_sayisi': oynanan_oyun_sayisi,
        'zorluk': zorluk,
        'tarih': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    puanlar[zorluk] = sorted(
        puanlar[zorluk],
        key=lambda x: (-x['puan'], x['sure'])
    )[:MAX_SCORES_PER_DIFFICULTY]

    with open(puan_dosyasi, 'w', encoding='utf-8') as f:
        json.dump(puanlar, f, ensure_ascii=False, indent=2)


def puan_kaydi_sil(parent, zorluk, satir_index, dosya_yolu=None):
    """Puan tablosundan belirtilen kaydı sil"""
    try:
        puan_dosyasi = get_puan_dosyasi(dosya_yolu)

        puanlar = {"Kolay": [], "Orta": [], "Zor": []}
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)

        zorluk_puanlari = sorted(
            puanlar.get(zorluk, []),
            key=lambda x: (-x['puan'], x['sure'])
        )

        if 0 <= satir_index < len(zorluk_puanlari):
            silinen = zorluk_puanlari.pop(satir_index)
            puanlar[zorluk] = zorluk_puanlari

            with open(puan_dosyasi, 'w', encoding='utf-8') as f:
                json.dump(puanlar, f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                parent,
                "Başarılı",
                f"{silinen['isim']} kullanıcısının kaydı silindi."
            )
    except Exception as e:
        QMessageBox.warning(parent, "Hata", f"Kayıt silinirken hata oluştu: {str(e)}")


def puan_tablosu_sag_tus_menusu(parent, pos, zorluk, tablo, on_sil_callback=None):
    """Puan tablosunda sağ tıklama menüsü"""
    secili_satirlar = tablo.selectionModel().selectedRows()
    if len(secili_satirlar) != 1:
        return

    secili_satir = secili_satirlar[0].row()

    menu = QMenu(parent)
    sil_action = menu.addAction("Bu Puan Kaydını Sil")

    action = menu.exec_(tablo.viewport().mapToGlobal(pos))

    if action == sil_action:
        cevap = QMessageBox.question(
            parent,
            "Silme Onayı",
            f"{secili_satir + 1}. sıradaki kaydı silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if cevap == QMessageBox.Yes:
            if on_sil_callback:
                on_sil_callback(zorluk, secili_satir)
            else:
                puan_kaydi_sil(parent, zorluk, secili_satir)
            tablo.parent().parent().close()
            puan_tablosunu_goster(parent, on_sil_callback)


def puan_tablosunu_goster(parent, on_sil_callback=None):
    """Puan tablosunu tablo formatında göster"""
    try:
        puan_dosyasi = get_puan_dosyasi()

        puanlar = {"Kolay": [], "Orta": [], "Zor": []}
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)

        dialog = QDialog(parent)
        dialog.setWindowTitle("Puan Tablosu")
        dialog.setModal(True)
        dialog.resize(1000, 1300)

        duzen = QVBoxLayout()

        for zorluk in ["Kolay", "Orta", "Zor"]:
            grup = QGroupBox(zorluk)
            grup_duzen = QVBoxLayout()

            tablo = QTableWidget()
            tablo.setColumnCount(8)
            tablo.setHorizontalHeaderLabels(["Tarih", "İsim", "Puan", "Süre", "Oyun", "İpucu", "Silme", "Kontrol"])
            tablo.setContextMenuPolicy(Qt.CustomContextMenu)
            tablo.customContextMenuRequested.connect(
                lambda pos, z=zorluk, t=tablo: puan_tablosu_sag_tus_menusu(parent, pos, z, t, on_sil_callback)
            )

            zorluk_puanlari = sorted(
                puanlar.get(zorluk, []),
                key=lambda x: (-x['puan'], x['sure'])
            )[:MAX_SCORES_PER_DIFFICULTY]

            tablo.setRowCount(len(zorluk_puanlari))

            for i, kayit in enumerate(zorluk_puanlari):
                ipucu = kayit.get('ipucu', 0)
                silme = kayit.get('silme', 0)
                kontrol = kayit.get('kontrol', 0)
                oyun_sayisi = kayit.get('oyun_sayisi', 1)
                tarih = kayit.get('tarih', 'Bilinmiyor')

                sure = kayit['sure']
                dakika = sure // 60
                saniye = sure % 60

                if tarih != 'Bilinmiyor':
                    try:
                        dt = datetime.datetime.strptime(tarih.strip(), "%Y-%m-%d %H:%M:%S")
                        tarih = dt.strftime("%d-%m-%Y  %H:%M")
                    except Exception:
                        pass

                tablo.setItem(i, 0, QTableWidgetItem(str(tarih)))
                tablo.setItem(i, 1, QTableWidgetItem(kayit['isim']))

                item = QTableWidgetItem(str(kayit['puan']))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tablo.setItem(i, 2, item)

                tablo.setItem(i, 3, QTableWidgetItem(f"{dakika:02d}:{saniye:02d}"))
                tablo.setItem(i, 4, QTableWidgetItem(str(oyun_sayisi)))
                tablo.setItem(i, 5, QTableWidgetItem(str(ipucu)))
                tablo.setItem(i, 6, QTableWidgetItem(str(silme)))
                tablo.setItem(i, 7, QTableWidgetItem(str(kontrol)))

            for i in range(tablo.rowCount()):
                tablo.setRowHeight(i, 20)

            tablo.setColumnWidth(0, 180)
            tablo.setColumnWidth(1, 180)
            tablo.setColumnWidth(2, 80)
            tablo.setColumnWidth(3, 80)
            tablo.setColumnWidth(4, 60)
            tablo.setColumnWidth(5, 60)
            tablo.setColumnWidth(6, 60)
            tablo.setColumnWidth(7, 70)

            tablo.setEditTriggers(QTableWidget.NoEditTriggers)
            tablo.setSelectionBehavior(QTableWidget.SelectRows)

            grup_duzen.addWidget(tablo)
            grup.setLayout(grup_duzen)
            duzen.addWidget(grup)

        kapat_btn = QPushButton("Kapat")
        kapat_btn.clicked.connect(dialog.close)
        duzen.addWidget(kapat_btn)

        dialog.setLayout(duzen)
        dialog.exec_()

    except Exception as e:
        QMessageBox.warning(parent, "Hata", f"Puan tablosu gösterilirken hata oluştu: {str(e)}")


def yardim_goster(parent):
    """Yardım mesajını göster"""
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
        <li>Oyuncunun 15 silme hakkı vardır</li>
        <li>3 hata hakkı vardır</li>
        <li>Silme veya hata hakkı biterse oyun sonlanır</li>
        <li>Başarılı oyun bitiminde puanlar toplanır ve yeni oyuna devam edilebilir</li>
    </ul>
    
    <h3>Klavye Kontrolleri:</h3>
    <ul>
        <li>1-9: Sayı girmek için (Not modu kapalıyken)</li>
        <li>1-9: Not almak için (Not modu açıkken)</li>
        <li>Delete/Backspace: Hücreyi silmek için</li>
        <li>N: Not modunu aç/kapat</li>
        <li>Ctrl+Z/Y: Geri/İleri al</li>
        <li>F2: Yeni oyun başlatmak için</li>
        <li>F3: Puan tablosu</li>
        <li>F4: Oyunu bitir</li>
    </ul>
    
    <h3>Fare Kontrolleri:</h3>
    <ul>
        <li>Sol tık: Hücre seçmek için</li>
        <li>Sağ tık: Olası sayıları görmek için</li>
    </ul>
    
    <h3>Özellikler:</h3>
    <ul>
        <li><b>Not Modu:</b> Bir hücreye birden fazla olası sayı yazabilirsiniz</li>
        <li><b>Geri Al/İleri Al:</b> Hamlelerinizi geri alabilir veya tekrar yapabilirsiniz</li>
        <li><b>Sayı Vurgulama:</b> Bir sayıya tıkladığınızda aynı sayılar vurgulanır</li>
        <li><b>Bölge Vurgulama:</b> Seçili hücrenin satırı, sütunu ve bölgesi vurgulanır</li>
    </ul>
    
    <h3>Renkler:</h3>
    <ul>
        <li><span style="color:black; font-weight:bold;">Siyah sayılar:</span> Başlangıçta verilen sabit sayılar</li>
        <li><span style="color:#4169E1;">Mavi sayılar:</span> Oyuncu tarafından girilen sayılar</li>
        <li><span style="background-color:#2E8B57; color:white;">Koyu yeşil:</span> İpucu ile doldurulan hücreler</li>
        <li><span style="background-color:#FFB6C1;">Pembe:</span> Hatalı sayılar</li>
        <li><span style="background-color:#60EB60;">Açık yeşil:</span> Seçili hücre</li>
        <li><span style="background-color:#FFD700;">Altın sarısı:</span> Aynı sayıya sahip hücreler</li>
        <li><span style="background-color:#E8E8E8;">Açık gri:</span> İlgili satır/sütun/bölge</li>
    </ul>
    """

    QMessageBox.information(parent, "Nasıl Oynanır?", yardim_metni)

