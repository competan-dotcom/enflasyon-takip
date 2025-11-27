import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

st.set_page_config(page_title="Gerçek Enflasyon Sepeti", layout="wide", page_icon="🇹🇷")

st.title("🇹🇷 Kapsamlı Enflasyon Veri Madencisi")
st.markdown("""
**Kaynak:** `enf_veri_cekme_guncel.ipynb` (Orijinal Kod) | **Kapsam:** `12 Ana Harcama Grubu`
<br>
<small>*Not: Değişim oranları, sistemde tanımlı 'Baz Dönem' fiyatları ile anlık çekilen 'Canlı' fiyatlar kıyaslanarak hesaplanır.*</small>
""", unsafe_allow_html=True)

# --- REFERANS (GEÇEN AY) FİYATLARI ---
# Karşılaştırma yapabilmek için baz fiyatlar (Tahmini Piyasa Ortalamaları)
REF_PRICES = {
    "Sebze": 35.00, "Meyve": 45.00, "Et/Süt": 450.00, "Temel": 220.00, # Gıda
    "Kıyafet": 700.00, "Ayakkabı": 1800.00, # Giyim
    "Mobilya": 22000.00, "Beyaz Eşya": 14000.00, # Ev
    "Yakıt": 42.00, "Toplu Taşıma": 15.00, "Araç": 1150000.00, # Ulaşım
    "İlaç": 40.00, "Okul": 320000.00, "Sigara": 90.00, "Fatura": 28.00 # Diğer
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

# --- 1. GIDA VE ALKOLSÜZ İÇECEKLER ---
def fetch_gida():
    st.info("🍅 1. Gıda ve Market verileri çekiliyor... (Onur Market)")
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
            fiyat = 0
            isim = "Ürün Bulunamadı"
            if soup:
                isim_tag = soup.find("div", class_="ProductName")
                if isim_tag: isim = isim_tag.find("h1").get_text(strip=True)
                fiyat_tag = soup.find("span", class_="spanFiyat")
                if fiyat_tag: fiyat = clean_price(fiyat_tag.get_text())
            
            # Referans Fiyatı Al (Yoksa canlı fiyatı baz al ki değişim 0 çıksın)
            ref_fiyat = REF_PRICES.get(kat, fiyat if fiyat > 0 else 1)
            
            data.append({"Grup": "Gıda", "Kategori": kat, "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": ref_fiyat})
    return pd.DataFrame(data)

# --- 2. GİYİM VE AYAKKABI ---
def fetch_giyim():
    st.info("👕 2. Giyim ve Ayakkabı verileri çekiliyor... (Koton & Flo)")
    koton_urls = [
        "https://www.koton.com/pamuklu-slim-fit-uzun-kollu-italyan-yaka-gomlek-lacivert-4022961-2/",
        "https://www.koton.com/straight-fit-kot-pantolon-mark-jean-siyah-3956949/"
    ]
    flo_urls = [
        "https://www.flo.com.tr/urun/inci-acel-4fx-kahverengi-erkek-klasik-ayakkabi-101544485",
        "https://www.flo.com.tr/urun/adidas-erkek-spor-ayakkabi-id7110-201257192"
    ]
    data = []
    
    # Koton
    for url in koton_urls:
        soup = get_soup(url)
        fiyat = 0; isim = "Koton Ürün"
        if soup:
            isim_tag = soup.find("h1", class_="product-info__header-title")
            if isim_tag: isim = isim_tag.get_text(strip=True)
            fiyat_tag = soup.find("div", class_="product-price__price")
            if not fiyat_tag: fiyat_tag = soup.find("div", class_="price__price")
            if fiyat_tag: fiyat = clean_price(fiyat_tag.get_text())
        
        ref = REF_PRICES.get("Kıyafet", fiyat)
        data.append({"Grup": "Giyim", "Kategori": "Kıyafet", "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": ref})

    # Flo
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
            
        ref = REF_PRICES.get("Ayakkabı", fiyat)
        data.append({"Grup": "Giyim", "Kategori": "Ayakkabı", "Ürün": isim, "Fiyat": fiyat, "Baz Fiyat": ref})
        
    return pd.DataFrame(data)

# --- 3. EV EŞYASI (Mobilya, Beyaz Eşya) ---
def fetch_ev():
    st.info("🛋️ 3. Ev Eşyası verileri çekiliyor... (İstikbal & Arçelik)")
    data = []
    
    # İstikbal
    s1 = get_soup("https://www.istikbal.com.tr/urun/briella-yemek-odasi-takimi")
    f1 = 0; i1 = "Yemek Odası"
    if s1:
        t = s1.find("div", class_="product-title")
        if t: i1 = t.get_text(strip=True)
        p = s1.find("div", class_="product-price-new")
        if p: f1 = clean_price(p.get_text())
    
    ref1 = REF_PRICES.get("Mobilya", f1)
    data.append({"Grup": "Ev Eşyası", "Kategori": "Mobilya", "Ürün": i1, "Fiyat": f1, "Baz Fiyat": ref1})
    
    # Arçelik
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
    
    ref2 = REF_PRICES.get("Beyaz Eşya", f2)
    data.append({"Grup": "Ev Eşyası", "Kategori": "Beyaz Eşya", "Ürün": i2, "Fiyat": f2, "Baz Fiyat": ref2})
    
    return pd.DataFrame(data)

# --- 4. ULAŞTIRMA (Yakıt, Araç, Metro) ---
def fetch_ulasim():
    st.info("🚗 4. Ulaşım verileri çekiliyor... (Petrol Ofisi & İBB)")
    data = []
    
    # Yakıt
    po_url = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
    soup = get_soup(po_url)
    ref_yakit = REF_PRICES.get("Yakıt", 40.0)
    
    if soup:
        rows = soup.find_all("tr", class_="price-row")
        if rows:
            cols = rows[0].find_all("td")
            benzin = clean_price(cols[1].find("span").get_text())
            motorin = clean_price(cols[2].find("span").get_text())
            data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Benzin", "Fiyat": benzin, "Baz Fiyat": ref_yakit})
            data.append({"Grup": "Ulaşım", "Kategori": "Yakıt", "Ürün": "Motorin", "Fiyat": motorin, "Baz Fiyat": ref_yakit})
            
    # Metro İstanbul
    s_metro = get_soup("https://www.metro.istanbul/seferdurumlari/biletucretleri")
    ref_metro = REF_PRICES.get("Toplu Taşıma", 15.0)
    
    if s_metro:
        ul = s_metro.find("ul", class_="price2")
        if ul:
            li = ul.find("li")
            if li:
                p = li.find("span", class_="float-right").get_text()
                data.append({"Grup": "Ulaşım", "Kategori": "Toplu Taşıma", "Ürün": "Metro Tam Bilet", "Fiyat": clean_price(p), "Baz Fiyat": ref_metro})
    
    # Araç (Manuel)
    ref_arac = REF_PRICES.get("Araç", 1100000.0)
    data.append({"Grup": "Ulaşım", "Kategori": "Araç", "Ürün": "Hyundai i20", "Fiyat": 1256000.00, "Baz Fiyat": ref_arac})
    
    return pd.DataFrame(data)

# --- 5. DİĞER KATEGORİLER (Kısa Kısa) ---
def fetch_diger():
    st.info("💊 5. Sağlık, Eğitim ve Diğerleri derleniyor...")
    data = []
    
    data.append({"Grup": "Sağlık", "Kategori": "İlaç", "Ürün": "Aspirin", "Fiyat": 50.00, "Baz Fiyat": REF_PRICES["İlaç"]})
    data.append({"Grup": "Eğitim", "Kategori": "Okul", "Ürün": "Özel Okul (Yıllık)", "Fiyat": 380000.00, "Baz Fiyat": REF_PRICES["Okul"]})
    data.append({"Grup": "Alkol/Tütün", "Kategori": "Sigara", "Ürün": "Marlboro", "Fiyat": 100.00, "Baz Fiyat": REF_PRICES["Sigara"]})
    data.append({"Grup": "Konut", "Kategori": "Fatura", "Ürün": "Su Birim Fiyat", "Fiyat": 32.50, "Baz Fiyat": REF_PRICES["Fatura"]})
    
    return pd.DataFrame(data)

# --- ANA MOTOR ---

if st.button("🚀 ENFLASYONU HESAPLA (DEĞİŞİM MODU)", type="primary"):
    
    df1 = fetch_gida()
    df2 = fetch_giyim()
    df3 = fetch_ev()
    df4 = fetch_ulasim()
    df5 = fetch_diger()
    
    df_final = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)
    
    # 0 olanları (çekilemeyenleri) temizle ki enflasyonu bozmasın
    df_final = df_final[df_final["Fiyat"] > 0]
    
    # Değişim Hesabı
    df_final["Değişim (%)"] = ((df_final["Fiyat"] - df_final["Baz Fiyat"]) / df_final["Baz Fiyat"]) * 100
    
    st.success("Analiz tamamlandı!")
    
    # --- METRİKLER ---
    total_now = df_final["Fiyat"].sum()
    total_base = df_final["Baz Fiyat"].sum()
    inflation_rate = ((total_now - total_base) / total_base) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Sepet (Canlı)", f"{total_now:,.2f} ₺")
    col2.metric("Baz Dönem (Referans)", f"{total_base:,.2f} ₺")
    col3.metric("Kişisel Enflasyon", f"%{inflation_rate:.2f}", delta=f"{inflation_rate:.2f}% Artış")
    
    # --- DETAY TABLO ---
    st.subheader("📊 Kategori Bazlı Detaylar")
    
    # Tabloyu Renklendir (Artış varsa kırmızı, düşüş varsa yeşil)
    def highlight_change(val):
        color = 'red' if val > 0 else 'green'
        return f'color: {color}'

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
    st.download_button("📥 Raporu İndir (CSV)", csv, "enflasyon_degisim_raporu.csv", "text/csv")

else:
    st.write("Anlık fiyatları çekip, baz dönem fiyatlarıyla kıyaslayarak **Gerçek Enflasyon Oranını** hesaplamak için butona basın.")
    st.warning("Veriler anlık olarak sitelerden çekilmektedir.")
