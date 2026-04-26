import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 页面配置与安全门禁 ---
st.set_page_config(page_title="Balance & Future Pro V16", layout="wide")

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

# --- 2. 战略计算引擎 ---
def run_strategic_calc(gross_a, gig_a, gross_b, gig_b, m_p, m_r, m_y, c_l, living, other, base_type_a, base_type_b, pf_rate):
    def get_net(gross, gig, base_type, p_rate):
        base_val = gross if base_type == "全额缴纳" else 2360
        deduct = base_val * (0.08 + 0.02 + 0.005 + p_rate)
        taxable = max(0, gross - deduct - 5000)
        # 阶梯税率
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

# --- 3. 侧边栏：全局战略配置 ---
st.sidebar.title("🚀 战略配置中心")

with st.sidebar.expander("👤 成员与梦想配置", expanded=False):
    n_a = st.text_input("我的称呼", "我")
    n_b = st.text_input("队友称呼", "队友")
    dream_dest = st.text_input("梦想目的地", "马尔代夫")
    dream_cost = st.number_input("预计人均花费", value=15000.0)
    travel_num = st.number_input("出行人数", value=2)

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    st.write(f"**{n_a}**")
    a_g = st.number_input(f"{n_a}主业月薪", value=26000.0)
    a_gig = st.number_input(f"{n_a}副业收入", value=0.0, key="a_gig_a")
    a_m = st.selectbox(f"{n_a}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="a_m_a")
    a_h = st.number_input(f"{n_a}月均工时", value=176)
    
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}主业月薪", value=18000.0)
    b_gig = st.number_input(f"{n_b}副业收入", value=0.0, key="b_gig_a")
    b_m = st.selectbox(f"{n_b}缴纳基数", ["全额缴纳", "最低标准(2360)"], key="b_m_a")
    b_h = st.number_input(f"{n_b}月均工时", value=176)
    
    pf_pct = st.slider("公积金比例(%)", 5, 12, 5) / 100
    st.write("---")
    m_p = st.number_input("房贷本金", value=400000.0)
    m_r = st.number_input("房贷利率(%)", value=3.2)
    m_y = st.number_input("房贷年限", value=30)
    asset_total = st.number_input("当前总资产", value=600000.0)
    c_l = st.number_input("每月车贷", value=2000.0)
    c_y = st.number_input("车贷剩余年数", value=5, min_value=0)
    living = st.number_input("基础生活费", value=6000.0)
    other = st.number_input("其他杂项开支", value=0.0)

st.sidebar.markdown("---")
show_b = st.sidebar.toggle("开启【平行时空 B】对比")
if show_b:
    with st.sidebar.expander("✨ 方案 B：变量预测", expanded=True):
        a_g_b = st.number_input(f"{n_a}预期月薪(B)", value=a_g + 5000)
        a_m_b = st.selectbox(f"{n_a}缴纳基数(B)", ["全额缴纳", "最低标准(2360)"], key="a_m_b")
        b_g_b = st.number_input(f"{n_b}预期月薪(B)", value=b_g)
        b_m_b = st.selectbox(f"{n_b}缴纳基数(B)", ["全额缴纳", "最低标准(2360)"], key="b_m_b")
        living_b = st.number_input("预期生活费(B)", value=living)
        purchase_b = st.number_input("预期年度大额开销", value=0.0)
else:
    a_g_b, a_m_b, b_g_b, b_m_b, living_b, purchase_b = a_g, a_m, b_g, b_m, living, 0

# --- 4. 执行核心计算 ---
data_a = run_strategic_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, a_m, b_m, pf_pct)
data_b = run_strategic_calc(a_g_b, a_gig, b_g_b, b_gig, m_p, m_r, m_y, c_l, living_b, other + purchase_b/12, a_m_b, b_m_b, pf_pct)

if 'act_mem' not in st.session_state: st.session_state.act_mem = n_a
active_hourly = (a_g + a_gig)/a_h if st.session_state.act_mem == n_a else (b_g + b_gig)/b_h

# --- 5. 页面路由 ---
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

if view == "🏠 Balance 看板":
    save_rate = data_a['savings'] / data_a['total_net'] if data_a['total_net'] > 0 else 0
    debt_ratio = (data_a['total_exp'] - living) / data_a['total_net'] if data_a['total_net'] > 0 else 1
    moat_months = asset_total / data_a['total_exp'] if data_a['total_exp'] > 0 else 0
    h_score = (min(save_rate/0.4, 1)*40) + (max(0, 1-debt_ratio/0.6)*30) + (min(moat_months/12, 1)*30)
    
    st.title(f"📊 Balance & Future | 家庭财务健康分：{int(h_score)}")
    st.progress(h_score/100)
    
    s_col = "rgba(16, 185, 129, 0.2)" if h_score > 75 else "rgba(255, 191, 0, 0.2)" if h_score > 55 else "rgba(239, 68, 68, 0.2)"
    st.markdown(f"<style>[data-testid='stMetric']:nth-child(3) {{ background-color: {s_col}; }}</style>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总到手现金(A)", f"¥{int(data_a['total_net']):,}")
    c2.metric("总月支出(A)", f"¥{int(data_a['total_exp']):,}")
    c3.metric("月度净结余(A)", f"¥{int(data_a['savings']):,}", delta=f"{int(save_rate*100)}% 储蓄率")
    c4.metric(f"{st.session_state.act_mem} 实时时薪", f"¥{active_hourly:.1f}")
    
    st.info(f"💡 **公积金抵消感增强：** 每月公积金入账 ¥{int((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2):,}，已对冲了房贷月供的 **{int(((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2)/data_a['curr_m']*100) if data_a['curr_m']>0 else 100}%**。")
    
    if data_a['savings'] > 0:
        t_cost = dream_cost * travel_num
        st.success(f"🏖️ **家庭旅行自由指数：** 按目前结余，每 **{t_cost/data_a['savings']:.1f}** 个月可全款去一次{dream_dest}。")

    st.divider()
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        st.selectbox("谁来买单？", [n_a, n_b], key="act_mem")
        item = st.text_input("心仪商品/梦想支出", "新智能手机")
        price = st.number_input("商品价格(元)", value=6000.0)
    with l2:
        h = float(price / active_hourly) if active_hourly > 0 else 0
        st.write(f"购买 **{item}** 相当于消耗 **{st.session_state.act_mem}** 约 **{h:.1f} 小时** 的奋斗成果。")
        st.progress(min(h/176, 1.0))

    st.divider()
    st.subheader("🛡️ 家庭护城河测试")
    cl, cr = st.columns(2)
    with cl:
        loss = st.radio("风险模拟：如果谁暂时失去收入？", [f"{n_a}失业", f"{n_b}失业"])
        survive = data_a['res_b']['net'] if loss == f"{n_a}失业" else data_a['res_a']['net']
        gap = survive - data_a['total_exp']
        if gap >= 0: st.success(f"护城河稳固：单薪仍可结余 ¥{int(gap):,}")
        else: st.error(f"护城河告急：每月缺口 ¥{int(abs(gap)):,}")
    with cr:
        dream = st.text_input("下一个大件梦想", "换一辆新车")
        d_p = st.number_input("梦想金额 (元)", value=300000.0)
        if data_a['savings'] > 0: st.warning(f"达成 **{dream}** 还需 **{d_p / data_a['savings']:.1f}** 个月。")

    st.divider()
    st.subheader("🍲 家庭支出精细化构成 (方案 A)")
    exp_df = pd.DataFrame({
        "项目": ["房贷", "车贷", "生活费", "杂项", f"{n_a}税费社保", f"{n_b}税费社保"],
        "金额": [data_a['curr_m'], c_l, living, other, data_a['res_a']['tax_ins'], data_a['res_b']['tax_ins']]
    })
    st.plotly_chart(px.bar(exp_df, x="项目", y="金额", color="项目", text_auto='.0f', template="plotly_white"), use_container_width=True)

elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变与 FIRE 审计")
    st.subheader("🔥 FIRE 退休进度（对比模式）")
    f_mode = st.radio("FIRE 目标计算方式", ["25倍年支原则", "自定义目标金额"], horizontal=True)
    t_a = data_a['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else st.number_input("自定义目标", value=5000000.0)
    t_b = data_b['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else t_a
    
    f1, f2 = st.columns(2)
    f1.metric("方案 A 目标", f"¥{int(t_a):,}", delta=f"{asset_total/t_a*100:.1f}% 达成")
    f1.progress(min(asset_total/t_a, 1.0))
    if show_b:
        f2.metric("方案 B 目标", f"¥{int(t_b):,}", delta=f"{asset_total/t_b*100:.1f}% 达成")
        f2.progress(min(asset_total/t_b, 1.0))
    
    st.info(f"💡 **FIRE 逻辑：** 达到 ¥{int(t_a):,} 后，理论上每年提取 4% 的资产即可覆盖全家全年开销（基于 25 倍原则）。目前的资产足以支撑约 **{int(asset_total/(data_a['total_exp']*12)) if data_a['total_exp']>0 else 0}** 年的生活。")
            
    st.divider()
    st.subheader("📈 20 年现金流博弈对比")
    
    c_y_months = int(c_y * 12)
    p_a = [{"月": m, "房贷": float(data_a['m_seq'][m]) if m < len(data_a['m_seq']) else 0.0, "车贷": float(c_l) if m < c_y_months else 0.0, "固定": float(living+other)} for m in range(240)]
    
    if show_b:
        p_b_flat = [{"月": m, "方案": "方案 B 总支出", "金额": (data_b['m_seq'][m] if m < len(data_b['m_seq']) else 0.0) + (c_l if m < c_y_months else 0.0) + living_b + other + purchase_b/12} for m in range(240)]
        # 修复了这里的 'm'，改为了 p["月"]，防止报错
        p_a_flat = [{"月": p["月"], "方案": "方案 A 总支出", "金额": p["房贷"] + p["车贷"] + p["固定"]} for p in p_a]
        st.plotly_chart(px.line(pd.DataFrame(p_a_flat + p_b_flat), x="月", y="金额", color="方案"), use_container_width=True)
    else:
        st.plotly_chart(px.area(pd.DataFrame(p_a), x="月", y=["房贷", "车贷", "固定"]), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制断头台")
    st.markdown("### 📌 什么是“无感支出”？\n财务学中著名的**“拿铁因子”**理论指出：那些微小的、自动续费的开销，在复利下会演变成巨大的黑洞。")
    
    st.subheader("✂️ 订阅制清单管理")
    if 'subs' not in st.session_state:
        st.session_state.subs = pd.DataFrame([{"项目": "视频会员", "月费": 35.0, "状态": True}, {"项目": "网盘", "月费": 21.0, "状态": True}])
    
    e_df = st.data_editor(st.session_state.subs, num_rows="dynamic")
    m_sub = e_df[e_df["状态"] == True]["月费"].sum()
    daily = st.number_input("每日其他‘无感’开销", value=50.0)
    y = st.slider("持续累积年数", 1, 30, 10)
    t_bh = (daily * 365 + m_sub * 12) * y
    st.error(f"😱 **断头台报告：** {y}年后累计消耗 ¥{t_bh:,.0f}，相当于你奋斗了 **{t_bh/active_hourly:.1f} 小时**。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("当前投资总资产", value=asset_total)
    roi = st.slider("年化收益率 (%)", 0, 15, 7)
    m_roi = (asset * roi / 100) / 12
    st.metric("被动月收益", f"¥{int(m_roi):,}")
    cov = (m_roi / data_a['curr_m'] * 100) if data_a['curr_m'] > 0 else 100
    st.write(f"### 🎯 房贷覆盖率: {cov:.1f}%")
    st.progress(min(cov/100, 1.0))