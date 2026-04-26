import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置与安全门禁 ---
st.set_page_config(page_title="Balance & Future Pro V17.2", layout="wide")

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

# --- 2. 云端数据调度中心 (支持备注列) ---
@st.cache_data(ttl=0)
def load_cloud_config():
    try:
        # 读取 3 列：参数名、值、备注
        df = conn.read(worksheet="Global_Config", usecols=[0, 1, 2])
        df = df.dropna(subset=['Parameter'])
        # 转换为字典，方便代码调用
        config_dict = pd.Series(df.Value.values, index=df.Parameter).to_dict()
        # 将备注也存入 session_state 备用
        memo_dict = pd.Series(df.备注.values, index=df.Parameter).to_dict()
        return {"values": config_dict, "memos": memo_dict}
    except:
        return {"values": {}, "memos": {}}

if 'full_config' not in st.session_state:
    st.session_state.full_config = load_cloud_config()

def get_cfg(key, default):
    val = st.session_state.full_config["values"].get(key, default)
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
    return {"total_net": total_net, "total_exp": curr_m + c_l + living + other, "savings": total_net - (curr_m + c_l + living + other), "m_seq": m_seq, "res_a": res_a, "res_b": res_b, "curr_m": curr_m}

# --- 4. 侧边栏配置 ---
st.sidebar.title("🚀 战略配置中心")

with st.sidebar.expander("👤 成员与梦想配置"):
    n_a = st.text_input("我的称呼", value=get_cfg("n_a", "Jim"))
    n_b = st.text_input("队友称呼", value=get_cfg("n_b", "队友"))
    dream_dest = st.text_input("梦想目的地", value=get_cfg("dream_dest", "马尔代夫"))
    dream_cost = st.number_input("预计人均花费", value=get_cfg("dream_cost", 15000.0))
    travel_num = st.number_input("出行人数", value=get_cfg("travel_num", 2))

with st.sidebar.expander("💰 方案 A：当前现实", expanded=True):
    a_g = st.number_input(f"{n_a}月薪", value=get_cfg("a_g", 26000.0))
    a_gig = st.number_input(f"{n_a}副业", value=get_cfg("a_gig", 0.0))
    a_m = st.selectbox(f"{n_a}基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("a_m", "全额缴纳")=="全额缴纳" else 1)
    a_h = st.number_input(f"{n_a}工时", value=get_cfg("a_h", 176))
    st.write("---")
    b_g = st.number_input(f"{n_b}月薪", value=get_cfg("b_g", 18000.0))
    b_gig = st.number_input(f"{n_b}副业", value=get_cfg("b_gig", 0.0))
    b_m = st.selectbox(f"{n_b}基数", ["全额缴纳", "最低标准(2360)"], index=0 if get_cfg("b_m", "全额缴纳")=="全额缴纳" else 1)
    b_h = st.number_input(f"{n_b}工时", value=get_cfg("b_h", 176))
    pf_pct = st.slider("公积金(%)", 5, 12, int(get_cfg("pf_pct", 0.05)*100)) / 100
    st.write("---")
    m_p = st.number_input("房贷本金", value=get_cfg("m_p", 400000.0))
    m_r = st.number_input("房贷利率(%)", value=get_cfg("m_r", 3.2))
    m_y = st.number_input("房贷年限", value=get_cfg("m_y", 30))
    asset_total = st.number_input("总资产", value=get_cfg("asset_total", 600000.0))
    c_l = st.number_input("车贷月供", value=get_cfg("c_l", 2000.0))
    c_y = st.number_input("车贷年数", value=get_cfg("c_y", 5))
    living = st.number_input("生活费", value=get_cfg("living", 6000.0))
    other = st.number_input("杂项", value=get_cfg("other", 0.0))

st.sidebar.divider()
view = st.sidebar.radio("战略地图", ["🏠 Balance 看板", "📉 资产演变长廊", "🕳️ “无感支出”黑洞", "🏦 资产对冲分析"])

# 💾 全量保存（含备注保护逻辑）
if st.sidebar.button("💾 全量保存至云端 (Google Drive)"):
    new_values = {
        "n_a": n_a, "n_b": n_b, "dream_dest": dream_dest, "dream_cost": dream_cost, "travel_num": travel_num,
        "a_g": a_g, "a_gig": a_gig, "a_m": a_m, "a_h": a_h, "b_g": b_g, "b_gig": b_gig, "b_m": b_m, "b_h": b_h,
        "pf_pct": pf_pct, "m_p": m_p, "m_r": m_r, "m_y": m_y, "asset_total": asset_total, 
        "c_l": c_l, "c_y": c_y, "living": living, "other": other
    }
    # 构造保存表：合并新值和原本的备注列，防止备注丢失
    save_list = []
    for k, v in new_values.items():
        memo = st.session_state.full_config["memos"].get(k, "") # 拿回原来的备注
        save_list.append({"Parameter": k, "Value": v, "备注": memo})
    
    df_save = pd.DataFrame(save_list)
    try:
        conn.update(worksheet="Global_Config", data=df_save)
        st.session_state.full_config["values"] = new_values
        st.sidebar.success("✅ 参数与备注已永久同步！")
    except Exception as e:
        st.sidebar.error(f"保存失败: {e}")

# --- 5. 计算与渲染 (逻辑同 V17.1) ---
data_a = run_strategic_calc(a_g, a_gig, b_g, b_gig, m_p, m_r, m_y, c_l, living, other, a_m, b_m, pf_pct)
if 'act_mem' not in st.session_state: st.session_state.act_mem = n_a
active_hourly = (a_g + a_gig)/a_h if st.session_state.act_mem == n_a else (b_g + b_gig)/b_h

if view == "🏠 Balance 看板":
    save_rate = data_a['savings'] / data_a['total_net'] if data_a['total_net'] > 0 else 0
    st.title(f"📊 Balance & Future | 家庭财务系统")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总到手", f"¥{int(data_a['total_net']):,}")
    c2.metric("总支出", f"¥{int(data_a['total_exp']):,}")
    c3.metric("月结余", f"¥{int(data_a['savings']):,}", delta=f"{int(save_rate*100)}% 储蓄率")
    c4.metric(f"{st.session_state.act_mem} 时薪", f"¥{active_hourly:.1f}")
    # ... 其他看板 UI 代码 ...

elif view == "🕳️ “无感支出”黑洞":
    st.title("🕳️ “无感支出”黑洞 & 订阅制断头台")
    # 核心修复：自动读取备注列
    try:
        sub_data = conn.read(worksheet="Subscriptions", usecols=[0, 1, 2, 3], ttl=0).dropna(how="all")
        sub_data['状态'] = sub_data['状态'].astype(bool)
    except:
        sub_data = pd.DataFrame([{"项目": "测试项目", "月费": 35.0, "状态": True, "备注": "这是备注示例"}])

    st.subheader("✂️ 订阅制清单管理 (支持备注编辑)")
    e_df = st.data_editor(sub_data, num_rows="dynamic", key="sub_editor")
    
    if st.button("💾 保存订阅更新至云端"):
        conn.update(worksheet="Subscriptions", data=e_df)
        st.success("✅ 订阅列表与备注已同步！")
    
    m_sub = e_df[e_df["状态"] == True]["月费"].sum()
    daily = st.number_input("每日其他开销", value=50.0)
    y = st.slider("持续年数", 1, 30, 10)
    tbh = (daily * 365 + m_sub * 12) * y
    st.error(f"😱 {y}年后累计消耗 ¥{tbh:,.0f}，相当于奋斗了 **{tbh/active_hourly:.1f} 小时**。")

# (其他页面 📉 资产演变长廊 和 🏦 资产对冲分析 代码逻辑与之前一致，仅需确保变量名对应即可)
