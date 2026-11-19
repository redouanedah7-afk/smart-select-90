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
    base = "https://v3.football.api-sports.io"
    
    url = f"{base}/fixtures?date={date_str}"
    headers = {"x-apisports-key": api_key}
    r = requests.get(url, headers=headers).json()
    if r.get("errors"):
        st.error(r["errors"])
    return r.get("response", [])


@st.cache_data(ttl=3600)
def fetch_team_last10(api_key, team_id):
    base = "https://v3.football.api-sports.io"
    headers = {"x-apisports-key": api_key}
    gf, ga = [], []
    for yr in [2026,2025,2024]:
        url = f"{base}/fixtures?team={team_id}&season={yr}&status=FT"
        r = requests.get(url, headers=headers).json().get("response", [])
        if r:
            for m in r[-10:]:
                is_home = (m["teams"]["home"]["id"] == team_id)
                gh = m["goals"]["home"] or 0
                ga_val = m["goals"]["away"] or 0
                gf.append(gh if is_home else ga_val)
                ga.append(ga_val if is_home else gh)
            break
    return gf[-10:], ga[-10:]


@st.cache_data(ttl=1800)
def fetch_odds_and_injuries(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    base = "https://v3.football.api-sports.io"
    odds_res = requests.get(f"{base}/odds?fixture={fixture_id}", headers=headers).json()
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
    url_inj = f"{base}/injuries?fixture={fixture_id}"
    inj_res = requests.get(url_inj, headers=headers).json()


    injuries = [f"{i['player']['name']} ({i['team']['name']})" for i in inj_res.get("response", [])]
    return o1, ox, o2, injuries

# --- الواجهة الرئيسية ---
default_key = st.secrets.get("API_FOOTBALL_KEY", "")
api_key = st.text_input("🔑 مفتاح API-Football (محفوظ تلقائياً)", value=default_key, type="password")


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
            if st.button("🟢 فحص سريع وعرض المباريات الخضراء فقط (أول 3 مباريات)"):
                green_list = []
                with st.spinner("جاري فحص المباريات ومطابقتها مع شروط الانتقاء الذكي 90..."):
                for item_lbl, item_m in list(options.items())[:3]:
                    fid_t = item_m["fixture"]["id"]
                    hid_t = item_m["teams"]["home"]["id"]
                    aid_t = item_m["teams"]["away"]["id"]
                    hgf_t, hga_t = fetch_team_last10(api_key, hid_t)
                    agf_t, aga_t = fetch_team_last10(api_key, aid_t)
                    _, _, _, inj_t = fetch_odds_and_injuries(api_key, fid_t)
                    if len(hgf_t) >= 5 and len(agf_t) >= 5 and len(inj_t) < 4:
                        green_list.append(item_lbl)
                if green_list:
                st.success(f"✅ تم العثور على {len(green_list)} مباراة مطابقة للشروط:")
                for g_m in green_list:
                    st.write(f"- **{g_m}**")
                else:
                st.warning("⚠️ لم تطابق أي مباراة من المجموعة المفحوصة جميع الشروط.")


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
                    if h_gf and np.mean(h_gf) >= 1.4:
                        lam_h = lam_h * 1.15

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
                    mc1.metric(f"فوز {h_name}", f"{p1}%", f"سوق: {m1}%")
                    mc2.metric("التعادل (X)", f"{px}%", f"سوق: {mx}%")
                    mc3.metric(f"فوز {a_name}", f"{p2}%", f"سوق: {m2}%")

                    st.divider()
                    st.subheader("📊 الإحصائيات المتوقعة (xG) وأداء الفريقين")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        st.info(f"**🏠 {h_name}**\n- الأهداف المتوقعة (xG): **{lam_h:.2f}**\n- معدل التسجيل (آخر 10): **{np.mean(h_gf) if h_gf else 0:.2f}**\n- معدل الاستقبال (آخر 10): **{np.mean(h_ga) if h_ga else 0:.2f}**")
                    with sc2:
                        st.info(f"**✈️ {a_name}**\n- الأهداف المتوقعة (xG): **{lam_a:.2f}**\n- معدل التسجيل (آخر 10): **{np.mean(a_gf) if a_gf else 0:.2f}**\n- معدل الاستقبال (آخر 10): **{np.mean(a_ga) if a_ga else 0:.2f}**")

                    # حساب أكثر 3 نتائج دقيقة احتمالاً من مصفوفة بواسون
                    flat_idx = np.argsort(matrix.ravel())[::-1][:3]
                    top_scores = [(idx // 9, idx % 9, round(matrix.ravel()[idx] * 100, 1)) for idx in flat_idx]
                    best_h, best_a, best_prob = top_scores[0]

                    # حساب احتمالات الأهداف (+2.5 و BTTS)
                    over25 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 2) * 100, 1)
                    btts = round(sum(matrix[i, j] for i in range(1, 9) for j in range(1, 9)) * 100, 1)

                    st.divider()
                    st.subheader("🎯 النتيجة النهائية المتوقعة والفلتر الذكي")
                    rc1, rc2, rc3 = st.columns(3)
                    rc1.metric("النتيجة الأقرب", f"{best_h} - {best_a}", f"احتمال {best_prob}%")
                    rc2.metric("أكثر من 2.5 هدف", f"{over25}%")
                    rc3.metric("كلا الفريقين يسجل (BTTS)", f"{btts}%")

                    st.write("**أقوى 3 سيناريوهات للنتيجة الدقيقة:**")
                    for s_h, s_a, s_p in top_scores:
                        st.write(f"- **{h_name} {s_h} - {s_a} {a_name}** (بنسبة **{s_p}%**)")

                    if data_ok and not tarot_conflict and not tactical_alert:
                        st.success("✅ **قرار الفلتر النهائي:** المباراة مطابقة لشروط الانتقاء الذكي 90.")
                    else:
                        reasons = []
                        if not data_ok:
                                reasons.append("نقص بيانات آخر 10 مباريات")
                        if tarot_conflict:
                                reasons.append("تعارض في قراءة المسار")
                        if tactical_alert:
                            reasons.append("وجود غيابات مؤثرة (4+)")
                        st.warning(f"⚠️ **تنبيه الفلتر النهائي:** يُنصح بالحذر بسبب ({' ، '.join(reasons)}).")
