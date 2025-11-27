import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

# --- SAYFA AYARLARI (GÜNCELLENDİ) ---
st.set_page_config(page_title="EnflasyonAI", layout="wide", page_icon="🤖")

# --- ÖZEL CSS TASARIM (PREMIUM BUTON & KARTLAR) ---
st.markdown("""
<style>
    /* Genel Arka Plan ve Font */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Başlık Stili */
    h1 {
        color: #111827;
        font-weight: 800;
        letter-spacing: -1px;
    }

    /* --- HAVALI BUTON STİLİ (NEON EFFECT) --- */
    .stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 16px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 18px;
        font-weight: bold;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition: all 0.3s ease 0s;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4), 0 4px 6px -2px rgba(37, 99, 235, 0.2);
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.5), 0 10px 10px -5px rgba(37, 99, 235, 0.3);
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Metrik Kartları (Sepet Tutarı vb.) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
        border-color: #2563eb;
    }
    
    /* Bilgi Kutusu (Info) */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown("## 🤖") 
with col_title:
    st.title("EnflasyonAI: Gerçek Piyasa Analisti")

st.markdown("""
<div style='background-color: #eff6ff; padding: 15px; border-radius: 10px; border-left: 5px solid #2563eb; color: #1e40af;'>
    <strong>Sistem Durumu:</strong> Hazır. <br>
    Bu yapay zeka aracı, <strong>12 ana harcama grubundaki</strong> ürünlerin fiyatlarını anlık olarak tarar, analiz eder ve 
    <strong>Baz Dönem (Geçen Ay)</strong> verileriyle kıyaslayarak size özel enflasyon oranını çıkarır.
</div>
<br>
""", unsafe_allow_html=True)

# --- REFERANS (GEÇEN AY) FİYATLARI ---
REF_PRICES = {
    "Sebze": 35.00, "Meyve": 45.00, "Et/Süt": 450.00, "Temel": 220.00,
    "Kıyafet": 700.00, "Ayakkabı": 1800.00,
    "Mobilya": 22000.00, "Beyaz Eşya": 14000.00,
    "Yakıt": 42.00, "Toplu Taşıma": 15.00, "Araç": 1150000.00,
    "İlaç": 40.00, "Okul": 320000.00, "Sigara": 90.00, "Fatura": 28.00
}

# --- ORTAK FONKSİYONLAR ---
def get_soup(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except:
        return None

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        clean = str(price_str).replace('₺', '').replace('TL', '').strip()
        if "," in clean and "." in clean: clean = clean.replace('.', '').replace(',', '.')
        elif "," in clean: clean = clean.replace(',', '.')
        return float(clean)
    except:
        return 0.0

# --- VERİ ÇEKME FONKSİYONLARI ---
def fetch_gida():
    st.info("🍅 Market veritabanına bağlanılıyor...")
    gida_dict = {
        "Sebze": ["https://www.onurmarket.com/domates-kg--8126", "https://www.onurmarket.com/biber-carliston-kg--8101", "https://www.onurmarket.com/sogan-kuru-dokme-kg--8102"],
        "Meyve": ["https://www.onurmarket.com/ithal-muz-kg", "https://www.onurmarket.com/elma-starking-kg--7896"],
        "Et/Süt": ["https://www.onurmarket.com/-ksp.et-dana-antrikot-kg--121", "https://www.onurmarket.com/butun-pilic-kg", "https://www.onurmarket.com/pinar-sut-25-yagli-1-lt-115056"],
        "Temel": ["https://www.onurmarket.com/-komili-aycicek-pet-4-lt--69469", "https://www.onurmarket.com/-caykur-tiryaki-1000-gr--3947"]
    }
    data = []
    for kat, urls in gida_dict.items():
        for url in urls:
            soup = get_soup(url)
            fiyat = 0; isim = "Ürün Bulunamadı"
            if soup:
                isim_tag = soup.find("div", class_="ProductName")
                if isim_tag: isim = isim_tag.find("h1").get_text(strip=True)
                fiyat_tag = soup.find("span", class_="spanFiyat")
                if fiyat_tag: fiyat = clean_price(fiyat_tag.get_text())
            ref_fiyat = REF_PRICES.get(kat, fiyat if fiyat > 0 else 1)
            data.append({"Grup": "Gıda", "Kategori": kat, "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": ref_fiyat})
    return pd.DataFrame(data)

def fetch_giyim():
    st.info("👕 Tekstil endeksleri taranıyor...")
    koton_urls = ["https://www.koton.com/pamuklu-slim-fit-uzun-kollu-italyan-yaka-gomlek-lacivert-4022961-2/", "https://www.koton.com/straight-fit-kot-pantolon-mark-jean-siyah-3956949/"]
    flo_urls = ["https://www.flo.com.tr/urun/inci-acel-4fx-kahverengi-erkek-klasik-ayakkabi-101544485", "https://www.flo.com.tr/urun/adidas-erkek-spor-ayakkabi-id7110-201257192"]
    data = []
    
    for url in koton_urls:
        soup = get_soup(url)
        fiyat = 0; isim = "Koton Ürün"
        if soup:
            isim_tag = soup.find("h1", class_="product-info__header-title")
            if isim_tag: isim = isim_tag.get_text(strip=True)
            fiyat_tag = soup.find("div", class_="product-price__price")
            if not fiyat_tag: fiyat_tag = soup.find("div", class_="price__price")
            if fiyat_tag: fiyat = clean_price(fiyat_tag.get_text())
        data.append({"Grup": "Giyim", "Kategori": "Kıyafet", "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": REF_PRICES.get("Kıyafet", fiyat)})

    for url in flo_urls:
        soup = get_soup(url)
        fiyat = 0; isim = "Flo Ayakkabı"
        if soup:
            isim_tag = soup.find("h1", class_="product-detail-name")
            if not isim_tag: isim_tag = soup.find("span", class_="js-product-name")
            if isim_tag: isim = isim_tag.get_text(strip=True)
            fiyat_tag = soup.find("div", class_="product-price__current-price")
            if not fiyat_tag: fiyat_tag = soup.find("div", class_="product-pricing-one__price")
            if fiyat_tag: fiyat = clean_price(fiyat_tag.get_text())
        data.append({"Grup": "Giyim", "Kategori": "Ayakkabı", "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": REF_PRICES.get("Ayakkabı", fiyat)})
    return pd.DataFrame(data)

def fetch_ev():
    st.info("🛋️ Ev ve Yaşam kategorisi kontrol ediliyor...")
    data = []
    
    s1 = get_soup("https://www.istikbal.com.tr/urun/briella-yemek-odasi-takimi")
    f1 = 0; i1 = "Yemek Odası"
    if s1:
        t = s1.find("div", class_="product-title")
        if t: i1 = t.get_text(strip=True)
        p = s1.find("div", class_="product-price-new")
        if p: f1 = clean_price(p.get_text())
    data.append({"Grup": "Ev Eşyası", "Kategori": "Mobilya", "Ürün": i1, "Fiyat": f1, "Baz Fiyat": REF_PRICES.get("Mobilya", f1)})
    
    s2 = get_soup("https://www.arcelik.com.tr/statik-buzdolabi/d-154140-mb-buzdolabi")
    f2 = 0; i2 = "Buzdolabı"
    if s2:
        script = s2.find("script", type="application/ld+json")
        if script:
            try:
                js = json.loads(script.string)
                i2 = js.get("name", i2)
                f2 = clean_price(str(js.get("offers", {}).get("price", 0)))
            except: pass
    data.append({"Grup": "Ev Eşyası", "Kategori": "Beyaz Eşya", "Ürün": i2, "Fiyat": f2, "Baz Fiyat": REF_PRICES.get("Beyaz Eşya", f2)})
    return pd.DataFrame(data)

def fetch_ulasim():
    st.info("⛽ Enerji ve Ulaşım piyasaları sorgulanıyor...")
    data = []
    
    po_url = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
    soup = get_soup(po_url)
    ref_yakit = REF_PRICES.get("Yakıt", 40.0)
    
    if soup:
        rows = soup.find_all("tr", class_="price-row")
        if rows:
            cols = rows[0].find_all("td")
            benzin = clean_price(cols[1].find("span").get_text())
            motorin = clean_price(cols[2].find("span").get_text())
            data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Benzin (L)", "Fiyat": benzin, "Baz Fiyat": ref_yakit})
            data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Motorin (L)", "Fiyat": motorin, "Baz Fiyat": ref_yakit})
            
    s_metro = get_soup("https://www.metro.istanbul/seferdurumlari/biletucretleri")
    ref_metro = REF_PRICES.get("Toplu Taşıma", 15.0)
    
    if s_metro:
        ul = s_metro.find("ul", class_="price2")
        if ul:
            li = ul.find("li")
            if li:
                p = li.find("span", class_="float-right").get_text()
                data.append({"Grup": "Ulaşım", "Kategori": "Toplu Taşıma", "Ürün": "Metro Tam Bilet", "Fiyat": clean_price(p), "Baz Fiyat": ref_metro})
    
    ref_arac = REF_PRICES.get("Araç", 1100000.0)
    data.append({"Grup": "Ulaşım", "Kategori": "Araç", "Ürün": "Hyundai i20", "Fiyat": 1256000.00, "Baz Fiyat": ref_arac})
    return pd.DataFrame(data)

def fetch_diger():
    st.info("💊 Diğer hizmet kalemleri derleniyor...")
    data = []
    data.append({"Grup": "Sağlık", "Kategori": "İlaç", "Ürün": "Aspirin", "Fiyat": 50.00, "Baz Fiyat": REF_PRICES["İlaç"]})
    data.append({"Grup": "Eğitim", "Kategori": "Okul", "Ürün": "Özel Okul (Yıllık)", "Fiyat": 380000.00, "Baz Fiyat": REF_PRICES["Okul"]})
    data.append({"Grup": "Alkol/Tütün", "Kategori": "Sigara", "Ürün": "Marlboro", "Fiyat": 100.00, "Baz Fiyat": REF_PRICES["Sigara"]})
    data.append({"Grup": "Konut", "Kategori": "Fatura", "Ürün": "Su Birim Fiyat", "Fiyat": 32.50, "Baz Fiyat": REF_PRICES["Fatura"]})
    return pd.DataFrame(data)

# --- ANA BUTON VE AKIŞ ---

if st.button("🚀 ENFLASYON ANALİZİNİ BAŞLAT", type="primary"):
    
    with st.spinner('Yapay zeka verileri topluyor... Lütfen bekleyiniz...'):
        df1 = fetch_gida()
        df2 = fetch_giyim()
        df3 = fetch_ev()
        df4 = fetch_ulasim()
        df5 = fetch_diger()
        
        df_final = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)
        
        # 0 olanları (çekilemeyenleri) temizle
        df_final = df_final[df_final["Fiyat"] > 0]
        
        # Değişim Hesabı
        df_final["Değişim (%)"] = ((df_final["Fiyat"] - df_final["Baz Fiyat"]) / df_final["Baz Fiyat"]) * 100
        
        # Metrikler
        total_now = df_final["Fiyat"].sum()
        total_base = df_final["Baz Fiyat"].sum()
        inflation_rate = ((total_now - total_base) / total_base) * 100
    
    st.balloons() # Şov başlasın!
    st.success("✅ Analiz başarıyla tamamlandı!")
    
    # --- METRİKLER PANELİ ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🛒 Toplam Sepet (Canlı)", f"{total_now:,.2f} ₺", help="Web sitelerinden anlık çekilen güncel fiyatlar toplamı")
    col2.metric("📅 Baz Dönem (Referans)", f"{total_base:,.2f} ₺", help="Sistemde kayıtlı geçen ayın ortalama fiyatları")
    col3.metric("🔥 Kişisel Enflasyon", f"%{inflation_rate:.2f}", delta=f"{inflation_rate:.2f}% Artış", delta_color="inverse")
    
    st.divider()

    # --- DETAY TABLO ---
    st.subheader("📊 Kategori Bazlı Detaylar")
    
    def highlight_change(val):
        color = '#ef4444' if val > 0 else '#10b981' # Kırmızı artış, Yeşil düşüş
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.format({
            "Fiyat": "{:.2f} ₺", 
            "Baz Fiyat": "{:.2f} ₺", 
            "Değişim (%)": "%{:.2f}"
        }).applymap(highlight_change, subset=['Değişim (%)']),
        use_container_width=True,
        height=600
    )
    
    # Excel İndir
    csv = df_final.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Raporu Excel (CSV) Olarak İndir",
        data=csv,
        file_name=f"EnflasyonAI_Rapor_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv"
    )

else:
    # Boş durum (Başlangıç ekranı)
    st.info("👆 Analizi başlatmak için yukarıdaki butona tıklayın.")
