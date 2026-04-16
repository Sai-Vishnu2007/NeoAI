"""
CYBERPUNK ADMIN DASHBOARD with LIVE TELEMETRY
Run with: streamlit run admin_dashboard.py
"""
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import time  # 🔥 NEW: Required for the live refresh loop

# ==========================================
# 🎨 CYBERPUNK CSS INJECTION
# ==========================================
st.set_page_config(page_title="Neo Overseer", layout="wide", page_icon="🛡️")

custom_css = """
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(168, 85, 247, 0.3);
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
        color: #f8fafc !important;
    }
    h1, h2, h3 { color: #a855f7 !important; font-weight: 900 !important; }
    [data-testid="stMetricValue"] { color: #22d3ee !important; }
    hr { border-color: rgba(168, 85, 247, 0.3) !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🗄️ DATABASE & TIME LOGIC
# ==========================================
DB_PATH = "agent.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_start_of_week():
    now = datetime.utcnow()
    start_of_window = now - timedelta(days=7)
    return start_of_window.replace(hour=0, minute=0, second=0, microsecond=0)

def get_weekly_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    start_str = get_start_of_week().isoformat()
    
    cursor.execute("""
        SELECT DATE(timestamp) as day, role, COUNT(*) as count 
        FROM messages WHERE timestamp >= ? GROUP BY DATE(timestamp), role ORDER BY day ASC
    """, (start_str,))
    daily_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(DISTINCT cs.user_id) as active_users
        FROM messages m JOIN chat_sessions cs ON m.session_id = cs.id WHERE m.timestamp >= ?
    """, (start_str,))
    active_users = cursor.fetchone()["active_users"]
    conn.close()
    return daily_data, active_users

def get_circular_chart_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    start_str = get_start_of_week().isoformat()
    
    cursor.execute("SELECT username FROM users")
    all_users = cursor.fetchall()
    auth_data = {"Google OAuth": 0, "Standard": 0}
    for u in all_users:
        if "@" in u["username"]: auth_data["Google OAuth"] += 1
        else: auth_data["Standard"] += 1
            
    cursor.execute("""
        SELECT u.username, COUNT(m.id) as msg_count
        FROM users u JOIN chat_sessions cs ON u.id = cs.user_id JOIN messages m ON cs.id = m.session_id
        WHERE m.timestamp >= ? AND m.role = 'user' GROUP BY u.id ORDER BY msg_count DESC LIMIT 5
    """, (start_str,))
    top_users = cursor.fetchall()
    conn.close()
    return auth_data, top_users

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin FROM users ORDER BY id")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_chat_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_session_messages(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, content, reasoning_content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    messages = cursor.fetchall()
    conn.close()
    return messages

# ==========================================
# 🖥️ STREAMLIT UI BUILDER
# ==========================================
st.title("🛡️ NEO OVERSEER COMMAND")
st.markdown(f"**Tracking cycle:** Rolling 7-Day Window")
st.markdown("---")

st.sidebar.markdown("## 🖥️ UBUNTU NODE")
st.sidebar.header("System Grid")
page = st.sidebar.radio("Navigation", ["System Analytics", "User Database", "Surveillance Logs"])

st.sidebar.markdown("---")
# 🔥 THE LIVE REFRESH TOGGLE
auto_refresh = st.sidebar.checkbox("🔴 Enable Live Auto-Refresh (5s)")

# --- PAGE 1: SYSTEM ANALYTICS ---
if page == "System Analytics":
    st.header("📊 Live Telemetry")
    daily_data, active_users = get_weekly_stats()
    
    if not daily_data:
        st.info("No messages have been sent yet this week. The grid is quiet.")
    else:
        df = pd.DataFrame([dict(row) for row in daily_data])
        user_prompts = df[df['role'] == 'user']['count'].sum() if 'user' in df['role'].values else 0
        ai_answers = df[df['role'] == 'assistant']['count'].sum() if 'assistant' in df['role'].values else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total Prompts (7 Days)", value=int(user_prompts))
        col2.metric(label="Neo AI Answers (7 Days)", value=int(ai_answers))
        col3.metric(label="Active Users (7 Days)", value=active_users)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📈 Network Traffic Area")
        chart_df = df.pivot(index='day', columns='role', values='count').fillna(0)
        chart_df = chart_df.rename(columns={'user': 'Human Prompts', 'assistant': 'Neo AI Responses'})
        st.area_chart(chart_df, color=["#a855f7", "#22d3ee"])

        st.markdown("---")
        st.subheader("🔮 System Distribution")
        auth_data, top_users = get_circular_chart_data()
        pie_col1, pie_col2 = st.columns(2)
        
        with pie_col1:
            st.markdown("**Identity Verification Methods**")
            auth_df = pd.DataFrame(list(auth_data.items()), columns=['Method', 'Users'])
            fig1 = px.pie(auth_df, values='Users', names='Method', hole=0.6, color_discrete_sequence=['#a855f7', '#22d3ee'])
            fig1.update_traces(textinfo='percent+label', textfont=dict(color='#ffffff', size=14), marker=dict(line=dict(color='#0f172a', width=2)))
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(font=dict(color="#f8fafc")), margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig1, use_container_width=True, theme=None)
            
        with pie_col2:
            st.markdown("**Top 5 Most Active Operatives**")
            if top_users:
                users_df = pd.DataFrame([dict(row) for row in top_users])
                fig2 = px.pie(users_df, values='msg_count', names='username', color_discrete_sequence=px.colors.sequential.Purp)
                fig2.update_traces(textinfo='percent+label', textfont=dict(color='#ffffff', size=14), marker=dict(line=dict(color='#0f172a', width=2)))
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(font=dict(color="#f8fafc")), margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig2, use_container_width=True, theme=None)
            else:
                st.info("Not enough data to map top operatives.")

# --- PAGE 2 & 3: USER DB & LOGS ---
elif page == "User Database":
    st.header("👥 Registered Users")
    users = get_all_users()
    if users:
        user_data = [{"ID": u["id"], "Username": u["username"], "Auth Type": "Google OAuth" if "@" in u["username"] else "Standard", "Admin Status": "✅ True" if u["is_admin"] else "❌ False"} for u in users]
        st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
        st.info(f"Total Users in Grid: {len(users)}")
    else: st.warning("No users found in the database.")

elif page == "Surveillance Logs":
    st.header("👁️ Surveillance Logs")
    users = get_all_users()
    if users:
        user_options = {f"{u['username']} (ID: {u['id']})": u['id'] for u in users}
        selected_user_id = user_options[st.selectbox("Target User:", list(user_options.keys()))]
        if selected_user_id:
            sessions = get_user_chat_sessions(selected_user_id)
            if sessions:
                session_options = {f"{s['name']} (Created: {s['created_at']})": s['id'] for s in sessions}
                selected_session_id = session_options[st.selectbox("Select Chat Session:", list(session_options.keys()))]
                st.markdown("---")
                messages = get_session_messages(selected_session_id)
                if messages:
                    for msg in messages:
                        with st.container():
                            if msg["role"] == "user": st.markdown(f"**👤 USER:** \n{msg['content']}")
                            else: st.markdown(f"**🤖 NEO AI:** \n{msg['content']}")
                            if msg["reasoning_content"]:
                                with st.expander("🧠 View AI Thought Process"): st.markdown(f"```text\n{msg['reasoning_content']}\n```")
                            st.markdown("---")
                else: st.info("No messages found.")
            else: st.warning("No chat history for this user.")

# ==========================================
# 🔄 LIVE REFRESH EXECUTION
# ==========================================
# If the switch is checked, wait 5 seconds and reload the page automatically!
if auto_refresh:
    time.sleep(5)
    st.rerun()