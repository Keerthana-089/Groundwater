# app.py — AquaCluster (chemical-focused filter + "Highly contaminated" + safe-to-use indicator)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path

st.set_page_config(page_title="AquaCluster", layout="wide", initial_sidebar_state="collapsed")

# ---------------- CSS (light aqua look) ----------------
st.markdown("""
<style>
.main > div.block-container { padding-top: 18px; }
html, body, .stApp {
  height:100%;
  background: linear-gradient(90deg,#dff4ff 0%, #bfe9ff 100%);
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial;
}
.navbar { position: sticky; top: 0; z-index: 999; background: rgba(255,255,255,0.95);
  border-bottom: 1px solid rgba(0,0,0,0.06); padding: 14px 28px;
  display:flex; align-items:center; justify-content:space-between;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.brand { display:flex;align-items:center;gap:12px; }
.brand .logo { width:40px;height:40px;border-radius:8px;background: linear-gradient(180deg,#9fe1ff,#66c4ff);
  display:flex;align-items:center;justify-content:center;font-weight:700;color:#06476b; }
.brand h1 { font-size:20px; margin:0; color:#08384f; font-weight:700; }
.hero { margin:22px auto 12px; width:95%; background: linear-gradient(180deg,#e9f9ff, #e0f4ff);
  padding: 22px; border-radius:14px; box-shadow: 0 6px 20px rgba(0,0,0,0.06);
  display:flex; gap:18px; align-items:center; }
.hero .left { flex:2 } .hero .right { flex:1; text-align:right; }
.stats { margin-top:18px; width:95%; display:flex; gap:18px; flex-wrap:wrap; }
.card { background: linear-gradient(180deg,#ffffff, #f6fbff); border-radius:14px; padding:18px;
  flex:1; min-width:200px; box-shadow: 0 6px 18px rgba(10,40,60,0.04); }
.card .num { font-size:28px; font-weight:700; color:#0a3d62; } .card .label { color:#3b6b88; margin-top:6px; }
.grid { margin:22px auto; width:95%; display:grid; grid-template-columns: 1fr 1fr; gap:18px; }
.alerts-wrap { margin:22px auto; width:95%; }
.alert-box { background: linear-gradient(180deg,#fff2f2,#fff7f7); border-left:6px solid rgba(220,30,30,0.9);
  border-radius:10px; padding:16px; margin-bottom:12px; color:#6d1818; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.login-wrap { display:flex; align-items:center; justify-content:center; height:82vh; }
.login-card { width:420px; background: linear-gradient(180deg,#e9f9ff,#e2f5ff); padding:28px; border-radius:12px;
  box-shadow: 0 8px 24px rgba(6,50,80,0.08); text-align:center; }
.login-card h2 { margin:6px 0 2px; color:#073b51; } .login-card p { color:#3b6b88; margin-bottom:18px; }
.stButton>button { background: linear-gradient(180deg,#4fb7e6,#2f9fd1); color:white; font-weight:600; border-radius:8px; padding:10px 14px; }
select, input, textarea { border-radius:8px !important; padding:10px !important; }
.success-box { background: linear-gradient(180deg,#ecfff0,#e6fff0); padding:12px;border-radius:10px;color:#0b6b2f; box-shadow: 0 2px 8px rgba(0,0,0,0.04);}
.warn-box { background: linear-gradient(180deg,#fff8e6,#fff7e0); padding:12px;border-radius:10px;color:#8a5a00; box-shadow: 0 2px 8px rgba(0,0,0,0.04);}
.danger-box { background: linear-gradient(180deg,#fff2f2,#fff0f0); padding:12px;border-radius:10px;color:#7a1b1b; box-shadow: 0 2px 8px rgba(0,0,0,0.04);}
</style>
""", unsafe_allow_html=True)

# ---------------- Load dataset ----------------
DATA_LOCAL = Path("Groundwater dataset.csv")
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# Sidebar: upload + mapping
with st.sidebar:
    st.header("Data & mapping")
    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
    use_local = False
    if (not uploaded) and DATA_LOCAL.exists():
        use_local = st.checkbox(f"Use local file: {DATA_LOCAL.name}", value=True)
    if uploaded:
        try:
            df = load_csv(uploaded)
            st.success("Uploaded dataset loaded")
        except Exception as e:
            st.error("Upload failed: " + str(e))
            st.stop()
    elif use_local:
        try:
            df = load_csv(DATA_LOCAL)
            st.success("Local dataset loaded")
        except Exception as e:
            st.error("Local load failed: " + str(e))
            st.stop()
    else:
        df = pd.DataFrame()

    st.markdown("### Column mapping (auto-detected)")
    def guess(cols, keys):
        for k in keys:
            if k in cols:
                return k
        for c in cols:
            low = c.lower()
            if any(k in low for k in keys):
                return c
        return ""
    cols = list(df.columns) if not df.empty else []
    default_state = guess(cols, ["gm_country_name","state","country","region"])
    default_chem = guess(cols, ["gm_chemical_name","chemical","contaminant","parameter"])
    default_lat = guess(cols, ["gm_latitude","latitude","lat"])
    default_lon = guess(cols, ["gm_longitude","longitude","lon","long"])
    default_val = guess(cols, ["gm_result","value","result","measurement","value"])
    state_col = st.text_input("State column", value=default_state)
    chem_col = st.text_input("Chemical/Contaminant column", value=default_chem)
    lat_col = st.text_input("Latitude column", value=default_lat)
    lon_col = st.text_input("Longitude column", value=default_lon)
    val_col = st.text_input("Measurement column", value=default_val)
    st.markdown("---")
    st.write("If your CSV uses different names, change mappings above and reload.")
    st.markdown("---")
    if st.button("Reset session (clear)"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

# If no dataset loaded, show instructions and sample option
if df.empty:
    st.title("AquaCluster — preview (no dataset)")
    st.write("No dataset loaded. Upload your CSV in the sidebar or place `Groundwater dataset.csv` in this folder.")
    sample = st.button("Use sample demo data")
    if sample:
        df = pd.DataFrame({
            "gm_country_name":["Andhra Pradesh"]*40 + ["Telangana"]*30,
            "gm_chemical_name": (["Nitrate"]*20 + ["Chloride"]*10 + ["Sulfate"]*10) + (["Nitrate"]*15 + ["Arsenic"]*10 + ["Fluoride"]*5),
            "gm_result": np.concatenate([np.random.normal(25,10,40), np.random.normal(120,60,30)]).clip(0,500),
            "gm_latitude": np.random.uniform(15.0,19.0,70),
            "gm_longitude": np.random.uniform(78.0,85.0,70)
        })
    else:
        st.stop()

# Validate mapping inputs
for c in (state_col, chem_col, lat_col, lon_col, val_col):
    if c and c not in df.columns:
        if c.strip():
            st.warning(f"Column '{c}' not in CSV. Check mapping in sidebar.")

df = df.copy()
# create normalized columns safely
if state_col in df.columns:
    df["state_norm"] = df[state_col].astype(str).str.title().str.strip()
else:
    df["state_norm"] = "Unknown"
if chem_col in df.columns:
    df["chem_norm"] = df[chem_col].astype(str).str.title().str.strip()
else:
    # fallback: use district if chemical missing
    fallback = guess(list(df.columns), ["district","place","area","location"])
    if fallback and fallback in df.columns:
        df["chem_norm"] = df[fallback].astype(str).str.title().str.strip()
    else:
        df["chem_norm"] = "All"

# numeric conversions
df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
df = df.dropna(subset=[lat_col, lon_col])

# ---------------- Simple login page (mock) ----------------
def login_page():
    if st.session_state.get("logged_in"):
        return
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/4149/4149636.png", width=70)
    st.markdown("<h2>AquaCluster</h2>", unsafe_allow_html=True)
    st.markdown("<p>Groundwater Contamination Analysis</p>", unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    pwd = st.text_input("Password", type="password", key="login_pwd")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Login"):
            if email.strip() == "":
                st.error("Enter email")
            else:
                st.session_state["logged_in"] = True
                st.session_state["user"] = email.split("@")[0]
                st.experimental_rerun()
    with col2:
        if st.button("Register"):
            st.info("Register is mock — data not persisted.")
    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------- Dashboard ----------------
def dashboard():
    st.markdown(f"""
    <div class="navbar">
      <div class="brand">
        <div class="logo">💧</div>
        <h1>AquaCluster</h1>
      </div>
      <div class="nav-actions">
        <div style="color:#08384f">Welcome, <b>{st.session_state.get('user','guest')}</b></div>
        <div style="width:12px"></div>
        <div><button onclick="window.open('/', '_self')" style="border-radius:8px;padding:8px 12px">Logout</button></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero + filter card (Chemical instead of District)
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown('<div class="left">', unsafe_allow_html=True)
    st.markdown("<h2 style='margin:0 0 6px;'>Select Location & Contaminant</h2>", unsafe_allow_html=True)
    st.markdown("<div style='color:#2f516b;margin-bottom:10px;'>Choose a state and contaminant to view contamination data</div>", unsafe_allow_html=True)
    cols = st.columns([2,2,1])
    states = sorted(df["state_norm"].unique())
    sel_state = cols[0].selectbox("State", options=states, index=0, key="sel_state")
    # chemicals list
    chems = ["All Chemicals"] + sorted(df[df["state_norm"]==sel_state]["chem_norm"].dropna().unique().tolist())
    sel_chem = cols[1].selectbox("Contaminant", options=chems, index=0, key="sel_chem")
    if cols[2].button("Download Report"):
        st.success("Report download (mock) — customize to export real CSV.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="right"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # apply filter by state + chemical
    if sel_chem == "All Chemicals":
        df_f = df[df["state_norm"]==sel_state].copy()
    else:
        df_f = df[(df["state_norm"]==sel_state) & (df["chem_norm"]==sel_chem)].copy()

    if df_f.empty:
        st.warning("No data in this filter. Try another state/contaminant.")

    # thresholds (sidebar)
    safe_thresh = st.sidebar.number_input("Safe threshold (value <=)", value=50.0)
    contaminated_thresh = st.sidebar.number_input("Contaminated threshold (value >=)", value=200.0)

    # compute quality and 'highly contaminated' flags
    def quality(v):
        if v >= contaminated_thresh: return "Contaminated"
        if v <= safe_thresh: return "Safe"
        return "Moderate"
    df_f["quality"] = df_f[val_col].apply(lambda x: quality(x if pd.notnull(x) else -999))
    df_f["highly_contaminated"] = df_f[val_col].apply(lambda x: True if pd.notnull(x) and x >= contaminated_thresh else False)

    total = len(df_f)
    safe = (df_f["quality"]=="Safe").sum()
    moderate = (df_f["quality"]=="Moderate").sum()
    cont = (df_f["quality"]=="Contaminated").sum()
    high_count = df_f["highly_contaminated"].sum()

    # statistic cards
    st.markdown('<div class="stats">', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="num">{total}</div><div class="label">Total Samples</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="num" style="color:green">{safe}</div><div class="label">Safe</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="num" style="color:#e69500">{moderate}</div><div class="label">Moderate</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="num" style="color:red">{cont}</div><div class="label">Contaminated</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="num" style="color:#a50f0f">{high_count}</div><div class="label">Highly contaminated (≥ {contaminated_thresh})</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # map + chart
    st.markdown('<div class="grid">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card"><h3>Contamination Map</h3>', unsafe_allow_html=True)
        if not df_f.empty:
            center = [df_f[lat_col].mean(), df_f[lon_col].mean()]
            m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
            for _, r in df_f.iterrows():
                q = r["quality"]
                color = "green" if q=="Safe" else "orange" if q=="Moderate" else "red"
                safe_text = "Yes" if not r["highly_contaminated"] else "No"
                popup_html = (f"<b>{r.get(chem_col,'') if chem_col in r else r.get('chem_norm','')}</b><br>"
                              f"Value: {r[val_col]:.2f}<br>"
                              f"Quality: {q}<br>"
                              f"Highly contaminated: {r['highly_contaminated']}<br>"
                              f"<b>Safe to use?</b> {safe_text}")
                folium.CircleMarker(location=[r[lat_col], r[lon_col]],
                                    radius=6,
                                    color=color,
                                    fill=True,
                                    fill_color=color,
                                    popup=folium.Popup(popup_html, max_width=300)).add_to(m)
            st_folium(m, width="100%", height=420)
        else:
            st.info("No spatial data to show for this filter.")
        st.markdown('</div>', unsafe_allow_html=True)

    # average contaminant bar chart
    with st.container():
        st.markdown('<div class="card"><h3>Average Contaminant Levels</h3>', unsafe_allow_html=True)
        if "gm_chemical_name" in df_f.columns or "chem_norm" in df_f.columns:
            avg = df_f.groupby("chem_norm")[val_col].mean().reset_index().sort_values(val_col, ascending=False).head(6)
            if avg.empty:
                st.info("No chemical measurements to chart.")
            else:
                fig = px.bar(avg, x="chem_norm", y=val_col, labels={"chem_norm":"Parameter", val_col:"Value"}, template="simple_white", height=420)
                fig.update_layout(margin=dict(l=10,r=10,t=30,b=30), plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
        else:
            if df_f[val_col].dropna().empty:
                st.info("No measurement values to chart.")
            else:
                mean_val = df_f[val_col].mean()
                fig = px.bar(x=["Value"], y=[mean_val], labels={"x":"Parameter","y":"Mean"}, height=420)
                st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Recent Alerts with Safe-to-use message ----------------
    st.markdown('<div class="alerts-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>Recent Alerts</h3><p style="color:#2f516b">Regional groundwater contamination status & safety</p>', unsafe_allow_html=True)

    alerts = df_f[df_f["quality"] == "Contaminated"]
    moderate = df_f[df_f["quality"] == "Moderate"]
    highly = df_f[df_f["highly_contaminated"]]

    # Safety message for the region: based on highly contaminated counts
    if len(highly) == 0 and len(moderate) == 0:
        st.markdown(f'<div class="success-box">✅ <b>This region is safe to use</b> — no contaminated samples were found for the selected filter ({sel_state} / {sel_chem}).</div>', unsafe_allow_html=True)
    elif len(highly) == 0 and len(moderate) > 0:
        st.markdown(f'<div class="warn-box">⚠️ <b>Moderate risk</b> — {len(moderate)} sample(s) are borderline; take caution and re-test before using water for drinking.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="danger-box">🔴 <b>High contamination detected</b> — {len(highly)} highly contaminated sample(s) found. Not safe for drinking/use without treatment.</div>', unsafe_allow_html=True)
        # list top highly contaminated by location/chemical
        grp = highly.groupby("chem_norm").size().reset_index().rename(columns={0: "count"}).sort_values("count", ascending=False)
        st.markdown("<br><b>Highly contaminated by contaminant</b>", unsafe_allow_html=True)
        for _, r in grp.iterrows():
            st.markdown(f'<div class="alert-box"><b>{r["chem_norm"]}</b> — {int(r["count"])} highly contaminated sample(s)</div>', unsafe_allow_html=True)

        # also list top sample rows (max values) to inspect
        top = highly.sort_values(val_col, ascending=False).head(6)
        st.markdown("<br><b>Top highly contaminated samples (value descending)</b>", unsafe_allow_html=True)
        for _, s in top.iterrows():
            safe_text = "No"
            st.markdown(
                f'<div style="padding:10px;border-radius:8px;background:#fff7f7;margin-bottom:8px;">'
                f'<b>{s.get("chem_norm","")}</b> — value: {s[val_col]:.2f} — {s.get("district_norm","")}, {s.get("state_norm","")}. '
                f'<b>Safe to use?</b> {safe_text}'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Routing ----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    dashboard()
