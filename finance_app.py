import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置与安全门禁 ---
st.set_page_config(page_title="Balance & Future Pro V17.1", layout="wide")

# 建立数据库连接 (确保已配置 Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

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

# --- 2. 云端数据调度中心 ---
@st.cache_data(ttl=0)
def load_cloud_config():
    try:
        df = conn.read(worksheet="Global_Config", usecols=[0, 1])
        df = df.dropna(subset=['Parameter'])
        return pd.Series(df.Value.values, index=df.Parameter).to_dict()
    except:
        return {}

if 'config' not in st.session_state:
    st.session_state.config = load_cloud_config()

def get_cfg(key, default):
    val = st.session_state.config.get(key, default)
    if pd.isna(val) or val == "": return default
    if isinstance(default, float): return float(val)
    if isinstance(default, int): return int(float(val))
    return str(val)

# --- 3. 战略计算引擎 ---
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
    m = int(m_y * 12); mr = m_r / 100 / 12; mp = m_p / m if m > 0 else 0
    m_seq = [float(mp + (m_p - i * mp) * mr) for i in range(m)] if m > 0 else [0.0]
    total_net = res_a['net'] + res_b['net']
    curr_m = m_seq[0] if m_seq else 0.0
    total_exp = curr_m + c_l + living + other
    return {"total_net": total_net, "total_exp": total_exp, "savings": total_net - total_exp, "m_seq": m_seq, "res_a": res_a, "res_b": res_b, "curr_m": curr_m}

# --- 4. 侧边栏：战略配置中心 (重新排版) ---
st.sidebar.title("🚀 战略配置中心")

# A. 基础参数展开
with st.sidebar.expander("👤 成员与梦想配置", expanded=False):
    n_a = st.text_input("我的称呼", value=get_cfg("n_a", "Jim"))
    n_b = st.text_input("队友称呼", value=get_cfg("n_b", "队友"))
    dream_dest = st.text_input("梦想目的地", value=get_cfg("dream_dest", "马尔代夫"))
    dream_cost = st.number_input("预计人均花费", value=get_cfg("dream_cost", 15000.0))
    travel_num = st.number_input("出行人数", value=get_cfg("travel_num", 2))

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    st.write(f"**{n_a}**")
    a_g = st.number_input(f"{n_a}主业月薪", value=get_cfg("a_g", 26000.0))
    a_gig = st.number_input(f"{n_a}副业收入", value=get_cfg("a_gig", 0.0), key="a_gig_sidebar")
    a_m = st.selectbox(f"{n_a}缴纳基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("a_m", "全额缴纳")=="全额缴纳" else 1, key="a_m_sidebar")
    a_h = st.number_input(f"{n_a}月均工时", value=get_cfg("a_h", 176))
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}主业月薪", value=get_cfg("b_g", 18000.0))
    b_gig = st.number_input(f"{n_b}副业收入", value=get_cfg("b_gig", 0.0), key="b_gig_sidebar")
    b_m = st.selectbox(f"{n_b}缴纳基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("b_m", "全额缴纳")=="全额缴纳" else 1, key="b_m_sidebar")
    b_h = st.number_input(f"{n_b}月均工时", value=get_cfg("b_h", 176))
    pf_pct = st.slider("公积金比例(%)", 5, 12, int(get_cfg("pf_pct", 0.05)*100)) / 100
    st.write("---")
    m_p = st.number_input("房贷本金", value=get_cfg("m_p", 400000.0))
    m_r = st.number_input("房贷利率(%)", value=get_cfg("m_r", 3.2))
    m_y = st.number_input("房贷年限", value=get_cfg("m_y", 30))
    asset_total = st.number_input("当前总资产", value=get_cfg("asset_total", 600000.0))
    c_l = st.number_input("每月车贷", value=get_cfg("c_l", 2000.0))
    c_y = st.number_input("车贷剩余年限", value=get_cfg("c_y", 5))
    living = st.number_input("基础生活费", value=get_cfg("living", 6000.0))
    other = st.number_input("其他杂项", value=get_cfg("other", 0.0))

# B. 导航菜单
st.sidebar.divider()
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

# C. 平行时空
st.sidebar.divider()
show_b = st.sidebar.toggle("开启【平行时空 B】对比")
if show_b:
    with st.sidebar.expander("✨ 方案 B 预测", expanded=True):
        a_g_b = st.number_input(f"{n_a}预期月薪(B)", value=a_g + 5000)
        a_m_b = st.selectbox(f"{n_a}缴纳基数(B)", ["全额缴纳", "最低标准(2360)"], key="a_m_b")
        b_g_b = st.number_input(f"{n_b}预期月薪(B)", value=b_g)
        b_m_b = st.selectbox(f"{n_b}缴纳基数(B)", ["全额缴纳", "最低标准(2360)"], key="b_m_b")
        living_b = st.number_input("预期生活费(B)", value=living)
        purchase_b = st.number_input("预期年度大额开销", value=0.0)
else:
    a_g_b, a_m_b, b_g_b, b_m_b, living_b, purchase_b = a_g, a_m, b_g, b_m, living, 0

# D. 💾 置底保存按钮
st.sidebar.divider()
if st.sidebar.button("💾 全量保存至云端 (Google Drive)"):
    new_cfg = {
        "n_a": n_a, "n_b": n_b, "dream_dest": dream_dest, "dream_cost": dream_cost, "travel_num": travel_num,
        "a_g": a_g, "a_gig": a_gig, "a_m": a_m, "a_h": a_h, "b_g": b_g, "b_gig": b_gig, "b_m": b_m, "b_h": b_h,
        "pf_pct": pf_pct, "m_p": m_p, "m_r": m_r, "m_y": m_y, "asset_total": asset_total, 
        "c_l": c_l, "c_y": c_y, "living": living, "other": other
    }
    df_save = pd.DataFrame(list(new_cfg.items()), columns=['Parameter', 'Value'])
    try:
        conn.update(worksheet="Global_Config", data=df_save)
        st.session_state.config = new_cfg
        st.sidebar.success("✅ 参数已永久同步至云端！")
    except Exception as e:
        st.sidebar.error(f"保存失败: {e}")

# --- 5. 执行核心计算 ---
data_a = run_strategic_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, a_m, b_m, pf_pct)
data_b = run_strategic_calc(a_g_b, a_gig, b_g_b, b_gig, m_p, m_r, m_y, c_l, living_b, other + purchase_b/12, a_m_b, b_m_b, pf_pct)

if 'act_mem' not in st.session_state: st.session_state.act_mem = n_a
active_hourly = (a_g + a_gig)/a_h if st.session_state.act_mem == n_a else (b_g + b_gig)/b_h

# --- 6. 页面渲染 ---
if view == "🏠 Balance 看板":
    save_rate = data_a['savings'] / data_a['total_net'] if data_a['total_net'] > 0 else 0
    debt_ratio = (data_a['total_exp'] - living) / data_a['total_net'] if data_a['total_net'] > 0 else 1
    moat_months = asset_total / data_a['total_exp'] if data_a['total_exp'] > 0 else 0
    h_score = (min(save_rate/0.4, 1)*40) + (max(0, 1-debt_ratio/0.6)*30) + (min(moat_months/12, 1)*30)
    
    st.title(f"📊 Balance & Future | 健康分：{int(h_score)}")
    st.progress(h_score/100)
    
    st.markdown(f"<style>[data-testid='stMetric']:nth-child(3) {{ background-color: rgba(16, 185, 129, 0.2); }}</style>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总到手(A)", f"¥{int(data_a['total_net']):,}")
    c2.metric("总月支(A)", f"¥{int(data_a['total_exp']):,}")
    c3.metric("月结余(A)", f"¥{int(data_a['savings']):,}", delta=f"{int(save_rate*100)}% 储蓄率")
    c4.metric(f"{st.session_state.act_mem} 时薪", f"¥{active_hourly:.1f}")
    
    st.info(f"💡 每月公积金对冲了房贷月供的 **{int(((data_a['res_a']['fund'] + data_a['res_b']['fund']) * 2)/data_a['curr_m']*100) if data_a['curr_m']>0 else 100}%**。")
    
    if data_a['savings'] > 0:
        st.success(f"🏖️ 每 **{(dream_cost * travel_num)/data_a['savings']:.1f}** 个月可全款去一次{dream_dest}。")

    st.divider()
    st.subheader("🔍 消费工时透视")
    l1, l2 = st.columns([1, 2])
    with l1:
        st.selectbox("谁来买单？", [n_a, n_b], key="act_mem")
        item = st.text_input("心仪商品", "新智能手机")
        price = st.number_input("价格(元)", value=6000.0)
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
        if gap >= 0: st.success(f"单薪仍可结余 ¥{int(gap):,}")
        else: st.error(f"每月缺口 ¥{int(abs(gap)):,}")
    with cr:
        dream = st.text_input("下一个大件", "换一辆新车")
        dp = st.number_input("金额 (元)", value=300000.0)
        if data_a['savings'] > 0: st.warning(f"达成还需 **{dp / data_a['savings']:.1f}** 个月。")

    st.divider()
    exp_df = pd.DataFrame({"项目": ["房贷", "车贷", "生活费", "杂项", f"{n_a}税费", f"{n_b}税费"], "金额": [data_a['curr_m'], c_l, living, other, data_a['res_a']['tax_ins'], data_a['res_b']['tax_ins']]})
    st.plotly_chart(px.bar(exp_df, x="项目", y="金额", color="项目", text_auto='.0f', template="plotly_white"), use_container_width=True)

elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变与 FIRE 审计")
    f_mode = st.radio("FIRE 计算方式", ["25倍年支原则", "自定义目标金额"], horizontal=True)
    ta = data_a['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else st.number_input("自定义目标", value=5000000.0)
    tb = data_b['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else ta
    f1, f2 = st.columns(2)
    f1.metric("方案 A 目标", f"¥{int(ta):,}", delta=f"{asset_total/ta*100:.1f}% 达成")
    f1.progress(min(asset_total/ta, 1.0))
    if show_b:
        f2.metric("方案 B 目标", f"¥{int(tb):,}", delta=f"{asset_total/tb*100:.1f}% 达成")
        f2.progress(min(asset_total/tb, 1.0))
    st.info(f"💡 目前资产足以支撑约 **{int(asset_total/(data_a['total_exp']*12)) if data_a['total_exp']>0 else 0}** 年的生活。")
    st.divider()
    cy_m = int(c_y * 12)
    p_a = [{"月": m, "房贷": float(data_a['m_seq'][m]) if m < len(data_a['m_seq']) else 0.0, "车贷": float(c_l) if m < cy_m else 0.0, "固定": float(living+other)} for m in range(240)]
    if show_b:
        pb_f = [{"月": m, "方案": "B 总支出", "金额": (data_b['m_seq'][m] if m < len(data_b['m_seq']) else 0.0) + (c_l if m < cy_m else 0.0) + living_b + other + purchase_b/12} for m in range(240)]
        pa_f = [{"月": p["月"], "方案": "A 总支出", "金额": p["房贷"] + p["车贷"] + p["固定"]} for p in p_a]
        st.plotly_chart(px.line(pd.DataFrame(pa_f + pb_f), x="月", y="金额", color="方案"), use_container_width=True)
    else:
        st.plotly_chart(px.area(pd.DataFrame(p_a), x="月", y=["房贷", "车贷", "固定"]), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制断头台")
    try:
        sub_data = conn.read(worksheet="Subscriptions", usecols=[0, 1, 2], ttl=0).dropna(how="all")
        sub_data['状态'] = sub_data['状态'].astype(bool)
    except:
        sub_data = pd.DataFrame([{"项目": "测试订阅", "月费": 35.0, "状态": True}])
    e_df = st.data_editor(sub_data, num_rows="dynamic", key="sub_editor")
    if st.button("💾 保存订阅更新至云端"):
        conn.update(worksheet="Subscriptions", data=e_df); st.success("✅ 订阅同步成功！")
    m_sub = e_df[e_df["状态"] == True]["月费"].sum()
    daily = st.number_input("每日其他开销", value=50.0)
    y = st.slider("持续年数", 1, 30, 10)
    tbh = (daily * 365 + m_sub * 12) * y
    st.error(f"😱 {y}年后累计消耗 ¥{tbh:,.0f}，相当于奋斗了 **{tbh/active_hourly:.1f} 小时**。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("当前投资资产", value=asset_total)
    roi = st.slider("收益率 (%)", 0, 15, 7)
    m_roi = (asset * roi / 100) / 12
    st.metric("被动月收", f"¥{int(m_roi):,}")
    cov = (m_roi / data_a['curr_m'] * 100) if data_a['curr_m'] > 0 else 100
    st.write(f"### 🎯 房贷覆盖率: {cov:.1f}%")
    st.progress(min(cov/100, 1.0))
