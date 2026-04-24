import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 页面配置 ---
st.set_page_config(page_title="Balance & Future Pro", layout="wide")

# --- 密码门禁逻辑 (使用 Secrets 安全模式) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.title("🔒 Balance & Future")
            st.write("这是一个私密的家庭财务系统，请证明你是自己人。")
            pwd = st.text_input("请输入家庭通行码：", type="password")
            if st.button("进入系统"):
                # 💡 注意：部署后请在 Streamlit Cloud 的 Secrets 中设置 password
                if pwd == st.secrets["password"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ 暗号不对，请确认。")
        return False
    return True

if not check_password():
    st.stop()

# --- 核心计算逻辑 ---
def calc_mortgage(p, r, y):
    m = int(y * 12)
    mr = r / 100 / 12
    mp = p / m if m > 0 else 0
    return [float(mp + (p - i * mp) * mr) for i in range(m)] if m > 0 else [0.0]

def calc_income(gross, gig, base, prov_rate=0.05):
    deduct = base * (0.08 + 0.02 + 0.005 + prov_rate)
    taxable = max(0, gross - deduct - 5000)
    if taxable <= 3000: tax = taxable * 0.03
    elif taxable <= 12000: tax = taxable * 0.1 - 210
    elif taxable <= 25000: tax = taxable * 0.2 - 1410
    elif taxable <= 35000: tax = taxable * 0.25 - 2660
    else: tax = taxable * 0.3 - 4410
    net = gross - deduct - tax + gig
    return {"net": float(net), "tax": float(tax), "ins": float(deduct), "fund": float(base * prov_rate)}

# --- 侧边栏战略配置 ---
st.sidebar.title("🚀 财务设置中心")

with st.sidebar.expander("👤 成员名称", expanded=True):
    n_a = st.text_input("我的称呼", "我")
    n_b = st.text_input("队友称呼", "队友")

with st.sidebar.expander("✈️ 梦想旅行配置", expanded=True): # 新增点：目的地配置
    dream_dest = st.text_input("梦想目的地", "马尔代夫")
    dream_cost = st.number_input("预计人均花费", value=15000.0, step=1000.0)
    travel_num = st.number_input("出行人数", value=2, min_value=1)
    total_travel_cost = dream_cost * travel_num

with st.sidebar.expander("💰 收入与副业配置", expanded=False):
    st.write(f"**{n_a}**")
    a_g = st.number_input(f"{n_a}主业税前", value=26000.0, step=500.0)
    a_gig = st.number_input(f"{n_a}副业月入", value=0.0)
    a_m = st.selectbox(f"{n_a}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="a_ms")
    a_h = st.number_input(f"{n_a}月均工时", value=176, min_value=1)
    st.write("---")
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}主业税前", value=18000.0, step=500.0)
    b_gig = st.number_input(f"{n_b}副业月入", value=0.0)
    b_m = st.selectbox(f"{n_b}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="b_ms")
    b_h = st.number_input(f"{n_b}月均工时", value=176, min_value=1)
    pf_pct = st.slider("公积金比例(%)", 5, 12, 5) / 100

with st.sidebar.expander("🏠 债务与资产", expanded=False):
    m_p = st.number_input("房贷本金", value=400000.0)
    m_r = st.number_input("房贷年利率(%)", value=3.2)
    m_y = st.number_input("房贷年限", value=30)
    asset_total = st.number_input("当前可变现总资产", value=600000.0) # 为 FIRE 准备
    c_l = st.number_input("车贷月供", value=2000.0)
    living = st.number_input("家庭基础生活费", value=6000.0)
    other = st.number_input("其他杂项", value=0.0)

# --- 数据预处理 ---
res_a = calc_income(a_g, a_gig, a_g if a_m=="全额缴纳" else 2360, pf_pct)
res_b = calc_income(b_g, b_gig, b_g if b_m=="全额缴纳" else 2360, pf_pct)
m_seq = calc_mortgage(m_p, m_r, m_y)
curr_m = float(m_seq[0]) if m_seq else 0.0
total_net = res_a['net'] + res_b['net']
total_exp = curr_m + c_l + living + other
savings = total_net - total_exp
total_pf = (res_a['fund'] + res_b['fund']) * 2

# --- 视觉样式 ---
health_color = "rgba(16, 185, 129, 0.2)" if savings > 0 else "rgba(239, 68, 68, 0.2)"
st.markdown(f"""
    <style>
    [data-testid="stMetric"] {{
        background-color: rgba(128, 128, 128, 0.1);
        padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
    }}
    [data-testid="stMetric"]:nth-child(3) {{ background-color: {health_color}; }}
    .stAppDeployButton {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 路由 ---
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

if view == "🏠 Balance 看板":
    st.title(f"📊 Balance & Future | 家庭财务系统")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("家庭总到手现金", f"¥{int(total_net):,}")
    col2.metric("家庭总月支出", f"¥{int(total_exp):,}")
    col3.metric("本月净结余", f"¥{int(savings):,}", delta=f"{int(savings/total_net*100) if total_net>0 else 0}% 储蓄率")
    if 'active' not in st.session_state: st.session_state.active = n_a
    hourly = (a_g + a_gig)/a_h if st.session_state.active == n_a else (b_g + b_gig)/b_h
    col4.metric(f"{st.session_state.active} 实时时薪", f"¥{hourly:.1f}")
    
    st.info(f"💡 **公积金抵消感：** 每月公积金入账 ¥{int(total_pf):,}，已自动对冲了房贷月供的 **{int(total_pf/curr_m*100) if curr_m>0 else 100}%**。")
    
    # 新增点：家庭旅行自由指数
    if savings > 0:
        months_to_travel = total_travel_cost / savings
        st.success(f"🏖️ **家庭旅行自由指数：** 按目前的净结余，你们每 **{months_to_travel:.1f}** 个月就能‘全款’去一次 **{dream_dest}**。")
    else:
        st.warning(f"🏖️ **家庭旅行自由指数：** 当前结余为负，暂无法支撑 **{dream_dest}** 的旅行计划，需优化开销。")

    st.divider()
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        who = st.selectbox("谁来买单？", [n_a, n_b], key="active")
        price = st.number_input("心仪商品价格(元)", value=6000.0)
    with l2:
        h = float(price / hourly) if hourly > 0 else 0
        st.write(f"购买此商品相当于消耗 **{who}** 约 **{h:.1f} 小时** 的奋斗成果。")
        st.progress(min(h/176, 1.0))

    st.divider()
    st.subheader("🛡️ 家庭护城河测试")
    c_l_p, c_r_p = st.columns(2)
    with c_l_p:
        loss = st.radio("风险模拟：如果谁暂时失去收入？", [f"{n_a}失业", f"{n_b}失业"])
        survive = res_b['net'] if loss == f"{n_a}失业" else res_a['net']
        gap = survive - total_exp
        if gap >= 0: st.success(f"护城河稳固：单薪仍可结余 ¥{int(gap):,}")
        else: st.error(f"护城河告急：每月缺口 ¥{int(abs(gap)):,}")
    with c_r_p:
        dream_item = st.text_input("下一个大件梦想", "换一辆新车")
        dream_p = st.number_input("梦想金额 (元)", value=300000.0)
        if savings > 0: st.warning(f"达成 **{dream_item}** 还需 **{dream_p / savings:.1f}** 个月。")

elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变长廊")
    
    # 新增点：FIRE 指数加在这里
    st.subheader("🔥 FIRE 退休进度审计")
    fire_target = total_exp * 12 * 25 # 25倍原则
    fire_prog = asset_total / fire_target if fire_target > 0 else 0
    f1, f2 = st.columns(2)
    f1.metric("FIRE 目标金额 (25倍年支)", f"¥{int(fire_target):,}")
    f1.write(f"目前达成率：{fire_prog*100:.2f}%")
    f1.progress(min(fire_prog, 1.0))
    f2.info(f"💡 **逻辑：** 达到 ¥{int(fire_target):,} 后，理论上你每年提取 4% 的资产即可覆盖全家全年开销 ¥{int(total_exp*12):,}，实现财务自由。")
    
    st.divider()
    st.subheader("📈 未来 20 年负债递减投影")
    proj = [{"月": m, "房贷": float(m_seq[m]) if m < len(m_seq) else 0.0, "车贷": float(c_l) if m < 60 else 0.0, "固定": float(living+other)} for m in range(240)]
    st.plotly_chart(px.area(pd.DataFrame(proj), x="月", y=["房贷", "车贷", "固定"]), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞")
    
    # 新增点：文字说明
    st.markdown("""
    ### 📌 什么是“无感支出”？
    财务学中著名的**“拿铁因子”**理论指出：生活中那些看似不起眼的微小开销（如每日奶茶、随手打车、自动续费的会员），在时间长河中会通过**复利效应**演变成巨大的财务黑洞。
    
    **💡 这个页面想告诉你：**
    如果你能审视这些“无感”的财务摩擦，将它们转化为资产投资，你的人生进度条可能会提前 3-5 年达成终极目标。
    """)
    
    daily = st.number_input("每日‘无感’开销 (咖啡/零食/打车)", value=50.0)
    y = st.slider("持续累积年数", 1, 30, 10)
    total = daily * 365 * y
    st.error(f"警惕：{y}年后，这些碎碎碎的支出将累计吞噬 ¥{total:,}。")
    st.write(f"这笔钱足以让你提前偿还约 **{int(total/m_p*100) if m_p>0 else 0}%** 的房贷本金。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("当前投资资产总额", value=asset_total)
    roi = st.slider("预期年化收益率 (%)", 0, 15, 7)
    m_roi = (asset * roi / 100) / 12
    st.metric("被动月收益", f"¥{int(m_roi):,}")
    cov = (m_roi / curr_m * 100) if curr_m > 0 else 100
    st.write(f"### 🎯 房贷覆盖率: {cov:.1f}%")
    st.progress(min(cov/100, 1.0))