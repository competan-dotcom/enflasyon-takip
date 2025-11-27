import streamlit as st
import pandas as pd
import numpy as np
import time
import random

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="EnflasyonAI",
    page_icon="🦖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Tasarım ---
st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        text-align: center;
    }
    .metric-title { font-size: 14px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 32px; font-weight: 800; margin-top: 5px; color: #38bdf8; }
    .metric-delta { font-size: 14px; font-weight: bold; color: #f43f5e; margin-top: 5px; }
    .dataframe { font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# --- 5000 ÜRÜN ÜRETME MOTORU ---
def generate_big_data():
    # Kategori Bazlı Şablonlar (Ortalama Fiyat, Varyasyon Sayısı)
    templates = {
        "Gıda": [("Ekmek", 15), ("Peynir", 250), ("Süt", 35), ("Et", 600), ("Yağ", 280), ("Çay", 200)],
        "Giyim": [("Pantolon", 900), ("Gömlek", 700), ("Ayakkabı", 2500), ("Mont", 3500)],
        "Teknoloji": [("Telefon", 35000), ("Kulaklık", 1500), ("Laptop", 45000), ("Şarj Aleti", 400)],
        "Ev & Yaşam": [("Deterjan", 250), ("Ampul", 80), ("Nevresim", 600), ("Havlu", 150)],
        "Ulaşım": [("Benzin", 45), ("Otobüs Bileti", 20), ("Taksi", 150)],
        "Hizmet": [("Berber", 300), ("Kuru Temizleme", 200), ("Tamirat", 1500)]
    }
    
    data = []
    
    # 5000 Satır Üret
    for i in range(1, 5001):
        kategori = random.choice(list(templates.keys()))
        urun_baz, ort_fiyat = random.choice(templates[kategori])
        
        # Rastgelelik Ekle (Gerçekçi olması için)
        fiyat_sapmasi = random.uniform(0.8, 1.2) # Fiyat %20 aşağı veya yukarı oynasın
        guncel_fiyat = ort_fiyat * fiyat_sapmasi
        
        # Enflasyon Simülasyonu (Geçen aya göre %3 ile %15 arası artış varmış gibi)
        enflasyon_etkisi = random.uniform(1.03, 1.15)
        gecen_ay_fiyat = guncel_fiyat / enflasyon_etkisi
        
        # Marka/Model Uydurma
        kod = f"#{random.randint(1000, 9999)}"
        varyasyon = random.choice(["Eco", "Lüks", "Standart", "Paket", "Mega", "İthal"])
        
        data.append({
            "ID": i,
            "Kategori": kategori,
            "Ürün Adı": f"{urun_baz} {varyasyon} {kod}",
            "Güncel Fiyat": round(guncel_fiyat, 2),
            "Geçen Ay": round(gecen_ay_fiyat, 2),
            "Fark (%)": round((enflasyon_etkisi - 1) * 100, 2),
            "Kaynak": "Veri Havuzu"
        })
        
    return pd.DataFrame(data)

# --- ANA UYGULAMA ---

st.title("🦖 T-REX ENFLASYON MOTORU")
st.markdown("**Veri Seti:** `5.000 Kalem Ürün` | **Mod:** `Simülasyon & Büyük Veri Analizi`")

if st.button("🔥 5.000 Ürünlük Analizi Başlat", type="primary", use_container_width=True):
    
    with st.spinner("Milyonlarca veri noktası işleniyor... Sunucular ısınıyor..."):
        # Yükleme efekti
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01) # Hızlıca dolsun
            progress_bar.progress(i + 1)
        
        # Veriyi Üret
        df = generate_big_data()
        
    st.success("Analiz Tamamlandı! 5000 Satır Veri İşlendi.")
    
    # HESAPLAMALAR
    total_now = df["Güncel Fiyat"].sum()
    total_prev = df["Geçen Ay"].sum()
    inflation = ((total_now - total_prev) / total_prev) * 100
    
    # 3'lü Gösterge Paneli
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Toplam Sepet Değeri</div>
            <div class="metric-value">{total_now:,.0f} ₺</div>
            <div class="metric-delta">5.000 Ürün</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-box" style="background: linear-gradient(135deg, #334155 0%, #1e293b 100%);">
            <div class="metric-title">Geçen Ay Tahmini</div>
            <div class="metric-value" style="color:#94a3b8;">{total_prev:,.0f} ₺</div>
             <div class="metric-delta" style="color:#94a3b8;">Baz Dönem</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="metric-box" style="background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);">
            <div class="metric-title">Genel Enflasyon</div>
            <div class="metric-value" style="color:#fca5a5;">%{inflation:.2f}</div>
            <div class="metric-delta">Aylık Artış 🔥</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- GRAFİK ŞOVU ---
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("📊 Kategori Bazlı Harcama Dağılımı")
        chart_data = df.groupby("Kategori")["Güncel Fiyat"].sum().reset_index()
        st.bar_chart(chart_data, x="Kategori", y="Güncel Fiyat", color="#38bdf8")
        
    with col_chart2:
        st.subheader("🥧 Enflasyonun Suçlusu Hangi Kategori?")
        # En yüksek artış olan kategorileri bul
        inf_data = df.groupby("Kategori")["Fark (%)"].mean()
        st.dataframe(inf_data, use_container_width=True)

    # --- DEV TABLO ---
    st.subheader("🗂️ 5.000 Satırlık Dev Veri Seti")
    st.dataframe(
        df.style.format({"Güncel Fiyat": "{:.2f} ₺", "Geçen Ay": "{:.2f} ₺", "Fark (%)": "%{:.2f}"})
          .background_gradient(subset=["Fark (%)"], cmap="Reds"),
        use_container_width=True,
        height=500 # Tabloyu uzun göster
    )

else:
    st.info("Devasa veri setini analiz etmek için butona bas.")
