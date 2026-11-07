"""
Sudoku temel hücre yapısı ve bulmaca oluşturma / çözme motoru.
"""

import random

MAX_DELETE_COUNT = 15  # Maksimum silme hakkı
MAX_SCORES_PER_DIFFICULTY = 15  # Her zorluk seviyesi için tutulacak maksimum skor
MAX_MISTAKES = 3  # Maksimum hata hakkı


class SudokuHucre:
    def __init__(self):
        self.deger = 0  # 0 boş hücreyi temsil eder
        self.sabit = False  # Başlangıçta verilen sayılar için
        self.notlar = set()  # Oyuncunun aldığı notlar


def bos_hucre_bul(tahta):
    """Boş hücre bul"""
    for i in range(9):
        for j in range(9):
            if tahta[i][j] == 0:
                return (i, j)
    return None


def sayi_uygun_mu(tahta, sayi, pos):
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


def sudoku_coz(tahta):
    """Sudoku çözme algoritması"""
    bos = bos_hucre_bul(tahta)
    if not bos:
        return tahta

    satir, sutun = bos
    sayilar = list(range(1, 10))
    random.shuffle(sayilar)  # Rastgele çözüm için sayıları karıştır

    for sayi in sayilar:
        if sayi_uygun_mu(tahta, sayi, (satir, sutun)):
            tahta[satir][sutun] = sayi

            if sudoku_coz(tahta):
                return tahta

            tahta[satir][sutun] = 0

    return False


def sudoku_olustur(zorluk):
    """Sudoku tahtası oluştur ve (tahta, cozum_tahtasi) döndürür"""
    tahta = [[SudokuHucre() for _ in range(9)] for _ in range(9)]

    # Yeni ve rastgele bir Sudoku tahtası oluştur
    bos_tahta = [[0 for _ in range(9)] for _ in range(9)]
    cozum_tahtasi = sudoku_coz(bos_tahta)  # Önce tam çözülmüş bir tahta oluştur

    # Zorluk seviyesine göre rakam sayısını belirle
    if zorluk == "Kolay":
        silinecek_sayi = 40  # 41 rakam görünür
    elif zorluk == "Orta":
        silinecek_sayi = 50  # 31 rakam görünür
    else:  # Zor
        silinecek_sayi = 60  # 21 rakam görünür

    # Rastgele hücreleri boşalt
    dolu_hucreler = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(dolu_hucreler)

    baslangic_tahtasi = [row[:] for row in cozum_tahtasi]
    for i, j in dolu_hucreler[:silinecek_sayi]:
        baslangic_tahtasi[i][j] = 0

    # Tahtayı ayarla
    for i in range(9):
        for j in range(9):
            tahta[i][j].deger = baslangic_tahtasi[i][j]
            if baslangic_tahtasi[i][j] != 0:
                tahta[i][j].sabit = True

    return tahta, cozum_tahtasi


def olasi_sayilari_bul(tahta, satir, sutun):
    """Bir hücreye yerleştirilebilecek olası sayıları bul"""
    olasi_sayilar = set(range(1, 10))

    # Aynı satırdaki sayıları çıkar
    for j in range(9):
        if tahta[satir][j].deger != 0:
            olasi_sayilar.discard(tahta[satir][j].deger)

    # Aynı sütundaki sayıları çıkar
    for i in range(9):
        if tahta[i][sutun].deger != 0:
            olasi_sayilar.discard(tahta[i][sutun].deger)

    # Aynı 3x3 bölgedeki sayıları çıkar
    kutu_satir = (satir // 3) * 3
    kutu_sutun = (sutun // 3) * 3
    for i in range(kutu_satir, kutu_satir + 3):
        for j in range(kutu_sutun, kutu_sutun + 3):
            if tahta[i][j].deger != 0:
                olasi_sayilar.discard(tahta[i][j].deger)

    return olasi_sayilar

