import datetime
from io import BytesIO
import json
import os
import pandas as pd
import streamlit as st

# Sayfa ayarları
st.set_page_config(
    page_title="Nöbetçim - Okul Nöbet ve Görevlendirme Sistemi",
    page_icon="📋",
    layout="wide",
)

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
    varsayilan = {
        "ediperdinc": {
            "password": "1234567890", "il": "Gaziantep", "ilce": "Şahinbey",
            "okul_adi": "Kürşat Tüzmen Ortaokulu", "mudur_adi": "Erdinç Uçar", "kurum_kodu": "123456"
        }
    }
    if os.path.exists(kullanici_dosyasi):
        try:
            with open(kullanici_dosyasi, "r", encoding="utf-8") as f:
                icerik = f.read().strip()
                if icerik:
                    veri = json.loads(icerik)
                    if isinstance(veri, dict) and veri: return veri
        except Exception:
            pass
    kullanicilari_kaydet(varsayilan)
    return varsayilan


# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "users" not in st.session_state: st.session_state.users = kullanicilari_yukle()

gunler_tr = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", "Thursday": "Perşembe",
             "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}

# --- 1. SOL MENÜ: GİRİŞ VE KAYIT YÖNETİMİ ---
st.sidebar.title("🔐 İdareci Paneli")
giris_tab = st.sidebar.radio("İşlem Seçin", ["Giriş Yap", "Kayıt Ol", "Şifremi Unuttum"])

if not st.session_state.logged_in:
    if giris_tab == "Giriş Yap":
        k_adi = st.sidebar.text_input("Kullanıcı Adı")
        sifre = st.sidebar.text_input("Şifre", type="password")
        if st.sidebar.button("Giriş Yap", type="primary"):
            if k_adi in st.session_state.users and st.session_state.users[k_adi].get("password") == sifre:
                st.session_state.logged_in = True
                st.session_state.current_user = k_adi
                st.rerun()
            else:
                st.sidebar.error("Hatalı kullanıcı adı veya şifre!")

    elif giris_tab == "Kayıt Ol":
        with st.sidebar.form("kayit_form"):
            k_ad = st.text_input("Kullanıcı Adı")
            okul = st.text_input("Kurum / Okul İsmi")
            kod = st.text_input("Kurum Kodu (6 haneli MEBBİS kodu)", max_chars=6)
            mudur = st.text_input("Müdür Adı Soyadı (İsteğe bağlı)")
            mail = st.text_input("E-posta")
            tel = st.text_input("Telefon")
            sifre = st.text_input("Şifre", type="password")
            sifre_tekrar = st.text_input("Şifre Tekrar", type="password")

            if st.form_submit_button("Kayıt Ol"):
                if not k_ad or not sifre:
                    st.error("Kullanıcı adı ve şifre zorunludur.")
                elif sifre != sifre_tekrar:
                    st.error("Şifreler eşleşmiyor!")
                elif k_ad in st.session_state.users:
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
        s_girdi = st.sidebar.text_input("Kullanıcı Adı, E-posta veya Telefon Numarası")
        yeni_sifre = st.sidebar.text_input("Yeni Şifre", type="password")
        yeni_sifre_tekrar = st.sidebar.text_input("Yeni Şifre Tekrar", type="password")
        if st.sidebar.button("Şifreyi Yenile"):
            bulundu = False
            for k, info in st.session_state.users.items():
                if k == s_girdi or info.get("eposta") == s_girdi or info.get("telefon") == s_girdi:
                    if yeni_sifre and yeni_sifre == yeni_sifre_tekrar:
                        st.session_state.users[k]["password"] = yeni_sifre
                        kullanicilari_kaydet(st.session_state.users)
                        st.success("Şifreniz başarıyla yenilendi! Giriş yapabilirsiniz.")
                        bulundu = True
                        break
                    else:
                        st.error("Şifreler uyuşmuyor veya boş.")
                        bulundu = True
                        break
            if not bulundu:
                st.error("Girilen bilgilere ait kayıt bulunamadı.")

    # --- GİRİŞ YAPILMAMIŞSA GÖSTERİLECEK TANITIM EKRANI ---
    st.title("🏫 Nöbetçim - Okul Nöbet ve Görevlendirme Sistemi")
    st.warning("⚠️ Lütfen sol taraftan giriş yapın veya yeni hesap oluşturun.")

    st.markdown("---")
    st.markdown("### 🚀 Nöbetçim Sistemi ile Neler Yapabilirsiniz?")
    st.info("""
    Bu sistem okullardaki nöbet ve ders görevlendirme süreçlerini tamamen dijitalleştirmek ve hızlandırmak için tasarlanmıştır. **Sol taraftaki menüyü kullanarak giriş yapabilir veya hemen ücretsiz kayıt olabilirsiniz.**

    * **📋 Ders Programı Entegrasyonu:** Okulunuza ait ders programı Excel dosyasını yükleyerek tüm öğretmenlerin programını dijital ortamda görüntüleme.
    * **⚡ Otomatik Acil Görevlendirme:** Günlük olarak gelmeyen/izinli öğretmenlerin ders saatlerine, nöbetçi öğretmenler arasından en adil ve otomatik şekilde görevlendirme yapma.
    * **📅 Günlük Nöbetçi Listesi:** Hangi gün kimin hangi katta/yerde nöbetçi olduğunu belirleme ve bu listeyi günlük olarak tek tıkla çıktı alma.
    * **📄 Tebligat ve Görev Raporlama:** Günlük görevlendirmeleri onaylayarak resmi tebligat ve imza listesi çıktısını (HTML formatında) alma.
    * **🛡️ Muafiyet ve Nöbet Yönetimi:** Öğretmenlerin nöbet veya görev muafiyet durumlarını toplu olarak düzenleyip takip etme.
    * **📊 Toplam Görev Takibi:** Eğitim öğretim yılı boyunca veya aylık bazda kimin kaç kez görev aldığını şeffaf bir şekilde raporlama.
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
        df = pd.read_csv(gecmis_dosyasi)
        if not df.empty and all(col in df.columns for col in ["Tarih", "Gelmeyen Öğretmen", "Ders Saati"]):
            df = df.drop_duplicates(subset=["Tarih", "Gelmeyen Öğretmen", "Ders Saati"], keep="last").reset_index(
                drop=True)
        return df
    return pd.DataFrame(
        columns=["Tarih", "Gün", "Ders Saati", "Gelmeyen Öğretmen", "Görevlendirilen Öğretmen", "Branş"])


def muafiyetleri_yukle():
    if os.path.exists(muafiyet_dosyasi):
        with open(muafiyet_dosyasi, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def muafiyetleri_kaydet(muaf_dict):
    with open(muafiyet_dosyasi, "w", encoding="utf-8") as f: json.dump(muaf_dict, f, ensure_ascii=False, indent=4)


def nobetleri_yukle():
    if os.path.exists(nobet_dosyasi): return pd.read_csv(nobet_dosyasi)
    return pd.DataFrame(columns=["Gün", "Nöbet Yeri", "Öğretmen Adı"])


def nobetleri_kaydet(df): df.to_csv(nobet_dosyasi, index=False)


def gelmeyenleri_yukle():
    if os.path.exists(gelmeyen_dosyasi):
        df = pd.read_csv(gelmeyen_dosyasi)
        if "Gelmeyen Saatler" not in df.columns: df["Gelmeyen Saatler"] = "1,2,3,4,5,6,7,8"
        if "Mazeret" not in df.columns: df["Mazeret"] = "İzinli"
        if "Onaylandi" not in df.columns: df["Onaylandi"] = False
        return df
    return pd.DataFrame(columns=["Tarih", "Gün", "Öğretmen Adı", "Gelmeyen Saatler", "Mazeret", "Onaylandi"])


def gelmeyenleri_kaydet(df): df.to_csv(gelmeyen_dosyasi, index=False)


def geri_bildirimleri_yukle():
    if os.path.exists(geri_bildirim_dosyasi):
        return pd.read_csv(geri_bildirim_dosyasi)
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

st.sidebar.success(f"Hoş geldiniz, {aktif_kullanici}!\n🏢 {okul_bilgisi}")
if st.sidebar.button("Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

st.title(f"🏫 {okul_bilgisi} | Nöbetçim")

# --- SEKMELER (MENÜLER) ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 Ders Programı & Görevlendir",
    "🛡️ Toplu Öğretmen & Nöbet Yönetimi",
    "📅 Günlük Nöbetçi Listesi",
    "📊 Toplam Görevlendirme",
    "📚 Öğretmen Ders Programları",
    "📁 Excel & Veri Yönetimi",
    "👤 Kurum Bilgileri",
    "💬 Geri Bildirim & Hata Bildir"
])

df_ders = dosya_okuma_yoneticisi(dosya_adi)
cols = list(df_ders.columns)
ogrt_col = next((c for c in cols if any(k in str(c).lower() for k in ["öğretmen", "ad soyad", "ad-soyad", "personel"])),
                cols[1] if len(cols) > 1 else cols[0])
brans_col = next((c for c in cols if any(k in str(c).lower() for k in ["branş", "brans", "alan", "ders"])),
                 cols[2] if len(cols) > 2 else cols[0])
ham_ogretmenler = df_ders[ogrt_col].dropna().astype(str).str.strip().tolist() if ogrt_col in df_ders.columns else []
ogretmenler_listesi = ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"] + ham_ogretmenler


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
        if is_nobetci == 0 and ogretmen_gunluk_toplam_ders_sayisi(df_ders, ogrt_tum_satir, secilen_gun) < 1: continue

        is_same_branch = 1 if (oto_brans and g_brans and brns and tr_normalize(brns) == tr_normalize(g_brans)) else 0

        aday = {"ogretmen": ogrt, "brans": brns, "is_same_branch": is_same_branch, "count": counts.get(ogrt, 0),
                "is_nobetci": is_nobetci}
        if is_nobetci == 1:
            musait_nobetciler.append(aday)
        else:
            musait_digerleri.append(aday)

    for lst in [musait_nobetciler, musait_digerleri]:
        lst.sort(key=lambda x: (-x["is_same_branch"], x["count"]))

    if musait_nobetciler:
        return musait_nobetciler
    else:
        return musait_digerleri if not sadece_nobetci else []


def otomatik_gorevlendirmeleri_guncelle(tarih, gun):
    tarih_str = str(tarih)[:10]
    gelenler_df = st.session_state.gelmeyen_listesi[
        st.session_state.gelmeyen_listesi["Tarih"].astype(str).str[:10] == tarih_str]

    hist = st.session_state.assignment_history
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

        orig_idx = grow.name
        sadece_nobet = not st.session_state.get(f"disi_cb_{orig_idx}", False)
        oto_brans = st.session_state.get(f"brans_cb_{orig_idx}", True)

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

                    if sadece_nobet and atanan_kisi_clean not in nobetci_isimleri_clean:
                        continue

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


# --- 1. SEKME: GÖREVLENDİRME VE CANLI ÖNİZLEME ---
with tab1:
    st.subheader("📋 Gelmeyen Öğretmenler, Canlı Önizleme ve Otomatik Görevlendirme")
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

        with st.form("gelmeyen_ekle_form"):
            secilen_mazeret = st.selectbox("Mazeret", ["Raporlu", "Görevli izinli", "İzinli", "Sevkli"])
            secilen_gelmeyen_saatler = st.multiselect("Gelmeyen Ders Saatleri", options=list(range(1, 9)),
                                                      default=list(range(1, 9)))
            form_brans_onceligi = st.checkbox("🔍 Branş Önceliği Uygula", value=True, key="form_brans_cb")

            if st.form_submit_button("🚀 Kaydet ve Otomatik Görevlendir", type="primary"):
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
                        yeni = pd.DataFrame(
                            {"Tarih": [str(t1_tarih)], "Gün": [secilen_gun], "Öğretmen Adı": [secilen_anlik_ogretmen],
                             "Gelmeyen Saatler": [saatler_str], "Mazeret": [secilen_mazeret], "Onaylandi": [False]})
                        mevcut = pd.concat([mevcut, yeni], ignore_index=True)
                        st.session_state.gelmeyen_listesi = mevcut
                        gelmeyenleri_kaydet(mevcut)

                        yeni_idx = mevcut.index[-1]
                        st.session_state[f"brans_cb_{yeni_idx}"] = form_brans_onceligi

                        otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                        st.success("Başarıyla kaydedildi ve otomatik görevlendirildi!")
                        st.rerun()

    with col_sag:
        st.markdown("#### 👤 Kayıtlı Gelmeyenler ve Onay Ekranı")
        ogun_gelmeyenler_df = st.session_state.gelmeyen_listesi[
            st.session_state.gelmeyen_listesi["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]].copy()

        if not ogun_gelmeyenler_df.empty:
            for orig_idx, row_g in ogun_gelmeyenler_df.iterrows():
                g_ogrt, g_mazeret, g_onayli = row_g["Öğretmen Adı"], row_g.get("Mazeret", "İzinli"), bool(
                    row_g.get("Onaylandi", False))
                g_saatler = [int(x) for x in str(row_g.get("Gelmeyen Saatler", "1,2,3,4,5,6,7,8")).split(",") if
                             x.strip().isdigit()]

                with st.expander(f"🔴 {g_ogrt} ({g_mazeret}) {'🔒 (Onaylandı)' if g_onayli else '🔓 (Beklemede)'}",
                                 expanded=True):
                    mevcut_gorevler = st.session_state.assignment_history[
                        (st.session_state.assignment_history["Tarih"].astype(str).str[:10] == str(t1_tarih)[:10]) &
                        (st.session_state.assignment_history["Gelmeyen Öğretmen"].apply(tr_normalize) == tr_normalize(
                            g_ogrt))
                        ]

                    for saat in range(1, 9):
                        sut = ders_sutunu_bul(df_ders, secilen_gun, saat)
                        match_atama = mevcut_gorevler[
                            mevcut_gorevler["Ders Saati"].astype(str).str.strip().str.lower() == f"{saat}. saat"]
                        atanan_kisi = match_atama["Görevlendirilen Öğretmen"].values[
                            0] if not match_atama.empty else "-"

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
                                f"🟢 **{saat}.S:** Kendi Dersi (`{ders_durumu_str}`) 👉 **Atanan:** `{atanan_kisi}`")
                        else:
                            st.markdown(f"🔴 **{saat}.S:** Boş Saat 👉 **Atanan:** `{atanan_kisi}`")

                    st.markdown("---")
                    cb_key = f"disi_cb_{orig_idx}"
                    yeni_cb = st.checkbox("🌐 Nöbetçi Dışı Öğretmen Görevlendirilebilsin",
                                          value=st.session_state.get(cb_key, False), key=cb_key)

                    brans_cb_key = f"brans_cb_{orig_idx}"
                    yeni_brans_cb = st.checkbox("🔍 Branş Önceliği Uygula",
                                                value=st.session_state.get(brans_cb_key, True), key=brans_cb_key)

                    if (yeni_cb != st.session_state.get(f"old_cb_{orig_idx}", False)) or (
                            yeni_brans_cb != st.session_state.get(f"old_brans_cb_{orig_idx}", True)):
                        st.session_state[f"old_cb_{orig_idx}"] = yeni_cb
                        st.session_state[f"old_brans_cb_{orig_idx}"] = yeni_brans_cb
                        otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                        st.rerun()

                    c_onay, c_sil = st.columns(2)
                    with c_onay:
                        if not g_onayli and st.button("✅ Onayla", key=f"onay_{orig_idx}"):
                            st.session_state.gelmeyen_listesi.loc[orig_idx, "Onaylandi"] = True
                            gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                            st.success("Onaylandı!")
                            st.rerun()
                        elif g_onayli and st.button("🔓 Onayı Kaldır", key=f"kaldir_{orig_idx}"):
                            st.session_state.gelmeyen_listesi.loc[orig_idx, "Onaylandi"] = False
                            gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                            st.rerun()
                    with c_sil:
                        if st.button("🗑️ Sil", key=f"sil_{orig_idx}"):
                            st.session_state.gelmeyen_listesi = st.session_state.gelmeyen_listesi.drop(
                                orig_idx).reset_index(drop=True)
                            gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                            otomatik_gorevlendirmeleri_guncelle(t1_tarih, secilen_gun)
                            st.success("Kayıt silindi.")
                            st.rerun()
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
                html_print = f"<html><body><h3 style='text-align:center;'>{il_bilgisi.upper()} VALİLİĞİ<br>{ilce_bilgisi.upper()} İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ<br>{okul_bilgisi.upper()} MÜDÜRLÜĞÜ</h3><table border='1' width='100%' style='border-collapse:collapse;'><thead><tr><th>S.No</th><th>Ders Saati</th><th>Gelmeyen Öğretmen</th><th>Görevlendirilen Öğretmen</th><th>İmza</th></tr></thead><tbody>{table_rows}</tbody></table><br><p style='float:right;'><strong>{mudur_bilgisi}</strong><br>Okul Müdürü</p></body></html>"
                st.download_button("📄 Tebligat Çıktı Dosyasını İndir (HTML)", data=html_print,
                                   file_name=f"Tebligat_{t1_tarih}.html", mime="text/html")
            else:
                st.warning(
                    "🔒 Çıktı alabilmek için günün tüm gelmeyen öğretmen görevlendirmelerini onaylayın veya en alttaki toplu onayla butonunu kullanın.")

        if not ogun_gelmeyenler_df.empty and not ogun_gelmeyenler_df["Onaylandi"].all():
            if st.button("✅ Tüm Görevlendirmeleri Toplu Olarak Onayla"):
                st.session_state.gelmeyen_listesi.loc[ogun_gelmeyenler_df.index, "Onaylandi"] = True
                gelmeyenleri_kaydet(st.session_state.gelmeyen_listesi)
                st.success("Tüm görevlendirmeler onaylandı!")
                st.rerun()

# --- 2. SEKME: TOPLU ÖĞRETMEN & NÖBET YÖNETİMİ ---
with tab2:
    st.subheader("🛡️ Toplu Öğretmen, Nöbet ve Muafiyet Yönetimi")
    st.write(
        "Okulunuzdaki tüm öğretmenlerin nöbet muafiyet durumlarını aşağıdaki tablodan toplu olarak görebilir ve tek tıkla güncelleyebilirsiniz.")

    if ham_ogretmenler:
        muaf_dict = st.session_state.muafiyet_listesi
        tablo_verisi = []
        for ogrt in ham_ogretmenler:
            ogrt_satir = ogretmen_satiri_bul(df_ders, ogrt, ogrt_col)
            brns = str(ogrt_satir[brans_col].values[
                           0]).strip() if not ogrt_satir.empty and brans_col in ogrt_satir.columns else "-"
            muaf_mu = muaf_dict.get(ogrt, {}).get("nobet_tutmuyor", False)
            nobet_tutabilir = not muaf_mu

            tablo_verisi.append({
                "Öğretmen Adı": ogrt,
                "Branş": brns,
                "Nöbet Tutabilir mi?": nobet_tutabilir
            })

        df_muaf_tablo = pd.DataFrame(tablo_verisi)

        with st.form("toplu_muafiyet_form"):
            st.markdown("##### 📝 Öğretmen Nöbet Durum Listesi")
            st.info(
                "💡 Tablodaki **'Nöbet Tutabilir mi?'** sütunundaki kutucukları işaretleyerek veya kaldırarak nöbet durumlarını düzenleyebilir, ardından alttaki butonla kaydedebilirsiniz.")

            edited_df = st.data_editor(
                df_muaf_tablo,
                column_config={
                    "Öğretmen Adı": st.column_config.TextColumn("Öğretmen Adı", disabled=True),
                    "Branş": st.column_config.TextColumn("Branş", disabled=True),
                    "Nöbet Tutabilir mi?": st.column_config.CheckboxColumn("Nöbet Tutabilir mi?",
                                                                           help="İşaretli ise nöbet tutar, işaretsiz ise nöbet muafıdır.")
                },
                hide_index=True,
                use_container_width=True,
                key="muafiyet_data_editor"
            )

            if st.form_submit_button("💾 Değişiklikleri Kaydet", type="primary"):
                for _, row in edited_df.iterrows():
                    ogr_adi = row["Öğretmen Adı"]
                    yeni_durum = row["Nöbet Tutabilir mi?"]

                    if ogr_adi not in st.session_state.muafiyet_listesi:
                        st.session_state.muafiyet_listesi[ogr_adi] = {}

                    st.session_state.muafiyet_listesi[ogr_adi]["nobet_tutmuyor"] = not yeni_durum

                muafiyetleri_kaydet(st.session_state.muafiyet_listesi)
                st.success("✅ Tüm öğretmenlerin nöbet muafiyet durumları başarıyla güncellendi ve kaydedildi!")
                st.rerun()
    else:
        st.warning("⚠️ Henüz ders programı yüklenmemiş veya öğretmen bulunamadı.")

# --- 3. SEKME: GÜNLÜK NÖBETÇİ LİSTESİ ---
with tab3:
    st.subheader("📅 Günlük Nöbetçi Listesi ve Çıktı Ekranı")
    n_tarih = st.date_input("Nöbet Günü Seçin", value=st.session_state.secilen_tarih, key="nobet_tarih_secim")
    n_gun = gunler_tr.get(n_tarih.strftime("%A"), "Pazartesi")
    st.markdown(f"### Seçilen Gün: **{n_gun}** ({n_tarih.strftime('%d.%m.%Y')})")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.markdown("#### ➕ Nöbetçi Öğretmen Ekle")
        eklenecek_nobetci = st.selectbox("Öğretmen Seç", options=ogretmenler_listesi, key="nobet_ekle_ogrt")
        nobet_yeri = st.text_input("Nöbet Yeri / Kat", value="Zemin Kat")

        if st.button("Nöbetçi Ekle"):
            if eklenecek_nobetci in ["Lütfen Öğretmen Seçin...", "Tüm Öğretmenler"]:
                st.warning("Geçerli bir öğretmen seçin.")
            else:
                mevcut_nobetciler = st.session_state.nobet_listesi
                zaten_var = not mevcut_nobetciler[
                    (mevcut_nobetciler["Gün"] == n_gun) &
                    (mevcut_nobetciler["Öğretmen Adı"].apply(tr_normalize) == tr_normalize(eklenecek_nobetci))
                    ].empty

                if zaten_var:
                    st.warning(f"⚠️ {eklenecek_nobetci} adlı öğretmen {n_gun} günü zaten nöbetçi olarak eklenmiş!")
                else:
                    yeni_n = pd.DataFrame(
                        {"Gün": [n_gun], "Nöbet Yeri": [nobet_yeri], "Öğretmen Adı": [eklenecek_nobetci]})
                    st.session_state.nobet_listesi = pd.concat([mevcut_nobetciler, yeni_n], ignore_index=True)
                    nobetleri_kaydet(st.session_state.nobet_listesi)
                    st.success("Nöbetçi başarıyla eklendi!")
                    st.rerun()

    with col_n2:
        st.markdown(f"#### 📋 {n_gun} Günü Nöbetçi Listesi ve Canlı Önizleme")
        gunluk_nobetciler = st.session_state.nobet_listesi[st.session_state.nobet_listesi["Gün"] == n_gun]
        if not gunluk_nobetciler.empty:
            for idx, r_n in gunluk_nobetciler.iterrows():
                n_ogr = r_n["Öğretmen Adı"]
                n_yer = r_n["Nöbet Yeri"]
                with st.expander(f"📌 {n_ogr} ({n_yer})"):
                    ogr_row = ogretmen_satiri_bul(df_ders, n_ogr, ogrt_col)
                    if not ogr_row.empty:
                        onizleme_veri = []
                        for s in range(1, 9):
                            sut_adi = ders_sutunu_bul(df_ders, n_gun, s)
                            d_val = str(
                                ogr_row[sut_adi].values[0]).strip() if sut_adi in ogr_row.columns and not pd.isna(
                                ogr_row[sut_adi].values[0]) else ""
                            durum = f"🟢 Dolu ({d_val})" if (d_val != "" and d_val != "Boş") else "🔴 Boş"
                            onizleme_veri.append({"Ders Saati": f"{s}. Saat", "Program Durumu": durum})
                        st.dataframe(pd.DataFrame(onizleme_veri), use_container_width=True, hide_index=True)
                    if st.button("🗑️ Nöbeti Sil", key=f"sil_nobet_{idx}"):
                        st.session_state.nobet_listesi = st.session_state.nobet_listesi.drop(idx).reset_index(drop=True)
                        nobetleri_kaydet(st.session_state.nobet_listesi)
                        st.success("Nöbet silindi.")
                        st.rerun()
        else:
            st.info("Bu gün için eklenmiş nöbetçi yok.")

    # GÜNLÜK NÖBETÇİ LİSTESİ HTML ÇIKTISI
    st.markdown("---")
    st.markdown(f"### 🖨️ Günlük Nöbetçi Listesi Yazdırma ve Çıktı Ekranı ({n_tarih.strftime('%d.%m.%Y')})")
    if not gunluk_nobetciler.empty:
        n_table_rows = "".join([
                                   f"<tr><td style='text-align: center;'>{i + 1}</td><td>{r['Öğretmen Adı']}</td><td>{r['Nöbet Yeri']}</td><td></td></tr>"
                                   for i, r in gunluk_nobetciler.reset_index(drop=True).iterrows()])
        n_html_print = f"<html><body><h3 style='text-align:center;'>{il_bilgisi.upper()} VALİLİĞİ<br>{ilce_bilgisi.upper()} İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ<br>{okul_bilgisi.upper()} MÜDÜRLÜĞÜ<br><br>{n_tarih.strftime('%d.%m.%Y')} ({n_gun}) GÜNLÜK NÖBETÇİ ÖĞRETMENLER LİSTESİ</h3><table border='1' width='100%' style='border-collapse:collapse; margin-top:20px; font-size:14px;' cellpadding='8'><thead><tr><th>S.No</th><th>Öğretmen Adı Soyadı</th><th>Nöbet Yeri / Kat</th><th>İmza</th></tr></thead><tbody>{n_table_rows}</tbody></table><br><br><p style='float:right;'><strong>{mudur_bilgisi}</strong><br>Okul Müdürü</p></body></html>"
        st.download_button("📄 Günlük Nöbetçi Listesi Çıktısını İndir (HTML)", data=n_html_print,
                           file_name=f"Nobetci_Listesi_{n_tarih}.html", mime="text/html")
    else:
        st.info("Çıktı alabilmek için bu güne ait nöbetçi öğretmen ekleyin.")

# --- 4. SEKME: TOPLAM GÖREVLENDİRME ---
with tab4:
    st.subheader("📊 Toplam Görevlendirme Sayıları ve Raporlama")
    secim_modu = st.radio("Raporlama Türü", ["Tümü (Eğitim Öğretim Yılı)", "Ay Bazlı Filtreleme"], horizontal=True)

    hist_df = st.session_state.assignment_history
    if secim_modu == "Ay Bazlı Filtreleme" and not hist_df.empty:
        hist_df["Ay"] = pd.to_datetime(hist_df["Tarih"]).dt.strftime("%Y-%m")
        secilen_ay = st.selectbox("Ay Seçin", options=sorted(hist_df["Ay"].unique().tolist()))
        hist_df = hist_df[hist_df["Ay"] == secilen_ay]

    counts = get_assignment_counts()
    if counts:
        df_counts = pd.DataFrame(list(counts.items()), columns=["Öğretmen Adı", "Toplam Görev"]).sort_values(
            by="Toplam Görev", ascending=False)
        st.dataframe(df_counts, use_container_width=True)

        st.markdown("---")
        if not st.session_state.sifirlama_onayi:
            if st.button("🔄 Görevlendirme Geçmişini Sıfırla"):
                st.session_state.sifirlama_onayi = True
                st.rerun()
        else:
            st.warning("⚠️ **DİKKAT:** Tüm görevlendirme geçmişi ve sayıları sıfırlanacaktır. Bu işlem geri alınamaz!")
            col_onay1, col_onay2 = st.columns(2)
            with col_onay1:
                if st.button("Evet, Kesinlikle Sıfırla", type="primary"):
                    st.session_state.assignment_history = pd.DataFrame(
                        columns=["Tarih", "Gün", "Ders Saati", "Gelmeyen Öğretmen", "Görevlendirilen Öğretmen",
                                 "Branş"])
                    gecmisi_kaydet(st.session_state.assignment_history)
                    st.session_state.sifirlama_onayi = False
                    st.success("Tüm görevlendirme geçmişi başarıyla sıfırlandı!")
                    st.rerun()
            with col_onay2:
                if st.button("Vazgeç / İptal Et"):
                    st.session_state.sifirlama_onayi = False
                    st.rerun()
    else:
        st.info("Henüz gerçekleştirilmiş bir görevlendirme kaydı bulunmuyor.")

# --- 5. SEKME: ÖĞRETMEN DERS PROGRAMLARI VE MANÜEL DÜZENLEME ---
with tab5:
    st.subheader("📚 Öğretmen Ders Programları, Gün Seçimi ve Manuel Düzenleme")
    st.write(
        "İstediğiniz öğretmeni ve günü seçerek programını inceleyebilir, hücreleri doğrudan düzenleyebilir ve branşını güncelleyebilirsiniz.")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        secilen_goruntu_ogrt = st.selectbox("Öğretmen Seçin", options=ogretmenler_listesi, key="goruntu_ogrt_secim")
    with col_g2:
        secilen_goruntu_gun = st.selectbox("Gün Seçin", options=["Tüm Günler"] + list(gunler_tr.values()),
                                           key="goruntu_gun_secim")

    if secilen_goruntu_ogrt == "Tüm Öğretmenler":
        st.dataframe(df_ders.style.map(stil_uygula), use_container_width=True)
    elif secilen_goruntu_ogrt != "Lütfen Öğretmen Seçin...":
        ogrt_satir_df = ogretmen_satiri_bul(df_ders, secilen_goruntu_ogrt, ogrt_col)
        if not ogrt_satir_df.empty:
            idx_orig = ogrt_satir_df.index[0]
            mevcut_brans = str(ogrt_satir_df[brans_col].values[0]) if brans_col in ogrt_satir_df.columns else ""

            st.markdown(f"##### 👁️ Program Önizlemesi (Renkli)")
            if secilen_goruntu_gun == "Tüm Günler":
                gosterilecek_sutunlar = [c for c in df_ders.columns if any(
                    g in tr_normalize(c) for g in ["saat", "pazartesi", "salı", "çarşamba", "perşembe", "cuma"])]
            else:
                gosterilecek_sutunlar = [ders_sutunu_bul(df_ders, secilen_goruntu_gun, s) for s in range(1, 9)]
                gosterilecek_sutunlar = [c for c in gosterilecek_sutunlar if c in df_ders.columns]

            onizleme_df = ogrt_satir_df[
                [ogrt_col, brans_col] + gosterilecek_sutunlar].copy() if brans_col in ogrt_satir_df.columns else \
            ogrt_satir_df[[ogrt_col] + gosterilecek_sutunlar].copy()

            cols_seen_onizleme = set()
            new_cols_onizleme = []
            for c in onizleme_df.columns:
                col_name = str(c)
                if col_name in cols_seen_onizleme:
                    i = 1
                    while f"{col_name}_{i}" in cols_seen_onizleme:
                        i += 1
                    col_name = f"{col_name}_{i}"
                cols_seen_onizleme.add(col_name)
                new_cols_onizleme.append(col_name)
            onizleme_df.columns = new_cols_onizleme

            st.dataframe(onizleme_df.style.map(stil_uygula), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown(f"##### ✍️ Manuel Düzenleme Paneli: {secilen_goruntu_ogrt}")
            yeni_brans_input = st.text_input("Öğretmen Branşı", value=mevcut_brans, key=f"brans_input_{idx_orig}")

            D_cols_to_edit = [c for c in gosterilecek_sutunlar if c in ogrt_satir_df.columns]
            alt_df = ogrt_satir_df[D_cols_to_edit].copy()

            cols_seen = set()
            new_cols = []
            for c in alt_df.columns:
                col_name = str(c)
                if col_name in cols_seen:
                    i = 1
                    while f"{col_name}_{i}" in cols_seen:
                        i += 1
                    col_name = f"{col_name}_{i}"
                cols_seen.add(col_name)
                new_cols.append(col_name)
            alt_df.columns = new_cols

            st.info(
                "💡 Aşağıdaki tablo üzerinden yalnızca ders saatlerini değiştirebilir, yukarıdaki kutudan da branşınızı güncelleyip kaydedebilirsiniz.")
            edited_ogrt_df = st.data_editor(alt_df, hide_index=True, use_container_width=True,
                                            key=f"editor_ogrt_{idx_orig}")

            if st.button("💾 Değişiklikleri ve Branşı Kaydet", type="primary"):
                if brans_col in df_ders.columns:
                    df_ders.loc[idx_orig, brans_col] = yeni_brans_input

                for orig_col, edited_col in zip(D_cols_to_edit, alt_df.columns):
                    if edited_col in edited_ogrt_df.columns:
                        yeni_val = str(edited_ogrt_df[edited_col].values[0])
                        df_ders.loc[idx_orig, orig_col] = yeni_val

                df_ders.to_excel(dosya_adi, index=False)
                st.success("✅ Öğretmen ders programı ve branş bilgisi başarıyla güncellendi!")
                st.rerun()
    else:
        st.info("Lütfen yukarıdan bir öğretmen seçin.")

# --- 6. SEKME: EXCEL & VERİ YÖNETİMİ ---
with tab6:
    st.subheader("📁 Excel Ders Programı Yükleme ve Şablon")
    st.write(
        "Okulunuza ait ders programı Excel dosyasını yükleyebilir veya branş sütununu içeren güncel şablonu indirebilirsiniz.")

    with open(dosya_adi, "rb") as f:
        st.download_button("📥 Güncel Excel Şablonunu İndir (Branş Sütunlu)", data=f,
                           file_name="okul_ders_programi.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    yuklenen = st.file_uploader("Yeni Excel Dosyası Yükle", type=["xlsx", "xls"])
    if yuklenen:
        with open(dosya_adi, "wb") as f: f.write(yuklenen.getbuffer())
        st.success("Dosya başarıyla yüklendi! Lütfen sayfayı yenileyin.")

# --- 7. SEKME: KURUM BİLGİLERİ ---
with tab7:
    st.subheader("👤 Kurum ve İdareci Bilgileri")
    y_okul = st.text_input("Okul Adı", value=user_data.get("okul_adi", ""))
    y_mudur = st.text_input("Müdür Adı Soyadı", value=user_data.get("mudur_adi", ""))
    y_ilce = st.text_input("İlçe Adı", value=user_data.get("ilce", ""))
    y_il = st.text_input("İl Adı", value=user_data.get("il", ""))

    if st.button("Bilgileri Güncelle"):
        st.session_state.users[aktif_kullanici].update(
            {"okul_adi": y_okul, "mudur_adi": y_mudur, "ilce": y_ilce, "il": y_il})
        kullanicilari_kaydet(st.session_state.users)
        st.success("Kurum bilgileri güncellendi!")
        st.rerun()

# --- 8. SEKME: GERİ BİLDİRİM & HATA BİLDİR ---
with tab8:
    st.subheader("💬 Geri Bildirim, Hata ve Veri Düzeltme Talebi")
    st.write(
        "Sistemde karşılaştığınız hataları, eksik verileri veya eklenmesini istediğiniz özellikleri doğrudan iletebilirsiniz.")

    with st.form("geri_bildirim_form"):
        konu_secimi = st.selectbox("Bildirim Konusu", ["Ders Programı / Veri Hatası", "Nöbet Dağıtım Hatası / İsteği",
                                                       "Arayüz / Tasarım Önerisi", "Diğer"])
        mesaj_detayi = st.text_area("Hata Açıklaması veya Eklenmesini / Düzeltilmesini İstediğiniz Veriler",
                                    placeholder="Örn: Ahmet Yılmaz'ın Çarşamba günü 3. ve 4. saati boş görünmesine rağmen atama yapılırken hata oluştu. Düzeltilmesini rica ederim.")

        if st.form_submit_button("🚀 Geri Bildirimi Gönder", type="primary"):
            if not mesaj_detayi.strip():
                st.warning("Lütfen bildirim detayını yazın.")
            else:
                yeni_bildirim = pd.DataFrame({
                    "Tarih": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "Kullanıcı": [aktif_kullanici],
                    "Konu": [konu_secimi],
                    "Mesaj": [mesaj_detayi],
                    "Durum": ["Beklemede"]
                })

                st.session_state.geri_bildirim_listesi = pd.concat(
                    [st.session_state.geri_bildirim_listesi, yeni_bildirim], ignore_index=True)
                geri_bildirimleri_kaydet(st.session_state.geri_bildirim_listesi)

                st.success("🎉 Geri bildiriminiz başarıyla iletildi! İlginiz için teşekkür ederiz.")
                st.rerun()

    # Sadece ana yönetici (ediperdinc) tüm geri bildirim listesini ve raporu görebilir!
    if aktif_kullanici == "ediperdinc":
        st.markdown("---")
        st.markdown("#### 📥 Yönetici Paneli: İletilen Tüm Geri Bildirimler ve Talepler")
        if not st.session_state.geri_bildirim_listesi.empty:
            st.dataframe(st.session_state.geri_bildirim_listesi, use_container_width=True, hide_index=True)

            with open(geri_bildirim_dosyasi, "rb") as f:
                st.download_button("📥 Geri Bildirim Raporunu İndir (CSV)", data=f, file_name="geri_bildirimler.csv",
                                   mime="text/html")
        else:
            st.info("Henüz iletilen bir geri bildirim bulunmuyor.")