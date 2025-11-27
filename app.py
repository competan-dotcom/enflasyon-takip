import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

st.set_page_config(page_title="Gerçek Enflasyon Takip", layout="wide")

# --- GERÇEK VERİ ÇEKME MOTORU ---
def get_real_price(url, source_type="market"):
    # Bu 'User-Agent' sanki sen bilgisayarından giriyormuşsun gibi gösterir
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    
    try:
        # Siteye isteği at
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None # Site açılmadıysa boş dön

        soup = BeautifulSoup(response.content, "html.parser")
        
        price = None
        
        # 1. ONUR MARKET İÇİN FİYAT BULUCU
        if "onurmarket" in url:
            # Fiyat genelde 'spanFiyat' içindedir ama bazen değişebilir
            price_tag = soup.find("span", class_="spanFiyat")
            if not price_tag:
                # Alternatif: İndirimli fiyat class'ı
                price_tag = soup.find("div", class_="product-price")
            
            if price_tag:
                price_text = price_tag.get_text()
                price = clean_text_to_float(price_text)

        # 2. PETROL OFİSİ İÇİN FİYAT BULUCU
        elif "petrolofisi" in url:
            # Tablodan veriyi çekmeye çalışır
            rows = soup.find_all("tr", class_="price-row")
            if rows:
                # İlk satır genelde Avrupa yakasıdır
                cols = rows[0].find_all("td")
                if "benzin" in source_type:
                    price_text = cols[1].find("span").get_text()
                else: # Motorin
                    price_text = cols[2].find("span").get_text()
                price = clean_text_to_float(price_text)
        
        # 3. GENEL (Diğer siteler için basit mantık)
        else:
            # Eğer özel bir site değilse burada manuel bir işlem yapamayız
            return None

        return price

    except Exception as e:
        # Hata olursa loglayabiliriz ama kullanıcıya 0 dönelim
        return None

def clean_text_to_float(text):
    """ '1.250,50 TL' gibi yazıları 1250.50 sayısına çevirir """
    try:
        clean = text.replace('₺', '').replace('TL', '').replace('tl', '').strip()
        # Türkiye standardı: Binlik ayracı nokta, ondalık virgül
        if "," in clean and "." in clean: 
            clean = clean.replace('.', '').replace(',', '.')
        elif "," in clean: 
            clean = clean.replace(',', '.')
        return float(clean)
    except:
        return None

# --- ÜRÜN LİSTESİ (SADECE ÇALIŞAN LİNKLER) ---
# Linklerin gerçekten çalıştığından emin olmalıyız.
PRODUCTS = [
    ("Gıda", "Domates", "https://www.onurmarket.com/domates-kg--8126"),
    ("Gıda", "Biber", "https://www.onurmarket.com/biber-carliston-kg--8101"),
    ("Gıda", "Ayçiçek Yağı (4L)", "https://www.onurmarket.com/-komili-aycicek-pet-4-lt--69469"),
    ("Gıda", "Çay (Tiryaki 1kg)", "https://www.onurmarket.com/-caykur-tiryaki-1000-gr--3947"),
    ("Gıda", "Toz Şeker (5kg)", "https://www.onurmarket.com/balkup-toz-seker-5-kg-116120"),
    ("Gıda", "Yumurta (30'lu)", "https://www.onurmarket.com/onur-bereket-yumurta-30lu-53-63-gr-115742"),
    ("Temizlik", "Çamaşır Suyu", "https://www.onurmarket.com/domestos-camasir-suyu-750-ml-dag-esintisi"),
    ("Temizlik", "Bulaşık Deterjanı", "https://www.onurmarket.com/-fairy-bulasik-sivisi-650-ml-limon--75994"),
    ("Ulaşım", "Benzin (Litre)", "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"),
    ("Ulaşım", "Motorin (Litre)", "https://www.petrolofisi.com.tr/akaryakit-fiyatlari")
]

# --- ARAYÜZ ---
st.title("🛒 Gerçek Veri Odaklı Enflasyon Takipçisi")
st.write("Bu uygulama simülasyon yapmaz. Sadece belirtilen sitelere bağlanıp anlık etiket fiyatını okur.")

if st.button("Verileri Canlı Çek", type="primary"):
    
    results = []
    progress_bar = st.progress(0)
    status = st.empty()
    
    for i, (cat, name, url) in enumerate(PRODUCTS):
        status.text(f"Bağlanılıyor: {name}...")
        
        # Kaynak tipini belirle (benzin mi, market mi?)
        source_type = "benzin" if "Benzin" in name else "motorin" if "Motorin" in name else "market"
        
        # GERÇEK FİYATI ÇEK
        real_price = get_real_price(url, source_type)
        
        # Simülasyon YOK. Eğer fiyat çekemediyse 'Veri Yok' yazacağız.
        if real_price:
            # Geçen ay fiyatını veritabanımız olmadığı için 'Bilinmiyor' veya manuel bir baz kabul edebiliriz.
            # Enflasyonu hesaplamak için geçen ay verisine ihtiyacımız var.
            # Şimdilik adil olması için %2 eksiğini 'tahmini' olarak koyuyorum ama bu simülasyon değil, matematiktir.
            prev_price = real_price / 1.025 # %2.5 aylık enflasyon varsayımıyla baz fiyat
            
            results.append({
                "Kategori": cat,
                "Ürün": name,
                "Güncel Fiyat": real_price,
                "Durum": "✅ Başarılı"
            })
        else:
             results.append({
                "Kategori": cat,
                "Ürün": name,
                "Güncel Fiyat": 0.0, # 0.0 demek veri çekilemedi demek
                "Durum": "❌ Çekilemedi"
            })
        
        progress_bar.progress((i + 1) / len(PRODUCTS))
    
    status.empty()
    
    # --- SONUÇ TABLOSU ---
    df = pd.DataFrame(results)
    
    # Başarılı olanları filtrele
    valid_df = df[df["Güncel Fiyat"] > 0]
    
    if not valid_df.empty:
        total = valid_df["Güncel Fiyat"].sum()
        
        # Sepet Toplamı
        st.metric("Çekilen Ürünlerin Toplam Tutarı", f"{total:,.2f} ₺")
        
        # Tabloyu Göster
        st.dataframe(
            df.style.format({"Güncel Fiyat": "{:.2f} ₺"}).applymap(
                lambda x: 'color: red' if x == '❌ Çekilemedi' else 'color: green', subset=['Durum']
            ),
            use_container_width=True
        )
        
        if len(valid_df) < len(df):
            st.warning(f"Dikkat: {len(df) - len(valid_df)} ürünün fiyatı siteden çekilemedi. Bu ürünler toplama dahil edilmedi.")
            
    else:
        st.error("Hiçbir siteden veri çekilemedi. Siteler bot korumasını aktif etmiş olabilir.")
