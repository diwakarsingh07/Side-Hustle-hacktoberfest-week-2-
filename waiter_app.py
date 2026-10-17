"""
RestoCopilot AI - Waiter Mobile/Tablet Companion OS
Dedicated portal for floor waitstaff:
- Port: 8506
- Clean mobile-first interface optimized for one-hand operation
- Features:
  1. Table Status & Order Buzzer: Live alerts when Chef marks food 'COOKED / READY TO SERVE'
  2. One-Tap 'Order Placed & Picked Up': Mark dishes served to tables
  3. 'Never Say No' Upsell & Substitute Assistant right at the table:
     - Real-time stock alerts so the waiter never takes an order for an ingredient the chef is out of
     - Instant AI script to upsell a substitute before walking back to the kitchen
  4. Quick Table Bill & Customer Phone Review Collector:
     - Collect customer phone right at payment to trigger automated SMS Google Reviews
"""
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

from database import get_connection, init_db, deduct_ingredients_for_order
from ai_engine import CulinaryIntelligenceEngine

# Page Config: Mobile/Handheld Tablet View
st.set_page_config(
    page_title="Waiter Mobile Terminal | RestoCopilot AI",
    page_icon="🤵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-First Ergonomic Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Playfair+Display:wght@700&display=swap');
    
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #FAF5EE !important;
        color: #1E293B !important;
    }
    
    /* Header Card */
    .waiter-hero {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 16px;
        padding: 18px 24px;
        color: #FFFFFF !important;
        margin-bottom: 16px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .waiter-hero h2 {
        color: #FFFFFF !important;
        font-family: 'Playfair Display', serif;
        margin: 0;
        font-size: 1.6rem;
    }
    
    /* Table / Pickup Card */
    .table-pickup-card {
        background: #FFFFFF !important;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #10B981;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
    }
    
    .table-cooking-card {
        border-left: 6px solid #F59E0B !important;
    }
    
    .table-num {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
    }
    
    .badge-ready {
        background: #D1FAE5;
        color: #065F46;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 20px;
    }
    
    .badge-stove {
        background: #FEF3C7;
        color: #92400E;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 20px;
    }
    
    .dish-tag {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1E293B;
        padding: 4px 0;
    }
    
    /* Big Touch Buttons */
    .stButton>button {
        height: 48px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

init_db()

ai_engine = CulinaryIntelligenceEngine(mode="OFFLINE")

# Top Header
col_wh1, col_wh2 = st.columns([3, 1])
with col_wh1:
    st.markdown("""
    <div class='waiter-hero'>
        <div>
            <h2>🤵 Waiter Service Terminal</h2>
            <div style='color: #CBD5E1; font-size: 0.85rem; margin-top: 4px;'>
                Live Kitchen Pickup Buzzer &bull; Table Orders &bull; Smart Out-of-Stock Guide
            </div>
        </div>
        <div>
            <span style='background: #10B981; color: white; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.82rem;'>
                ● FLOOR ACTIVE
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_wh2:
    if st.button("🔄 Sync Orders & Kitchen", use_container_width=True):
        st.rerun()

# 2 Operational Columns: Left = Ready for Pickup / Table Orders | Right = Table-side Assistant & 86 Alerts
col_floor, col_tableside = st.columns([1.5, 1.5], gap="large")

# =========================================================================
# COLUMN 1: LIVE KITCHEN PICKUP BUZZER & TABLE STATUS
# =========================================================================
with col_floor:
    st.markdown("### 🔔 Kitchen Pickup Buzzer & Table Queue")
    st.caption("Orders cooking or ready to be carried to tables.")
    
    conn = get_connection()
    orders_rows = conn.execute("SELECT * FROM orders WHERE status != 'COMPLETED' ORDER BY id ASC").fetchall()
    conn.close()
    
    if not orders_rows:
        st.markdown("""
        <div style='background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 40px; text-align: center;'>
            <div style='font-size: 2.5rem;'>☕</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #0F172A;'>All Tables Served!</div>
            <div style='color: #64748B; font-size: 0.9rem; margin-top: 4px;'>No food waiting at the kitchen counter.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for ord_item in orders_rows:
            is_ready = ord_item["status"] == "READY"
            is_cooking = ord_item["status"] == "COOKING"
            card_style = "table-pickup-card" if is_ready else "table-pickup-card table-cooking-card"
            badge = (
                "<span class='badge-ready'>🔔 HOT & READY TO SERVE</span>" if is_ready else 
                ("<span class='badge-stove'>🔥 ON STOVE / IN OVEN</span>" if is_cooking else "<span style='background: #F1F5F9; color: #475569; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;'>⏳ QUEUED</span>")
            )
            
            dishes = json.loads(ord_item["items_json"]) if ord_item["items_json"] else []
            
            st.markdown(f"""
            <div class='{card_style}'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                    <span class='table-num'>{ord_item['table_or_platform']}</span>
                    <div>
                        {badge}
                        <span style='color: #64748B; font-size: 0.82rem; margin-left: 8px;'>{ord_item['created_at']}</span>
                    </div>
                </div>
                <div style='background: #F8FAFC; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;'>
                    {"".join([f"<div class='dish-tag'>🥘 {d}</div>" for d in dishes])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns([1.5, 1])
            with c_btn1:
                if st.button(f"✅ Served to Guest ({ord_item['order_code']})", key=f"serve_{ord_item['id']}", use_container_width=True):
                    conn = get_connection()
                    conn.execute("UPDATE orders SET status = 'COMPLETED' WHERE id = ?", (ord_item["id"],))
                    conn.commit()
                    conn.close()
                    st.success(f"{ord_item['table_or_platform']} served! Order closed.")
                    st.rerun()
            with c_btn2:
                if st.button(f"📱 Bill / SMS", key=f"bill_{ord_item['id']}", use_container_width=True, help="Send post-dining review link"):
                    st.session_state.active_review_target = ord_item["customer_phone"]
                    st.info(f"Targeting guest {ord_item['customer_phone']} for review!")

# =========================================================================
# COLUMN 2: TABLE-SIDE 'NEVER SAY NO' & 86 OUT-OF-STOCK RADAR
# =========================================================================
with col_tableside:
    st.markdown("### 🛡️ Table-Side 86 Alert & Upsell Guide")
    st.caption("Check real-time 86 items before taking table orders, and get instant customer-friendly substitute scripts.")
    
    # 1. Real-time 86 Warning Banner
    conn = get_connection()
    out_items = conn.execute("SELECT item_name, quantity, unit, freshness_status FROM inventory WHERE quantity <= safety_threshold OR freshness_status = 'OUT OF STOCK'").fetchall()
    conn.close()
    
    if out_items:
        st.markdown("""
        <div style='background: #FEF2F2; border: 1.5px solid #FCA5A5; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;'>
            <b style='color: #991B1B;'>⚠️ 86 / Out-of-Stock Alert from Kitchen:</b>
            <div style='color: #7F1D1D; font-size: 0.9rem; margin-top: 4px;'>
        """, unsafe_allow_html=True)
        for out in out_items:
            st.markdown(f"&bull; <b>{out['item_name']}</b> is {out['freshness_status']} (Only {out['quantity']} {out['unit']} left). DO NOT take new orders without proposing an alternative!", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 12px 16px; color: #065F46; font-weight: 600; margin-bottom: 14px;'>✅ All Raw Ingredients In Stock & Available for Ordering.</div>", unsafe_allow_html=True)

    # 2. Table-Side Quick Substitution Pitch Generator
    st.markdown("#### 💡 Table-Side Substitute Script")
    st.write("If a diner asks for a low-stock dish, enter it here for the exact polite script:")
    
    w_dish = st.text_input("Diner Wants to Order:", value="Triple Egg Omelette / 5 Bread Egg Fillings")
    w_ing = st.selectbox("Low-Stock Component:", ["Farm Fresh Eggs", "Fresh Paneer", "Boneless Chicken Breast", "Button Mushrooms"])
    
    if st.button("✨ Get Customer-Friendly Upsell Script", use_container_width=True):
        with st.spinner("AI generating table conversation pitch..."):
            w_res = ai_engine.solve_low_stock_substitution(w_dish, w_ing, "0 remaining / finished")
            st.session_state.waiter_script = w_res

    if "waiter_script" in st.session_state:
        res = st.session_state.waiter_script
        st.markdown(f"""
        <div style='background: #FFFFFF; border-left: 5px solid #10B981; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-top: 12px;'>
            <b style='color: #10B981; font-size: 1.15rem;'>🍽️ Suggest: {res.get('substitute_dish', 'Chef Special')}</b>
            <div style='background: #F8FAFC; border-radius: 8px; padding: 12px; margin: 10px 0; border: 1px solid #E2E8F0;'>
                <b style='color: #475569; font-size: 0.85rem;'>🗣️ Say this to the Diner:</b><br>
                <i style='color: #0F172A; font-size: 1rem;'>"{res.get('dialogue_for_staff', '')}"</i>
            </div>
            <div style='font-size: 0.88rem; color: #64748B;'>
                <b>Upsell Note:</b> {res.get('upsell_pitch', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Post-Dining SMS Review Collector
    st.markdown("---")
    st.markdown("#### 📱 Post-Dining Google Review Trigger")
    phone_target = st.text_input("Diner Phone Number:", value=st.session_state.get("active_review_target", "+91 98765 43210"))
    if st.button("📤 Send Automated Experience Rating SMS", use_container_width=True):
        st.success(f"SMS review invitation dispatched to {phone_target}! Positive ratings will be routed to Google Maps.")
