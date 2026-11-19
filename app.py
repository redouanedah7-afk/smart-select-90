import streamlit as st
import numpy as np
from scipy.stats import poisson
import hashlib

# إعداد صفحة التطبيق لتناسب الهاتف وباللغة العربية
st.set_page_config(page_title="الانتقاء الذكي 90", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"] { font-size: 22px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ منهج الانتقاء الذكي 90")
st.caption("نظام التصفية الإحصائية والطاقية للمباريات (1X2 + سوق الأهداف المستقل)")

# --- قائمة البطاقات الحاكمة ---
MAJOR_ARCANA = [
    "0 - الأحمق (تقلبات غير متوقعة)", "I - الساحر (مبادرة ومهارة فردية)",
    "II - الكاهنة العليا (غموض وتحفظ)", "III - الإمبراطورة (وفرة أهداف وانفتاح)",
    "IV - الإمبراطور (انضباط وسيطرة تكتيكية)", "V - الكاهن (التزام بالخطة التقليدية)",
    "VI - العشاق (توازن وتقارب شديد)", "VII - العربة (اندفاع وهجوم مباشر)",
    "VIII - القوة (صراع بدني وحسم للأنضبط)", "IX - الناسك (بطء إيقاع وحذر دفاعي)",
    "X - عجلة الحظ (تغير مفاجئ في مجرى اللعب)", "XI - العدالة (توازن وانضباط تحكيمي)",
    "XII - المشنوق (توقف وجمود تكتيكي)", "XIII - الموت (تحول جذري في النتيجة)",
    "XIV - الاعتدال (توازن وتبادل السيطرة)", "XV - الشيطان (ضغط عصبي وأخطاء)",
    "XVI - البرج (صدمة أو خطأ دفاعي فادح)", "XVII - النجمة (صفاء ذهني وانسيابية)",
    "XVIII - القمر (ضبابية وخطر المفاجأة)", "XIX - الشمس (وضوح وحسم مستحق)",
    "XX - المحاكمة (حسم في الدقائق الأخيرة)", "XXI - العالم (اكتمال السيطرة والنتيجة)"
]

def get_ruling_card(city, dt):
    seed = f"{city.strip().lower()}_{dt.strip()}"
    idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 22
    risk_cards = [0, 10, 16, 18]

    return MAJOR_ARCANA[idx], (idx in risk_cards)

def weighted_avg(goals_str):
    nums = [float(x.strip()) for x in goals_str.split(",") if x.strip()]
    weights = np.linspace(0.5, 1.5, len(nums))
    return np.average(nums, weights=weights)

# --- واجهة إدخال بيانات المباراة ---
with st.form("match_form"):
    st.subheader("1️⃣ بيانات المباراة والزمان والمكان")
    col1, col2 = st.columns(2)
    home_team = col1.text_input("الفريق المحلي", "كورتيبا")
    away_team = col2.text_input("الفريق الضيف", "سانتوس")
    
    col3, col4 = st.columns(2)
    city = col3.text_input("مدينة المباراة", "Curitiba")
    match_dt = col4.text_input("التاريخ والتوقيت", "2026-11-18 23:30")

    st.subheader("2️⃣ الطبقة 01: أهداف آخر 10 مباريات (من الأقدم للأحدث)")
    h_gf = st.text_input(f"أهداف سجلها {home_team}", "1, 0, 2, 1, 0, 1, 0, 2, 0, 0")
    h_ga = st.text_input(f"أهداف استقبلها {home_team}", "1, 1, 0, 2, 1, 1, 1, 0, 1, 1")
    a_gf = st.text_input(f"أهداف سجلها {away_team}", "1, 2, 1, 0, 2, 1, 2, 1, 2, 1")
    a_ga = st.text_input(f"أهداف استقبلها {away_team}", "1, 1, 2, 1, 0, 1, 1, 0, 1, 2")

    st.subheader("3️⃣ الطبقة 02 و 03: احتمالات السوق والتنبيهات الفنية")
    c1, c2, c3 = st.columns(3)
    odds_1 = c1.number_input("احتمال 1", value=3.70, step=0.05)
    odds_x = c2.number_input("احتمال X", value=3.30, step=0.05)
    odds_2 = c3.number_input("احتمال 2", value=1.95, step=0.05)

    tactical_alert = st.checkbox("⚠️ يوجد غيابات مؤثرة أو تضارب في الأخبار الفنية (الطبقة 02)")
    submit = st.form_submit_button("🔍 تشغيل المنهج والفلتر النهائي", use_container_width=True)

if submit:
    # الحسابات الرياضية
    lam_h = ((weighted_avg(h_gf) + weighted_avg(a_ga)) / 2) * 1.08
    lam_a = (weighted_avg(a_gf) + weighted_avg(h_ga)) / 2

    matrix = np.zeros((9, 9))
    rho = -0.13
    for i in range(9):
        for j in range(9):
            p = poisson.pmf(i, lam_h) * poisson.pmf(j, lam_a)
            if i == 0 and j == 0: p *= (1 - lam_h * lam_a * rho)
            elif i == 0 and j == 1: p *= (1 + lam_h * rho)
            elif i == 1 and j == 0: p *= (1 + lam_a * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            matrix[i, j] = max(p, 0)
    matrix /= np.sum(matrix)

    p1 = round(np.sum(np.tril(matrix, -1)) * 100, 1)
    px = round(np.sum(np.diag(matrix)) * 100, 1)
    p2 = round(np.sum(np.triu(matrix, 1)) * 100, 1)

    inv = [1/odds_1, 1/odds_x, 1/odds_2]
    m1, mx, m2 = [round((x / sum(inv)) * 100, 1) for x in inv]

    o15 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 1.5) * 100, 1)
    o25 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 2.5) * 100, 1)
    o35 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 3.5) * 100, 1)
    btts = round(sum(matrix[i, j] for i in range(1, 9) for j in range(1, 9)) * 100, 1)
    h_o05 = round((1 - np.sum(matrix[0, :])) * 100, 1)
    a_o05 = round((1 - np.sum(matrix[:, 0])) * 100, 1)

    card_name, card_risk = get_ruling_card(city, match_dt)

    st.divider()
    st.subheader(f"🔮 البطاقة الحاكمة: {card_name}")
    
    st.subheader("📊 مسار النتيجة المباشرة (1X2)")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(f"فوز {home_team}", f"{p1}%", f"السوق: {m1}%")
    m_col2.metric("التعادل (X)", f"{px}%", f"السوق: {mx}%")
    m_col3.metric(f"فوز {away_team}", f"{p2}%", f"السوق: {m2}%")

    # فلتر 1X2
    picks_1x2 = []
    if not tactical_alert and not card_risk:
        for lbl, mp, mkp in [(f"فوز {home_team}", p1, m1), ("التعادل", px, mx), (f"فوز {away_team}", p2, m2)]:
            if mp >= 70.0 and abs(mp - mkp) <= 7.0:
                picks_1x2.append(f"✅ مقبول: {lbl} ({mp}%)")

    if picks_1x2:
        for p in picks_1x2: st.success(p)
    else:
        st.error("🚫 قرار الفلتر (1X2): مُستبعدة (NO BET) — لا تتوفر شروط الأمان أو يوجد مؤشر مفاجأة.")

    st.subheader("⚽ مسار سوق الأهداف (مستقل)")
    goals_dict = {
        "Over 1.5": o15, "Under 1.5": round(100 - o15, 1),
        "Over 2.5": o25, "Under 2.5": round(100 - o25, 1),
        "Over 3.5": o35, "Under 3.5": round(100 - o35, 1),
        "BTTS نعم": btts, "BTTS لا": round(100 - btts, 1),
        f"{home_team} Over 0.5": h_o05,
        f"{away_team} Over 0.5": a_o05
    }

    accepted_goals = [f"✅ {k}: {v}%" for k, v in goals_dict.items() if v >= 74.0]
    if accepted_goals:
        for g in accepted_goals: st.success(g)
    else:
        st.warning("⚠️ لا توجد فرصة أهداف تتجاوز عتبة الأمان (74%).")

    with st.expander("عرض جميع نسب الأهداف التفصيلية"):
        st.json(goals_dict)
