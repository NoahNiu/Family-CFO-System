import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 页面配置 ---
st.set_page_config(page_title="Balance & Future Pro V15.1", layout="wide")

# --- 核心逻辑：密码检查 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.title("🔒 Balance & Future")
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

# --- 计算引擎 ---
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
        return {"net": float(gross - deduct - tax + gig), "fund": float(base_val * p_rate)}

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
st.sidebar.title("🚀 战略配置中心")

with st.sidebar.expander("👤 成员与梦想配置", expanded=False):
    n_a = st.text_input("我的称呼", "Jim")
    n_b = st.text_input("队友称呼", "队友")
    dream_dest = st.text_input("梦想目的地", "马尔代夫")
    dream_cost = st.number_input("预计人均花费", value=15000.0)
    travel_num = st.number_input("出行人数", value=2)

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    st.write(f"**{n_a}**")
    a_g = st.number_input(f"{n_a}月薪", value=26000.0)
    a_gig = st.number_input(f"{n_a}副业月入", value=0.0, key="a_gig_a")
    a_h = st.number_input(f"{n_a}月均工时", value=176)
    
    st.write("---")
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}月薪", value=18000.0)
    b_gig = st.number_input(f"{n_b}副业月入", value=0.0, key="b_gig_a")
    b_h = st.number_input(f"{n_b}月均工时", value=176) # 修复点：找回 b_h
    
    pf_pct = st.slider("公积金比例(%)", 5, 12, 5) / 100
    m_p = st.number_input("房贷本金", value=400000.0)
    m_r = st.number_input("房贷利率(%)", value=3.2)
    m_y = st.number_input("还款年限", value=30)
    asset_total = st.number_input("当前总资产", value=600000.0)
    c_l = st.number_input("车贷月供", value=2000.0)
    living = st.number_input("基础生活费", value=6000.0)
    other = st.number_input("杂项开支", value=0.0)

# --- 平行时空 B ---
st.sidebar.markdown("---")
show_b = st.sidebar.toggle("开启【平行时空 B】对比")
if show_b:
    with st.sidebar.expander("✨ 方案 B：变量预测", expanded=True):
        a_g_b = st.number_input(f"{n_a}预期月薪(B)", value=a_g + 5000)
        living_b = st.number_input("预期生活费(B)", value=living)
        purchase_b = st.number_input("预期大额支出(B)", value=0.0)
else:
    a_g_b, living_b, purchase_b = a_g, living, 0

# --- 执行计算 ---
data_a = run_strategic_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, "全额缴纳", "全额缴纳", pf_pct)
data_b = run_strategic_calc(a_g_b, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living_b, other + purchase_b/12, "全额缴纳", "全额缴纳", pf_pct)

# --- 页面内容 ---
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

if view == "🏠 Balance 看板":
    # 健康分逻辑
    save_rate = data_a['savings'] / data_a['total_net'] if data_a['total_net'] > 0 else 0
    debt_ratio = (data_a['total_exp'] - living) / data_a['total_net'] if data_a['total_net'] > 0 else 1
    moat_months = asset_total / data_a['total_exp'] if data_a['total_exp'] > 0 else 0
    health_score = (min(save_rate/0.4, 1)*40) + (max(0, 1-debt_ratio/0.6)*30) + (min(moat_months/12, 1)*30)
    
    st.title(f"📊 Balance & Future | 健康分：{int(health_score)}")
    st.progress(health_score/100)
    
    score_color = "rgba(16, 185, 129, 0.2)" if health_score > 75 else "rgba(255, 191, 0, 0.2)" if health_score > 55 else "rgba(239, 68, 68, 0.2)"
    st.markdown(f"<style>[data-testid='stMetric']:nth-child(3) {{ background-color: {score_color}; }}</style>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总到手现金(A)", f"¥{int(data_a['total_net']):,}")
    col2.metric("总月支出(A)", f"¥{int(data_a['total_exp']):,}")
    col3.metric("月度净结余(A)", f"¥{int(data_a['savings']):,}", delta=f"{int(save_rate*100)}% 储蓄率")
    
    if 'act' not in st.session_state: st.session_state.act = n_a
    # 修复点：正确调用侧边栏定义的变量
    active_hourly = (a_g + a_gig)/a_h if st.session_state.act == n_a else (b_g + b_gig)/b_h
    col4.metric(f"{st.session_state.act} 实时时薪", f"¥{active_hourly:.1f}")
    
    st.info(f"💡 **公积金抵消感：** 每月公积金对冲了房贷月供的 **{int(((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2)/data_a['curr_m']*100) if data_a['curr_m']>0 else 100}%**。")

    st.divider()
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        who = st.selectbox("谁来买单？", [n_a, n_b], key="act")
        item = st.text_input("心仪商品/梦想支出", "新智能手机")
        price = st.number_input("价格(元)", value=6000.0)
    with l2:
        h = float(price / active_hourly) if active_hourly > 0 else 0
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

# --- 其他页面逻辑保持不变 ---
elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变与 FIRE 审计")
    fire_mode = st.radio("FIRE 目标计算方式", ["25倍年支原则", "自定义目标金额"], horizontal=True)
    target_a = data_a['total_exp'] * 12 * 25 if fire_mode == "25倍年支原则" else st.number_input("自定义目标", value=5000000.0)
    st.metric("方案 A FIRE 进度", f"¥{int(target_a):,}", delta=f"{asset_total/target_a*100:.1f}%")
    st.progress(min(asset_total/target_a, 1.0))
    st.divider()
    proj_a = [{"月": m, "方案": "方案 A", "月支出": data_a['m_seq'][m] if m < len(data_a['m_seq']) else 0 + c_l + living} for m in range(120)]
    if show_b:
        proj_b = [{"月": m, "方案": "方案 B", "月支出": data_b['m_seq'][m] if m < len(data_b['m_seq']) else 0 + c_l + living_b} for m in range(120)]
        st.plotly_chart(px.line(pd.DataFrame(proj_a + proj_b), x="月", y="月支出", color="方案"), use_container_width=True)
    else:
        st.plotly_chart(px.area(pd.DataFrame(proj_a), x="月", y="月支出"), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制断头台")
    if 'subs' not in st.session_state:
        st.session_state.subs = pd.DataFrame([{"项目": "视频会员", "月费": 35.0, "状态": True}, {"项目": "云空间", "月费": 21.0, "状态": True}])
    edited_df = st.data_editor(st.session_state.subs, num_rows="dynamic")
    monthly_sub = edited_df[edited_df["状态"] == True]["月费"].sum()
    daily = st.number_input("每日其他‘无感’开销", value=50.0)
    total_bh = (daily * 365 + monthly_sub * 12) * 10
    st.error(f"😱 10 年累计消耗 ¥{total_bh:,.0f}，相当于你奋斗了 **{total_bh/active_hourly:.1f} 小时**。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    roi = st.slider("预期收益率 (%)", 0, 15, 7)
    m_roi = (asset_total * roi / 100) / 12
    st.metric("被动收益", f"¥{int(m_roi):,}")
    cov = (m_roi / data_a['curr_m'] * 100) if data_a['curr_m'] > 0 else 100
    st.progress(min(cov/100, 1.0))