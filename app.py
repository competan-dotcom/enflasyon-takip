import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import time  # <-- EKLENDİ: Artık "time is not defined" hatası vermeyecek.

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="EnflasyonAI", layout="wide", page_icon="🤖")

# --- 🎨 PREMIUM TASARIM (CSS) ---
st.markdown("""
<style>
    /* Google Font: Poppins */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        background-color: #f3f4f6; /* Çok açık gri arka plan */
        color: #1f2937;
    }

    /* HERO SECTION (Üst Başlık) */
    .hero {
        background: linear-gradient(120deg, #2563eb, #1e40af);
        padding: 40px 20px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -10px rgba(37, 99, 235, 0.5);
    }
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        color: white;
        letter-spacing: -1px;
    }
    .hero p {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin-top: 10px;
    }

    /* METRİK KARTLARI */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: center;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    div[data-testid="metric-container"] label {
        font-weight: 600;
        color: #6b7280;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827;
    }

    /* BUTON STİLİ (PULSE ANİMASYONLU) */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
    }

    .stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 20px 40px;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 50px;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        animation: pulse 2s infinite;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.4);
        animation: none; /* Üzerine gelince animasyon dursun */
    }
    
    /* BİLGİ KUTULARI (INFO) */
    .stAlert {
        border-radius: 12px;
        border: none;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* TABLO TASARIMI */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- MODERN HEADER (HTML) ---
st.markdown("""
<div class="hero">
    <h1>🤖 EnflasyonAI</h1>
    <p>Yapay Zeka Destekli Gerçek Zamanlı Piyasa Analisti</p>
</div>
""", unsafe_allow_html=True)

# --- REFERANS (GEÇEN AY) FİYATLARI ---
REF_PRICES = {
    "Sebze": 55.00, "Meyve": 75.00, "Et/Süt": 950.00, "Temel": 420.00,
    "Kıyafet": 1100.00, "Ayakkabı": 3600.00,
    "Mobilya": 52000.00, "Beyaz Eşya": 24000.00,
    "Yakıt": 52.00, "Toplu Taşıma": 35.00, "Araç": 1250000.00,
    "İlaç": 46.00, "Okul": 320000.00, "Sigara": 90.00, "Fatura": 88.00
}

# --- YARDIMCI FONKSİYONLAR ---
def get_soup(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10) # Timeout düşürdüm hızlansın
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
    except:
        return None
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

# --- VERİ ÇEKME MODÜLLERİ ---
def fetch_gida():
    data = []
    gida_dict = {
        "Sebze": ["https://www.onurmarket.com/domates-kg--8126", "https://www.onurmarket.com/biber-carliston-kg--8101"],
        "Et/Süt": ["https://www.onurmarket.com/-ksp.et-dana-antrikot-kg--121", "https://www.onurmarket.com/butun-pilic-kg"],
        "Temel": ["https://www.onurmarket.com/-komili-aycicek-pet-4-lt--69469", "https://www.onurmarket.com/-caykur-tiryaki-1000-gr--3947"]
    }
    for kat, urls in gida_dict.items():
        for url in urls:
            soup = get_soup(url)
            fiyat = 0; isim = "Veri Alınamadı"
            if soup:
                tag = soup.find("div", class_="ProductName")
                if tag: isim = tag.find("h1").get_text(strip=True)
                p_tag = soup.find("span", class_="spanFiyat")
                if p_tag: fiyat = clean_price(p_tag.get_text())
            
            # Fallback (Eğer site engellerse 0 görünmesin diye ortalama bir değer - Opsiyonel)
            # if fiyat == 0: fiyat = REF_PRICES.get(kat, 0) * 1.05 
            
            data.append({"Grup": "Gıda", "Kategori": kat, "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": REF_PRICES.get(kat, 1)})
    return pd.DataFrame(data)

def fetch_giyim():
    data = []
    # Koton & Flo Örnekleri
    urls = [
        ("Kıyafet", "https://www.koton.com/pamuklu-slim-fit-uzun-kollu-italyan-yaka-gomlek-lacivert-4022961-2/"),
        ("Ayakkabı", "https://www.flo.com.tr/urun/inci-acel-4fx-kahverengi-erkek-klasik-ayakkabi-101544485")
    ]
    for kat, url in urls:
        soup = get_soup(url)
        fiyat = 0; isim = "Moda Ürünü"
        if soup:
            # Basit genel tarama
            title = soup.find("h1")
            if title: isim = title.get_text(strip=True)
            # Flo ve Koton fiyat classları değişebiliyor, genel arama
            price_divs = soup.find_all("div", class_=re.compile("price"))
            for p in price_divs:
                txt = p.get_text()
                if "TL" in txt:
                    extracted = clean_price(txt)
                    if extracted > 10: # Mantıklı bir fiyatsa al
                        fiyat = extracted
                        break
        data.append({"Grup": "Giyim", "Kategori": kat, "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": REF_PRICES.get(kat, 1)})
    return pd.DataFrame(data)

def fetch_genel_piyasa():
    data = []
    # Ulaşım & Yakıt
    po_url = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
    soup = get_soup(po_url)
    f_benzin = 0; f_motorin = 0
    if soup:
        rows = soup.find_all("tr", class_="price-row")
        if rows:
            cols = rows[0].find_all("td")
            f_benzin = clean_price(cols[1].find("span").get_text())
            f_motorin = clean_price(cols[2].find("span").get_text())
    
    data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Benzin (L)", "Fiyat": f_benzin, "Baz Fiyat": REF_PRICES["Yakıt"]})
    data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Motorin (L)", "Fiyat": f_motorin, "Baz Fiyat": REF_PRICES["Yakıt"]})
    
    # Diğer Sabitler
    data.append({"Grup": "Ulaşım", "Kategori": "Araç", "Ürün": "Hyundai i20", "Fiyat": 1256000.00, "Baz Fiyat": REF_PRICES["Araç"]})
    data.append({"Grup": "Sağlık", "Kategori": "İlaç", "Ürün": "Aspirin", "Fiyat": 50.00, "Baz Fiyat": REF_PRICES["İlaç"]})
    
    return pd.DataFrame(data)

# --- ANA GÖVDE ---

# Kullanıcıyı karşılayan info kutusu (Daha şık)
st.info("ℹ️ Analizi başlatmak için aşağıdaki butona tıklayın. Sistem anlık olarak market ve borsa verilerini tarayacaktır.")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    start_btn = st.button("🚀 ANALİZİ BAŞLAT")

if start_btn:
    
    # İlerleme Çubuğu ve Spinner
    progress_text = "Yapay zeka piyasayı tarıyor..."
    my_bar = st.progress(0, text=progress_text)
    
    # Adım 1: Gıda
    df1 = fetch_gida()
    my_bar.progress(40, text="Gıda fiyatları güncellendi...")
    
    # Adım 2: Giyim
    df2 = fetch_giyim()
    my_bar.progress(70, text="Tekstil verileri işleniyor...")
    
    # Adım 3: Genel
    df3 = fetch_genel_piyasa()
    my_bar.progress(100, text="Analiz tamamlandı!")
    
    # Birleştir
    df_final = pd.concat([df1, df2, df3], ignore_index=True)
    df_final = df_final[df_final["Fiyat"] > 0] # Sadece verisi olanlar
    
    # Hesaplama
    df_final["Değişim (%)"] = ((df_final["Fiyat"] - df_final["Baz Fiyat"]) / df_final["Baz Fiyat"]) * 100
    
    total_now = df_final["Fiyat"].sum()
    total_base = df_final["Baz Fiyat"].sum()
    inflation = ((total_now - total_base) / total_base) * 100
    
    time.sleep(0.5)
    my_bar.empty()
    
    # --- SONUÇ EKRANI ---
    
    # Metrikler
    c1, c2, c3 = st.columns(3)
    c1.metric("🛒 Canlı Sepet Tutarı", f"{total_now:,.2f} ₺")
    c2.metric("📅 Baz Dönem (Geçen Ay)", f"{total_base:,.2f} ₺")
    
    # Enflasyon rengi (Yüksekse kırmızı)
    delta_color = "inverse" if inflation > 0 else "normal"
    c3.metric("🔥 Kişisel Enflasyon", f"%{inflation:.2f}", delta=f"{inflation:.2f}% Değişim", delta_color=delta_color)
    
    st.markdown("---")
    
    # Tablo
    st.subheader("📋 Detaylı Ürün Analizi")
    
    def color_change(val):
        color = '#ef4444' if val > 0 else '#10b981'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df_final.style.format({
            "Fiyat": "{:.2f} ₺", 
            "Baz Fiyat": "{:.2f} ₺", 
            "Değişim (%)": "%{:.2f}"
        }).applymap(color_change, subset=['Değişim (%)']),
        use_container_width=True,
        height=500
    )
    
    # İndirme Butonu (Ortalanmış)
    csv = df_final.to_csv(index=False).encode('utf-8-sig')
    col_d1, col_d2, col_d3 = st.columns([1,2,1])
    with col_d2:
        st.download_button(
            label="📥 Raporu İndir (Excel/CSV)",
            data=csv,
            file_name="EnflasyonAI_Raporu.csv",
            mime="text/csv",
            key='download-btn'
        )

