import yfinance as yf
import pandas as pd
import requests
import os

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

# WT_CROSS_LB [LazyBear] (10, 21, 60, 53) Birebir Hesaplama
def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()       # Yeşil Çizgi
    wt2 = wt1.rolling(window=4).mean()               # Kırmızı Çizgi
    df['WT1'] = wt1
    df['WT2'] = wt2
    return df

def check_signals(symbol="^NDX", name="NAS100 (Günlük)", interval="1d"):
    df = yf.download(symbol, period="6mo", interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = calculate_wavetrend(df)
    
    wt1_prev, wt2_prev = float(df['WT1'].iloc[-2]), float(df['WT2'].iloc[-2])
    wt1_curr, wt2_curr = float(df['WT1'].iloc[-1]), float(df['WT2'].iloc[-1])
    price = float(df['Close'].iloc[-1])

    # 1. ASIL AL SİNYALİ: Yeşil çizgi Kırmızıyı YUKARI kesti (Yeşil Nokta Yandı)
    if wt1_prev <= wt2_prev and wt1_curr > wt2_curr:
        if wt1_prev <= -50 or wt1_curr <= -50:
            msg = (f"🟢 *{name} - GÜÇLÜ AL SİNYALİ (YEŞİL NOKTA YANDI!)*\n\n"
                   f"✅ *Durum:* Aşırı satım bölgesinde yukarı kesişim gerçekleşti!\n"
                   f"💵 *Fiyat:* {price:.1f}\n"
                   f"📊 *WT1 (Yeşil):* {wt1_curr:.1f} | *WT2 (Kırmızı):* {wt2_curr:.1f}")
        else:
            msg = (f"🟢 *{name} - WAVETREND YUKARI KESİŞİM (AL)*\n\n"
                   f"📈 *Durum:* Yeşil çizgi Kırmızıyı yukarı kesti (Ara bölge)\n"
                   f"💵 *Fiyat:* {price:.1f}\n"
                   f"📊 *WT1 (Yeşil):* {wt1_curr:.1f} | *WT2 (Kırmızı):* {wt2_curr:.1f}")
        send_telegram(msg)

    # 2. HAZIRLIK UYARISI: Aşırı satıma (-53 altına) indi ama henüz kesişmedi
    elif wt1_prev > -53 and wt1_curr <= -53:
        msg = (f"⚠️ *{name} - AŞIRI SATIM BÖLGESİNDE (ACELE ETMEYİN!)*\n\n"
               f"⏳ *Durum:* Yeşil çizgi -53'ün altına indi. Henüz AL sinyali yok, yeşil nokta (kesişim) bekleniyor.\n"
               f"💵 *Fiyat:* {price:.1f}\n"
               f"📊 *WT1 (Yeşil):* {wt1_curr:.1f} | *WT2 (Kırmızı):* {wt2_curr:.1f}")
        send_telegram(msg)

    # 3. SAT SİNYALİ: Aşırı alımda (+53 üstü) aşağı kesişim (Kırmızı Nokta Yandı)
    elif wt1_prev >= wt2_prev and wt1_curr < wt2_curr and wt1_prev >= 50:
        msg = (f"🔴 *{name} - WAVETREND SAT SİNYALİ (KIRMIZI NOKTA!)*\n\n"
               f"📉 *Durum:* Aşırı alım bölgesinde aşağı kesişim gerçekleşti!\n"
               f"💵 *Fiyat:* {price:.1f}\n"
               f"📊 *WT1 (Yeşil):* {wt1_curr:.1f} | *WT2 (Kırmızı):* {wt2_curr:.1f}")
        send_telegram(msg)

    # Manuel Test Butonuna Basıldığında Güncel Özeti Gönder
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        durum = "⚠️ Aşırı Satımda (Kesişim Bekleniyor)" if wt1_curr <= -53 else ("🔥 Aşırı Alımda" if wt1_curr >= 53 else "Normal Bölgede")
        yon = "Yukarı (Yeşil > Kırmızı)" if wt1_curr > wt2_curr else "Aşağı (Yeşil < Kırmızı)"
        msg = (f"📊 *GÜNCEL DURUM RAPORU: {name}*\n\n"
               f"💵 *Fiyat:* {price:.1f}\n"
               f"🟢 *WT1 (Yeşil):* {wt1_curr:.1f}\n"
               f"🔴 *WT2 (Kırmızı):* {wt2_curr:.1f}\n"
               f"🧭 *Yön:* {yon}\n"
               f"📌 *Bölge:* {durum}")
        send_telegram(msg)

if __name__ == "__main__":
    check_signals("^NDX", "NAS100 (Günlük)", "1d")
