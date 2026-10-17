"""
RestoCopilot AI - Chef Kitchen Station (KDS & Recipe Emergency Copilot)
Dedicated touchscreen-friendly portal for kitchen cooks and head chefs:
- Port: 8505
- Live sync with main database (D:\\resto_copilot_ai\\kitchen_vault.db)
- Real-time station queue with big touch controls ('🔥 Start Cooking', '✅ Plated & Served', '🔊 Callout Replay')
- 'Stock-Less Recipe Emergency Assistant': Instant chef tweaks when ingredients run out + 86/Low Stock alerts to counter
- Auto-refresh every 5 seconds for incoming orders
"""
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

from database import get_connection, init_db
from voice_announcer import generate_voice_callout
from ai_engine import CulinaryIntelligenceEngine

# Page Config: Touchscreen Fullscreen Feel
st.set_page_config(
    page_title="Chef Station KDS | RestoCopilot AI",
    page_icon="👨‍🍳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# High-Visibility Kitchen Touchscreen CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Playfair+Display:wght@700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    /* Chef Station Header */
    .chef-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }
    
    .chef-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.85rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }
    
    .chef-sub {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-top: 4px;
    }
    
    /* Touchscreen KDS Card */
    .chef-ticket {
        background: #1E293B !important;
        border-radius: 14px;
        border: 1px solid #334155;
        border-left: 8px solid #F59E0B;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .chef-ticket-cooking {
        border-left: 8px solid #3B82F6 !important;
    }
    
    .ticket-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed #334155;
        padding-bottom: 12px;
        margin-bottom: 14px;
    }
    
    .ticket-code {
        font-size: 1.4rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    
    .dish-row {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        padding: 8px 12px;
        background: #0F172A;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #10B981;
    }
    
    .urgency-badge {
        background: #EF4444;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 20px;
        letter-spacing: 0.5px;
    }
    
    .status-badge-pending {
        background: #F59E0B;
        color: #0F172A;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 20px;
    }
    
    .status-badge-cooking {
        background: #3B82F6;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 20px;
    }
    
    /* Touchscreen Big Buttons */
    .stButton>button {
        height: 52px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        transition: all 0.15s ease !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database
init_db()

# Auto-refresh helper (poll orders every 10s without page lag)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if "chef_audio_cache" not in st.session_state:
    st.session_state.chef_audio_cache = None

ai_engine = CulinaryIntelligenceEngine(mode="OFFLINE")

# Top Chef Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div class='chef-header'>
        <div>
            <div class='chef-title'>👨‍🍳 Line Chef & Kitchen Station KDS</div>
            <div class='chef-sub'>Live Ticket Line • Automated BOM Deduction • Emergency Recipe Alternatives</div>
        </div>
        <div style='text-align: right;'>
            <span style='background: #10B981; color: #FFFFFF; font-weight: 800; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem;'>
                ● LINE ACTIVE
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    if st.button("🔄 Refresh Orders Line", use_container_width=True):
        st.rerun()

# 2 Core Operational Columns: Left = Active Tickets | Right = Emergency Stock-Less Recipe Assistant
col_kds_line, col_emergency = st.columns([1.6, 1.4], gap="large")

# =========================================================================
# COLUMN 1: LIVE KITCHEN ORDER TICKETS
# =========================================================================
with col_kds_line:
    st.markdown("### 📋 Active Orders Station")
    st.caption("Touch a button to update status. Completed orders notify the front desk immediately.")
    
    # Auto-polling sync and voice callout for Chef
    conn = get_connection()
    unannounced = conn.execute("SELECT * FROM orders WHERE announced = 0 AND status != 'COMPLETED' LIMIT 1").fetchone()
    if unannounced:
        dishes_raw = json.loads(unannounced["items_json"]) if unannounced["items_json"] else []
        speech_text = f"Attention Kitchen! New order for {unannounced['table_or_platform']}. Prepare: {', '.join(dishes_raw)}."
        audio_path = generate_voice_callout(speech_text)
        st.session_state.chef_audio_cache = audio_path
        # Mark as announced
        conn.execute("UPDATE orders SET announced = 1 WHERE id = ?", (unannounced["id"],))
        conn.commit()
    
    active_tickets = conn.execute("SELECT * FROM orders WHERE status != 'COMPLETED' ORDER BY id ASC").fetchall()
    conn.close()
    
    # Auto-refresh helper (poll orders line every 3 seconds for live syncing)
    st.markdown("""
    <script>
        setTimeout(function() {
            window.location.reload();
        }, 4000);
    </script>
    """, unsafe_allow_html=True)
    
    if not active_tickets:
        st.markdown("""
        <div style='background: #1E293B; border: 1px dashed #475569; border-radius: 14px; padding: 50px; text-align: center;'>
            <div style='font-size: 3rem;'>✨</div>
            <div style='font-size: 1.5rem; font-weight: 700; color: #F8FAFC; margin-top: 10px;'>Station All Clear!</div>
            <div style='color: #94A3B8; margin-top: 6px;'>No pending tickets right now. Plating area is ready.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for ticket in active_tickets:
            dishes = json.loads(ticket["items_json"]) if ticket["items_json"] else []
            is_cooking = ticket["status"] == "COOKING"
            is_ready = ticket["status"] == "READY"
            
            if is_ready:
                card_class = "chef-ticket"
                badge_html = "<span style='background: #10B981; color: white; font-weight: 800; font-size: 0.8rem; padding: 4px 12px; border-radius: 20px;'>🔔 WAITER NOTIFIED</span>"
            elif is_cooking:
                card_class = "chef-ticket chef-ticket-cooking"
                badge_html = "<span class='status-badge-cooking'>🔥 IN COOKING</span>"
            else:
                card_class = "chef-ticket"
                badge_html = "<span class='status-badge-pending'>🟡 PENDING</span>"
            
            st.markdown(f"""
            <div class='{card_class}'>
                <div class='ticket-head'>
                    <div>
                        <span class='ticket-code'>{ticket['order_code']}</span>
                        <span style='color: #CBD5E1; font-size: 1.1rem; margin-left: 10px; font-weight: 600;'>{ticket['table_or_platform']}</span>
                    </div>
                    <div>
                        {badge_html}
                        <span style='color: #94A3B8; margin-left: 8px; font-size: 0.9rem;'>{ticket['created_at']}</span>
                    </div>
                </div>
                <div>
                    {"".join([f"<div class='dish-row'>🥘 {d}</div>" for d in dishes])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 0.8])
            with btn_col1:
                if not is_cooking:
                    if st.button(f"🔥 Start Cooking", key=f"chef_cook_{ticket['id']}", use_container_width=True):
                        conn = get_connection()
                        conn.execute("UPDATE orders SET status = 'COOKING' WHERE id = ?", (ticket["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()
            with btn_col2:
                if ticket["status"] != "READY":
                    if st.button(f"🔔 Notify Waiter (Ready)", key=f"chef_ready_{ticket['id']}", use_container_width=True):
                        conn = get_connection()
                        conn.execute("UPDATE orders SET status = 'READY' WHERE id = ?", (ticket["id"],))
                        conn.commit()
                        conn.close()
                        st.success(f"Buzzed Waitstaff! {ticket['order_code']} marked ready for pickup.")
                        st.rerun()
                else:
                    st.markdown("<div style='background: #065F46; color: #34D399; font-weight: 700; font-size: 0.85rem; padding: 12px; border-radius: 8px; text-align: center;'>🔔 Waiter Buzzed &bull; Ready at Pass</div>", unsafe_allow_html=True)
            with btn_col3:
                if st.button(f"🔊 Replay", key=f"chef_audio_{ticket['id']}", use_container_width=True):
                    speech = f"Attention Kitchen! Prepare: {', '.join(dishes)}."
                    p = generate_voice_callout(speech)
                    st.session_state.chef_audio_cache = p
                    st.rerun()
                    
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # Audio Playback
    if st.session_state.chef_audio_cache and os.path.exists(st.session_state.chef_audio_cache):
        st.audio(st.session_state.chef_audio_cache, format="audio/mp3", autoplay=True)

# =========================================================================
# COLUMN 2: STOCK-LESS RECIPE EMERGENCY ASSISTANT
# =========================================================================
with col_emergency:
    st.markdown("### 🚨 Stock-Less Recipe Emergency Assistant")
    st.caption("Did an ingredient just run out on the stove? Get instant chef substitutes and alert the front counter without stopping service.")
    
    st.markdown("""
    <div style='background: #1E293B; border-radius: 12px; padding: 18px; border: 1px solid #334155; margin-bottom: 16px;'>
        <b style='color: #F59E0B;'>⚡ Quick Tap Out-of-Stock Preset:</b>
    </div>
    """, unsafe_allow_html=True)
    
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_item = None
    with q_col1:
        if st.button("🥚 Out of Eggs", use_container_width=True):
            st.session_state.short_ing = "Farm Fresh Eggs"
            st.session_state.ordered_dish_target = "5 Bread Egg Fillings / Omelette"
    with q_col2:
        if st.button("🧀 Out of Paneer", use_container_width=True):
            st.session_state.short_ing = "Fresh Paneer"
            st.session_state.ordered_dish_target = "Kadhai Paneer Tikka Masala"
    with q_col3:
        if st.button("🍗 Low Chicken", use_container_width=True):
            st.session_state.short_ing = "Boneless Chicken Breast"
            st.session_state.ordered_dish_target = "Butter Chicken Gravy"

    target_dish = st.text_input("Ordered Dish Being Cooked:", value=st.session_state.get("ordered_dish_target", "Triple Egg & Herb Breakfast Omelette"))
    short_ing = st.selectbox("Scarce / Missing Ingredient:", [
        "Farm Fresh Eggs",
        "Fresh Paneer",
        "Boneless Chicken Breast",
        "Button Mushrooms",
        "English Cheddar Cheese",
        "Heavy Cooking Cream"
    ], index=0)
    qty_left = st.text_input("Current Line Quantity Left:", value="0 left / completely finished")
    
    if st.button("✨ Generate Emergency Substitute Dish", use_container_width=True):
        with st.spinner("AI generating alternative plating & kitchen adjustments..."):
            sub_res = ai_engine.solve_low_stock_substitution(target_dish, short_ing, qty_left)
            st.session_state.chef_emergency_result = sub_res

    if "chef_emergency_result" in st.session_state:
        res = st.session_state.chef_emergency_result
        st.markdown(f"""
        <div style='background: #1E293B; border-left: 6px solid #10B981; border-radius: 12px; padding: 20px; border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; margin-top: 16px;'>
            <div style='font-size: 1.25rem; font-weight: 800; color: #10B981;'>🍽️ Substitute: {res.get('substitute_dish', 'Chef Special')}</div>
            <div style='background: #0F172A; border-radius: 8px; padding: 14px; margin: 12px 0; border: 1px solid #334155;'>
                <b style='color: #F59E0B;'>🗣️ Waiter / Cashier Script:</b><br>
                <i style='color: #E2E8F0; font-size: 1.05rem;'>"{res.get('dialogue_for_staff', '')}"</i>
            </div>
            <div style='color: #94A3B8; font-size: 0.95rem; line-height: 1.6;'>
                <b>📈 Margin & Kitchen Impact:</b> {res.get('margin_impact', '+14% Margin')}<br>
                <b>💡 Upsell Pairing:</b> {res.get('upsell_pitch', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            if st.button(f"🚨 Broadcast 86 '{short_ing}' to Counter", use_container_width=True):
                # Update SQLite stock to 0 and alert status
                conn = get_connection()
                conn.execute("UPDATE inventory SET quantity = 0, freshness_status = 'OUT OF STOCK' WHERE item_name = ?", (short_ing,))
                conn.commit()
                conn.close()
                st.error(f"Alert sent to Counter! '{short_ing}' marked 86 (Out of Stock). Front desk notified.")
        with col_b2:
            if st.button(f"📢 Announce Substitute to Line", use_container_width=True):
                voice_msg = f"Kitchen notice! For {target_dish}, we are now serving: {res.get('substitute_dish')}."
                p = generate_voice_callout(voice_msg)
                st.session_state.chef_audio_cache = p
                st.rerun()

# Live Vault Status Ribbon at bottom
st.markdown("---")
st.markdown("#### 📦 Live Perishable Stock Monitor")
conn = get_connection()
inv_rows = conn.execute("SELECT item_name, quantity, unit, freshness_status FROM inventory").fetchall()
conn.close()

inv_cols = st.columns(len(inv_rows))
for idx, r in enumerate(inv_rows):
    with inv_cols[idx]:
        is_low = "Low" in r["freshness_status"] or "OUT" in r["freshness_status"]
        color = "#EF4444" if is_low else "#10B981"
        st.markdown(f"""
        <div style='background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 10px; text-align: center;'>
            <div style='font-size: 0.78rem; color: #94A3B8;'>{r['item_name']}</div>
            <div style='font-size: 1.1rem; font-weight: 800; color: {color};'>{r['quantity']} {r['unit']}</div>
            <div style='font-size: 0.7rem; color: {color};'>{r['freshness_status']}</div>
        </div>
        """, unsafe_allow_html=True)
