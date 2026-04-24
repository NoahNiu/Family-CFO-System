import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 页面配置 ---
st.set_page_config(page_title="Balance & Future Pro V15", layout="wide")

# --- 密码门禁逻辑 (Secrets 安全模式) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.title("🔒 Balance & Future")
            st.write("这是一个私密的家庭财务系统。")
            pwd = st.text_input("请输入家庭通行码：", type="password")
            if st.button("进入系统"):
                if pwd == st.secrets["password"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ 暗号不对。")
        return False
    return True

if not check_password():
    st.stop()

# --- 核心计算引擎 ---
def run_strategic_calc(gross_a, gig_a, gross_b, gig_b, m_p, m_r, m_y, c_l, living, other, base_type_a, base_type_b, pf_rate):
    def get_net(gross, gig, base_type, p_rate):
        base_val = gross if base_type == "全额缴纳" else 2360
        deduct = base_val * (0.08 + 0.02 + 0.005 + p_rate)
        taxable = max(0, gross - deduct - 5000)
        if taxable <= 3000: tax = taxable * 0.03
        elif taxable <= 12000: tax = taxable * 0.1 - 210
        elif taxable <= 25000: tax = taxable * 0.2 - 1410
        elif taxable <= 35000: tax = taxable * 0.25 - 2660
        else: tax = taxable * 0.3 - 4410
        return {"net": float(gross - deduct - tax + gig), "fund": float(base_val * p_rate), "tax_ins": float(tax + deduct)}

    res_a = get_net(gross_a, gig_a, base_type_a, pf_rate)
    res_b = get_net(gross_b, gig_b, base_type_b, pf_rate)
    
    m = int(m_y * 12)
    mr = m_r / 100 / 12
    mp = m_p / m if m > 0 else 0
    m_seq = [float(mp + (m_p - i * mp) * mr) for i in range(m)] if m > 0 else [0.0]
    
    total_net = res_a['net'] + res_b['net']
    curr_m = m_seq[0] if m_seq else 0.0
    total_exp = curr_m + c_l + living + other
    return {
        "total_net": total_net, "total_exp": total_exp, "savings": total_net - total_exp,
        "m_seq": m_seq, "res_a": res_a, "res_b": res_b, "curr_m": curr_m
    }

# --- 侧边栏：战略配置中心 ---
st.sidebar.title("🚀 财务设置中心")

with st.sidebar.expander("👤 成员与旅行目标", expanded=False):
    n_a = st.text_input("我的称呼", "Jim")
    n_b = st.text_input("队友称呼", "队友")
    dream_dest = st.text_input("梦想目的地", "马尔代夫")
    dream_cost = st.number_input("预计人均花费", value=15000.0)
    travel_num = st.number_input("出行人数", value=2)

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    a_g = st.number_input(f"{n_a}主业税前", value=26000.0)
    a_gig = st.number_input(f"{n_a}副业收入", value=0.0)
    a_h = st.number_input(f"{n_a}月均工时", value=176)
    b_g = st.number_input(f"{n_b}主业税前", value=18000.0)
    b_gig = st.number_input(f"{n_b}副业收入", value=0.0)
    pf_pct = st.slider("公积金比例(%)", 5, 12, 5) / 100
    m_p = st.number_input("房贷本金", value=400000.0)
    m_r = st.number_input("房贷利率(%)", value=3.2)
    m_y = st.number_input("房贷年限", value=30)
    asset_total = st.number_input("当前总资产", value=600000.0)
    c_l = st.number_input("车贷月供", value=2000.0)
    living = st.number_input("基础生活费", value=6000.0)
    other = st.number_input("其他杂项", value=0.0)

# 💡 核心升级 1：平行时空模拟器
st.sidebar.markdown("---")
show_b = st.sidebar.toggle("开启【平行时空 B】对比")
if show_b:
    with st.sidebar.expander("✨ 方案 B：变量预测", expanded=True):
        st.write("设置与方案 A 的不同之处（如加薪或大笔开销）")
        a_g_b = st.number_input(f"{n_a}预期加薪后月薪", value=a_g + 5000)
        living_b = st.number_input("预期生活费变动", value=living)
        purchase_b = st.number_input("预期年度大额开销", value=0.0, help="例如明年买车计划，折算到每月")

# --- 执行计算 ---
data_a = run_strategic_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, "全额缴纳", "全额缴纳", pf_pct)
if show_b:
    data_b = run_strategic_calc(a_g_b, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living_b, other + purchase_b/12, "全额缴纳", "全额缴纳", pf_pct)
else:
    data_b = data_a

# --- 页面路由 ---
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

if view == "🏠 Balance 看板":
    # 💡 核心升级 2：家庭财务健康分
    save_rate = data_a['savings'] / data_a['total_net'] if data_a['total_net'] > 0 else 0
    debt_ratio = (data_a['total_exp'] - living) / data_a['total_net'] if data_a['total_net'] > 0 else 1
    moat_months = asset_total / data_a['total_exp'] if data_a['total_exp'] > 0 else 0
    health_score = (min(save_rate/0.4, 1)*40) + (max(0, 1-debt_ratio/0.6)*30) + (min(moat_months/12, 1)*30)
    
    st.title(f"📊 Balance & Future | 家庭财务健康分：{int(health_score)}")
    st.progress(health_score/100)
    
    # 动态磁贴颜色反馈
    score_color = "rgba(16, 185, 129, 0.2)" if health_score > 75 else "rgba(255, 191, 0, 0.2)" if health_score > 55 else "rgba(239, 68, 68, 0.2)"
    st.markdown(f"<style>[data-testid='stMetric']:nth-child(3) {{ background-color: {score_color}; }}</style>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("家庭到手现金(A)", f"¥{int(data_a['total_net']):,}")
    col2.metric("家庭总月支出(A)", f"¥{int(data_a['total_exp']):,}")
    col3.metric("本月净结余(A)", f"¥{int(data_a['savings']):,}", delta=f"{int(save_rate*100)}% 储蓄率")
    
    if 'act' not in st.session_state: st.session_state.act = n_a
    hourly = (a_g + a_gig)/a_h if st.session_state.act == n_a else (b_g + b_gig)/b_h
    col4.metric(f"{st.session_state.act} 实时时薪", f"¥{hourly:.1f}")
    
    st.info(f"💡 **公积金抵消感：** 每月入账 ¥{int((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2):,}，已对冲了房贷月供的 **{int(((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2)/data_a['curr_m']*100) if data_a['curr_m']>0 else 100}%**。")
    
    if data_a['savings'] > 0:
        travel_total = dream_cost * travel_num
        m_a = travel_total / data_a['savings']
        msg = f"🏖️ **家庭旅行自由指数：** 按方案 A，每 **{m_a:.1f}** 个月可全款去一次{dream_dest}。"
        if show_b and data_b['savings'] > 0:
            m_b = travel_total / data_b['savings']
            msg += f" 而在方案 B 下，仅需 **{m_b:.1f}** 个月！"
        st.success(msg)

    st.divider()
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        who = st.selectbox("谁来买单？", [n_a, n_b], key="act")
        item = st.text_input("心仪商品/梦想支出", "新智能手机")
        price = st.number_input("价格(元)", value=6000.0)
    with l2:
        h = float(price / hourly) if hourly > 0 else 0
        st.write(f"购买 **{item}** 相当于消耗 **{who}** 约 **{h:.1f} 小时** 的奋斗成果。")
        st.progress(min(h/176, 1.0))

    st.divider()
    st.subheader("🛡️ 家庭护城河测试")
    c_l_p, c_r_p = st.columns(2)
    with c_l_p:
        loss = st.radio("风险模拟：如果谁暂时失去收入？", [f"{n_a}失业", f"{n_b}失业"])
        survive = data_a['res_b']['net'] if loss == f"{n_a}失业" else data_a['res_a']['net']
        gap = survive - data_a['total_exp']
        if gap >= 0: st.success(f"护城河稳固：单薪仍可结余 ¥{int(gap):,}")
        else: st.error(f"护城河告急：每月缺口 ¥{int(abs(gap)):,}")
    with c_r_p:
        dream_item = st.text_input("下一个大件梦想", "换一辆新车")
        dream_p = st.number_input("梦想金额 (元)", value=300000.0)
        if data_a['savings'] > 0: st.warning(f"达成 **{dream_item}** 还需 **{dream_p / data_a['savings']:.1f}** 个月。")

elif view == "📈 资产演变长廊":
    st.title("⏳ 资产演变与 FIRE 进度")
    
    st.subheader("🔥 FIRE 退休进度（平行时空对比）")
    fire_mode = st.radio("FIRE 目标计算方式", ["25倍年支原则 (科学默认)", "自定义目标金额"], horizontal=True)
    
    target_a = data_a['total_exp'] * 12 * 25 if fire_mode == "25倍年支原则 (科学默认)" else st.number_input("自定义目标金额", value=5000000.0)
    target_b = data_b['total_exp'] * 12 * 25 if fire_mode == "25倍年支原则 (科学默认)" else target_a
    
    f1, f2 = st.columns(2)
    with f1:
        st.metric("方案 A 目标", f"¥{int(target_a):,}", delta=f"达成率 {asset_total/target_a*100:.1f}%")
        st.progress(min(asset_total/target_a, 1.0))
    with f2:
        if show_b:
            st.metric("方案 B 目标", f"¥{int(target_b):,}", delta=f"达成率 {asset_total/target_b*100:.1f}%")
            st.progress(min(asset_total/target_b, 1.0))
            
    st.divider()
    st.subheader("📈 20 年现金流博弈对比")
    proj_a = [{"月": m, "方案": "方案 A", "月支出": data_a['m_seq'][m] if m < len(data_a['m_seq']) else 0 + c_l + living} for m in range(120)]
    if show_b:
        proj_b = [{"月": m, "方案": "方案 B", "月支出": data_b['m_seq'][m] if m < len(data_b['m_seq']) else 0 + c_l + living_b} for m in range(120)]
        df_proj = pd.DataFrame(proj_a + proj_b)
        st.plotly_chart(px.line(df_proj, x="月", y="月支出", color="方案", title="支出演变对比趋势"), use_container_width=True)
    else:
        st.plotly_chart(px.area(pd.DataFrame(proj_a), x="月", y="月支出", title="资产演变投影"), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制产品")
    st.markdown("""
    ### 📌 什么是“无感支出”？
    财务学中著名的**“拿铁因子”**理论指出：生活中那些看似不起眼的微小开销（如每日奶茶、随手打车、自动续费的会员），在时间长河中会通过**复利效应**演变成巨大的财务黑洞。
    
    **💡 这个页面想告诉你：**
    如果你能审视这些“无感”的财务摩擦，将它们转化为资产投资，你的人生进度条可能会提前 3-5 年达成终极目标。
    """)
    
    # 💡 核心升级 3：订阅制断头台
    st.subheader("✂️ 订阅制清单管理（自定义）")
    if 'subs' not in st.session_state:
        st.session_state.subs = pd.DataFrame([
            {"项目名称": "视频/音乐会员", "月费": 35.0, "状态": True},
            {"项目名称": "云空间/网盘", "月费": 21.0, "状态": True},
            {"项目名称": "健身/外卖红包", "月费": 100.0, "状态": True}
        ])
    
    edited_df = st.data_editor(st.session_state.subs, num_rows="dynamic")
    monthly_sub = edited_df[edited_df["状态"] == True]["月费"].sum()
    
    daily = st.number_input("每日其他‘无感’开销 (咖啡/零食/打车)", value=50.0)
    y = st.slider("持续累积年数", 1, 30, 10)
    total_blackhole = (daily * 365 + monthly_sub * 12) * y
    
    st.error(f"😱 **断头台报告：** 加上这些订阅，{y}年后你将累计消耗 ¥{total_blackhole:,.0f}，相当于你奋斗了 **{total_blackhole/hourly:.1f} 小时**。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("当前投资资产总额", value=asset_total)
    roi = st.slider("预期年化收益率 (%)", 0, 15, 7)
    m_roi = (asset * roi / 100) / 12
    st.metric("被动月收益", f"¥{int(m_roi):,}")
    cov = (m_roi / data_a['curr_m'] * 100) if data_a['curr_m'] > 0 else 100
    st.write(f"### 🎯 房贷覆盖率: {cov:.1f}%")
    st.progress(min(cov/100, 1.0))