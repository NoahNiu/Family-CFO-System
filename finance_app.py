import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置与安全门禁 ---
st.set_page_config(page_title="Balance & Future Pro V18.1", layout="wide")

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
def load_cloud_config(profile_name):
    try:
        sheet_name = f"Config_{profile_name}"
        df = conn.read(worksheet=sheet_name, usecols=[0, 1, 2])
        df = df.dropna(subset=['Parameter'])
        val_dict = pd.Series(df.Value.values, index=df.Parameter).to_dict()
        memo_dict = pd.Series(df.备注.values, index=df.Parameter).to_dict()
        return {"values": val_dict, "memos": memo_dict}
    except Exception as e:
        return {"values": {}, "memos": {}}

st.sidebar.title("🚀 战略配置中心")
st.sidebar.markdown("### 📂 当前档案槽位")
active_profile = st.sidebar.selectbox(
    "切换云端存档 (互相独立)", 
    ["A", "B"], 
    format_func=lambda x: "存档 A (牛计划)" if x == "A" else "存档 B (贤计划)"
)

if st.session_state.get('current_profile') != active_profile:
    st.session_state.current_profile = active_profile
    st.session_state.full_config = load_cloud_config(active_profile)
    if 'sub_ed' in st.session_state:
        del st.session_state['sub_ed']
    st.rerun()

def get_cfg(key, default):
    val = st.session_state.full_config["values"].get(key, default)
    if pd.isna(val) or val == "": return default
    if isinstance(default, float): return float(val)
    if isinstance(default, int): return int(float(val))
    return str(val)

# --- 3. 战略计算引擎 ---
def run_calc(gross_a, gig_a, gross_b, gig_b, m_p, m_r, m_y, c_l, living, other, base_a, base_b, pf_rate):
    def get_net(gross, gig, b_type, p_rate):
        bv = gross if b_type == "全额缴纳" else 2360
        deduct = bv * (0.08 + 0.02 + 0.005 + p_rate)
        taxable = max(0, gross - deduct - 5000)
        if taxable <= 3000: tax = taxable * 0.03
        elif taxable <= 12000: tax = taxable * 0.1 - 210
        elif taxable <= 25000: tax = taxable * 0.2 - 1410
        elif taxable <= 35000: tax = taxable * 0.25 - 2660
        else: tax = taxable * 0.3 - 4410
        return {"net": float(gross - deduct - tax + gig), "fund": float(bv * p_rate), "tax_ins": float(tax + deduct)}

    res_a = get_net(gross_a, gig_a, base_a, pf_rate)
    res_b = get_net(gross_b, gig_b, base_b, pf_rate)
    m = int(m_y * 12); mr = m_r / 100 / 12; mp = m_p / m if m > 0 else 0
    m_seq = [float(mp + (m_p - i * mp) * mr) for i in range(m)] if m > 0 else [0.0]
    t_net = res_a['net'] + res_b['net']
    curr_m = m_seq[0] if m_seq else 0.0
    t_exp = curr_m + c_l + living + other
    return {"total_net": t_net, "total_exp": t_exp, "savings": t_net - t_exp, "m_seq": m_seq, "res_a": res_a, "res_b": res_b, "curr_m": curr_m}

# --- 4. 侧边栏：战略配置项 ---
st.sidebar.divider()
with st.sidebar.expander("👤 成员与梦想配置", expanded=False):
    n_a = st.text_input("我的称呼", value=get_cfg("n_a", "Jim"))
    n_b = st.text_input("队友称呼", value=get_cfg("n_b", "队友"))
    dream_dest = st.text_input("梦想目的地", value=get_cfg("dream_dest", "马尔代夫"))
    dream_cost = st.number_input("预计人均花费", value=get_cfg("dream_cost", 15000.0))
    travel_num = st.number_input("出行人数", value=get_cfg("travel_num", 2))

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    st.write(f"**{n_a}**")
    a_g = st.number_input(f"{n_a}主业月薪", value=get_cfg("a_g", 26000.0))
    a_gig = st.number_input(f"{n_a}副业月入", value=get_cfg("a_gig", 0.0))
    a_m = st.selectbox(f"{n_a}缴纳基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("a_m", "全额缴纳")=="全额缴纳" else 1)
    a_h = st.number_input(f"{n_a}月均工时", value=get_cfg("a_h", 176))
    st.write(f"**{n_b}**")
    b_g = st.number_input(f"{n_b}主业月薪", value=get_cfg("b_g", 18000.0))
    b_gig = st.number_input(f"{n_b}副业月入", value=get_cfg("b_gig", 0.0))
    b_m = st.selectbox(f"{n_b}缴纳基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("b_m", "全额缴纳")=="全额缴纳" else 1)
    b_h = st.number_input(f"{n_b}月均工时", value=get_cfg("b_h", 176))
    pf_pct = st.slider("公积金比例(%)", 5, 12, int(get_cfg("pf_pct", 0.05)*100)) / 100
    st.write("---")
    m_p = st.number_input("房贷本金", value=get_cfg("m_p", 400000.0))
    m_r = st.number_input("房贷利率(%)", value=get_cfg("m_r", 3.2))
    m_y = st.number_input("房贷年限", value=get_cfg("m_y", 30))
    asset_total = st.number_input("当前总资产", value=get_cfg("asset_total", 600000.0))
    c_l = st.number_input("车贷月供", value=get_cfg("c_l", 2000.0))
    c_y = st.number_input("车贷剩余年限", value=get_cfg("c_y", 5))
    living = st.number_input("基础生活费", value=get_cfg("living", 6000.0))
    other = st.number_input("其他杂项", value=get_cfg("other", 0.0))

st.sidebar.divider()
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

st.sidebar.divider()
show_b = st.sidebar.toggle("开启【平行时空 B】对比")
if show_b:
    with st.sidebar.expander("✨ 方案 B 预测", expanded=True):
        a_g_b = st.number_input(f"{n_a}预期月薪(B)", value=a_g + 5000)
        a_m_b = st.selectbox(f"{n_a}基数(B)", ["全额缴纳", "最低标准(2360)"], key="a_mb")
        b_g_b = st.number_input(f"{n_b}预期月薪(B)", value=b_g)
        b_m_b = st.selectbox(f"{n_b}基数(B)", ["全额缴纳", "最低标准(2360)"], key="b_mb")
        living_b = st.number_input("预期生活费(B)", value=living)
        purchase_b = st.number_input("预期大额支出", value=0.0)
else:
    a_g_b, a_m_b, b_g_b, b_m_b, living_b, purchase_b = a_g, a_m, b_g, b_m, living, 0

st.sidebar.divider()
if st.sidebar.button(f"💾 覆盖保存至【存档 {active_profile}】"):
    new_v = {"n_a": n_a, "n_b": n_b, "dream_dest": dream_dest, "dream_cost": dream_cost, "travel_num": travel_num, "a_g": a_g, "a_gig": a_gig, "a_m": a_m, "a_h": a_h, "b_g": b_g, "b_gig": b_gig, "b_m": b_m, "b_h": b_h, "pf_pct": pf_pct, "m_p": m_p, "m_r": m_r, "m_y": m_y, "asset_total": asset_total, "c_l": c_l, "c_y": c_y, "living": living, "other": other}
    save_data = [{"Parameter": k, "Value": v, "备注": st.session_state.full_config["memos"].get(k, "")} for k, v in new_v.items()]
    try:
        conn.update(worksheet=f"Config_{active_profile}", data=pd.DataFrame(save_data))
        st.session_state.full_config["values"] = new_v
        st.sidebar.success(f"✅ 全局参数已同步至存档 {active_profile}！")
    except Exception as e: st.sidebar.error(f"保存失败: {e}")

# --- 5. 核心计算逻辑执行 ---
data_a = run_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, a_m, b_m, pf_pct)
data_b = run_calc(a_g_b, a_gig, b_g_b, b_gig, m_p, m_r, m_y, c_l, living_b, other + purchase_b/12, a_m_b, b_m_b, pf_pct)

if 'act_m' not in st.session_state: st.session_state.act_m = n_a
# 维持全局变量给黑洞页面使用
active_hourly = (a_g + a_gig)/a_h if st.session_state.act_m == n_a else (b_g + b_gig)/b_h

# --- 6. 页面渲染 ---
if view == "🏠 Balance 看板":
    
    # 💡 核心新增：看板视角的自由切换
    if show_b:
        view_mode = st.radio("👀 选择看板全局视角：", ["⚖️ A/B 核心对决 (对比模式)", "📊 仅看方案 A (现实)", "🚀 仅看方案 B (预测)"], horizontal=True)
        st.divider()
    else:
        view_mode = "📊 仅看方案 A (现实)"

    if view_mode == "⚖️ A/B 核心对决 (对比模式)":
        st.title("⚖️ 平行时空核心指标对决")
        
        # 指标对比
        c1, c2, c3 = st.columns(3)
        c1.metric("家庭总到手 (方案 B)", f"¥{int(data_b['total_net']):,}", delta=f"较方案 A: {int(data_b['total_net'] - data_a['total_net']):,}")
        c2.metric("家庭总月支 (方案 B)", f"¥{int(data_b['total_exp']):,}", delta=f"较方案 A: {int(data_b['total_exp'] - data_a['total_exp']):,}", delta_color="inverse")
        c3.metric("月度净结余 (方案 B)", f"¥{int(data_b['savings']):,}", delta=f"较方案 A: {int(data_b['savings'] - data_a['savings']):,}")

        # 图形化结构对比
        st.subheader("📊 收入支出结构直观对比")
        comp_df = pd.DataFrame([
            {"方案": "方案 A (现实)", "核心指标": "1. 总月收入", "金额 (元)": data_a['total_net']},
            {"方案": "方案 B (预测)", "核心指标": "1. 总月收入", "金额 (元)": data_b['total_net']},
            {"方案": "方案 A (现实)", "核心指标": "2. 总月支出", "金额 (元)": data_a['total_exp']},
            {"方案": "方案 B (预测)", "核心指标": "2. 总月支出", "金额 (元)": data_b['total_exp']},
            {"方案": "方案 A (现实)", "核心指标": "3. 净结余", "金额 (元)": data_a['savings']},
            {"方案": "方案 B (预测)", "核心指标": "3. 净结余", "金额 (元)": data_b['savings']}
        ])
        fig = px.bar(comp_df, x="核心指标", y="金额 (元)", color="方案", barmode="group", text_auto='.0f', template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        # 旅行对比补充
        st.info(f"🏖️ **旅行自由度竞技：** 按方案 A 每 **{(dream_cost*travel_num)/data_a['savings']:.1f}** 个月去一次{dream_dest} 🆚 按方案 B 每 **{(dream_cost*travel_num)/data_b['savings']:.1f}** 个月去一次。")

    else:
        # 💡 核心不变：利用动态映射，0 代码冗余实现 B 方案独立渲染
        is_b = (view_mode == "🚀 仅看方案 B (预测)")
        act_d = data_b if is_b else data_a
        act_liv = living_b if is_b else living
        act_oth = other + purchase_b/12 if is_b else other
        act_ag = a_g_b if is_b else a_g
        act_bg = b_g_b if is_b else b_g
        label = "B" if is_b else "A"

        sr = act_d['savings'] / act_d['total_net'] if act_d['total_net'] > 0 else 0
        dr = (act_d['total_exp'] - act_liv) / act_d['total_net'] if act_d['total_net'] > 0 else 1
        moat = asset_total / act_d['total_exp'] if act_d['total_exp'] > 0 else 0
        score = (min(sr/0.4, 1)*40) + (max(0, 1-dr/0.6)*30) + (min(moat/12, 1)*30)
        
        st.title(f"📊 Balance & Future | 健康分 ({label})：{int(score)}")
        st.progress(score/100)
        st.markdown("<style>[data-testid='stMetric']:nth-child(3) { background-color: rgba(16, 185, 129, 0.2); }</style>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"总到手({label})", f"¥{int(act_d['total_net']):,}")
        c2.metric(f"总支出({label})", f"¥{int(act_d['total_exp']):,}")
        c3.metric(f"月结余({label})", f"¥{int(act_d['savings']):,}", delta=f"{int(sr*100)}% 储蓄率")
        
        # 局部时薪逻辑
        if 'act_m' not in st.session_state: st.session_state.act_m = n_a
        act_h_rate = (act_ag + a_gig)/a_h if st.session_state.act_m == n_a else (act_bg + b_gig)/b_h
        c4.metric(f"{st.session_state.act_m} 时薪", f"¥{act_h_rate:.1f}")
        
        st.info(f"💡 每月公积金对冲了房贷月供的 **{int(((act_d['res_a']['fund'] + act_d['res_b']['fund']) * 2)/act_d['curr_m']*100) if act_d['curr_m']>0 else 100}%**。")
        if act_d['savings'] > 0: st.success(f"🏖️ 每 **{(dream_cost*travel_num)/act_d['savings']:.1f}** 个月可全款去一次{dream_dest}。")

        st.divider()
        st.subheader("🔍 消费工时透视")
        l1, l2 = st.columns([1, 2])
        with l1:
            # 引入独立的 Key 防止切换时报错
            st.selectbox("谁来买单？", [n_a, n_b], key=f"act_m_{label}")
            item = st.text_input("心仪商品", "新智能手机", key=f"i_{label}")
            price = st.number_input("价格(元)", value=6000.0, key=f"p_{label}")
        with l2:
            curr_payer = st.session_state.get(f"act_m_{label}", n_a)
            h_rate = (act_ag + a_gig)/a_h if curr_payer == n_a else (act_bg + b_gig)/b_h
            h = float(price / h_rate) if h_rate > 0 else 0
            st.write(f"购买 **{item}** 相当于消耗 **{curr_payer}** 约 **{h:.1f} 小时** 的奋斗成果。")
            st.progress(min(h/176, 1.0))

        st.divider()
        st.subheader("🛡️ 家庭护城河测试")
        cl_p, cr_p = st.columns(2)
        with cl_p:
            loss = st.radio("风险模拟：如果谁暂时失去收入？", [f"{n_a}失业", f"{n_b}失业"], key=f"l_{label}")
            survive = act_d['res_b']['net'] if loss == f"{n_a}失业" else act_d['res_a']['net']
            gap = survive - act_d['total_exp']
            if gap >= 0: st.success(f"护城河稳固：单薪仍可结余 ¥{int(gap):,}")
            else: st.error(f"每月缺口 ¥{int(abs(gap)):,}")
        with cr_p:
            dream = st.text_input("下一个大件梦想", "换一辆新车", key=f"d_{label}"); dp = st.number_input("梦想金额 (元)", value=300000.0, key=f"dp_{label}")
            if act_d['savings'] > 0: st.warning(f"达成还需 **{dp / act_d['savings']:.1f}** 个月。")

        st.divider()
        st.subheader(f"🍲 家庭支出精细化构成 (方案 {label})")
        exp_df = pd.DataFrame({"项目": ["房贷", "车贷", "生活费", "杂项", f"{n_a}税费", f"{n_b}税费"], "金额": [act_d['curr_m'], c_l, act_liv, act_oth, act_d['res_a']['tax_ins'], act_d['res_b']['tax_ins']]})
        st.plotly_chart(px.bar(exp_df, x="项目", y="金额", color="项目", text_auto='.0f', template="plotly_white"), use_container_width=True)

elif view == "📉 资产演变长廊":
    st.title("⏳ 资产演变与 FIRE 审计")
    f_mode = st.radio("FIRE 目标计算方式", ["25倍年支原则", "自定义目标金额"], horizontal=True)
    ta = data_a['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else st.number_input("自定义退休金目标", value=5000000.0)
    tb = data_b['total_exp'] * 12 * 25 if f_mode == "25倍年支原则" else ta
    f1, f2 = st.columns(2)
    f1.metric("方案 A FIRE 目标", f"¥{int(ta):,}", delta=f"{asset_total/ta*100:.1f}% 达成")
    f1.progress(min(asset_total/ta, 1.0))
    if show_b:
        f2.metric("方案 B FIRE 目标", f"¥{int(tb):,}", delta=f"{asset_total/tb*100:.1f}% 达成")
        f2.progress(min(asset_total/tb, 1.0))
    st.info(f"💡 **FIRE 逻辑：** 达到 ¥{int(ta):,} 后，理论上每年提取 4% 的资产即可覆盖全家全年开销。目前资产足以支撑约 **{int(asset_total/(data_a['total_exp']*12)) if data_a['total_exp']>0 else 0}** 年。")
    
    st.divider()
    st.subheader("📈 20 年现金流博弈对比")
    cy_m = int(c_y * 12)
    p_a = [{"月": m, "房贷": float(data_a['m_seq'][m]) if m < len(data_a['m_seq']) else 0.0, "车贷": float(c_l) if m < cy_m else 0.0, "固定支出": float(living+other)} for m in range(240)]
    if show_b:
        pb_f = [{"月": m, "方案": "方案 B 总支出", "金额": (data_b['m_seq'][m] if m < len(data_b['m_seq']) else 0.0) + (c_l if m < cy_m else 0.0) + living_b + other + purchase_b/12} for m in range(240)]
        pa_f = [{"月": p["月"], "方案": "方案 A 总支出", "金额": p["房贷"] + p["车贷"] + p["固定支出"]} for p in p_a]
        st.plotly_chart(px.line(pd.DataFrame(pa_f + pb_f), x="月", y="金额", color="方案"), use_container_width=True)
    else:
        st.plotly_chart(px.area(pd.DataFrame(p_a), x="月", y=["房贷", "车贷", "固定支出"], title="资产演变详细構成投影"), use_container_width=True)

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制断头台")
    st.markdown("### 📌 什么是“无感支出”？\n财务学中著名的**“拿铁因子”**理论指出：那些微小的开销在复利下会演变成巨大的黑洞。")
    try:
        sub_d = conn.read(worksheet=f"Sub_{active_profile}", usecols=[0, 1, 2, 3], ttl=0).dropna(how="all")
        sub_d['状态'] = sub_d['状态'].astype(bool)
    except: 
        sub_d = pd.DataFrame([{"项目": "测试项目", "月费": 35.0, "状态": True, "备注": ""}])
        
    e_df = st.data_editor(sub_d, num_rows="dynamic", key="sub_ed")
    if st.button(f"💾 保存订阅更新至【存档 {active_profile}】"):
        conn.update(worksheet=f"Sub_{active_profile}", data=e_df)
        st.success(f"✅ 订阅数据已同步至存档 {active_profile}！")
        
    m_sub = e_df[e_df["状态"] == True]["月费"].sum(); daily = st.number_input("每日其他开支", value=50.0); y = st.slider("持续年数", 1, 30, 10); tbh = (daily * 365 + m_sub * 12) * y
    st.error(f"😱 {y}年后累计消耗 ¥{tbh:,.0f}，相当于奋斗了 **{tbh/active_hourly:.1f} 小时**。")

elif view == "🏦 资产对冲分析":
    st.title("🛡️ 资产收益对冲分析")
    asset = st.number_input("当前投资资产", value=asset_total); roi = st.slider("收益率 (%)", 0, 15, 7); m_roi = (asset * roi / 100) / 12
    st.metric("被动月收", f"¥{int(m_roi):,}"); cov = (m_roi / data_a['curr_m'] * 100) if data_a['curr_m'] > 0 else 100
    st.write(f"### 🎯 房贷覆盖率: {cov:.1f}%"); st.progress(min(cov/100, 1.0))
