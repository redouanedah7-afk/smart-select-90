
import streamlit as st
import requests
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta

st.set_page_config(page_title="الانتقاء الذكي 90 - كرة السلة", page_icon="🏀", layout="wide")
st.title("🏀 الانتقاء الذكي 90 – تحليل كرة السلة")

@st.cache_data(ttl=3600)
def fetch_bball_games(api_key, date_str):
    url = f"https://v1.basketball.api-sports.io/games?date={date_str}"
    headers = {"x-apisports-key": api_key}
    try:
        res = requests.get(url, headers=headers, timeout=15).json()
        if res.get("errors"):
            return []
        return res.get("response", [])
    except Exception:
        return []

@st.cache_data(ttl=21600)
def fetch_bball_recent(api_key, team_id, base_date_str):
    headers = {"x-apisports-key": api_key}
    base_dt = datetime.strptime(base_date_str, "%Y-%m-%d")
    season = base_dt.year if base_dt.month >= 9 else base_dt.year - 1
    url = f"https://v1.basketball.api-sports.io/games?team={team_id}&season={season}"
    pts_for, pts_ag = [], []
    try:
        games = requests.get(url, headers=headers, timeout=15).json().get("response", [])
        finished = [ g for g in games
            if g.get("status", {}).get("short") in ("FT", "AOT")
            and g.get("date", "")[:10] < base_date_st]
        finished.sort(key=lambda x: x.get("date", ""), reverse=True)
        for g in finished[:5]:
            hid = g["teams"]["home"]["id"]
            hs = int(g["scores"]["home"]["total"] or 0)
            as_ = int(g["scores"]["away"]["total"] or 0)
            is_home = (hid == team_id)
            pts_for.append(hs if is_home else as_)
            pts_ag.append(as_ if is_home else hs)
    except Exception:
        pass
    return pts_for, pts_ag


def tarot_bball_reading(h_name, a_name, date_str):
    cards =(
        ("الشمس (XIX)", "open", "إيقاع هجومي مرتفع وتسجيل غزير"),
        ("البرج (XVI)", "volatile", "تراجع دفاعي مفاجئ وانهيار في الربع الأخير"),
        ("الاعتدال (XIV)", "balanced", "توازن في الأداء وتقارب كبير في النقاط"),
        ("العربة (VII)", "open", "اندفاع هجومي قوي وسيطرة تحت السلة"),
        ("الناسك (IX)", "closed", "لعب بطيء وتحفظ دفاعي يقلل النقاط"),
        ("القمر (XVIII)", "volatile", "تقلبات غير متوقعة في الربع الرابع"),
    )
    seed = (sum(ord(c) for c in f"{h_name}{a_name}{date_str}"))
    c_h = cards[seed % len(cards)]
    c_a = cards[(seed * 3 + 1) % len(cards)]
    c_m = cards[(seed * 7 + 2) % len(cards)]
    conflict = (c_m[1] == "volatile") or (c_h[1] != c_a[1] and c_m[1] == "closed")
    return c_h, c_a, c_m, conflict

with st.sidebar:
    st.header("⚙️ إعدادات كرة السلة")
    default_key = st.secrets.get("API_FOOTBALL_KEY", "")
    api_key = st.text_input("🔑 مفتاح API-Sports", value=default_key, type="password")
    selected_date = st.date_input("📅 اختر تاريخ المباريات")
    if api_key and st.button("🔄 جلب مباريات السلة", use_container_width=True):
        with st.spinner("جاري سحب مباريات كرة السلة..."):
            st.session_state["bball_games"] = fetch_bball_games(api_key, str(selected_date))

if not api_key:
    st.info("👈 افتح القائمة الجانبية وأدخل مفتاح API-Sports للبدء.")
else:
    games = st.session_state.get("bball_games", [])
    if not games:
        st.info("👈 افتح القائمة الجانبية واضغط على **جلب مباريات السلة**.")
    else:
        leagues = sorted(list({f"{g['country']['name']} - {g['league']['name']}" for g in games}))
        chosen_lg = st.selectbox("🏆 اختر البطولة:", ("🌍 جميع البطولات",) + tuple(leagues))

        filtered = tuple(
            g for g in games
            if chosen_lg.startswith("🌍") or chosen_lg == f"{g['country']['name']} - {g['league']['name']}"
        )

        if not filtered:
            st.warning("⚠️ لا توجد مباريات في هذه البطولة.")
        else:
            options = {f"{g['teams']['home']['name']} 🆚 {g['teams']['away']['name']} | ({g['league']['name']})": 
            g for g in filtered}
            lbl_match = "🎯 اختر المباراة:"
            chosen_lbl = st.selectbox(lbl_match, list(options.keys()))

            game = options[chosen_lbl]

            if st.button("🚀 تشغيل التحليل الذكي لكرة السلة", use_container_width=True):
                h_id = game["teams"]["home"]["id"]
                a_id = game["teams"]["away"]["id"]
                h_name = game["teams"]["home"]["name"]
                a_name = game["teams"]["away"]["name"]

                with st.spinner("جاري تحليل آخر مباريات الفريقين في 2026..."):
                    h_pf, h_pa = fetch_bball_recent(api_key, h_id, str(selected_date))
                    a_pf, a_pa = fetch_bball_recent(api_key, a_id, str(selected_date))

                data_ok = (len(h_pf) >= 1 and len(a_pf) >= 1)
                
            c_h, c_a, c_m, tarot_conflict = tarot_bball_reading(h_name, a_name, str(selected_date))

            st.subheader("🔮 قراءة مسار المباراة (التاروت)")
            st.info(f"**🏠 {h_name}:** {c_h[0]} — {c_h[2]}  |  **✈️ {a_name}:** {c_a[0]} — {c_a[2]}  |  **⚖️ المسار:** {c_m[0]} — {c_m[2]}")

            st.divider()
            st.subheader("📊 التوقعات الإحصائية (التوزيع الطبيعي)")
            if data_ok:
                exp_h = (np.mean(h_pf) + np.mean(a_pa)) / 2
                exp_a = (np.mean(a_pf) + np.mean(h_pa)) / 2
                exp_total = exp_h + exp_a
                diff = exp_h - exp_a
                win_prob_h = round(norm.cdf(diff / 11.5) * 100, 1)
                win_prob_a = round(100 - win_prob_h, 1)

                c1, c2, c3 = st.columns(3)
                c1.metric(f"فوز {h_name}", f"{win_prob_h}%", f"{round(exp_h, 1)} نقطة")
                c2.metric(f"فوز {a_name}", f"{win_prob_a}%", f"{round(exp_a, 1)} نقطة")
                c3.metric("المجموع المتوقع (Total)", f"{round(exp_total, 1)} نقطة")
            else:
                st.warning("⚠️ لا توجد مباريات سابقة كافية لأحد الفريقين لحساب التوقع الإحصائي بدقة.")

                st.divider()
                if data_ok and not tarot_conflict:
                    st.success("✅ **الفلتر النهائي:** المباراة مطابقة لشروط الانتقاء الذكي 90")
                else:
                    reasons = []
                    if not data_ok:
                        reasons.append("نقص بيانات المباريات الأخيرة")
                    if tarot_conflict:
                        reasons.append("تعارض/تقلب في قراءة المسار")
                    st.warning(f"⚠️ **الفلتر النهائي:** يُنصح بالحذر بسبب ({' + '.join(reasons)})")
