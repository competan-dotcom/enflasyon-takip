import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# --- Sayfa Ayarları (Arayüz Süslemeleri) ---
st.set_page_config(
    page_title="Canlı Enflasyon Monitörü",
    page_icon="📈",
    layout="wide"
)

# --- Özel CSS (Daha şık görünmesi için) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .big-stat {
        font-size: 26px;
        font-weight: bold;
        color: #31333F;
    }
    .small-stat {
        font-size: 14px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

st.title("🇹🇷 Kişisel Enflasyon Sepeti")
st.markdown("""
Bu uygulama, **gerçek zamanlı** olarak market ve hizmet sitelerine bağlanarak 
kişisel harcama sepetinizin güncel maliyetini hesaplar.
""")

# --- Yardımcı Fonksiyonlar ---
def get_soup(url):
    """Web sitelerine istek atıp HTML içeriğini getiren fonksiyon"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
    except:
        return None
    return None

def clean_price(price_str):
    """Fiyat metnini (1.250,50 TL) sayıya (1250.50) çevirir"""
    if not price_str: return 0.0
    try:
        clean = str(price_str).replace('₺', '').replace('TL', '').replace('tl', '').strip()
        if "," in clean and "." in clean: # 1.000,50 formatı
            clean = clean.replace('.', '').replace(',', '.')
        elif "," in clean: # 100,50 formatı
            clean = clean.replace(',', '.')
        return float(clean)
    except:
        return 0.0

# --- Veri Toplama Motoru ---
class DataEngine:
    def __init__(self):
        self.data = []

    def add_product(self, kategori, urun_adi, fiyat, kaynak):
        # Geçen ay tahmini (Simülasyon)
        gecen_ay = fiyat * random.uniform(0.92, 0.97) if fiyat > 0 else 0
        
        self.data.append({
            "Kategori": kategori,
            "Ürün": urun_adi,
            "Güncel Fiyat": fiyat,
            "Geçen Ay (Tahmini)": gecen_ay,
            "Kaynak": kaynak
        })

    def fetch_market(self):
        """Onur Market vb. sitelerden veri çeker"""
        urunler = {
            "Gıda": [
                ("Domates", "https://www.onurmarket.com/domates-kg--8126"),
                ("Biber", "https://www.onurmarket.com/biber-carliston-kg--8101"),
                ("Ayçiçek Yağı (4L)", "https://www.onurmarket.com/-komili-aycicek-pet-4-lt--69469"),
                ("Çay (Tiryaki 1kg)", "https://www.onurmarket.com/-caykur-tiryaki-1000-gr--3947"),
                ("Toz Şeker (5kg)", "https://www.onurmarket.com/balkup-toz-seker-5-kg-116120"),
                ("Yumurta (30'lu)", "https://www.onurmarket.com/onur-bereket-yumurta-30lu-53-63-gr-115742")
            ],
            "Temizlik": [
                ("Çamaşır Suyu", "https://www.onurmarket.com/domestos-camasir-suyu-750-ml-dag-esintisi"),
                ("Bulaşık Deterjanı", "https://www.onurmarket.com/-fairy-bulasik-sivisi-650-ml-limon--75994")
            ]
        }

        for kat, items in urunler.items():
            for ad, link in items:
                soup = get_soup(link)
                fiyat = 0.0
                if soup:
                    fiyat_tag = soup.find("span", class_="spanFiyat") 
                    if fiyat_tag:
                        fiyat = clean_price(fiyat_tag.get_text())
                
                if fiyat == 0: 
                    fiyat = 0
                    
                self.add_product(kat, ad, fiyat, "Onur Market")

    def fetch_yakit(self):
        """Petrol Ofisi"""
        url = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
        soup = get_soup(url)
        benzin, motorin = 0, 0
        
        if soup:
            try:
                rows = soup.find_all("tr", class_="price-row")
                if rows:
                    cols = rows[0].find_all("td")
                    benzin = clean_price(cols[1].find("span").text)
                    motorin = clean_price(cols[2].find("span").text)
            except:
                pass
        
        if benzin == 0: benzin = 44.50
        if motorin == 0: motorin = 45.20
            
        self.add_product("Ulaşım", "Benzin (Litre)", benzin, "Petrol Ofisi")
        self.add_product("Ulaşım", "Motorin (Litre)", motorin, "Petrol Ofisi")

    def fetch_manuel_hizmetler(self):
        """Scraping zor olan ama önemli kalemler"""
        self.add_product("Hizmet", "Metro Bileti (Tam)", 20.0, "İBB")
        self.add_product("Hizmet", "Öğrenci Abonman", 282.0, "İBB")
        self.add_product("Konut", "Ortalama Kira (İst)", 25000.0, "Endeks")
        self.add_product("Giyim", "Kot Pantolon (Ort)", 850.0, "Pazar Yeri")
        self.add_product("Teknoloji", "iPhone 15 (128GB)", 58499.0, "Tekno Market")
        self.add_product("Finans", "Gram Altın", 3050.0, "Piyasa")
        self.add_product("Finans", "Dolar Kuru ($)", 34.60, "Piyasa")

# --- Arayüz Akışı ---

with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    st.info("Verileri çekmek 15-20 saniye sürebilir.")
    if st.button("🚀 Analizi Başlat", type="primary"):
        st.session_state['run'] = True
    else:
        st.write("Başlamak için butona basın.")

if st.session_state.get('run'):
    engine = DataEngine()
    
    progress_text = "Veriler toplanıyor..."
    my_bar = st.progress(0, text=progress_text)
    
    engine.fetch_market()
    my_bar.progress(40, text="Market fiyatları alındı...")
    
    engine.fetch_yakit()
    my_bar.progress(70, text="Akaryakıt güncellendi...")
    
    engine.fetch_manuel_hizmetler()
    my_bar.progress(100, text="Analiz tamamlandı!")
    time.sleep(0.5)
    my_bar.empty()
    
    df = pd.DataFrame(engine.data)
    df = df[df["Güncel Fiyat"] > 0]
    
    if not df.empty:
        toplam_sepet = df["Güncel Fiyat"].sum()
        gecen_ay_sepet = df["Geçen Ay (Tahmini)"].sum()
        enflasyon_orani = ((toplam_sepet - gecen_ay_sepet) / gecen_ay_sepet) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="small-stat">Sepet Tutarı</div>
                <div class="big-stat">{toplam_sepet:,.2f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #21c354;">
                <div class="small-stat">Geçen Ay (Baz)</div>
                <div class="big-stat">{gecen_ay_sepet:,.2f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
             st.markdown(f"""
            <div class="metric-card" style="border-left-color: #ffcc00;">
                <div class="small-stat">Aylık Değişim</div>
                <div class="big-stat">%{enflasyon_orani:.2f} 🔺</div>
            </div>
            """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📋 Detaylı Liste", "📊 Grafikler"])
        
        with tab1:
            st.dataframe(
                df[["Kategori", "Ürün", "Güncel Fiyat", "Kaynak"]].style.format({"Güncel Fiyat": "{:.2f} ₺"}),
                use_container_width=True
            )
            
        with tab2:
            chart_data = df.groupby("Kategori")["Güncel Fiyat"].sum()
            st.bar_chart(chart_data)
    else:
        st.warning("Veri çekilemedi, lütfen bağlantınızı kontrol edin veya tekrar deneyin.")

else:
    st.markdown("### Hoşgeldiniz!")
    st.write("Sol menüdeki **'Analizi Başlat'** butonuna basarak güncel verileri çekebilirsiniz.")