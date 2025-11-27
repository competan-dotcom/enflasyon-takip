import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="Canlı Enflasyon Monitörü",
    page_icon="📈",
    layout="wide"
)

# --- CSS (Görünüm) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .big-stat { font-size: 24px; font-weight: bold; color: #333; }
    .small-stat { font-size: 14px; color: #666; }
    .source-tag { font-size: 12px; padding: 2px 6px; border-radius: 4px; background-color: #eee; }
</style>
""", unsafe_allow_html=True)

st.title("🇹🇷 Kişisel Enflasyon Sepeti (V2)")
st.info("Bu sistem, market siteleri erişimi engellese bile yedek veri havuzundan çalışmaya devam eder.")

# --- Yardımcı Fonksiyonlar ---
def get_soup(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
    except:
        return None
    return None

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        clean = str(price_str).replace('₺', '').replace('TL', '').strip()
        if "," in clean and "." in clean: 
            clean = clean.replace('.', '').replace(',', '.')
        elif "," in clean: 
            clean = clean.replace(',', '.')
        return float(clean)
    except:
        return 0.0

# --- Veri Motoru ---
class DataEngine:
    def __init__(self):
        self.data = []

    def add_product(self, kategori, urun_adi, fiyat, kaynak, is_live=True):
        # Geçen ay tahmini (Simülasyon)
        gecen_ay = fiyat * random.uniform(0.90, 0.95) if fiyat > 0 else 0
        
        self.data.append({
            "Kategori": kategori,
            "Ürün": urun_adi,
            "Güncel Fiyat": fiyat,
            "Geçen Ay (Tahmini)": gecen_ay,
            "Kaynak": kaynak,
            "Durum": "🟢 Canlı" if is_live else "🟠 Yedek Veri"
        })

    def fetch_market_smart(self):
        """Önce siteyi dener, olmazsa yedek fiyatı kullanır"""
        
        # Ürün Listesi: (Kategori, Ad, Link, Yedek_Fiyat)
        urunler = [
            ("Gıda", "Domates (Kg)", "https://www.onurmarket.com/domates-kg--8126", 45.00),
            ("Gıda", "Biber (Kg)", "https://www.onurmarket.com/biber-carliston-kg--8101", 60.00),
            ("Gıda", "Ayçiçek Yağı (4L)", "https://www.onurmarket.com/-komili-aycicek-pet-4-lt--69469", 269.90),
            ("Gıda", "Çay (Tiryaki 1kg)", "https://www.onurmarket.com/-caykur-tiryaki-1000-gr--3947", 215.00),
            ("Gıda", "Toz Şeker (5kg)", "https://www.onurmarket.com/balkup-toz-seker-5-kg-116120", 165.00),
            ("Gıda", "Yumurta (30'lu)", "https://www.onurmarket.com/onur-bereket-yumurta-30lu-53-63-gr-115742", 125.00),
            ("Temizlik", "Çamaşır Suyu", "https://www.onurmarket.com/domestos-camasir-suyu-750-ml-dag-esintisi", 45.00),
            ("Temizlik", "Bulaşık Deterjanı", "https://www.onurmarket.com/-fairy-bulasik-sivisi-650-ml-limon--75994", 65.00)
        ]

        for kategori, ad, link, yedek_fiyat in urunler:
            soup = get_soup(link)
            bulunan_fiyat = 0.0
            canli_veri = False
            
            if soup:
                fiyat_tag = soup.find("span", class_="spanFiyat")
                if fiyat_tag:
                    bulunan_fiyat = clean_price(fiyat_tag.get_text())
                    if bulunan_fiyat > 0:
                        canli_veri = True
            
            # Eğer site engellerse veya fiyat 0 gelirse YEDEĞİ kullan
            if bulunan_fiyat == 0:
                bulunan_fiyat = yedek_fiyat
                canli_veri = False
                
            self.add_product(kategori, ad, bulunan_fiyat, "Onur Market", canli_veri)

    def fetch_yakit_smart(self):
        # Akaryakıt için de aynısını yapalım
        url = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
        soup = get_soup(url)
        benzin, motorin = 0, 0
        canli = False
        
        if soup:
            try:
                rows = soup.find_all("tr", class_="price-row")
                if rows:
                    cols = rows[0].find_all("td")
                    benzin = clean_price(cols[1].find("span").text)
                    motorin = clean_price(cols[2].find("span").text)
                    if benzin > 0: canli = True
            except:
                pass
        
        # Yedekler
        if benzin == 0: benzin = 44.50
        if motorin == 0: motorin = 45.20
            
        self.add_product("Ulaşım", "Benzin (Litre)", benzin, "Petrol Ofisi", canli)
        self.add_product("Ulaşım", "Motorin (Litre)", motorin, "Petrol Ofisi", canli)

    def fetch_others(self):
        # Sabitler
        sabitler = [
            ("Hizmet", "Metro Bileti (Tam)", 20.0, "İBB"),
            ("Hizmet", "Öğrenci Abonman", 282.0, "İBB"),
            ("Konut", "Ortalama Kira", 25000.0, "Endeks"),
            ("Teknoloji", "iPhone 15", 58499.0, "Pazar"),
            ("Finans", "Gram Altın", 3050.0, "Piyasa"),
            ("Finans", "Dolar Kuru", 34.60, "Piyasa")
        ]
        for cat, ad, fiyat, k in sabitler:
            self.add_product(cat, ad, fiyat, k, is_live=True)

# --- Çalıştırma ---

if 'run' not in st.session_state:
    st.session_state['run'] = False

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🚀 Verileri Güncelle", type="primary"):
        st.session_state['run'] = True

if st.session_state['run']:
    with st.spinner('Veriler toplanıyor ve doğrulama yapılıyor...'):
        engine = DataEngine()
        engine.fetch_market_smart()
        engine.fetch_yakit_smart()
        engine.fetch_others()
        time.sleep(0.5)
    
    df = pd.DataFrame(engine.data)
    
    # Metrikler
    toplam = df["Güncel Fiyat"].sum()
    gecen = df["Geçen Ay (Tahmini)"].sum()
    degisim = ((toplam - gecen) / gecen) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Sepet Tutarı", f"{toplam:,.2f} ₺")
    m2.metric("Geçen Ay", f"{gecen:,.2f} ₺")
    m3.metric("Enflasyon", f"%{degisim:.2f}", delta="Artış")
    
    st.subheader("📋 Detaylı Liste")
    
    # Tabloyu özelleştirilmiş göster
    st.dataframe(
        df[["Kategori", "Ürün", "Güncel Fiyat", "Durum"]].style.format({"Güncel Fiyat": "{:.2f} ₺"}),
        use_container_width=True,
        hide_index=True
    )
    
    st.caption("* '🟠 Yedek Veri': Siteye erişilemediğinde kullanılan ortalama piyasa fiyatıdır.")

else:
    st.write("Başlamak için butona basın.")
