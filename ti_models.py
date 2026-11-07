"""
Kronometre ve Zamanlayıcı veri modellerini barındıran modül.
"""

import datetime
import random

VARSAYILAN_ALARM_DOSYASI = "01.mp3"


def format_alarm_bilgisi(alarm_degeri):
    """Favori ve geçmiş listeleri için alarm bilgisini (.mp3 uzantısı olmadan) her zaman metin olarak biçimlendirir."""
    def _uzanti_temizle(dosya_adi):
        ad = str(dosya_adi).strip()
        return ad[:-4] if ad.lower().endswith(".mp3") else ad

    if isinstance(alarm_degeri, list):
        alarmlar = [_uzanti_temizle(a) for a in alarm_degeri if a]
    elif isinstance(alarm_degeri, str) and alarm_degeri.strip():
        alarmlar = [_uzanti_temizle(alarm_degeri)]
    else:
        alarmlar = []

    if not alarmlar:
        alarmlar = [_uzanti_temizle(VARSAYILAN_ALARM_DOSYASI)]

    if len(alarmlar) == 1:
        return f" - Alarm: {alarmlar[0]}"
    return f" - Alarm (🎲 {len(alarmlar)} ses): {', '.join(alarmlar)}"


class Kronometre:
    """Kronometre sınıfı - yukarı doğru sayan zamanlayıcı"""
    def __init__(self, id, isim, baslama_zamani=None):
        self.id = id
        self.isim = isim
        self.gecen_sure = 0  # saniye cinsinden geçen süre
        self.calisma_durumu = True  # True: çalışıyor, False: duraklatılmış
        self.baslama_zamani = baslama_zamani or datetime.datetime.now()
        self.turlar = []  # Tur zamanları listesi [(tur_no, gecen_sure, tur_suresi), ...]
        self.son_tur_suresi = 0  # Son tur için referans süre

    def get_formatted_time(self):
        """Geçen süreyi saat:dakika:saniye formatında döndürür"""
        saat = self.gecen_sure // 3600
        dakika = (self.gecen_sure % 3600) // 60
        saniye = self.gecen_sure % 60
        return f"{saat:02d}:{dakika:02d}:{saniye:02d}"

    def tur_ekle(self):
        """Yeni tur ekler"""
        tur_no = len(self.turlar) + 1
        tur_suresi = self.gecen_sure - self.son_tur_suresi
        self.turlar.append((tur_no, self.gecen_sure, tur_suresi))
        self.son_tur_suresi = self.gecen_sure
        return tur_no, self.gecen_sure, tur_suresi

    def sifirla(self):
        """Kronometreyi sıfırlar"""
        self.gecen_sure = 0
        self.turlar = []
        self.son_tur_suresi = 0
        self.baslama_zamani = datetime.datetime.now()

    def to_dict(self):
        """Kronometreyi sözlük olarak kaydetmek için"""
        return {
            'id': self.id,
            'isim': self.isim,
            'gecen_sure': self.gecen_sure,
            'calisma_durumu': self.calisma_durumu,
            'baslama_zamani': self.baslama_zamani.isoformat(),
            'turlar': self.turlar,
            'son_tur_suresi': self.son_tur_suresi,
            'son_guncelleme_zamani': datetime.datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """Sözlükten kronometre oluşturmak için"""
        kronometre = cls(
            id=data['id'],
            isim=data['isim'],
            baslama_zamani=datetime.datetime.fromisoformat(data['baslama_zamani'])
        )
        kronometre.gecen_sure = data['gecen_sure']
        kronometre.calisma_durumu = data.get('calisma_durumu', True)
        kronometre.turlar = data.get('turlar', [])
        kronometre.son_tur_suresi = data.get('son_tur_suresi', 0)

        # Program kapalıyken geçen süreyi ekle (sadece çalışıyorsa)
        if kronometre.calisma_durumu and 'son_guncelleme_zamani' in data:
            try:
                son_guncelleme = datetime.datetime.fromisoformat(data['son_guncelleme_zamani'])
                gecen = int((datetime.datetime.now() - son_guncelleme).total_seconds())
                kronometre.gecen_sure += gecen
            except Exception:
                pass

        return kronometre


class Zamanlayici:
    def __init__(self, id, dakika_ayari, temel_aciklama, alarm=VARSAYILAN_ALARM_DOSYASI, baslama_zamani_ilk_kurulum=None,
                 tekrar_toplam_sayi=1, tekrar_mevcut_calisma=1, tekrar_araligi_dakika=10,
                 ozel_saat_aktif_ilk_calisma=False, ozel_saat_str=None,
                 sonra_baslat_aktif=False, beklenen_favori_aciklama=None):
        self.id = id
        self.dakika_ayari = dakika_ayari  # Kullanıcının girdiği dakika
        self.temel_aciklama = temel_aciklama
        self.calisma_durumu = True
        self.baslama_zamani_ilk_kurulum = baslama_zamani_ilk_kurulum or datetime.datetime.now()
        self.alarm_dosyasi = alarm

        self.tekrar_toplam_sayi = tekrar_toplam_sayi
        self.tekrar_mevcut_calisma = tekrar_mevcut_calisma
        self.tekrar_araligi_dakika = tekrar_araligi_dakika

        self.ozel_saat_aktif_ilk_calisma = ozel_saat_aktif_ilk_calisma
        self.ozel_saat_str = ozel_saat_str

        self.sure = 0  # saniye cinsinden kalan süre
        self.toplam_sure = 0  # saniye cinsinden bu döngünün toplam süresi
        self.sonra_baslat_aktif = sonra_baslat_aktif
        self.beklenen_favori_aciklama = beklenen_favori_aciklama
        self.bekleme_modunda = False  # Tekrar aralığında bekleme durumu

    def get_gorunen_aciklama(self):
        """Görüntülenecek açıklamayı döndürür, tekrar bilgisini içerir."""
        if self.sonra_baslat_aktif and self.beklenen_favori_aciklama:
            return f"{self.beklenen_favori_aciklama} zamanlayıcısı bekleniyor"
        if self.tekrar_toplam_sayi > 1:
            return f"{self.temel_aciklama} ({self.tekrar_mevcut_calisma}/{self.tekrar_toplam_sayi})"
        return self.temel_aciklama

    def secili_alarmlari_al(self):
        """Zamanlayıcı için seçilmiş alarm dosyalarını liste olarak döndürür."""
        if isinstance(self.alarm_dosyasi, list):
            temiz = [a for a in self.alarm_dosyasi if a]
            return temiz if temiz else [VARSAYILAN_ALARM_DOSYASI]
        if isinstance(self.alarm_dosyasi, str) and self.alarm_dosyasi:
            return [self.alarm_dosyasi]
        return [VARSAYILAN_ALARM_DOSYASI]

    def rastgele_alarm_sec(self):
        """İşaretlenen alarm sesleri arasından rastgele bir tanesini seçip döndürür."""
        return random.choice(self.secili_alarmlari_al())

    def varsayilan_disi_alarm_var_mi(self):
        """Varsayılan tekil alarm sesi dışında bir alarm veya çoklu seçim olup olmadığını döndürür."""
        alarmlar = self.secili_alarmlari_al()
        return len(alarmlar) > 1 or alarmlar[0] != VARSAYILAN_ALARM_DOSYASI

    def get_alarm_kisa_etiket(self):
        """Aktif zamanlayıcı kartında gösterilecek kısa alarm etiketini döndürür."""
        alarmlar = self.secili_alarmlari_al()
        if len(alarmlar) > 1:
            return f"[🎲 {len(alarmlar)} ses]"
        return f"[{alarmlar[0]}]"

    def get_alarm_ipucu(self):
        """Aktif zamanlayıcı kartındaki alarm etiketinin araç ipucunu (tooltip) döndürür."""
        alarmlar = self.secili_alarmlari_al()
        if len(alarmlar) > 1:
            return "Rastgele çalınacak sesler:\n• " + "\n• ".join(alarmlar)
        return f"Alarm sesi: {alarmlar[0]}"

    def to_dict(self):
        """Zamanlayıcıyı sözlük olarak kaydetmek için"""
        return {
            'id': self.id,
            'dakika_ayari': self.dakika_ayari,
            'toplam_sure': self.toplam_sure, 
            'sure': self.sure,
            'temel_aciklama': self.temel_aciklama,
            'baslama_zamani_ilk_kurulum': self.baslama_zamani_ilk_kurulum.isoformat(),
            'alarm_dosyasi': self.alarm_dosyasi,
            'calisma_durumu': self.calisma_durumu,
            'tekrar_toplam_sayi': self.tekrar_toplam_sayi,
            'tekrar_mevcut_calisma': self.tekrar_mevcut_calisma,
            'tekrar_araligi_dakika': self.tekrar_araligi_dakika,
            'ozel_saat_aktif_ilk_calisma': self.ozel_saat_aktif_ilk_calisma,
            'ozel_saat_str': self.ozel_saat_str,
            'sonra_baslat_aktif': self.sonra_baslat_aktif,
            'beklenen_favori_aciklama': self.beklenen_favori_aciklama,
            'bekleme_modunda': self.bekleme_modunda,
            'son_guncelleme_zamani': datetime.datetime.now().isoformat()              
        }

    @classmethod
    def from_dict(cls, data):
        """Sözlükten zamanlayıcı oluşturmak için"""
        zamanlayici = cls(
            id=data['id'],
            dakika_ayari=data.get('dakika_ayari', data.get('dakika', data.get('toplam_sure', 0) // 60)),
            temel_aciklama=data.get('temel_aciklama', data.get('aciklama', 'Zamanlayıcı')),
            alarm=data['alarm_dosyasi'],
            baslama_zamani_ilk_kurulum=datetime.datetime.fromisoformat(data['baslama_zamani_ilk_kurulum']),
            tekrar_toplam_sayi=data.get('tekrar_toplam_sayi', 1),
            tekrar_mevcut_calisma=data.get('tekrar_mevcut_calisma', 1),
            tekrar_araligi_dakika=data.get('tekrar_araligi_dakika', 10),
            ozel_saat_aktif_ilk_calisma=data.get('ozel_saat_aktif_ilk_calisma', False),
            ozel_saat_str=data.get('ozel_saat_str', None),
            sonra_baslat_aktif=data.get('sonra_baslat_aktif', False),
            beklenen_favori_aciklama=data.get('beklenen_favori_aciklama', None)
        )
        zamanlayici.sure = data['sure'] 
        zamanlayici.toplam_sure = data.get('toplam_sure', zamanlayici.dakika_ayari * 60)
        zamanlayici.calisma_durumu = data.get('calisma_durumu', True)
        zamanlayici.bekleme_modunda = data.get('bekleme_modunda', False)

        if 'son_guncelleme_zamani' in data:
            zamanlayici.son_guncelleme_zamani = data['son_guncelleme_zamani']

        if not zamanlayici.ozel_saat_aktif_ilk_calisma or zamanlayici.tekrar_mevcut_calisma > 1:
            if zamanlayici.toplam_sure != zamanlayici.dakika_ayari * 60:
                pass

        return zamanlayici

