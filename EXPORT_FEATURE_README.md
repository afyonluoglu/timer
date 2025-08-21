# Dosya Analizi Penceresi - Dışarıya Aktarma Özelliği

## Yapılan Değişiklikler

### 1. Yeni Düğme Eklendi
- `timer_file_analyzer.py` dosyasına "Dışarıya Aktar" düğmesi eklendi
- Düğme başlangıçta devre dışı durumda
- Klasör seçildiğinde otomatik olarak etkinleşir

### 2. Export Fonksiyonalitesi
`tablo_disariya_aktar()` metodu eklendi:

#### Özellikler:
- Analiz sonuçlarını TXT formatında dışarıya aktarır
- Tablo sütunları düzgün hizalanmış şekilde formatlanır
- Otomatik dosya adı önerisi: `klasor_analizi_{klasor_adi}.txt`
- UTF-8 kodlaması ile Türkçe karakter desteği

#### İçerik Formatı:
```
KLASÖR ANALİZİ RAPORU
================================================================================
Analiz Tarihi: 2025-08-21 14:30:25
Analiz Edilen Klasör: C:\Example\Folder
================================================================================

Klasör Adı              | Boyut                | Dosya Sayısı       
-----------------------+-----------------------+--------------------
Documents              | 1.2 GB               | 150                
Images                 | 850.5 MB             | 75                 
Videos                 | 2.1 GB               | 25                 
Bu klasördeki dosyalar | 45.2 MB              | 10                 
TOPLAM                 | 4.2 GB               | 260                

================================================================================
Rapor Sonu
```

### 3. Kullanıcı Deneyimi İyileştirmeleri
- Başarılı dışa aktarımda bilgilendirme mesajı
- Hata durumlarında detaylı hata mesajları
- Log dosyasına kayıt tutma
- Dosya seçme dialog'u ile kolay kayıt yeri seçimi

### 4. Test Dosyası
`test_export.py` dosyası oluşturuldu:
- Dışarıya aktarma özelliğini test etmek için
- Bağımsız çalışabilir
- Kullanım talimatları içerir

## Kullanım
1. Timer uygulamasını çalıştırın
2. "Dosya Analizi" menüsünü açın
3. "Klasör Seç" düğmesine tıklayın ve analiz edilecek klasörü seçin
4. Analiz tamamlandıktan sonra "Dışarıya Aktar" düğmesine tıklayın
5. Kayıt edilecek dosya adını ve konumunu seçin
6. TXT dosyası oluşturulacak ve başarı mesajı gösterilecektir

## Teknik Detaylar
- Sütun genişlikleri otomatik hesaplanır
- Minimum sütun genişliği 20 karakter
- Tablo başlıkları ve ayırıcı çizgiler eklenir
- Tarih/saat damgası otomatik eklenir
- UTF-8 kodlaması ile Türkçe karakter desteği
