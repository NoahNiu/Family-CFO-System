import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 页面配置 ---
st.set_page_config(page_title="Balance & Future Pro", layout="wide")

# --- 锦囊一：密码门禁逻辑 ---
def check_password():
    """从云端私密设置中读取密码"""
    INTERNAL_PASSWORD = st.secrets["password"] 

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.title("🔒 Balance & Future")
            st.write("这是一个私密的家庭财务系统，请证明你是自己人。")
            pwd = st.text_input("请输入家庭通行码：", type="password")
            if st.button("进入系统"):
                if pwd == INTERNAL_PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ 暗号不对，请联系 Jim 确认。")
        return False
    return True

# 执行密码检查
if not check_password():
    st.stop() # 密码没过，后面的代码统统不运行

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

# --- 侧边栏控制塔 ---
st.sidebar.title("🚀 战略配置中心")

with st.sidebar.expander("👤 成员名称自定义", expanded=True):
    n_a = st.text_input("我的称呼", "我")
    n_b = st.text_input("队友称呼", "队友")

with st.sidebar.expander("💰 收入与副业配置", expanded=True):
    st.write(f"**{n_a}**")
    # 建议部署时将以下默认值改为 0，保护隐私
    a_g = st.number_input(f"{n_a}主业税前", value=20000.0, step=500.0, min_value=0.0)
    a_gig = st.number_input(f"{n_a}兼职/副业月入", value=0.0, step=500.0, min_value=0.0)
    a_m = st.selectbox(f"{n_a}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="a_ms")
    a_h = st.number_input(f"{n_a}月均工时", value=176, min_value=1)
    
    st.write("---")
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}主业税前", value=15000.0, step=500.0, min_value=0.0)
    b_gig = st.number_input(f"{n_b}兼职/副业月入", value=0.0, step=500.0, min_value=0.0)
    b_m = st.selectbox(f"{n_b}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="b_ms")
    b_h = st.number_input(f"{n_b}月均工时", value=176, min_value=1)
    
    pf_pct = st.slider("公积金比例(%)", 5, 12, 5) / 100

with st.sidebar.expander("🏠 债务与开销", expanded=False):
    m_p = st.number_input("房贷本金总额", value=0.0, min_value=0.0)
    m_r = st.number_input("年利率(%)", value=3.2, format="%.2f", min_value=0.0)
    m_y = st.number_input("年限(年)", value=30, min_value=1)
    c_l = st.number_input("每月车贷月供", value=0.0, min_value=0.0)
    c_y = st.number_input("车贷剩余年数", value=0, min_value=0)
    living = st.number_input("家庭基础生活费", value=5000.0, min_value=0.0)
    other = st.number_input("其他支出/教育", value=0.0, min_value=0.0)

# --- 数据预计算 ---
res_a = calc_income(a_g, a_gig, a_g if a_m=="全额缴纳" else 2360, pf_pct)
res_b = calc_income(b_g, b_gig, b_g if b_m=="全额缴纳" else 2360, pf_pct)
m_seq = calc_mortgage(m_p, m_r, m_y)
curr_m = float(m_seq[0]) if m_seq else 0.0
total_net = res_a['net'] + res_b['net']
total_exp = curr_m + float(c_l) + float(living) + float(other)
savings = total_net - total_exp
total_pf = (res_a['fund'] + res_b['fund']) * 2 

# --- 样式与视觉逻辑 ---
health_color = "rgba(16, 185, 129, 0.2)" if savings > 0 else "rgba(239, 68, 68, 0.2)"
st.markdown(f"""
    <style>
    [data-testid="stMetric"] {{
        background-color: rgba(128, 128, 128, 0.1);
        padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }}
    [data-testid="stMetric"]:nth-child(3) {{ background-color: {health_color}; }}
    .stAppDeployButton {{ display: none !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 导航 ---
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

if view == "🏠 Balance 看板":
    st.title(f"📊 Balance & Future | 家庭财务战略系统")
    
    # 1. 4个大白块
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("家庭总到手现金", f"¥{int(total_net):,}")
    col2.metric("家庭总月支出", f"¥{int(total_exp):,}")
    col3.metric("本月净结余", f"¥{int(savings):,}", delta=f"{int(savings/total_net*100) if total_net>0 else 0}% 储蓄率")
    
    if 'active' not in st.session_state: st.session_state.active = n_a
    hourly = (a_g + a_gig)/a_h if st.session_state.active == n_a else (b_g + b_gig)/b_h
    col4.metric(f"{st.session_state.active} 实时时薪", f"¥{hourly:.1f}")
    
    st.info(f"💡 **公积金抵消感增强：** 每月有 ¥{int(total_pf):,} 自动对冲了房贷月供的 **{int(total_pf/curr_m*100) if curr_m>0 else 100}%**。")

    st.divider()

    # 2. 消费工时透视
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        who = st.selectbox("谁来买单？", [n_a, n_b], key="active")
        item = st.text_input("心仪商品", "新智能手机")
        price = st.number_input("价格(元)", value=6000.0, min_value=0.0)
    with l2:
        h = float(price / hourly) if hourly > 0 else 0
        st.success(f"购买 **{item}** 相当于消耗 **{who}** 约 **{h:.1f} 小时** 的奋斗成果。")
        st.progress(min(h/176, 1.0))

    st.divider()

    # 3. 家庭护城河测试 & 梦想达成度
    st.subheader("🛡️ 家庭护城河测试 & 🎯 梦想达成度")
    c_l_p, c_r_p = st.columns(2)
    with c_l_p:
        loss = st.radio("风险模拟：如果谁暂时失去收入？", [f"{n_a}失业", f"{n_b}失业"])
        survive = res_b['net'] if loss == f"{n_a}失业" else res_a['net']
        gap = survive - total_exp
        if gap >= 0: st.success(f"护城河稳固：单薪仍可结余 ¥{int(gap):,}")
        else: st.error(f"护城河告急：每月缺口 ¥{int(abs(gap)):,}")
    
    with c_r_p:
        dream_item = st.text_input("下一个大件梦想", "换一辆新车")
        dream_p = st.number_input("梦想金额 (元)", value=500000.0, min_value=0.0)
        if savings > 0:
            m_needed = dream_p / savings
            st.warning(f"达成 **{dream_item}** 还需 **{m_needed:.1f}** 个月。")
        else:
            st.error("当前无结余，梦想达成时间无限长。")

    st.divider()

    # 4. 家庭支出精细化构成
    st.subheader("🍲 家庭支出精细化构成")
    try:
        df_exp = pd.DataFrame({
            "项目": ["房贷", "车贷", "生活费", "杂项", f"{n_a}个税社保", f"{n_b}个税社保"],
            "金额": [float(curr_m), float(c_l), float(living), float(other), 
                    float(res_a['tax']+res_a['ins']), float(res_b['tax']+res_b['ins'])]
        })
        st.plotly_chart(px.bar(df_exp, x="项目", y="金额", color="项目", text_auto='.0f', template="plotly_white"), use_container_width=True)
    except:
        st.write("输入数据后显示图表...")

elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变长廊 (20年负债递减投影)")
    proj = [{"月": m, "房贷": float(m_seq[m]) if m < len(m_seq) else 0.0, "车贷": float(c_l) if m < c_y*12 else 0.0, "固定": float(living+other)} for m in range(240)]
    st.plotly_chart(px.area(pd.DataFrame(proj), x="月", y=["房贷", "车贷", "固定"]), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞")
    daily = st.number_input("每日‘无感’开销", value=50.0, min_value=0.0)
    y = st.slider("累积年数", 1, 30, 10)
    total = daily * 365 * y
    st.error(f"警惕：{y}年后，这些支出将吞噬 ¥{total:,}。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("家庭投资资产总额", value=600000.0, min_value=0.0)
    roi = st.slider("年化收益率 (%)", 0, 15, 7)
    m_roi = (asset * roi / 100) / 12
    st.metric("被动月收益", f"¥{int(m_roi):,}")
    cov = (m_roi / curr_m * 100) if curr_m > 0 else 100
    st.write(f"### 房贷覆盖率: {cov:.1f}%")
    st.progress(min(cov/100, 1.0))