import streamlit as st
import numpy as np
from scipy.stats import poisson
import hashlib
import requests
from datetime import datetime

st.set_page_config(page_title="الانتقاء الذكي 90", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    .tarot-box { background-color: #1e2130; padding: 12px; border-radius: 10px; border-right: 4px solid #ff4b4b; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ الانتقاء الذكي 90 (v3.0)")
st.caption("النظام الآلي للتصفية الإحصائية والطاقية للمباريات")

# --- قاعدة بيانات التاروت ---
TAROT_DECK = [
    ("0 - الأحمق", "تقلبات غير متوقعة وعشوائية", True),
    ("I - الساحر", "مبادرة هجومية ومهارة فردية حاسمة", False),
    ("II - الكاهنة العليا", "غموض تكتيكي وتحفظ دفاعي", False),
    ("III - الإمبراطورة", "وفرة أهداف وانفتاح هجومي", False),
    ("IV - الإمبراطور", "انضباط وسيطرة تكتيكية صارمة", False),
    ("V - الكاهن", "التزام بالخطة التقليدية دون مجازفة", False),
    ("VI - العشاق", "توازن وتقارب شديد (احتمال تعادل)", True),
    ("VII - العربة", "اندفاع وهجوم مباشر وسرعة إيقاع", False),
    ("VIII - القوة", "صراع بدني وحسم للطرف الأكثر انضباطاً", False),
    ("IX - الناسك", "بطء إيقاع وحذر دفاعي مبالغ فيه", False),
    ("X - عجلة الحظ", "تغير مفاجئ في مجرى اللعب", True),
    ("XI - العدالة", "توازن وانضباط تحكيمي ونتيجة منطقية", False),
    ("XII - المشنوق", "توقف وجمود تكتيكي وعجز عن التسجيل", True),
    ("XIII - الموت", "تحول جذري في النتيجة خلال اللقاء", True),
    ("XIV - الاعتدال", "توازن وتبادل السيطرة بين الفريقين", False),
    ("XV - الشيطان", "ضغط عصبي وأخطاء فردية قاتلة", True),
    ("XVI - البرج", "صدمة أو خطأ دفاعي فادح يقلب الموازين", True),
    ("XVII - النجمة", "صفاء ذهني وانسيابية في بناء اللعب", False),
    ("XVIII - القمر", "ضبابية وخطر المفاجأة في النتيجة", True),
    ("XIX - الشمس", "وضوح وحسم مستحق دون تعقيدات", False),
    ("XX - المحاكمة", "حسم في الدقائق الأخيرة من المباراة", False),
    ("XXI - العالم", "اكتمال السيطرة وتحقيق الهدف المطلوب", False),
    ("آس الصولجانات", "بداية نارية وضغط هجومي مبكر", False),
    ("خمسة السيوف", "تشتت دفاعي ولعب تحت ضغط الخسارة", True),
    ("فارس العملات", "ثبات وتدرج هادئ في فرض الإيقاع", False),
    ("عشرة السيوف", "إرهاق ذهني وانهيار دفاعي متكرر", True),
    ("اثنان من العملات", "محاولة الحفاظ على التوازن وتسيير النتيجة", True),
    ("سبعة الكؤوس", "إهدار فرص سهلة وتسرع أمام المرمى", True)
]

def draw_card(seed_text):
    idx = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % len(TAROT_DECK)
    card_name, card_desc, is_risk = TAROT_DECK[idx]
    return f"{card_name} ({card_desc})", is_risk

def weighted_avg(goals_list):
    if not goals_list:
        return 1.0
    weights = np.linspace(0.5, 1.5, len(goals_list))
    return np.average(goals_list, weights=weights)

# --- دوال الاتصال بـ API-Football ---
@st.cache_data(ttl=1800)
def fetch_fixtures(api_key, date_str):
    url = f"https://api-sports.io{date_str}"
    headers = {"x-apisports-key": api_key}
    r = requests.get(url, headers=headers).json()
    return r.get("response", [])

@st.cache_data(ttl=3600)
def fetch_team_last10(api_key, team_id):
    url = f"https://api-sports.io{team_id}&last=10&status=FT"
    headers = {"x-apisports-key": api_key}
    r = requests.get(url, headers=headers).json()
    gf, ga = [], []
    for m in reversed(r.get("response", [])):
        is_home = (m["teams"]["home"]["id"] == team_id)
        gh = m["goals"]["home"] or 0
        ga_val = m["goals"]["away"] or 0
        gf.append(gh if is_home else ga_val)
        ga.append(ga_val if is_home else gh)
    return gf, ga

@st.cache_data(ttl=1800)
def fetch_odds_and_injuries(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    odds_res = requests.get(f"https://api-sports.io{fixture_id}", headers=headers).json()
    o1, ox, o2 = 2.50, 3.20, 2.80
    try:
        bets = odds_res["response"]["bookmakers"]["bets"]
        for b in bets:
            if b["name"] == "Match Winner":
                for v in b["values"]:
                    if v["value"] == "Home":
                        o1 = float(v["odd"])
                    elif v["value"] == "Draw":
                        ox = float(v["odd"])
                    elif v["value"] == "Away":
                        o2 = float(v["odd"])
                break
    except Exception:
        pass
    inj_res = requests.get(f"https://api-sports.io{fixture_id}", headers=headers).json()
    injuries = [f"{i['player']['name']} ({i['team']['name']})" for i in inj_res.get("response", [])]
    return o1, ox, o2, injuries

# --- الواجهة الرئيسية ---
api_key = st.text_input("🔑 الصق مفتاح API-Football المجاني هنا:", type="password")

if api_key:
    selected_date = st.date_input("📅 اختر تاريخ المباريات:", datetime.today())
    if st.button("🔄 جلب مباريات هذا اليوم", use_container_width=True):
        with st.spinner("جاري سحب المباريات من السيرفر..."):
            st.session_state["fixtures"] = fetch_fixtures(api_key, selected_date.strftime("%Y-%m-%d"))

    fixtures = st.session_state.get("fixtures", [])
    if fixtures:
        search_q = st.text_input("🔍 ابحث باسم الفريق أو الدوري (اختياري):")
        filtered = [
            f for f in fixtures
            if not search_q or search_q.lower() in f["teams"]["home"]["name"].lower()
            or search_q.lower() in f["teams"]["away"]["name"].lower()
            or search_q.lower() in f["league"]["name"].lower()
        ]

        if filtered:
            options = {
                f"{f['league']['country']} - {f['league']['name']} | {f['teams']['home']['name']} vs {f['teams']['away']['name']} ({f['fixture']['date'][11:16]})": f
                for f in filtered
            }
            chosen_label = st.selectbox("اختر المباراة للتحليل:", list(options.keys()))
            match_data = options[chosen_label]

            if st.button("🚀 تشغيل التحليل التلقائي والفلتر النهائي", type="primary", use_container_width=True):
                with st.spinner("جاري سحب آخر 10 مباريات، الاحتمالات، الغيابات، وحساب المصفوفة..."):
                    f_id = match_data["fixture"]["id"]
                    h_id = match_data["teams"]["home"]["id"]
                    a_id = match_data["teams"]["away"]["id"]
                    h_name = match_data["teams"]["home"]["name"]
                    a_name = match_data["teams"]["away"]["name"]
                    city = match_data["fixture"]["venue"]["city"] or "Unknown"
                    dt_str = match_data["fixture"]["date"][:16].replace("T", " ")

                    h_gf, h_ga = fetch_team_last10(api_key, h_id)
                    a_gf, a_ga = fetch_team_last10(api_key, a_id)
                    o1, ox, o2, injuries = fetch_odds_and_injuries(api_key, f_id)

                    data_ok = (len(h_gf) >= 5 and len(a_gf) >= 5)
                    tactical_alert = len(injuries) >= 4

                    # الطبقة 01 و 03
                    lam_h = ((weighted_avg(h_gf) + weighted_avg(a_ga)) / 2) * 1.08
                    lam_a = (weighted_avg(a_gf) + weighted_avg(h_ga)) / 2

                    matrix = np.zeros((9, 9))
                    rho = -0.13
                    for i in range(9):
                        for j in range(9):
                            p = poisson.pmf(i, lam_h) * poisson.pmf(j, lam_a)
                            if i == 0 and j == 0:
                                p *= (1 - lam_h * lam_a * rho)
                            elif i == 0 and j == 1:
                                p *= (1 + lam_h * rho)
                            elif i == 1 and j == 0:
                                p *= (1 + lam_a * rho)
                            elif i == 1 and j == 1:
                                p *= (1 - rho)
                            matrix[i, j] = max(p, 0)
                    matrix /= np.sum(matrix)

                    p1 = round(np.sum(np.tril(matrix, -1)) * 100, 1)
                    px = round(np.sum(np.diag(matrix)) * 100, 1)
                    p2 = round(np.sum(np.triu(matrix, 1)) * 100, 1)

                    inv = [1/o1, 1/ox, 1/o2]
                    m1, mx, m2 = [round((x / sum(inv)) * 100, 1) for x in inv]

                    # الطبقة 04
                    base_seed = f"{city.strip().lower()}_{dt_str}"
                    ruling_c, r_risk = draw_card(f"ruling_{base_seed}")
                    home_c, _ = draw_card(f"home_{h_name}_{base_seed}")
                    away_c, _ = draw_card(f"away_{a_name}_{base_seed}")
                    path1_c, _ = draw_card(f"path1_{base_seed}")
                    path2_c, p2_risk = draw_card(f"path2_{base_seed}")
                    path3_c, p3_risk = draw_card(f"path3_{base_seed}")
                    tarot_conflict = r_risk or p2_risk or p3_risk

                    st.divider()
                    st.subheader(f"📋 التقرير الكامل: {h_name} ضد {a_name}")
                    st.caption(f"📍 المدينة: {city} | 🕒 التوقيت (UTC): {dt_str}")

                    if injuries:
                        with st.expander(f"⚠️ الغيابات المرصودة ({len(injuries)} لاعبين)"):
                            for inj in injuries:
                                st.write(f"- {inj}")

                    st.markdown(f"""
                    <div class="tarot-box">
                    <b>👑 البطاقة الحاكمة:</b> {ruling_c}<br>
                    <b>🏠 {h_name}:</b> {home_c}<br>
                    <b>✈️ {a_name}:</b> {away_c}<br><br>
                    <b>🛤️ مسار المباراة:</b><br>
                    1️⃣ {path1_c}<br>
                    2️⃣ {path2_c}<br>
                    3️⃣ {path3_c}
                    </div>
                    """, unsafe_allow_html=True)

                    st.subheader("📊 مسار النتيجة المباشرة (1X2)")
                    mc1, mc2, mc3 = st.columns(3)
