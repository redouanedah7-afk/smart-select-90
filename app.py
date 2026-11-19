import streamlit as st
import numpy as np
from scipy.stats import poisson
import hashlib

st.set_page_config(page_title="الانتقاء الذكي 90", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    .tarot-box { background-color: #1e2130; padding: 12px; border-radius: 10px; border-right: 4px solid #ff4b4b; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ الانتقاء الذكي 90 (v2.0)")
st.caption("نظام التصفية الإحصائية والطاقية المتكامل")

# --- قاعدة بيانات التاروت الكاملة (الكبرى + الصغرى المؤثرة) ---
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
    return TAROT_DECK[idx]

def weighted_avg(goals_str):
    nums = [float(x.strip()) for x in goals_str.split(",") if x.strip()]
    weights = np.linspace(0.5, 1.5, len(nums))
    return np.average(nums, weights=weights)

# --- تنظيم الواجهة بتبويبات مريحة للهاتف ---
tab1, tab2 = st.tabs(["📝 إدخال البيانات", "📊 التقرير والفلتر النهائي"])

with tab1:
    home_team = st.text_input("الفريق المحلي", "كورتيبا")
    away_team = st.text_input("الفريق الضيف", "سانتوس")
    col1, col2 = st.columns(2)
    city = col1.text_input("المدينة", "Curitiba")
    match_dt = col2.text_input("التاريخ والتوقيت", "2026-11-18 23:30")

    st.markdown("---")
    st.markdown("**الطبقة 01: أهداف آخر 10 مباريات (من الأقدم للأحدث)**")
    h_gf = st.text_input(f"سجل {home_team}", "1, 0, 2, 1, 0, 1, 0, 2, 0, 0")
    h_ga = st.text_input(f"استقبل {home_team}", "1, 1, 0, 2, 1, 1, 1, 0, 1, 1")
    a_gf = st.text_input(f"سجل {away_team}", "1, 2, 1, 0, 2, 1, 2, 1, 2, 1")
    a_ga = st.text_input(f"استقبل {away_team}", "1, 1, 2, 1, 0, 1, 1, 0, 1, 2")

    st.markdown("---")
    st.markdown("**الطبقة 02 و 03: احتمالات السوق والتنبيهات**")
    c1, c2, c3 = st.columns(3)
    odds_1 = c1.number_input("1", value=3.70, step=0.05)
    odds_x = c2.number_input("X", value=3.30, step=0.05)
    odds_2 = c3.number_input("2", value=1.95, step=0.05)
    tactical_alert = st.checkbox("⚠️ وجود غيابات مؤثرة أو تضارب أخبار (الطبقة 02)")

    run_btn = st.button("🚀 تحليل المباراة وتطبيق الفلتر", use_container_width=True, type="primary")

with tab2:
    if run_btn:
        # 1. الحسابات الرياضية
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

        # 2. الطبقة 04 الكاملة (5 بطاقات)
        base_seed = f"{city.strip().lower()}_{match_dt.strip()}"
        ruling_c, r_risk = draw_card(f"ruling_{base_seed}")
        home_c, h_risk = draw_card(f"home_{home_team}_{base_seed}")
        away_c, a_risk = draw_card(f"away_{away_team}_{base_seed}")
        path1_c, p1_risk = draw_card(f"path1_{base_seed}")
        path2_c, p2_risk = draw_card(f"path2_{base_seed}")
        path3_c, p3_risk = draw_card(f"path3_{base_seed}")

        tarot_conflict = r_risk or p2_risk or p3_risk

        st.subheader("🔮 الطبقة 04: قراءة التاروت ومسار المباراة")
        st.markdown(f"""
        <div class="tarot-box">
        <b>👑 البطاقة الحاكمة:</b> {ruling_c}<br>
        <b>🏠 {home_team}:</b> {home_c}<br>
        <b>✈️ {away_team}:</b> {away_c}<br><br>
        <b>🛤️ مسار المباراة (3 أوراق):</b><br>
        1️⃣ البداية: {path1_c}<br>
        2️⃣ التحول: {path2_c}<br>
        3️⃣ النهاية: {path3_c}
        </div>
        """, unsafe_allow_html=True)

        # 3. مسار 1X2
        st.subheader("📊 مسار النتيجة المباشرة (1X2)")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric(home_team, f"{p1}%", f"سوق: {m1}%")
        mc2.metric("تعادل", f"{px}%", f"سوق: {mx}%")
        mc3.metric(away_team, f"{p2}%", f"سوق: {m2}%")

        picks_1x2 = []
        if not tactical_alert and not tarot_conflict:
            for lbl, mp, mkp in [(f"فوز {home_team}", p1, m1), ("التعادل", px, mx), (f"فوز {away_team}", p2, m2)]:
                if mp >= 70.0 and abs(mp - mkp) <= 7.0:
                    picks_1x2.append(f"✅ مقبول: {lbl} ({mp}%)")

        if picks_1x2:
            for p in picks_1x2: st.success(p)
        else:
            reason = "تضارب تكتيكي (الطبقة 02)" if tactical_alert else ("مؤشر مفاجأة/تقلب في التاروت (الطبقة 04)" if tarot_conflict else "النسب دون عتبة الأمان 70%")
            st.error(f"🚫 1X2 مُستبعدة — السبب: {reason}")

        # 4. مسار الأهداف
        st.subheader("⚽ مسار سوق الأهداف (مستقل)")
        o15 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 1.5) * 100, 1)
        o25 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 2.5) * 100, 1)
        o35 = round(sum(matrix[i, j] for i in range(9) for j in range(9) if i + j > 3.5) * 100, 1)
        btts = round(sum(matrix[i, j] for i in range(1, 9) for j in range(1, 9)) * 100, 1)
        h_o05 = round((1 - np.sum(matrix[0, :])) * 100, 1)
        a_o05 = round((1 - np.sum(matrix[:, 0])) * 100, 1)

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

        with st.expander("جدول جميع نسب الأهداف"):
            st.json(goals_dict)
    else:
        st.info("👈 املأ بيانات المباراة في تبويب (إدخال البيانات) واضغط على زر التحليل.")
