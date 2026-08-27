import datetime
from io import BytesIO
import json
import os
import pandas as pd
import streamlit as st
import pdfplumber

# Sayfa ayarları
st.set_page_config(
    page_title="Nöbetçim - Okul Nöbet ve Görevlendirme Sistemi",
    page_icon="📋",
    layout="wide",
)

# --- MODERN UI & CSS STYLING ---
st.markdown("""
    <style>
    /* Google Fonts Entegrasyonu */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Arka Plan Ferahlığı */
    .main {
        background-color: #f4f6f9;
    }

    /* Kart Yapıları */
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
        gap: 1.5rem;
    }

    /* Buton Tasarımları */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: 1px solid #d0d7de;
        background-color: #ffffff;
        color: #24292f;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        border-color: #0969da;
        color: #0969da;
        box-shadow: 0 3px 8px rgba(9, 105, 218, 0.12);
    }

    /* Birincil Butonlar */
    div.stButton > button[kind="primary"] {
        background-color: #0969da;
        color: #ffffff;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0860c4;
        box-shadow: 0 4px 12px rgba(9, 105, 218, 0.25);
    }

    /* Sekme (Tabs) Modernizasyonu */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        color: #57606a;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0969da !important;
        color: #ffffff !important;
    }

    /* Expander Şıklığı */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e1e4e8;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

kullanici_dosyasi = "kullanicilar.json"


# --- YARDIMCI FONKSİYONLAR ---
def tr_normalize(text):
    if pd.isna(text): return ""
    return str(text).strip().replace("İ", "i").replace("I", "ı").replace("Ş", "ş").replace("Ğ", "ğ").replace("Ü",
                                                                                                             "ü").replace(
        "Ö", "ö").replace("Ç", "ç").lower()


def kullanicilari_kaydet(users_dict):
    try:
        with open(kullanici_dosyasi, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def kullanicilari_yukle():
    if os.path.exists(kullanici_dosyasi):
        try:
            with open(kullanici_dosyasi, "r", encoding="utf-8") as f:
                icerik = f.read().strip()
                if icerik:
                    veri = json.loads(icerik)
                    if isinstance(veri, dict) and veri: return veri
        except Exception:
            pass

    varsayilan = {
        "ediperdinc": {
            "password": "1234567890", "il": "Gaziantep", "ilce": "Şahinbey",
            "okul_adi": "Kürşat Tüzmen Ortaokulu", "mudur_adi": "Erdinç Uçar", "kurum_kodu": "123456"
        }
    }
    kullanicilari_kaydet(varsayilan)
    return varsayilan


# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "users" not in st.session_state: st.session_state.users = kullanicilari_yukle()

gunler_tr = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", "Thursday": "Perşembe",
             "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}

# --- 1. SOL MENÜ: GİRİŞ VE KAYIT YÖNETİMİ ---
st.sidebar.markdown("### 🔐 İdareci Paneli")
giris_tab = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol", "Şifremi Unuttum"], label_visibility="collapsed")

if not st.session_state.logged_in:
    if giris_tab == "Giriş Yap":
        k_adi = st.sidebar.text_input("Kullanıcı Adı")
        sifre = st.sidebar.text_input("Şifre", type="password")
        if st.sidebar.button("Giriş Yap", type="primary", use_container_width=True):
            st.session_state.users = kullanicilari_yukle()
            if k_adi in st.session_state.users and st.session_state.users[k_adi].get("password") == sifre:
                st.session_state.logged_in = True
                st.session_state.current_user = k_adi
                st.success("Giriş başarılı, yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.sidebar.error("Hatalı kullanıcı adı veya şifre!")

    elif giris_tab == "Kayıt Ol":
        with st.sidebar.form("kayit_form"):
            k_ad = st.text_input("Kullanıcı Adı")
            okul = st.text_input("Kurum / Okul İsmi")
            kod = st.text_input("Kurum Kodu (6 haneli MEBBİS)", max_chars=6)
            mudur = st.text_input("Müdür Adı Soyadı")
            mail = st.text_input("E-posta")
            tel = st.text_input("Telefon")
            sifre = st.text_input("Şifre", type="password")
            sifre_tekrar = st.text_input("Şifre Tekrar", type="password")

            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                if not k_ad or not sifre:
                    st.error("Kullanıcı adı ve şifre zorunludur.")
                elif sifre != sifre_tekrar:
                    st.error("Şifreler eşleşmiyor!")
                else:
                    st.session_state.users = kullanicilari_yukle()
                    if k_ad in st.session_state.users:
                        st.error("Bu kullanıcı adı zaten alınmış!")
                    else:
                        st.session_state.users[k_ad] = {
                            "password": sifre, "eposta": mail, "telefon": tel,
                            "okul_adi": okul, "kurum_kodu": kod, "mudur_adi": mudur,
                            "il": "Gaziantep", "ilce": "Şahinbey"
                        }
                        kullanicilari_kaydet(st.session_state.users)
                        st.success("Kayıt başarılı! Lütfen sol menüden giriş yapın.")

    elif giris_tab == "Şifremi Unuttum":
        s_girdi = st.sidebar.text_input("Kullanıcı Adı, E-posta veya Telefon")
        yeni_sifre = st.sidebar.text_input("Yeni Şifre", type="password")
        yeni_sifre_tekrar = st.sidebar.text_input("Yeni Şifre Tekrar", type="password")
        if st.sidebar.button("Şifreyi Yenile", use_container_width=True):
            st.session_state.users = kullanicilari_yukle()
            bulundu = False
            for k, info in st.session_state.users.items():
                if k == s_girdi or info.get("eposta") == s_girdi or info.get("telefon") == s_girdi:
                    if yeni_sifre and yeni_sifre == yeni_sifre_tekrar:
                        st.session_state.users[k]["password"] = yeni_sifre
                        kullanicilari_kaydet(st.session_state.users)
                        st.success("Şifreniz başarıyla yenilendi!")
                        bulundu = True
                        break
                    else:
                        st.error("Şifreler uyuşmuyor.")
                        bulundu = True
                        break
            if not bulundu:
                st.error("Kayıt bulunamadı.")

    st.title("🏫 Nöbetçim - Okul Nöbet ve Görevlendirme Sistemi")
    st.info(
        "👋 Hoş geldiniz! Devam etmek için lütfen sol taraftaki panelden giriş yapın veya hemen ücretsiz kayıt olun.")

    st.markdown("---")
    st.markdown("### 🚀 Nöbetçim Sistemi ile Neler Yapabilirsiniz?")
    st.markdown("""
    Bu sistem okullardaki nöbet ve ders görevlendirme süreçlerini tamamen dijitalleştirmek ve hızlandırmak için tasarlanmıştır. 

    * **📋 Ders Programı Entegrasyonu:** Okulunuza ait ders programı Excel veya PDF dosyasını yükleyerek tüm öğretmenlerin programını dijital ortamda görüntüleyin.
    * **⚡ Otomatik Acil Görevlendirme:** Günlük olarak gelmeyen/izinli öğretmenlerin ders saatlerine, nöbetçi öğretmenler arasından en adil ve otomatik şekilde görevlendirme yapın.
    * **📅 Günlük Nöbetçi Listesi:** Hangi gün kimin hangi katta/yerde nöbetçi olduğunu belirleyin ve bu listeyi günlük olarak tek tıkla çıktı alın.
    * **📄 Tebligat ve Görev Raporlama:** Günlük görevlendirmeleri onaylayarak resmi tebligat ve imza listesi çıktısını (HTML formatında) alın.
    * **🛡️ Muafiyet ve Nöbet Yönetimi:** Öğretmenlerin nöbet veya görev muafiyet durumlarını toplu olarak düzenleyip takip edin.
    * **📊 Toplam Görev Takibi:** Eğitim öğretim yılı boyunca veya aylık bazda kimin kaç kez görev aldığını şeffaf bir şekilde raporlayın.
    * **💾 Günlük Yedekleme ve Kurtarma:** Tüm verilerinizi tek tıkla yedekleyin, olası bir durumda verilerinizi anında geri yükleyin.
    """)
    st.stop()

aktif_kullanici = st.session_state.current_user
user_data = st.session_state.users.get(aktif_kullanici, {})
okul_bilgisi = user_data.get("okul_adi", "Kürşat Tüzmen Ortaokulu")
mudur_bilgisi = user_data.get("mudur_adi", "Erdinç Uçar")
il_bilgisi = user_data.get("il", "Gaziantep")
ilce_bilgisi = user_data.get("ilce", "Şahinbey")

# --- KULLANICIYA ÖZEL DOSYA YOLLARI ---
dosya_adi = f"{aktif_kullanici}_okul_ders_programi.xlsx"
nobet_dosyasi = f"{aktif_kullanici}_nobet_listesi.csv"
gecmis_dosyasi = f"{aktif_kullanici}_assignment_history.csv"
gelmeyen_dosyasi = f"{aktif_kullanici}_gelmeyen_ogretmenler.csv"
muafiyet_dosyasi = f"{aktif_kullanici}_nobet_muafiyetleri.json"
geri_bildirim_dosyasi = "geri_bildirimler.csv"


def gecmisi_kaydet(df):
    if not df.empty and all(col in df.columns for col in ["Tarih", "Gelmeyen Öğretmen", "Ders Saati"]):
        df = df.drop_duplicates(subset=["Tarih", "Gelmeyen Öğretmen", "Ders Saati"], keep="last").reset_index(drop=True)
    df.to_csv(gecmis_dosyasi, index=False)


def gecmisi_yukle():
    if os.path.exists(gecmis_dosyasi):
        try:
            if os.path.getsize(gecmis_dosyasi) > 0:
                df = pd.read_csv(gecmis_dosyasi)
                if not df.empty and all(col in df.columns for col in ["Tarih", "Gelmeyen Öğretmen", "Ders Saati"]):
                    df = df.drop_duplicates(subset=["Tarih", "Gelmeyen Öğretmen", "Ders Saati"],
                                            keep="last").reset_index(drop=True)
                return df
        except Exception:
            pass
    return pd.DataFrame(
        columns=["Tarih", "Gün", "Ders Saati", "Gelmeyen Öğretmen", "Görevlendirilen Öğretmen", "Branş"])


def muafiyetleri_yukle():
    if os.path.exists(muafiyet_dosyasi):
        try:
            if os.path.getsize(muafiyet_dosyasi) > 0:
                with open(muafiyet_dosyasi, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
    return {}


def muafiyetleri_kaydet(muaf_dict):
    with open(muafiyet_dosyasi, "w", encoding="utf-8") as f: json.dump(muaf_dict, f, ensure_ascii=False, indent=4)


def nobetleri_yukle():
    if os.path.exists(nobet_dosyasi):
        try:
            if os.path.getsize(nobet_dosyasi) > 0:
                return pd.read_csv(nobet_dosyasi)
        except Exception:
            pass
    return pd.DataFrame(columns=["Gün", "Nöbet Yeri", "Öğretmen Adı"])


def nobetleri_kaydet(df): df.to_csv(nobet_dosyasi, index=False)


def gelmeyenleri_yukle():
    if os.path.exists(gelmeyen_dosyasi):
        try:
            if os.path.getsize(gelmeyen_dosyasi) > 0:
                df = pd.read_csv(gelmeyen_dosyasi)
                if "Gelmeyen Saatler" not in df.columns: df["Gelmeyen Saatler"] = "1,2,3,4,5,6,7,8"
                if "Mazeret" not in df.columns: df["Mazeret"] = "İzinli"
                if "Onaylandi" not in df.columns: df["Onaylandi"] = False
                if "SadeceNobet" not in df.columns: df["SadeceNobet"] = True
                if "BransOnceligi" not in df.columns: df["BransOnceligi"] = True
                return df
        except Exception:
            pass
    return pd.DataFrame(
        columns=["Tarih", "Gün", "Öğretmen Adı", "Gelmeyen Saatler", "Mazeret", "Onaylandi", "SadeceNobet",
                 "BransOnceligi"])


def gelmeyenleri_kaydet(df): df.to_csv(gelmeyen_dosyasi, index=False)


def geri_bildirimleri_yukle():
    if os.path.exists(geri_bildirim_dosyasi):
        try:
            if os.path.getsize(geri_bildirim_dosyasi) > 0:
                return pd.read_csv(geri_bildirim_dosyasi)
        except Exception:
            pass
    return pd.DataFrame(columns=["Tarih", "Kullanıcı", "Konu", "Mesaj", "Durum"])


def geri_bildirimleri_kaydet(df):
    df.to_csv(geri_bildirim_dosyasi, index=False)


def sablon_olustur():
    if not os.path.exists(dosya_adi):
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        sutunlar = ["Sıra No", "Öğretmen Adı Soyadı", "Branş", "Toplam Ders Saati"]
        for gun in gunler:
            for saat in range(1, 9): sutunlar.append(f"{gun} {saat}. Saat")
        df_sablon = pd.DataFrame([[1, "Ahmet Yılmaz", "Matematik", 0] + [""] * 40], columns=sutunlar)
        df_sablon.to_excel(dosya_adi, index=False)


sablon_olustur()


@st.cache_data
def excel_oku_guvenli(dosya_yolu, mtime):
    try:
        df = pd.read_excel(dosya_yolu, dtype=str)
        sutunlar_str = " ".join([str(c).lower() for c in df.columns])
        if not any(k in sutunlar_str for k in ["öğretmen", "ad soyad", "ad-soyad", "personel"]):
            for i in range(1, 4):
                df_tmp = pd.read_excel(dosya_yolu, header=i, dtype=str)
                tmp_str = " ".join([str(c).lower() for c in df_tmp.columns])
                if any(k in tmp_str for k in ["öğretmen", "ad soyad", "ad-soyad", "personel"]): return df_tmp
        return df
    except Exception:
        return pd.read_excel(dosya_yolu, dtype=str)


def dosya_okuma_yoneticisi(dosya_yolu):
    if os.path.exists(dosya_yolu):
        return excel_oku_guvenli(dosya_yolu, os.path.getmtime(dosya_yolu))
    else:
        sablon_olustur()
        return excel_oku_guvenli(dosya_yolu, os.path.getmtime(dosya_yolu))


def stil_uygula(val):
    s_val = str(val).strip()
    if s_val == "" or s_val.lower() == "boş" or s_val == "nan":
        return "background-color: #f8d7da; color: #842029"
    return "background-color: #d1e7dd; color: #0f5132"


# Session State yüklemeleri
st.session_state.nobet_listesi = nobetleri_yukle()
st.session_state.assignment_history = gecmisi_yukle()
st.session_state.gelmeyen_listesi = gelmeyenleri_yukle()
st.session_state.muafiyet_listesi = muafiyetleri_yukle()
if "geri_bildirim_listesi" not in st.session_state: st.session_state.geri_bildirim_listesi = geri_bildirimleri_yukle()
if "secilen_tarih" not in st.session_state: st.session_state.secilen_tarih = datetime.date.today()
if "sifirlama_onayi" not in st.session_state: st.session_state.sifirlama_onayi = False

# Sidebar Şık Profil Alanı
with st.sidebar:
    st.markdown(f"""
        <div style="padding: 16px; background: #ffffff; border: 1px solid #e1e4e8; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <p style="margin: 0; font-size: 11px; font-weight: 700; color: #57606a; text-transform: uppercase;">Aktif Oturum</p>
            <p style="margin: 4px 0 0 0; font-weight: 700; font-size: 15px; color: #24292f;">👤 {aktif_kullanici}</p>
            <p style="margin: 4px 0 0 0; font-size: 13px; color: #0969da; font-weight: 600;">🏢 {okul_bilgisi}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.success("Oturum kapatıldı.")
        st.rerun()

st.title(f"🏫 {okul_bilgisi} | Nöbetçim")

# --- SEKMELER ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📋 Gelmeyen Öğretmen Ekle",
    "🛡️ Toplu Öğretmen & Nöbet",
    "📅 Günlük Nöbetçi Listesi",
    "📊 Toplam Görevlendirme",
    "📚 Öğretmen Programları",
    "📁 Excel & Veri",
    "👤 Kurum Bilgileri",
    "💾 Yedekleme & Kurtarma",
    "💬 Geri Bildirim"
])

df_ders = dosya_okuma_yoneticisi(dosya_adi)
cols = list(df_ders.columns)
ogrt_col = next((c for c in cols if any(k in str(c).lower() for k in ["öğretmen", "ad soyad", "ad-soyad", "personel"])),
                cols[1] if len(cols) > 1 else cols[0])
brans_col = next((c for c in cols if any(k in str(c).lower() for k in ["branş", "brans", "alan", "ders"])),
                 cols[2] if len(cols) > 2 else cols[0])
ham_ogretmenler = df_ders[ogrt_col].dropna().astype(str).str.strip().tolist() if ogrt_col in df_ders.columns else []

muafiyet_sozlugu = st.session_state.muafiyet_listesi
aktif_nobetci_adaylari = [o for o in ham_ogretmenler if not muafiyet_sozlugu.get(o, {}).get("nobet_tutmuyor", False)]
ogretmenler_listesi = ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"] + ham_ogretmenler
nobetci_secim_listesi = ["Lütfen Öğretmen Seçin..."] + aktif_nobetci_adaylari


def get_assignment_counts():
    counts = {ogrt: 0 for ogrt in ham_ogretmenler}
    if not st.session_state.assignment_history.empty:
        df_hist_unique = st.session_state.assignment_history.drop_duplicates(
            subset=["Tarih", "Gelmeyen Öğretmen", "Ders Saati"], keep="last")
        for _, row in df_hist_unique.iterrows():
            g_ogrt = str(row["Görevlendirilen Öğretmen"]).strip()
            for ogrt in counts:
                if tr_normalize(ogrt) == tr_normalize(g_ogrt):
                    counts[ogrt] += 1
                    break
    return counts


def ders_sutunu_bul(df, gun, saat):
    gun_dict = {"Pazartesi": ["pazartesi", "pzt"], "Salı": ["salı", "sali"], "Çarşamba": ["çarşamba", "carsamba"],
                "Perşembe": ["perşembe", "persembe"], "Cuma": ["cuma"]}
    for col in df.columns:
        c_lower = tr_normalize(str(col))
        if any(g in c_lower for g in gun_dict.get(gun, [gun.lower()])) and str(saat) in c_lower: return col
    return f"{gun} {saat}. Saat"


def ogretmen_satiri_bul(df, ogrt_adi, ogrt_col):
    if ogrt_col not in df.columns: return pd.DataFrame()
    return df[df[ogrt_col].apply(tr_normalize) == tr_normalize(ogrt_adi)]


def ogretmen_gunluk_toplam_ders_sayisi(df_ders, ogrt_satir, secilen_gun):
    if ogrt_satir.empty: return 0
    return sum(1 for s in range(1, 9) if
               str(ogrt_satir[ders_sutunu_bul(df_ders, secilen_gun, s)].values[0]).strip() not in ["", "nan", "Boş"])


def uygun_ogretmenleri_bul(df_ders, secilen_tarih, secilen_gun, saat, g_ogrt, g_brans, oto_brans, sadece_nobetci=True):
    hedef_sutun = ders_sutunu_bul(df_ders, secilen_gun, saat)
    if hedef_sutun not in df_ders.columns: return []
    muaf_dict = st.session_state.muafiyet_listesi

    gunluk_nobetciler = st.session_state.nobet_listesi[st.session_state.nobet_listesi["Gün"] == secilen_gun]
    nobetci_isimleri = [tr_normalize(x) for x in gunluk_nobetciler["Öğretmen Adı"].tolist() if
                        not muaf_dict.get(x, {}).get("nobet_muaf", False)]

    tarihli_gelmeyenler = st.session_state.gelmeyen_listesi[
        st.session_state.gelmeyen_listesi["Tarih"].astype(str).str[:10] == str(secilen_tarih)[:10]]
    gelmeyen_isimleri_clean = set(tarihli_gelmeyenler["Öğretmen Adı"].apply(tr_normalize))

    gelmeyen_saatleri_map = {
        tr_normalize(r["Öğretmen Adı"]): [int(x) for x in str(r.get("Gelmeyen Saatler", "1,2,3,4,5,6,7,8")).split(",")
                                          if x.strip().isdigit()] for _, r in tarihli_gelmeyenler.iterrows()}

    zaten_gorevli_ayni_saatte = set(st.session_state.assignment_history[
                                        (st.session_state.assignment_history["Tarih"].astype(str).str[:10] == str(
                                            secilen_tarih)[:10]) &
                                        (st.session_state.assignment_history["Ders Saati"].astype(
                                            str).str.strip().str.lower() == f"{saat}. saat")
                                        ]["Görevlendirilen Öğretmen"].apply(tr_normalize))

    onceki_saat = saat - 1
    zaten_gorevli_onceki_saatte = set()
    if onceki_saat >= 1:
        zaten_gorevli_onceki_saatte = set(st.session_state.assignment_history[
                                              (st.session_state.assignment_history["Tarih"].astype(str).str[:10] == str(
                                                  secilen_tarih)[:10]) &
                                              (st.session_state.assignment_history["Ders Saati"].astype(
                                                  str).str.strip().str.lower() == f"{onceki_saat}. saat")
                                              ]["Görevlendirilen Öğretmen"].apply(tr_normalize))

    counts = get_assignment_counts()
    musait_nobetciler, musait_digerleri = [], []

    for _, row in df_ders.iterrows():
        ogrt = str(row[ogrt_col])
        ogrt_clean = tr_normalize(ogrt)
        brns = str(row[brans_col]) if brans_col in df_ders.columns else ""

        if ogrt_clean in gelmeyen_isimleri_clean: continue
        if muaf_dict.get(ogrt, {}).get("nobet_tutmuyor", False): continue

        if (ogrt_clean == tr_normalize(g_ogrt) or
                muaf_dict.get(ogrt, {}).get("gorev_muaf", False) or
                saat in gelmeyen_saatleri_map.get(ogrt_clean, []) or
                ogrt_clean in zaten_gorevli_ayni_saatte or
                ogrt_clean in zaten_gorevli_onceki_saatte):
            continue

        ogrt_tum_satir = ogretmen_satiri_bul(df_ders, ogrt, ogrt_col)
        if ogrt_tum_satir.empty: continue

        hucre_val = str(row[hedef_sutun]).strip()
        if hucre_val != "" and hucre_val.lower() != "boş" and hucre_val != "nan": continue

        is_nobetci = 1 if ogrt_clean in nobetci_isimleri else 0

        if sadece_nobetci and is_nobetci == 0: continue

        if is_nobetci == 0 and not sadece_nobetci:
            toplam_ders = ogretmen_gunluk_toplam_ders_sayisi(df_ders, ogrt_tum_satir, secilen_gun)
            if toplam_ders < 1: continue

            dolu_saatler = [s for s in range(1, 9) if
                            str(ogrt_tum_satir[ders_sutunu_bul(df_ders, secilen_gun, s)].values[0]).strip() not in ["",
                                                                                                                    "nan",
                                                                                                                    "Boş"]]
            if dolu_saatler:
                ilk_ders_saati = min(dolu_saatler)
                son_ders_saati = max(dolu_saatler)

                if saat <= 4 and ilk_ders_saati > 4: continue
                if saat >= 6 and son_ders_saati < 6: continue

        is_same_branch = 1 if (oto_brans and g_brans and brns and tr_normalize(brns) == tr_normalize(g_brans)) else 0

        aday = {"ogretmen": ogrt, "brans": brns, "is_same_branch": is_same_branch, "count": counts.get(ogrt, 0),
                "is_nobetci": is_nobetci}
        if is_nobetci == 1:
            musait_nobetciler.append(aday)
        else:
            musait_digerleri.append(aday)

    for lst in [musait_nobetciler, musait_digerleri]:
        lst.sort(key=lambda x: (-x["is_same_branch"], x["count"]))

    if not sadece_nobetci: return musait_nobetciler + musait_digerleri
    return musait_nobetciler


def otomatik_gorevlendirmeleri_guncelle(tarih, gun):
    tarih_str = str(tarih)[:10]
    gelenler_df = st.session_state.gelmeyen_listesi[
        st.session_state.gelmeyen_listesi["Tarih"].astype(str).str[:10] == tarih_str]
    gelmeyen_isimleri_clean = set(gelenler_df["Öğretmen Adı"].apply(tr_normalize))

    hist = st.session_state.assignment_history
    if not hist.empty:
        hist = hist[~hist["Görevlendirilen Öğretmen"].apply(tr_normalize).isin(gelmeyen_isimleri_clean)]

    if hist.empty:
        hist = pd.DataFrame(
            columns=["Tarih", "Gün", "Ders Saati", "Gelmeyen Öğretmen", "Görevlendirilen Öğretmen", "Branş"])

    muaf_dict = st.session_state.muafiyet_listesi
    gunluk_nobetciler = st.session_state.nobet_listesi[st.session_state.nobet_listesi["Gün"] == gun]
    nobetci_isimleri_clean = [tr_normalize(x) for x in gunluk_nobetciler["Öğretmen Adı"].tolist() if
                              not muaf_dict.get(x, {}).get("nobet_muaf", False)]

    diger_gunler_hist = hist[hist["Tarih"].astype(str).str[:10] != tarih_str] if not hist.empty else pd.DataFrame(
        columns=hist.columns)
    bugunku_mevcut_hist = hist[hist["Tarih"].astype(str).str[:10] == tarih_str] if not hist.empty else pd.DataFrame(
        columns=hist.columns)

    yeni_atama_listesi = []

    for _, grow in gelenler_df.iterrows():
        g_ogrt = grow["Öğretmen Adı"]
        g_saatler = [int(x) for x in str(grow.get("Gelmeyen Saatler", "1,2,3,4,5,6,7,8")).split(",") if
                     x.strip().isdigit()]

        gelen_row = ogretmen_satiri_bul(df_ders, g_ogrt, ogrt_col)
        g_brans = str(gelen_row[brans_col].values[0]) if not gelen_row.empty and brans_col in gelen_row.columns else ""

        sadece_nobet = bool(grow.get("SadeceNobet", True))
        oto_brans = bool(grow.get("BransOnceligi", True))

        for saat in g_saatler:
            hedef_sutun = ders_sutunu_bul(df_ders, gun, saat)
            if not gelen_row.empty and hedef_sutun in gelen_row.columns and str(
                    gelen_row[hedef_sutun].values[0]).strip() not in ["", "nan", "Boş"]:

                eski_atama_satiri = bugunku_mevcut_hist[
                    (bugunku_mevcut_hist["Gelmeyen Öğretmen"].apply(tr_normalize) == tr_normalize(g_ogrt)) &
                    (bugunku_mevcut_hist["Ders Saati"].astype(str).str.strip().str.lower() == f"{saat}. saat")
                    ]

                if not eski_atama_satiri.empty:
                    atanan_kisi = str(eski_atama_satiri["Görevlendirilen Öğretmen"].values[0])
                    atanan_kisi_clean = tr_normalize(atanan_kisi)

                    if atanan_kisi_clean in gelmeyen_isimleri_clean:
                        pass
                    elif sadece_nobet and atanan_kisi_clean not in nobetci_isimleri_clean:
                        continue
                    else:
                        yeni_atama_listesi.append(eski_atama_satiri.iloc[0].to_dict())
                        continue

                musaitler = uygun_ogretmenleri_bul(df_ders, tarih, gun, saat, g_ogrt, g_brans, oto_brans,
                                                   sadece_nobetci=sadece_nobet)
                if musaitler:
                    atama = musaitler[0]
                    yeni_atama_listesi.append({
                        "Tarih": tarih_str, "Gün": gun, "Ders Saati": f"{saat}. Saat",
                        "Gelmeyen Öğretmen": g_ogrt, "Görevlendirilen Öğretmen": atama["ogretmen"],
                        "Branş": atama["brans"]
                    })

    if yeni_atama_listesi:
        yeni_df = pd.DataFrame(yeni_atama_listesi)
        st.session_state.assignment_history = pd.concat([diger_gunler_hist, yeni_df], ignore_index=True)
    else:
        st.session_state.assignment_history = diger_gunler_hist

    gecmisi_kaydet(st.session_state.assignment_history)


# --- 1. SEKME: GELMEYEN ÖĞRETMEN EKLE VE GÖREVLENDİRME ---
with tab1:
    st.subheader("📋 Gelmeyen Öğretmenler ve Otomatik Görevlendirme")
    col_t1, col_t2 = st.columns([2, 3])
    with col_t1:
        t1_tarih = st.date_input("İşlem Yapılacak Tarih", value=st.session_state.secilen_tarih)
        st.session_state.secilen_tarih = t1_tarih
        secilen_gun = gunler_tr.get(t1_tarih.strftime("%A"), "Pazartesi")
    with col_t2:
        st.markdown(f"### Tarih: {t1_tarih.strftime('%d.%m.%Y')} ({secilen_gun})")

    st.markdown("---")
    col_sol, col_sag = st.columns([5, 6], gap="large")

    with col_sol:
        st.markdown("#### ➕ Yeni Gelmeyen Öğretmen Ekle")
        secilen_anlik_ogretmen = st.selectbox("Gelmeyen / İzinli Öğretmen Seç", options=ogretmenler_listesi,
                                              key="t1_anlik_ogrt_secim")

        if secilen_anlik_ogretmen not in ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"]:
            st.markdown(f"##### 👁️ Canlı Program Önizlemesi: {secilen_anlik_ogretmen} ({secilen_gun})")
            onizleme_row = ogretmen_satiri_bul(df_ders, secilen_anlik_ogretmen, ogrt_col)
            if not onizleme_row.empty:
                onizleme_veri = []
                for s in range(1, 9):
                    sut_adi = ders_sutunu_bul(df_ders, secilen_gun, s)
                    d_val = str(
                        onizleme_row[sut_adi].values[0]).strip() if sut_adi in onizleme_row.columns and not pd.isna(
                        onizleme_row[sut_adi].values[0]) else ""
                    durum = f"🟢 Dolu ({d_val})" if (d_val != "" and d_val != "Boş") else "🔴 Boş"
                    onizleme_veri.append({"Ders Saati": f"{s}. Saat", "Program Durumu": durum})
                st.dataframe(pd.DataFrame(onizleme_veri), use_container_width=True, hide_index=True)

        form_baslik = f"➕ Yeni Gelmeyen Öğretmen Ekle: {secilen_anlik_ogretmen}" if secilen_anlik_ogretmen not in [
            "Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"] else "➕ Yeni Gelmeyen Öğretmen Ekle"

        with st.form("gelmeyen_ekle_form"):
            st.markdown(f"##### {form_baslik}")
            secilen_mazeret = st.selectbox("Mazeret", ["Raporlu", "Görevli izinli", "İzinli", "Sevkli"])
            secilen_gelmeyen_saatler = st.multiselect("Gelmeyen Ders Saatleri", options=list(range(1, 9)),
                                                      default=list(range(1, 9)))
            form_brans_onceligi = st.checkbox("🔍 Branş Önceliği Uygula", value=True)

            if st.form_submit_button("🚀 Kaydet ve Otomatik Görevlendir", type="primary", use_container_width=True):
                if secilen_anlik_ogretmen in ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"]:
                    st.warning("Lütfen geçerli bir öğretmen seçin.")
                elif not secilen_gelmeyen_saatler:
                    st.warning("Lütfen saat seçin.")
                else:
                    mevcut = st.session_state.gelmeyen_listesi
                    mask_ayni = (mevcut["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]) & (
                                mevcut["Öğretmen Adı"].apply(tr_normalize) == tr_normalize(secilen_anlik_ogretmen))

                    if mask_ayni.any():
                        st.warning("⚠️ Bu öğretmen bugün zaten gelmeyenler listesine eklenmiş!")
                    else:
                        saatler_str = ",".join(map(str, secilen_gelmeyen_saatler))
                        yeni = pd.DataFrame({
                            "Tarih": [str(t1_tarih)], "Gün": [secilen_gun], "Öğretmen Adı": [secilen_anlik_ogretmen],
                            "Gelmeyen Saatler": [saatler_str], "Mazeret": [secilen_mazeret], "Onaylandi": [False],
                            "SadeceNobet": [True], "BransOnceligi": [form_brans_onceligi]
                        })
                        mevcut = pd.concat([mevcut, yeni], ignore_index=True)
                        st.session_state.gelmeyen_listesi = mevcut
                        gelmeyenleri_kaydet(mevcut)

                        otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                        st.success("✅ Kayıt başarıyla eklendi ve otomatik görevlendirildi!")
                        st.rerun()

    with col_sag:
        st.markdown("#### 👤 Kayıtlı Gelmeyenler ve Manuel Düzenleme")
        ogun_gelmeyenler_df = st.session_state.gelmeyen_listesi[
            st.session_state.gelmeyen_listesi["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]].copy()

        if not ogun_gelmeyenler_df.empty:
            for orig_idx, row_g in ogun_gelmeyenler_df.iterrows():
                g_ogrt, g_mazeret, g_onayli = row_g["Öğretmen Adı"], row_g.get("Mazeret", "İzinli"), bool(
                    row_g.get("Onaylandi", False))
                g_sadece_nobet = bool(row_g.get("SadeceNobet", True))

                with st.expander(f"🔴 {g_ogrt} ({g_mazeret}) {'🔒 (Onaylandı)' if g_onayli else '🔓 (Beklemede)'}",
                                 expanded=True):

                    yeni_sadece_nobet = st.checkbox(
                        "⭐ Sadece Nöbetçi Öğretmenlerden Seç (Nöbet Dışı Bırak)",
                        value=g_sadece_nobet,
                        key=f"dinamik_nobet_cb_{orig_idx}",
                        disabled=g_onayli,
                        help="Onaylı kayıtlar üzerinde değişiklik yapılamaz."
                    )

                    if not g_onayli and (yeni_s_nobet := (yeni_sadece_nobet != g_sadece_nobet)):
                        st.session_state.gelmeyen_listesi.loc[orig_idx, "SadeceNobet"] = yeni_sadece_nobet
                        gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                        otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                        st.success("✅ Tercih güncellendi ve görevlendirmeler yeniden hesaplandı!")
                        st.rerun()

                    st.markdown("---")

                    mevcut_gorevler = st.session_state.assignment_history[
                        (st.session_state.assignment_history["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]) &
                        (st.session_state.assignment_history["Gelmeyen Öğretmen"].apply(tr_normalize) == tr_normalize(
                            g_ogrt))
                        ]

                    muaf_dict = st.session_state.muafiyet_listesi
                    gunluk_nobetciler = st.session_state.nobet_listesi[
                        st.session_state.nobet_listesi["Gün"] == secilen_gun]
                    nobetci_isimleri_clean = [tr_normalize(x) for x in gunluk_nobetciler["Öğretmen Adı"].tolist() if
                                              not muaf_dict.get(x, {}).get("nobet_muaf", False)]

                    for saat in range(1, 9):
                        sut = ders_sutunu_bul(df_ders, secilen_gun, saat)
                        match_atama = mevcut_gorevler[
                            mevcut_gorevler["Ders Saati"].astype(str).str.strip().str.lower() == f"{saat}. saat"]

                        atanan_kisi = "-"
                        if not match_atama.empty:
                            ham_atanan = str(match_atama["Görevlendirilen Öğretmen"].values[0])
                            if tr_normalize(ham_atanan) in nobetci_isimleri_clean:
                                atanan_kisi = f"⭐ {ham_atanan}"
                            else:
                                atanan_kisi = ham_atanan

                        gelen_satir = ogretmen_satiri_bul(df_ders, g_ogrt, ogrt_col)
                        ders_durumu_str = ""
                        is_dersi_var = False

                        if not gelen_satir.empty and sut in gelen_satir.columns:
                            hucre_val = str(gelen_satir[sut].values[0]).strip()
                            if hucre_val != "" and hucre_val.lower() != "boş" and hucre_val != "nan":
                                is_dersi_var = True
                                ders_durumu_str = hucre_val

                        if is_dersi_var:
                            st.markdown(
                                f"**{saat}. Saat** | 🟢 Kendi Dersi (`{ders_durumu_str}`) | **Mevcut Atanan:** `{atanan_kisi}`")

                            if g_onayli:
                                st.info(f"🔒 Bu görevlendirme onaylandığı için {saat}. saatte değişiklik yapılamaz.")
                            else:
                                col_degis1, col_degis2 = st.columns([3, 1])
                                with col_degis1:
                                    musait_adaylar = uygun_ogretmenleri_bul(df_ders, t1_tarih, secilen_gun, saat,
                                                                            g_ogrt, "", False, sadece_nobetci=False)

                                    # Akıllı Başlık: Atama yapılmışsa "Görevliyi Değiştir", yapılmamışsa "Atama Yapılmadı / Görevli Ekle"
                                    if not match_atama.empty:
                                        ilk_secenek_metni = "Görevliyi Değiştir / Seçim Yap"
                                    else:
                                        ilk_secenek_metni = "Atama Yapılmadı / Görevli Ekle"

                                    secenekler = [ilk_secenek_metni]
                                    aday_map = {}
                                    for aday in musait_adaylar:
                                        ogr_adi = aday["ogretmen"]
                                        is_nob = tr_normalize(ogr_adi) in nobetci_isimleri_clean
                                        etiket = f"⭐ [NÖBETÇİ] {ogr_adi} ({aday['brans']})" if is_nob else f"{ogr_adi} ({aday['brans']})"
                                        secenekler.append(etiket)
                                        aday_map[etiket] = ogr_adi

                                    secilen_manuel = st.selectbox(f"Manuel İşlem ({saat}. Saat)", options=secenekler,
                                                                  key=f"manuel_sec_{orig_idx}_{saat}")

                                    if secilen_manuel != ilk_secenek_metni:
                                        secilen_ogretmen_adi = aday_map[secilen_manuel]
                                        ogr_satir_secilen = ogretmen_satiri_bul(df_ders, secilen_ogretmen_adi, ogrt_col)

                                        secilen_brans_sutun = next((c for c in ogr_satir_secilen.columns if any(
                                            k in str(c).lower() for k in ["branş", "brans", "alan", "ders"])), None)
                                        s_brans = str(ogr_satir_secilen[secilen_brans_sutun].values[
                                                          0]) if not ogr_satir_secilen.empty and secilen_brans_sutun and not pd.isna(
                                            ogr_satir_secilen[secilen_brans_sutun].values[0]) else ""

                                        hist = st.session_state.assignment_history
                                        tarih_str = str(t1_tarih)[:10]

                                        mask_satir = (hist["Tarih"].astype(str).str[:10] == tarih_str) & \
                                                     (hist["Gelmeyen Öğretmen"].apply(tr_normalize) == tr_normalize(
                                                         g_ogrt)) & \
                                                     (hist["Ders Saati"].astype(
                                                         str).str.strip().str.lower() == f"{saat}. saat")

                                        if mask_satir.any():
                                            st.session_state.assignment_history.loc[
                                                mask_satir, "Görevlendirilen Öğretmen"] = secilen_ogretmen_adi
                                            st.session_state.assignment_history.loc[mask_satir, "Branş"] = s_brans
                                        else:
                                            yeni_satir = pd.DataFrame({
                                                "Tarih": [tarih_str], "Gün": [secilen_gun],
                                                "Ders Saati": [f"{saat}. Saat"],
                                                "Gelmeyen Öğretmen": [g_ogrt],
                                                "Görevlendirilen Öğretmen": [secilen_ogretmen_adi], "Branş": [s_brans]
                                            })
                                            st.session_state.assignment_history = pd.concat([hist, yeni_satir],
                                                                                            ignore_index=True)

                                        gecmisi_kaydet(st.session_state.assignment_history)
                                        st.success(
                                            f"✅ {saat}. saat için görevli {secilen_ogretmen_adi} olarak güncellendi ve kaydedildi!")
                                        st.rerun()

                                with col_degis2:
                                    if not match_atama.empty and st.button("🗑️ Sil", key=f"tek_sil_{orig_idx}_{saat}",
                                                                           use_container_width=True):
                                        idx_to_drop = match_atama.index
                                        st.session_state.assignment_history = st.session_state.assignment_history.drop(
                                            idx_to_drop).reset_index(drop=True)
                                        gecmisi_kaydet(st.session_state.assignment_history)
                                        st.success("✅ Görev başarıyla silindi ve kaydedildi!")
                                        st.rerun()
                        else:
                            st.markdown(f"**{saat}. Saat** | 🔴 Boş Saat")

                        st.markdown("---")

                    c_onay, c_sil = st.columns(2)
                    with c_onay:
                        if not g_onayli and st.button("✅ Onayla", key=f"onay_{orig_idx}", use_container_width=True):
                            st.session_state.gelmeyen_listesi.loc[orig_idx, "Onaylandi"] = True
                            gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                            st.success("✅ Görevlendirme onaylandı ve kaydedildi!")
                            st.rerun()
                        elif g_onayli and st.button("🔓 Onayı Kaldır (Düzenlemeyi Aç)", key=f"kaldir_{orig_idx}",
                                                    use_container_width=True):
                            st.session_state.gelmeyen_listesi.loc[orig_idx, "Onaylandi"] = False
                            gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                            st.success("✅ Onay kaldırıldı, artık düzenleme yapabilirsiniz!")
                            st.rerun()
                    with c_sil:
                        if not g_onayli:
                            if st.button("🗑️ Kaydı Sil", key=f"sil_{orig_idx}", use_container_width=True):
                                st.session_state.gelmeyen_listesi = st.session_state.gelmeyen_listesi.drop(
                                    orig_idx).reset_index(drop=True)
                                gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                                otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                                st.success("✅ Kayıt silindi ve güncellendi!")
                                st.rerun()
                        else:
                            st.markdown(
                                "<p style='text-align:center; color:gray; font-size:12px;'>Onaylıyken silinemez</p>",
                                unsafe_allow_html=True)
        else:
            st.info("Bu tarih için kayıtlı gelmeyen öğretmen yok.")

    # TEBLİGAT RAPORU
    st.markdown("---")
    st.markdown(f"### 📄 Tebligat Raporu ve Çıktı Ekranı ({t1_tarih.strftime('%d.%m.%Y')})")

    if not ogun_gelmeyenler_df.empty:
        tum_onayli = ogun_gelmeyenler_df["Onaylandi"].all()
        bugun_gelmeyen_isimleri = [tr_normalize(x) for x in ogun_gelmeyenler_df["Öğretmen Adı"].tolist()]
        tarihli_gorevler = st.session_state.assignment_history[
            (st.session_state.assignment_history["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]) &
            (st.session_state.assignment_history["Gelmeyen Öğretmen"].apply(tr_normalize).isin(bugun_gelmeyen_isimleri))
            ] if bugun_gelmeyen_isimleri else pd.DataFrame()

        if not tarihli_gorevler.empty:
            table_rows = "".join([
                                     f"<tr><td style='text-align: center;'>{i + 1}</td><td style='text-align: center;'>{r['Ders Saati']}</td><td>{r['Gelmeyen Öğretmen']}</td><td>{r['Görevlendirilen Öğretmen']} ({r.get('Branş', '')})</td><td></td></tr>"
                                     for i, r in tarihli_gorevler.iterrows()])
            if tum_onayli:
                html_print = f"<html><head><meta charset='UTF-8'></head><body><h3 style='text-align:center;'>{il_bilgisi.upper()} VALİLİĞİ<br>{ilce_bilgisi.upper()} İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ<br>{okul_bilgisi.upper()} MÜDÜRLÜĞÜ</h3><table border='1' width='100%' style='border-collapse:collapse;' cellpadding='8'><thead><tr><th>S.No</th><th>Ders Saati</th><th>Gelmeyen Öğretmen</th><th>Görevlendirilen Öğretmen</th><th>İmza</th></tr></thead><tbody>{table_rows}</tbody></table><br><p style='float:right;'><strong>{mudur_bilgisi}</strong><br>Okul Müdürü</p></body></html>"
                st.download_button("📄 Tebligat Çıktısını İndir (HTML)", data=html_print,
                                   file_name=f"Tebligat_{t1_tarih}.html", mime="text/html")
            else:
                st.warning("🔒 Çıktı alabilmek için günün tüm görevlendirmelerini onaylayın.")

        if not ogun_gelmeyenler_df.empty and not ogun_gelmeyenler_df["Onaylandi"].all():
            if st.button("✅ Tümünü Toplu Olarak Onayla", type="primary"):
                st.session_state.gelmeyen_listesi.loc[ogun_gelmeyenler_df.index, "Onaylandi"] = True
                gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                st.success("✅ Tüm görevlendirmeler toplu olarak onaylandı ve kaydedildi!")
                st.rerun()

# --- 2. SEKME: TOPLU ÖĞRETMEN & NÖBET YÖNETİMİ ---
with tab2:
    st.subheader("🛡️ Toplu Öğretmen, Nöbet ve Muafiyet Yönetimi")
    if ham_ogretmenler:
        muaf_dict = st.session_state.muafiyet_listesi
        tablo_verisi = []
        for ogrt in ham_ogretmenler:
            ogrt_satir = ogretmen_satiri_bul(df_ders, ogrt, ogrt_col)
            brns = str(ogrt_satir[brans_col].values[
                           0]).strip() if not ogrt_satir.empty and brans_col in ogrt_satir.columns else "-"
            muaf_mu = muaf_dict.get(ogrt, {}).get("nobet_tutmuyor", False)
            tablo_verisi.append({"Öğretmen Adı": ogrt, "Branş": brns, "Nöbet Tutabilir mi?": not muaf_mu})

        df_muaf_tablo = pd.DataFrame(tablo_verisi)
        with st.form("toplu_muafiyet_form"):
            edited_df = st.data_editor(df_muaf_tablo,
                                       column_config={"Öğretmen Adı": st.column_config.TextColumn(disabled=True),
                                                      "Branş": st.column_config.TextColumn(disabled=True),
                                                      "Nöbet Tutabilir mi?": st.column_config.CheckboxColumn()},
                                       hide_index=True, use_container_width=True)
            if st.form_submit_button("💾 Değişiklikleri Kaydet", type="primary", use_container_width=True):
                for _, row in edited_df.iterrows():
                    ogr_adi, yeni_durum = row["Öğretmen Adı"], row["Nöbet Tutabilir mi?"]
                    if ogr_adi not in st.session_state.muafiyet_listesi: st.session_state.muafiyet_listesi[ogr_adi] = {}
                    st.session_state.muafiyet_listesi[ogr_adi]["nobet_tutmuyor"] = not yeni_durum
                muafiyetleri_kaydet(st.session_state.muafiyet_listesi)
                st.success("✅ Kaydedildi!")
                st.rerun()
    else:
        st.warning("⚠️ Öğretmen bulunamadı.")

# --- 3. SEKME: GÜNLÜK NÖBETÇİ LİSTESİ ---
with tab3:
    st.subheader("📅 Günlük Nöbetçi Listesi ve Çıktı Ekranı")
    n_tarih = st.date_input("Nöbet Günü Seçin", value=st.session_state.secilen_tarih, key="nobet_tarih_secim")
    n_gun = gunler_tr.get(n_tarih.strftime("%A"), "Pazartesi")
    st.markdown(f"### Seçilen Gün: **{n_gun}** ({n_tarih.strftime('%d.%m.%Y')})")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.markdown("#### ➕ Nöbetçi Öğretmen Ekle")
        eklenecek_nobetci = st.selectbox("Öğretmen Seç", options=nobetci_secim_listesi, key="nobet_ekle_ogrt")
        nobet_yeri = st.text_input("Nöbet Yeri / Kat", value="Zemin Kat")
        if st.button("Nöbetçi Ekle", use_container_width=True):
            if eklenecek_nobetci != "Lütfen Öğretmen Seçin...":
                mevcut_nobetciler = st.session_state.nobet_listesi
                yeni_n = pd.DataFrame({"Gün": [n_gun], "Nöbet Yeri": [nobet_yeri], "Öğretmen Adı": [eklenecek_nobetci]})
                st.session_state.nobet_listesi = pd.concat([mevcut_nobetciler, yeni_n], ignore_index=True)
                nobetleri_kaydet(st.session_state.nobet_listesi)
                st.success("✅ Eklendi!")
                st.rerun()
    with col_n2:
        st.markdown(f"#### 📋 {n_gun} Günü Nöbetçiler")
        gunluk_nobetciler = st.session_state.nobet_listesi[st.session_state.nobet_listesi["Gün"] == n_gun]
        if not gunluk_nobetciler.empty:
            for idx, r_n in gunluk_nobetciler.iterrows():
                if st.button(f"🗑️ Sil: {r_n['Öğretmen Adı']} ({r_n['Nöbet Yeri']})", key=f"sil_nobet_{idx}"):
                    st.session_state.nobet_listesi = st.session_state.nobet_listesi.drop(idx).reset_index(drop=True)
                    nobetleri_kaydet(st.session_state.nobet_listesi)
                    st.rerun()

# --- 4. SEKME: TOPLAM GÖREVLENDİRME ---
with tab4:
    st.subheader("📊 Toplam Görevlendirme Sayıları")
    counts = get_assignment_counts()
    if counts:
        st.dataframe(
            pd.DataFrame(list(counts.items()), columns=["Öğretmen Adı", "Toplam Görev"]).sort_values(by="Toplam Görev",
                                                                                                     ascending=False),
            use_container_width=True)

# --- 5. SEKME: ÖĞRETMEN DERS PROGRAMLARI ---
with tab5:
    st.subheader("📚 Öğretmen Ders Programları")
    secilen_goruntu_ogrt = st.selectbox("Öğretmen Seçin", options=ogretmenler_listesi, key="goruntu_ogrt_secim")
    if secilen_goruntu_ogrt not in ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"]:
        ogrt_satir_df = ogretmen_satiri_bul(df_ders, secilen_goruntu_ogrt, ogrt_col)
        st.dataframe(ogrt_satir_df.style.map(stil_uygula), use_container_width=True, hide_index=True)

# --- 6. SEKME: EXCEL & VERİ YÖNETİMİ (PDF DESTEKLİ) ---
with tab6:
    st.subheader("📁 Ders Programı Yükleme (Excel veya PDF)")
    st.write("Okulunuza ait ders programı dosyasını ister Excel (.xlsx) ister MEB/e-Okul çıkışlı PDF formatında yükleyebilirsiniz.")

    yuklenen_dosya = st.file_uploader("Dosya Seç (Excel veya PDF)", type=["xlsx", "xls", "pdf"])
    if yuklenen_dosya:
        dosya_uzantisi = yuklenen_dosya.name.split(".")[-1].lower()
        if dosya_uzantisi in ["xlsx", "xls"]:
            with open(dosya_adi, "wb") as f: f.write(yuklenen_dosya.getbuffer())
            st.success("✅ Excel ders programı başarıyla yüklendi!")
            st.rerun()
        elif dosya_uzantisi == "pdf":
            try:
                with pdfplumber.open(yuklenen_dosya) as pdf:
                    tum_satirlar = []
                    for sayfa in pdf.pages:
                        tablo = sayfa.extract_table()
                        if tablo:
                            tum_satirlar.extend(tablo)
                if tum_satirlar:
                    # Sütun ve veri uyuşmazlığını önlemek için dinamik kolon oluşturma
                    max_len = max(len(satir) for satir in tum_satirlar)
                    basliklar = [f"Kolon_{i}" for i in range(max_len)]

                    temiz_satirlar = []
                    for satir in tum_satirlar:
                        while len(satir) < max_len:
                            satir.append("")
                        temiz_satirlar.append(satir)

                    df_pdf = pd.DataFrame(temiz_satirlar[1:], columns=basliklar)
                    df_pdf.to_excel(dosya_adi, index=False)
                    st.success("✅ PDF ders programı başarıyla okundu ve Excel formatına dönüştürüldü!")
                    st.rerun()
                else:
                    st.error("❌ PDF içinde okunabilir bir tablo bulunamadı.")
            except Exception as e:
                st.error(f"❌ PDF okunurken hata oluştu: {e}")

# --- 7. SEKME: KURUM BİLGİLERİ ---
with tab7:
    st.subheader("👤 Kurum ve İdareci Bilgileri")
    y_okul = st.text_input("Okul Adı", value=user_data.get("okul_adi", ""))
    y_mudur = st.text_input("Müdür Adı Soyadı", value=user_data.get("mudur_adi", ""))
    if st.button("Bilgileri Güncelle", type="primary", use_container_width=True):
        st.session_state.users[aktif_kullanici].update({"okul_adi": y_okul, "mudur_adi": y_mudur})
        kullanicilari_kaydet(st.session_state.users)
        st.success("✅ Güncellendi!")
        st.rerun()

# --- 8. SEKME: YEDEKLEME & KURTARMA ---
with tab8:
    st.subheader("💾 Yedekleme ve Kurtarma")
    ders_prog_records = pd.read_excel(dosya_adi, dtype=str).to_dict(orient="records") if os.path.exists(
        dosya_adi) else []
    yedek_paketi = {
        "aktif_kullanici": aktif_kullanici, "tarih": str(datetime.datetime.now()),
        "muafiyetler": muafiyetleri_yukle(), "gelmeyenler": gelmeyenleri_yukle().to_dict(orient="records"),
        "nobetler": nobetleri_yukle().to_dict(orient="records"), "gecmis": gecmisi_yukle().to_dict(orient="records"),
        "ders_programi": ders_prog_records
    }
    st.download_button("💾 Tüm Verileri Yedekle (JSON)", data=json.dumps(yedek_paketi, ensure_ascii=False, indent=4),
                       file_name=f"nobetcim_yedek_{aktif_kullanici}.json", mime="application/json",
                       use_container_width=True)

# --- 9. SEKME: GERİ BİLDİRİM ---
with tab9:
    st.subheader("💬 Geri Bildirim")
    mesaj = st.text_area("Görüş ve önerileriniz...")
    if st.button("Gönder", type="primary"):
        if mesaj.strip():
            st.success("✅ Teşekkürler!")