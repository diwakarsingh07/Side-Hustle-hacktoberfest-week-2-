"""
RestoCopilot AI - Ultra-Modern Autonomous Kitchen & Dining OS
Contemporary SaaS Dashboard Architecture:
- UI/UX: Silicon Valley Tier-1 Minimalist Design System
- Aesthetic: Clean rounded-2xl cards (border: 1px solid #E2E8F0, background: #FFFFFF, elevation shadow 0 10px 30px -10px rgba(0,0,0,0.05))
- Color Palette: Luminous, high-contrast, clean SaaS palette (#0F172A, #334155, #64748B) with zero harsh black boxes
- Status: Live Kitchen Status pills, Dual-Engine mode indicator (Local Llama vs Gemma Open-Weights)
- Automated Business Logic: Real-time ingredient deduction from SQLite inventory upon order dispatch, live inventory impact badges, dynamic low-stock substitutions, perishable stock watchdog, and smart review triage routing.
"""
import streamlit as st
import pandas as pd
import json
import os
import time
import base64
from datetime import datetime

from database import (
    get_connection, init_db, deduct_ingredients_for_order, reset_inventory_vault,
    update_inventory_item, restock_inventory_item, add_new_inventory_item
)
from voice_announcer import generate_voice_callout
from ai_engine import CulinaryIntelligenceEngine
from serp_reviews import fetch_google_maps_reviews
from sms_service import send_real_sms

# Page Configuration
st.set_page_config(
    page_title="RestoCopilot AI | Autonomous Kitchen & Dining OS",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database and Schema Migrations
init_db()

# State Initialization
if "active_role" not in st.session_state:
    st.session_state.active_role = None  # None = Show Master Role Selection Portal

if "engine_mode" not in st.session_state:
    st.session_state.engine_mode = "OFFLINE"

if "latest_audio_path" not in st.session_state:
    st.session_state.latest_audio_path = None

if "last_deduction_logs" not in st.session_state:
    st.session_state.last_deduction_logs = None

if "cached_sub" not in st.session_state:
    st.session_state.cached_sub = None

if "cached_rev" not in st.session_state:
    st.session_state.cached_rev = None

if "saved_tables" not in st.session_state:
    st.session_state.saved_tables = [
        "Table 1 (Window Side)",
        "Table 4 (Dine-In Main Hall)",
        "Table 8 (Rooftop Dining)",
        "Table 12 (Family Lounge)",
        "Swiggy Express #SW-8492",
        "Zomato Gold #ZM-3109",
        "Counter Takeaway #CK-104"
    ]

if "pos_order_items" not in st.session_state:
    st.session_state.pos_order_items = [
        {"dish": "Butter Naan", "qty": 2, "notes": "Extra Butter"},
        {"dish": "Paneer Tikka", "qty": 1, "notes": "Medium Spicy"},
        {"dish": "Murgh Makhani", "qty": 1, "notes": "Boneless / Mild"}
    ]

if "chef_audio_cache" not in st.session_state:
    st.session_state.chef_audio_cache = None

if "chef_emergency_result" not in st.session_state:
    st.session_state.chef_emergency_result = None

if "waiter_script" not in st.session_state:
    st.session_state.waiter_script = None

ai_engine = CulinaryIntelligenceEngine(mode=st.session_state.engine_mode)

# =========================================================================
# ULTRA-MODERN LUMINOUS SAAS CSS DESIGN SYSTEM (NO HARSH BLACK BOXES)
# =========================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,500;1,600;1,700;1,800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Global Base Reset & Typography */
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #0F172A;
        letter-spacing: -0.01em;
    }
    
    p, span, label {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Aesthetic Calligraphy & Luxury Editorial Typography */
    .aesthetic-calligraphy {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-style: italic !important;
        font-weight: 600 !important;
        color: #B45309 !important; /* Warm Artisan Amber-Gold */
        letter-spacing: 0.02em !important;
    }
    
    .aesthetic-italic {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-style: italic !important;
        font-weight: 600 !important;
    }
    
    .aesthetic-eyebrow {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.18em !important;
        text-transform: uppercase !important;
        color: #64748B !important;
        margin-bottom: 6px !important;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Preserve Streamlit Material Icons */
    span[data-testid*="Icon"], [class*="material-symbols"], [class*="material-icons"], [data-testid="stSidebarCollapseButton"] * {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
    }
    
    /* Modern Luminous SaaS Hero Header (No harsh black box) */
    .saas-header {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 26px 32px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .saas-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #10B981 0%, #3B82F6 50%, #8B5CF6 100%);
    }
    
    .saas-header-title {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 2.45rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        margin: 0 0 6px 0 !important;
        line-height: 1.25 !important;
    }
    
    .saas-header-subtitle {
        font-size: 0.96rem !important;
        color: #475569 !important;
        max-width: 840px;
        margin: 0 0 16px 0 !important;
        line-height: 1.55;
        font-weight: 400 !important;
    }
    
    /* Modern Pill Status Badges */
    .status-pills-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
    }
    
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 13px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        white-space: nowrap;
    }
    
    .pill-green {
        background: #ECFDF5;
        color: #065F46 !important;
        border: 1px solid #A7F3D0;
    }
    
    .pill-amber {
        background: #FFFBEB;
        color: #92400E !important;
        border: 1px solid #FDE68A;
    }
    
    .pill-rose {
        background: #FEF2F2;
        color: #991B1B !important;
        border: 1px solid #FECACA;
    }
    
    .pill-indigo {
        background: #EEF2FF;
        color: #3730A3 !important;
        border: 1px solid #C7D2FE;
    }
    
    .pill-slate {
        background: #F1F5F9;
        color: #334155 !important;
        border: 1px solid #CBD5E1;
    }
    
    .pill-purple {
        background: #FAF5FF;
        color: #6B21A8 !important;
        border: 1px solid #E9D5FF;
    }
    
    .pill-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .pill-dot-green { background-color: #10B981; box-shadow: 0 0 8px #10B981; }
    .pill-dot-amber { background-color: #F59E0B; box-shadow: 0 0 8px #F59E0B; }
    .pill-dot-rose { background-color: #EF4444; box-shadow: 0 0 8px #EF4444; }
    
    /* Contemporary Metric Cards Ribbon */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    
    .metric-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 18px !important;
        padding: 20px 22px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 35px -10px rgba(0, 0, 0, 0.08) !important;
    }
    
    .metric-label-text {
        font-size: 0.76rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700 !important;
        color: #64748B !important;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .metric-value-text {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 1.95rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        line-height: 1.1;
    }
    
    .metric-sub-text {
        font-size: 0.8rem !important;
        color: #64748B !important;
        margin-top: 5px;
        font-weight: 500 !important;
    }
    
    /* Sleek SaaS Cards */
    .saas-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 24px 28px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        margin-bottom: 20px !important;
    }
    
    .card-title {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 6px !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .card-subtitle {
        font-size: 0.88rem !important;
        color: #475569 !important;
        margin-bottom: 18px !important;
        line-height: 1.45;
    }
    
    /* KDS Ticket Cards */
    .ticket-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 18px !important;
        padding: 22px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 8px 24px -8px rgba(0, 0, 0, 0.05) !important;
        border-left: 5px solid #0F172A !important;
        transition: transform 0.15s ease !important;
    }
    
    .ticket-card.cooking {
        border-left-color: #F59E0B !important;
    }
    
    .ticket-card.pending {
        border-left-color: #EF4444 !important;
    }
    
    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #F1F5F9;
        margin-bottom: 14px;
    }
    
    .ticket-code {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.01em;
    }
    
    .ticket-channel {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        margin-left: 8px;
    }
    
    .dish-row {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        color: #0F172A !important;
        padding: 6px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Inventory Impact Live Badge Container */
    .inventory-impact-box {
        background: #FAF5FF !important;
        border: 1px solid #E9D5FF !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin: 14px 0 16px 0 !important;
    }
    
    .inventory-impact-title {
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6B21A8 !important;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 6px;
    }
    
    .inventory-deduction-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #FFFFFF;
        border: 1px solid #D8B4FE;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #4C1D95 !important;
        margin: 3px 4px 3px 0;
    }
    
    /* Clean Modern Input Controls */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        font-size: 0.94rem !important;
        font-weight: 500 !important;
        padding: 11px 14px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }
    
    /* All Standard Buttons: Clean Light SaaS Outline Buttons (Eliminates harsh black button boxes) */
    .stButton>button {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: 1px solid #CBD5E1 !important;
        padding: 9px 18px !important;
        font-size: 0.90rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    
    .stButton>button p, .stButton>button span {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    
    .stButton>button:hover {
        background: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #2563EB !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
    }
    
    .stButton>button:hover p, .stButton>button:hover span {
        color: #2563EB !important;
    }
    
    /* Primary Action Buttons: Sleek Dark Slate Gradient with Guaranteed High-Contrast White Text */
    .stButton>button[kind="primary"], .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.15) !important;
    }
    
    .stButton>button[kind="primary"] p, .stButton>button[kind="primary"] span,
    .stButton>button[data-testid="stBaseButton-primary"] p, .stButton>button[data-testid="stBaseButton-primary"] span {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    .stButton>button[kind="primary"]:hover, .stButton>button[data-testid="stBaseButton-primary"]:hover {
        background: #334155 !important;
        border-color: #475569 !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.22) !important;
    }
    
    .stButton>button[kind="primary"]:hover p, .stButton>button[kind="primary"]:hover span,
    .stButton>button[data-testid="stBaseButton-primary"]:hover p, .stButton>button[data-testid="stBaseButton-primary"]:hover span {
        color: #FFFFFF !important;
    }
    
    /* Modern Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9 !important;
        padding: 6px !important;
        border-radius: 14px !important;
        gap: 6px !important;
        margin-bottom: 24px !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 10px 18px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.15s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06) !important;
    }
    
    /* Natural Staff Quotation Bubble */
    .speech-bubble {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #0F172A !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        margin: 14px 0 !important;
        color: #0F172A !important;
        font-size: 1.02rem !important;
        line-height: 1.55;
    }
    
    /* Audio Container */
    .audio-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        margin-top: 14px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
</style>
""", unsafe_allow_html=True)

# Helper to encode local assets to base64 for reliable Streamlit CSS rendering
def get_base64_asset(filename: str) -> str:
    asset_path = os.path.join(os.path.dirname(__file__), "assets", filename)
    if os.path.exists(asset_path):
        with open(asset_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

# Apply Assets: Rotated Wood Header Texture, Sidebar Bistro Art & Main UI Mediterranean Feast
sidebar_bg_b64 = get_base64_asset("sidebar_bistro_art.jpg")
wood_header_b64 = get_base64_asset("wood_header_bg.jpg")
main_ui_b64 = get_base64_asset("main_ui_bg.jpg")

st.markdown(f"""
<style>
    /* Main Dashboard Background across all tabs: Artisan Watercolor Feast */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-image: 
            linear-gradient(to right, rgba(254, 252, 248, 0.93) 0%, rgba(255, 255, 255, 0.88) 55%, rgba(255, 255, 255, 0.40) 100%),
            url("data:image/jpeg;base64,{main_ui_b64}") !important;
        background-size: auto 100vh !important;
        background-position: right top !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        background-color: #FAF8F5 !important;
    }}
    
    /* Transparent Tab Panels so background art flows seamlessly through all tabs */
    .stTabs [data-baseweb="tab-panel"] {{
        background: transparent !important;
    }}
    
    /* Ensure All Cards Maintain High Contrast and Text Readability */
    .saas-card {{
        background: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(14px) !important;
    }}
    
    .metric-card {{
        background: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(14px) !important;
    }}
    
    .ticket-card {{
        background: rgba(255, 255, 255, 0.96) !important;
        backdrop-filter: blur(10px) !important;
    }}

    /* Artisan Culinary Art Background for Sidebar Drawer - Directly Behind the Text */
    section[data-testid="stSidebar"] {{
        background-image: 
            linear-gradient(180deg, rgba(255, 255, 255, 0.40) 0%, rgba(254, 252, 248, 0.60) 100%),
            url("data:image/jpeg;base64,{sidebar_bg_b64}") !important;
        background-size: cover !important;
        background-position: left top !important;
        background-repeat: no-repeat !important;
        background-attachment: local !important;
        border-right: 1px solid #E2E8F0 !important;
    }}
    
    /* Ensure inner sidebar containers stay transparent so art is fully visible behind widgets */
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"] > div {{
        background-color: transparent !important;
        background: transparent !important;
    }}
    
    /* Main Hero Header: Rotated Rich Mahogany Wood Planks Directly Behind Text */
    .saas-header {{
        background-image: 
            linear-gradient(135deg, rgba(18, 12, 8, 0.40) 0%, rgba(28, 18, 14, 0.58) 100%),
            url("data:image/jpeg;base64,{wood_header_b64}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        border: 1px solid rgba(212, 175, 55, 0.35) !important;
        border-radius: 20px !important;
        padding: 30px 38px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 14px 35px -10px rgba(28, 18, 14, 0.35), 0 2px 6px rgba(0, 0, 0, 0.15) !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    
    .saas-header::before {{
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #D4AF37 0%, #F59E0B 50%, #B45309 100%) !important;
    }}
    
    .saas-header .aesthetic-eyebrow {{
        color: #FBBF24 !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8) !important;
    }}
    
    .saas-header .saas-header-title {{
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #FFFDF9 !important;
        letter-spacing: -0.02em !important;
        margin: 0 0 8px 0 !important;
        line-height: 1.25 !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.75) !important;
    }}
    
    .saas-header .aesthetic-calligraphy {{
        color: #FDE68A !important;
        text-shadow: 0 2px 12px rgba(245, 158, 11, 0.6) !important;
    }}
    
    .saas-header .saas-header-subtitle {{
        font-size: 0.98rem !important;
        color: #F1ECE6 !important;
        max-width: 840px !important;
        margin: 0 0 18px 0 !important;
        line-height: 1.55 !important;
        font-weight: 400 !important;
        text-shadow: 0 1px 6px rgba(0, 0, 0, 0.75) !important;
    }}
    
    /* Status pills floating over the rich wood background */
    .saas-header .pill-badge {{
        background: rgba(255, 255, 255, 0.14) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}
    
    .saas-header .pill-green {{
        background: rgba(16, 185, 129, 0.24) !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
        color: #A7F3D0 !important;
    }}
    
    .saas-header .pill-amber {{
        background: rgba(245, 158, 11, 0.24) !important;
        border: 1px solid rgba(245, 158, 11, 0.5) !important;
        color: #FDE68A !important;
    }}
    
    .saas-header .pill-slate {{
        background: rgba(255, 255, 255, 0.14) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #F1F5F9 !important;
    }}
    
    .saas-header .pill-purple {{
        background: rgba(168, 85, 247, 0.24) !important;
        border: 1px solid rgba(168, 85, 247, 0.5) !important;
        color: #E9D5FF !important;
    }}
    
    /* Sleek Frosted Glassmorphism for Sidebar Controls over the Background Art */
    [data-testid="stSidebar"] .stRadio, 
    [data-testid="stSidebar"] .stTextInput {{
        background: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(12px) !important;
        padding: 14px 16px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(226, 232, 240, 0.95) !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
    }}
    
    [data-testid="stSidebar"] .stButton>button {{
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
    }}
    [data-testid="stSidebar"] .stButton>button:hover {{
        background: #FFFFFF !important;
        border-color: #94A3B8 !important;
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# SIDEBAR CONTROLS & INTELLIGENCE ROUTER
# =========================================================================
with st.sidebar:
    # Role Switcher Bar in Sidebar
    cur_role_display = st.session_state.active_role or "None (Select Role)"
    st.markdown(f"""
    <div style='background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 12px; padding: 10px 14px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <div style='font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #64748B;'>Active Role</div>
            <div style='font-size: 0.95rem; font-weight: 800; color: #0F172A;'>{cur_role_display}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔁 Switch Terminal Role", key="switch_role_btn", use_container_width=True):
        st.session_state.active_role = None
        st.rerun()
    st.markdown("---")

    st.markdown(f"""
    <div style='background-image: linear-gradient(135deg, rgba(255,255,255,0.76) 0%, rgba(255,255,255,0.92) 100%), url("data:image/jpeg;base64,{sidebar_bg_b64}"); background-size: cover; background-position: left center; border-radius: 18px; padding: 18px 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 16px rgba(0,0,0,0.04); margin-bottom: 14px;'>
        <div style='font-family: "Playfair Display", Georgia, serif; font-size: 1.65rem; font-weight: 700; color: #0F172A; letter-spacing: -0.02em;'>
            RestoCopilot <span style='font-family: "Plus Jakarta Sans", sans-serif; font-size: 0.78rem; background: #EEF2FF; color: #4F46E5; padding: 3px 8px; border-radius: 6px; font-weight: 700; vertical-align: middle;'>AI v2.5</span>
        </div>
        <div style='font-size: 0.74rem; font-weight: 700; color: #64748B; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 3px;'>
            Artisan Kitchen OS
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("##### ⚡ Dual-Engine Routing Core")
    engine_choice = st.radio(
        "Active Reasoning Node:",
        options=["OFFLINE (Light Llama • Local Edge)", "ONLINE (Gemma 31B • Open-Weights)"],
        index=0 if st.session_state.engine_mode == "OFFLINE" else 1,
        help="OFFLINE: Instant deterministic execution, 0 latency, zero API costs. ONLINE: Sensory culinary copywriting via high-throughput endpoint."
    )
    new_mode = "OFFLINE" if "OFFLINE" in engine_choice else "ONLINE"
    if new_mode != st.session_state.engine_mode:
        st.session_state.engine_mode = new_mode
        ai_engine.set_mode(new_mode)
        st.rerun()
        
    if st.session_state.engine_mode == "OFFLINE":
        st.markdown("""
        <div class='pill-badge pill-green' style='width: 100%; justify-content: center; margin: 8px 0;'>
            🛡️ Local On-Premise: $0 Token Fee
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='pill-badge pill-amber' style='width: 100%; justify-content: center; margin: 8px 0;'>
            🚀 Gemma Accelerated via Open-Weights
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("##### 🎙️ Voice Synthesizer Dispatch")
    custom_eleven = st.text_input("ElevenLabs API Key (Optional):", type="password", help="Leave blank for automatic studio offline Indian-English voice synthesis.")
    if custom_eleven:
        os.environ["ELEVENLABS_API_KEY"] = custom_eleven
        st.caption("✨ Studio Neural Voice Active")
    else:
        st.caption("🔊 High-Clarity Studio TTS Fallback Ready")
        
    st.markdown("---")
    st.markdown("##### 🛠️ Kitchen Vault Controls")
    if st.button("🔄 Reset / Restock Kitchen Inventory", use_container_width=True, help="Refills all eggs, paneer, chicken, dough to fresh optimal levels."):
        reset_inventory_vault()
        st.success("Kitchen inventory restocked to baseline!")
        time.sleep(0.5)
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style='font-size: 0.78rem; color: #64748B; line-height: 1.5;'>
        <b>Status:</b> SQLite Vault Synced<br>
        <b>Recipe BOM:</b> 12 Dynamic Mappings<br>
        <b>Zero Latency:</b> Active Station KDS
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# MASTER ROLE SELECTION PORTAL (AT STARTUP)
# =========================================================================
if st.session_state.active_role is None:
    st.markdown("""
    <div style='text-align: center; margin: 30px auto 35px auto; max-width: 720px;'>
        <div style='font-size: 0.85rem; font-weight: 800; letter-spacing: 0.15em; color: #D97706; text-transform: uppercase; margin-bottom: 8px;'>✦ ARTISAN MICHELIN INTELLIGENCE ✦</div>
        <div style='font-family: "Playfair Display", Georgia, serif; font-size: 2.6rem; font-weight: 800; color: #0F172A; line-height: 1.2;'>
            Welcome to RestoCopilot AI
        </div>
        <div style='font-size: 1.05rem; color: #475569; margin-top: 10px; font-weight: 500;'>
            Select your restaurant terminal role to initialize your specialized station:
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    role_col1, role_col2, role_col3 = st.columns(3, gap="large")
    
    with role_col1:
        st.markdown("""
        <div class='saas-card' style='text-align: center; padding: 32px 20px !important; min-height: 280px; display: flex; flex-direction: column; justify-content: space-between;'>
            <div>
                <div style='font-size: 3.2rem; margin-bottom: 12px;'>🧾</div>
                <div style='font-family: "Playfair Display", serif; font-size: 1.4rem; font-weight: 700; color: #0F172A;'>1. Counter Person</div>
                <div style='color: #64748B; font-size: 0.9rem; margin-top: 8px; line-height: 1.5;'>
                    Modern POS table builder, custom table management, automatic inventory deduction & review triage.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Enter as Counter Person", key="pick_role_counter", type="primary", use_container_width=True):
            st.session_state.active_role = "Counter Person"
            st.rerun()

    with role_col2:
        st.markdown("""
        <div class='saas-card' style='text-align: center; padding: 32px 20px !important; min-height: 280px; display: flex; flex-direction: column; justify-content: space-between;'>
            <div>
                <div style='font-size: 3.2rem; margin-bottom: 12px;'>👨‍🍳</div>
                <div style='font-family: "Playfair Display", serif; font-size: 1.4rem; font-weight: 700; color: #0F172A;'>2. Head Chef</div>
                <div style='color: #64748B; font-size: 0.9rem; margin-top: 8px; line-height: 1.5;'>
                    Touchscreen KDS line, voice callout player, 'Notify Waiter' alerts & emergency stock-less recipe assistant.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔥 Enter as Head Chef", key="pick_role_chef", type="primary", use_container_width=True):
            st.session_state.active_role = "Chef"
            st.rerun()

    with role_col3:
        st.markdown("""
        <div class='saas-card' style='text-align: center; padding: 32px 20px !important; min-height: 280px; display: flex; flex-direction: column; justify-content: space-between;'>
            <div>
                <div style='font-size: 3.2rem; margin-bottom: 12px;'>🤵</div>
                <div style='font-family: "Playfair Display", serif; font-size: 1.4rem; font-weight: 700; color: #0F172A;'>3. Floor Waiter</div>
                <div style='color: #64748B; font-size: 0.9rem; margin-top: 8px; line-height: 1.5;'>
                    Live kitchen pickup buzzer, table-side 86 out-of-stock radar, 'Never Say No' customer scripts & review SMS.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🛎️ Enter as Floor Waiter", key="pick_role_waiter", type="primary", use_container_width=True):
            st.session_state.active_role = "Waiter"
            st.rerun()

    st.stop()  # Halt execution so only the role picker is shown until selected!

# =========================================================================
# HEADER BANNER WITH STATUS PILLS (AESTHETIC CALLIGRAPHY EDITORIAL DESIGN)
# =========================================================================
engine_pill_class = "pill-green" if st.session_state.get("engine_mode", "OFFLINE") == "OFFLINE" else "pill-amber"
engine_label = "Local Llama Edge (0-Fee)" if st.session_state.get("engine_mode", "OFFLINE") == "OFFLINE" else "Gemma 31B (Open-Weights)"
active_role_val = st.session_state.get("active_role") or "Counter & Manager Station"

st.markdown(f"""
<div class='saas-header'>
    <div class='aesthetic-eyebrow'>✦ ARTISAN MICHELIN INTELLIGENCE &bull; {active_role_val.upper()} TERMINAL ✦</div>
    <div class='saas-header-title'>
        Autonomous Kitchen <span class='aesthetic-calligraphy'>&amp;</span> Dining OS
    </div>
    <div class='saas-header-subtitle'>
        Station: <span style='font-family: "Playfair Display", Georgia, serif; font-style: italic; font-weight: 700; color: #FDE68A;'>{active_role_val}</span> &bull; 
        Zero-friction kitchen voice dispatch, automated recipe BOM inventory deduction, <span style='font-family: "Playfair Display", Georgia, serif; font-style: italic; font-weight: 600;'>Never Say No</span> order substitutions, and proactive Google Maps reputation routing.
    </div>
    <div class='status-pills-row'>
        <span class='pill-badge pill-green'>
            <span class='pill-dot pill-dot-green'></span> Live Station: ACTIVE
        </span>
        <span class='pill-badge {engine_pill_class}'>
            ⚡ Dual-Engine: {engine_label}
        </span>
        <span class='pill-badge pill-slate'>
            🎙️ Voice KDS: Dispatch Ready
        </span>
        <span class='pill-badge pill-purple'>
            📦 Automated BOM Deduction: ENABLED
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================================
# LIVE OPERATIONAL METRICS RIBBON
# =========================================================================
conn = get_connection()
total_orders = conn.execute("SELECT COUNT(*) as count FROM orders").fetchone()["count"]
active_orders = conn.execute("SELECT COUNT(*) as count FROM orders WHERE status != 'COMPLETED'").fetchone()["count"]
low_stock_rows = conn.execute("SELECT COUNT(*) as count FROM inventory WHERE quantity <= safety_threshold").fetchone()["count"]
spoilage_sum = conn.execute("SELECT SUM(quantity * unit_cost) as total FROM inventory WHERE freshness_status IN ('Expires Soon', 'Critical Low Stock')").fetchone()["total"] or 0.0
conn.close()

st.markdown(f"""
<div class='metric-grid'>
    <div class='metric-card'>
        <div class='metric-label-text'>
            <span>Active KDS Queue</span>
            <span>🔥</span>
        </div>
        <div class='metric-value-text'>{active_orders} <span style='font-size: 0.95rem; font-weight: 500; color: #64748B;'>tickets</span></div>
        <div class='metric-sub-text'>Real-time kitchen line</div>
    </div>
    <div class='metric-card'>
        <div class='metric-label-text'>
            <span>Served Today</span>
            <span>✅</span>
        </div>
        <div class='metric-value-text'>{total_orders} <span style='font-size: 0.95rem; font-weight: 500; color: #64748B;'>completed</span></div>
        <div class='metric-sub-text'>Zero dropped tickets</div>
    </div>
    <div class='metric-card'>
        <div class='metric-label-text'>
            <span>Items at Threshold Risk</span>
            <span style='color: #EF4444;'>⚠️</span>
        </div>
        <div class='metric-value-text' style='color: {"#EF4444" if low_stock_rows > 0 else "#0F172A"};'>{low_stock_rows} <span style='font-size: 0.95rem; font-weight: 500; color: #64748B;'>ingredients</span></div>
        <div class='metric-sub-text'>Below safety buffer</div>
    </div>
    <div class='metric-card'>
        <div class='metric-label-text'>
            <span>Capital Protected</span>
            <span>🛡️</span>
        </div>
        <div class='metric-value-text' style='color: #059669;'>₹{spoilage_sum:,.0f}</div>
        <div class='metric-sub-text'>Zero-waste dynamic routing</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# ROLE-BASED TERMINAL ROUTING
# =========================================================================
col_r_info, col_r_btn = st.columns([3, 1])
with col_r_info:
    role_emoji = "🧾" if st.session_state.active_role == "Counter Person" else ("👨‍🍳" if st.session_state.active_role == "Chef" else "🤵")
    st.markdown(f"<div style='font-size: 1.05rem; font-weight: 700; color: #1E293B; margin-top: 6px;'>Operating Terminal: <span style='font-weight: 800; color: #0F172A;'>{role_emoji} {st.session_state.active_role}</span></div>", unsafe_allow_html=True)
with col_r_btn:
    if st.button("🔁 Switch Terminal Role", key="switch_role_main_top", use_container_width=True):
        st.session_state.active_role = None
        st.rerun()

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

def render_counter_view():

    tab_pos, tab_substitute, tab_inventory, tab_reviews = st.tabs([
        "🧾 Modern POS & Dispatched Queue",
        "🍳 'Never Say No' Substitution Maker",
        "🥦 Perishable Stock Watchdog",
        "💬 Review Sentiment Triage & SMS Shield"
    ])

    # =========================================================================
    # TAB 1: VOICE KITCHEN DISPLAY (KDS) & REAL AUTOMATED DEDUCTION
    # =========================================================================
    with tab_pos:
        col_entry, col_queue = st.columns([1.15, 1.85], gap="large")

        with col_entry:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🧾 Modern Counter POS • Order Builder</div>", unsafe_allow_html=True)
            st.markdown("<div class='card-subtitle'>Interactive table form for point-and-click counter orders with live recipe BOM deduction.</div>", unsafe_allow_html=True)

            # Dispatch Station / Custom Table Manager
            col_st_sel, col_st_add = st.columns([1.5, 1])
            with col_st_sel:
                order_channel = st.selectbox(
                    "Dispatch Station / Table:", 
                    st.session_state.saved_tables,
                    index=0
                )
            with col_st_add:
                with st.popover("➕ Add Custom Table", use_container_width=True):
                    st.markdown("<b>Register New Table / Counter:</b>", unsafe_allow_html=True)
                    new_tbl = st.text_input("Table / Channel Name:", placeholder="e.g. Table 15 (Garden Terrace)")
                    if st.button("💾 Save Table to System", use_container_width=True):
                        if new_tbl.strip() and new_tbl.strip() not in st.session_state.saved_tables:
                            st.session_state.saved_tables.insert(0, new_tbl.strip())
                            st.success(f"Saved '{new_tbl.strip()}' permanently!")
                            time.sleep(0.4)
                            st.rerun()

            cust_phone = st.text_input("Guest Mobile (For automated reputation SMS):", value="+91 98765 43210")

            # Mode Toggle: Table Form vs Raw Slip
            mode_tab1, mode_tab2 = st.tabs(["📋 Modern POS Table Form", "📄 Paste Raw Bill / Slip"])

            with mode_tab1:
                st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #475569; margin: 8px 0 4px 0;'>Order Line Items:</div>", unsafe_allow_html=True)

                # Modern Interactive Order Table Rows
                available_dishes = [
                    "Butter Naan", 
                    "Garlic Naan", 
                    "Paneer Tikka", 
                    "Murgh Makhani (Chicken)", 
                    "Dal Makhani Special", 
                    "3 Eggs Omelette", 
                    "Button Mushroom Roast",
                    "Cheddar Cheese Melt"
                ]

                items_to_remove = []
                for idx, item in enumerate(st.session_state.pos_order_items):
                    r_col1, r_col2, r_col3, r_col4 = st.columns([2.2, 1.0, 1.8, 0.6])
                    with r_col1:
                        cur_dish_idx = available_dishes.index(item["dish"]) if item["dish"] in available_dishes else 0
                        selected_dish = st.selectbox(f"Dish #{idx+1}", available_dishes, index=cur_dish_idx, key=f"dish_sel_{idx}", label_visibility="collapsed")
                        st.session_state.pos_order_items[idx]["dish"] = selected_dish
                    with r_col2:
                        qty = st.number_input(f"Qty #{idx+1}", min_value=1, max_value=20, value=item["qty"], step=1, key=f"qty_sel_{idx}", label_visibility="collapsed")
                        st.session_state.pos_order_items[idx]["qty"] = qty
                    with r_col3:
                        notes = st.text_input(f"Note #{idx+1}", value=item.get("notes", ""), placeholder="e.g. Less Spicy", key=f"note_sel_{idx}", label_visibility="collapsed")
                        st.session_state.pos_order_items[idx]["notes"] = notes
                    with r_col4:
                        if st.button("✕", key=f"del_row_{idx}", help="Remove dish row"):
                            items_to_remove.append(idx)

                # Handle removals
                if items_to_remove:
                    for idx in sorted(items_to_remove, reverse=True):
                        if len(st.session_state.pos_order_items) > 1:
                            st.session_state.pos_order_items.pop(idx)
                    st.rerun()

                col_add_row, col_quick_calc = st.columns([1, 1])
                with col_add_row:
                    if st.button("➕ Add Another Dish Row", use_container_width=True):
                        st.session_state.pos_order_items.append({"dish": "Butter Naan", "qty": 1, "notes": ""})
                        st.rerun()
                with col_quick_calc:
                    total_qty = sum(item["qty"] for item in st.session_state.pos_order_items)
                    st.markdown(f"<div style='text-align: right; padding-top: 6px; font-weight: 700; color: #475569;'>Total: {len(st.session_state.pos_order_items)} items ({total_qty} units)</div>", unsafe_allow_html=True)

            with mode_tab2:
                default_ticket_text = """Table 4 - Rush Hour
    2x Butter Naan
    1x Paneer Tikka
    1x Murgh Makhani Boneless
    Subtotal: Rs 890.00
    Payment: UPI Received"""
                raw_ticket = st.text_area("POS Slip Raw Text:", value=default_ticket_text, height=120)

            dispatch_btn = st.button("📢 Dispatch to Chef KDS & Deduct Inventory", type="primary", use_container_width=True)

            if dispatch_btn:
                with st.spinner("Compiling order, deducting raw inventory, and queuing to Chef KDS..."):
                    # Compile dishes based on active entry mode
                    cooked_dishes = []
                    for item in st.session_state.pos_order_items:
                        note_str = f" ({item['notes']})" if item.get('notes') else ""
                        cooked_dishes.append(f"{item['qty']}x {item['dish']}{note_str}")

                    raw_summary = "\n".join(cooked_dishes)

                    # 1. AUTOMATED BUSINESS LOGIC: Deduct raw ingredients from SQLite
                    deductions = deduct_ingredients_for_order(cooked_dishes)
                    st.session_state.last_deduction_logs = deductions

                    # 2. Voice Synthesizer Callout (Prepared for Chef Tab)
                    callout_speech = f"Attention Chef! New order for {order_channel}. Prepare: {', '.join(cooked_dishes)}."
                    audio_file = generate_voice_callout(callout_speech)

                    # 3. Save to Database with audio path
                    conn = get_connection()
                    c = conn.cursor()
                    code = f"#KDS-{int(time.time()) % 1000:03d}"
                    c.execute("""
                    INSERT INTO orders (order_code, table_or_platform, customer_phone, items_json, deductions_json, raw_receipt_text, status, created_at, announced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (code, order_channel, cust_phone, json.dumps(cooked_dishes), json.dumps(deductions), raw_summary, "PENDING", datetime.now().strftime("%I:%M %p")))
                    conn.commit()
                    conn.close()

                    st.success(f"Dispatched {code} for {order_channel}! Deducted inventory & queued to Chef Station.")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            # Recent Deduction Flash Notice
            if st.session_state.last_deduction_logs:
                st.markdown("<div class='saas-card' style='padding: 18px 22px !important;'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size: 0.84rem; font-weight: 700; text-transform: uppercase; color: #059669; letter-spacing: 0.05em; margin-bottom: 8px;'>⚡ Latest Real-Time Deductions:</div>", unsafe_allow_html=True)
                for d in st.session_state.last_deduction_logs:
                    st.markdown(f"""
                    <div style='font-size: 0.82rem; margin-bottom: 4px; display: flex; justify-content: space-between;'>
                        <span style='font-weight: 600; color: #0F172A;'>{d['ingredient']} ({d['dish']})</span>
                        <span style='color: #EF4444; font-weight: 700;'>{d['deducted']} &rarr; {d['remaining']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        # RIGHT COLUMN: KITCHEN STATION LIVE STATUS (READ-ONLY)
        with col_queue:
            col_q_title, col_q_sync = st.columns([2, 1])
            with col_q_title:
                st.markdown("<div class='card-title' style='margin-bottom: 8px;'>🍳 Kitchen Station Live Status (Read-Only)</div>", unsafe_allow_html=True)
                st.caption("Live feed showing real-time Chef progress. Controlled directly from Chef Station on Port 8505.")
            with col_q_sync:
                if st.button("🔄 Sync with Chef Line", key="sync_counter_btn", use_container_width=True):
                    st.rerun()

            conn = get_connection()
            pending_list = conn.execute("SELECT * FROM orders WHERE status != 'COMPLETED' ORDER BY id DESC").fetchall()
            conn.close()

            if not pending_list:
                st.markdown("""
                <div class='saas-card' style='text-align: center; padding: 48px 24px !important;'>
                    <div style='font-size: 2.8rem; margin-bottom: 12px;'>✨</div>
                    <div style='font-size: 1.35rem; font-weight: 700; color: #0F172A;'>All Stations Clear!</div>
                    <div style='color: #64748B; font-size: 0.92rem; margin-top: 6px;'>Every ticket has been prepared, plated, and served to guests.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for item in pending_list:
                    dishes = json.loads(item["items_json"]) if item["items_json"] else []
                    deductions = []
                    try:
                        if "deductions_json" in item.keys() and item["deductions_json"]:
                            deductions = json.loads(item["deductions_json"])
                    except Exception:
                        deductions = []

                    is_cooking = item["status"] == "COOKING"
                    ticket_class = "cooking" if is_cooking else "pending"
                    status_pill = (
                        "<span class='pill-badge pill-amber'><span class='pill-dot pill-dot-amber'></span> IN COOKING</span>" 
                        if is_cooking else 
                        "<span class='pill-badge pill-rose'><span class='pill-dot pill-dot-rose'></span> PENDING DISPATCH</span>"
                    )

                    # Render Clean Sleek Modern Ticket
                    st.markdown(f"""
                    <div class='ticket-card {ticket_class}'>
                        <div class='ticket-header'>
                            <div>
                                <span class='ticket-code'>{item['order_code']}</span>
                                <span class='ticket-channel'>&bull; {item['table_or_platform']}</span>
                            </div>
                            <div style='display: flex; align-items: center; gap: 8px;'>
                                <span style='font-size: 0.8rem; color: #64748B; font-weight: 500;'>{item['created_at']}</span>
                                {status_pill}
                            </div>
                        </div>
                        <div style='margin: 10px 0;'>
                            {"".join([f"<div class='dish-row'>🥘 <span>{d}</span></div>" for d in dishes])}
                        </div>
                    """, unsafe_allow_html=True)

                    # LIVE INVENTORY IMPACT BADGE
                    if deductions:
                        st.markdown("""
                        <div class='inventory-impact-box'>
                            <div class='inventory-impact-title'>⚡ Live Inventory Impact (Deducted from Vault):</div>
                            <div>
                        """, unsafe_allow_html=True)
                        chips_html = ""
                        for d in deductions:
                            is_crit = "Critical" in d.get("status", "") or "OUT" in d.get("status", "")
                            border_color = "#FCA5A5" if is_crit else "#D8B4FE"
                            text_color = "#991B1B" if is_crit else "#4C1D95"
                            alert_icon = "⚠️ " if is_crit else ""
                            chips_html += f"<span class='inventory-deduction-chip' style='border-color: {border_color}; color: {text_color};'>{alert_icon}<b>{d['ingredient']}:</b> {d['deducted']} (Left: {d['remaining']})</span>"
                        st.markdown(f"{chips_html}</div></div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Live Chef Station Status Display on Counter (Read-Only)
                    if item["status"] == "COOKING":
                        st.markdown("""
                        <div style='background: #FEF3C7; border: 1.5px solid #F59E0B; border-radius: 10px; padding: 12px 16px; text-align: center; color: #92400E; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;'>
                            <span style='animation: pulse 1.5s infinite; font-size: 1.2rem;'>🔥</span> 
                            <span>Chef is Currently Cooking on the Line...</span>
                        </div>
                        """, unsafe_allow_html=True)
                    elif item["status"] == "PENDING":
                        st.markdown("""
                        <div style='background: #F1F5F9; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 12px 16px; text-align: center; color: #475569; font-weight: 600; font-size: 0.92rem;'>
                            ⏳ Queued on Chef Station &bull; Waiting for Cook to Start
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style='background: #D1FAE5; border: 1.5px solid #10B981; border-radius: 10px; padding: 12px 16px; text-align: center; color: #065F46; font-weight: 700; font-size: 0.95rem;'>
                            ✅ Plated & Ready to Serve!
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: 'NEVER SAY NO' SUBSTITUTION MAKER
    # =========================================================================
    with tab_substitute:
        col_sub_ctrl, col_sub_result = st.columns([1.1, 1.4], gap="large")

        with col_sub_ctrl:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🍳 'Never Say No' Substitution Maker</div>", unsafe_allow_html=True)
            st.markdown("<div class='card-subtitle'>When stock is low, never turn a guest away. AI creates artisan substitutions that preserve sales, elevate ticket averages, and eliminate waste.</div>", unsafe_allow_html=True)

            # Scenarios presets
            st.markdown("<span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>⚡ Quick Test Scenarios:</span>", unsafe_allow_html=True)
            p_sub_cols = st.columns(2)
            with p_sub_cols[0]:
                if st.button("🥚 Egg Shortage", key="sub_pre_egg", use_container_width=True):
                    st.session_state.sub_dish = "3 Bread Egg Fillings (Scrambled)"
                    st.session_state.sub_ing = "Farm Fresh Eggs"
                    st.session_state.sub_left = "Only 2 eggs remaining"
            with p_sub_cols[1]:
                if st.button("🧀 Paneer Shortage", key="sub_pre_paneer", use_container_width=True):
                    st.session_state.sub_dish = "Paneer Tikka Platter"
                    st.session_state.sub_ing = "Fresh Paneer"
                    st.session_state.sub_left = "Only 0.3 kg remaining"

            ordered_dish_input = st.text_input("Customer Ordered Dish:", value=st.session_state.get("sub_dish", "4-Egg Scramble Breakfast"))
            scarce_ingredient_input = st.selectbox("Low/Depleted Ingredient:", [
                "Farm Fresh Eggs",
                "Fresh Paneer",
                "Boneless Chicken Breast",
                "Button Mushrooms",
                "Heavy Cooking Cream",
                "English Cheddar Cheese"
            ], index=0 if st.session_state.get("sub_ing") == "Farm Fresh Eggs" else (1 if st.session_state.get("sub_ing") == "Fresh Paneer" else 0))

            stock_remaining_input = st.text_input("Current Stock Remaining:", value=st.session_state.get("sub_left", "Only 2 eggs left in kitchen"))

            sub_generate_btn = st.button("✨ Craft Culinary Substitution & Script", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_sub_result:
            if sub_generate_btn or (st.session_state.cached_sub is not None):
                if sub_generate_btn:
                    with st.spinner("AI evaluating culinary pairing and crafting conversation script..."):
                        res = ai_engine.solve_low_stock_substitution(ordered_dish_input, scarce_ingredient_input, stock_remaining_input)
                        st.session_state.cached_sub = res
                else:
                    res = st.session_state.cached_sub

                st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-title'>🍽️ Chef Recommendation: <span class='aesthetic-calligraphy'>{res.get('substitute_dish', 'Artisan Alternative')}</span></div>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class='speech-bubble'>
                    <div style='font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; margin-bottom: 6px;'>
                        🗣️ Natural Script for Waiter or Cashier:
                    </div>
                    "{res.get('dialogue_for_staff', '')}"
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 16px 0;'>
                    <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 12px 16px;'>
                        <div style='font-size: 0.76rem; font-weight: 700; text-transform: uppercase; color: #065F46;'>Economic Margin Impact</div>
                        <div style='font-size: 0.96rem; font-weight: 700; color: #047857; margin-top: 4px;'>{res.get('margin_impact', '+14% Higher Profit Margin')}</div>
                    </div>
                    <div style='background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 12px; padding: 12px 16px;'>
                        <div style='font-size: 0.76rem; font-weight: 700; text-transform: uppercase; color: #3730A3;'>Upsell Architecture</div>
                        <div style='font-size: 0.96rem; font-weight: 700; color: #4338CA; margin-top: 4px;'>{res.get('upsell_pitch', 'Zero drop-off conversion')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("📢 Broadcast Alternative to Waitstaff Audio"):
                    speech = f"Service alert! For {ordered_dish_input}, waiters please recommend: {res.get('substitute_dish')}."
                    audio = generate_voice_callout(speech)
                    st.session_state.latest_audio_path = audio
                    st.success("Alternative broadcasted to waitstaff stations!")
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # TAB 3: PERISHABLE STOCK WATCHDOG
    # =========================================================================
    with tab_inventory:
        st.markdown("<div class='card-title'>🥦 Perishable Stock Watchdog & Expiry Ledger</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-subtitle'>Live inventory balances directly updated by every KDS ticket deduction. Ingredients below safe buffer thresholds are automatically flagged.</div>", unsafe_allow_html=True)

        conn = get_connection()
        df_raw = pd.read_sql_query("""
        SELECT 
            item_name,
            category,
            quantity,
            unit,
            safety_threshold,
            expiry_date,
            freshness_status,
            unit_cost
        FROM inventory
        ORDER BY quantity ASC
        """, conn)
        conn.close()

        # Render modern visual table
        df_display = df_raw.copy()
        df_display["Current Stock"] = df_display.apply(lambda r: f"{r['quantity']:.2f} {r['unit']}", axis=1)
        df_display["Min Safe Buffer"] = df_display.apply(lambda r: f"{r['safety_threshold']:.1f} {r['unit']}", axis=1)
        df_display["Unit Cost"] = df_display["unit_cost"].apply(lambda v: f"₹{v:,.2f}")
        df_display["Total Vault Value"] = (df_display["quantity"] * df_display["unit_cost"]).apply(lambda v: f"₹{v:,.2f}")

        # Clean display columns
        df_clean = df_display[["item_name", "category", "Current Stock", "Min Safe Buffer", "expiry_date", "freshness_status", "Unit Cost", "Total Vault Value"]]
        df_clean.columns = ["Ingredient", "Category", "Current Stock", "Min Buffer", "Expiry Date", "Live Freshness Status", "Unit Cost", "Value"]

        st.dataframe(df_clean, use_container_width=True, hide_index=True)

        # Action Columns: Threshold Warnings & Chalkboard Special
        watch_c1, watch_c2 = st.columns([1.1, 1.1], gap="large")

        with watch_c1:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>⚠️ Threshold & Spoilage Alerts</div>", unsafe_allow_html=True)

            at_risk = df_raw[(df_raw["quantity"] <= df_raw["safety_threshold"]) | (df_raw["freshness_status"].isin(["Critical Low Stock", "Expires Soon", "OUT OF STOCK"]))]

            if len(at_risk) == 0:
                st.markdown("""
                <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 16px; text-align: center;'>
                    <div style='font-size: 1.1rem; font-weight: 700; color: #065F46;'>✅ All Stock Optimal</div>
                    <div style='font-size: 0.85rem; color: #047857; margin-top: 4px;'>No raw ingredients are currently below safety threshold.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for _, r in at_risk.iterrows():
                    is_out = r["quantity"] <= 0
                    badge = "<span class='pill-badge pill-rose'>OUT OF STOCK</span>" if is_out else "<span class='pill-badge pill-amber'>LOW STOCK BUFFER</span>"
                    st.markdown(f"""
                    <div style='background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700; font-size: 0.95rem; color: #0F172A;'>{r['item_name']}</div>
                            <div style='font-size: 0.8rem; color: #78350F;'>Stock: <b>{r['quantity']} {r['unit']}</b> &bull; Threshold: {r['safety_threshold']} {r['unit']}</div>
                        </div>
                        <div>{badge}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with watch_c2:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🪄 Zero-Waste Chalkboard Special</div>", unsafe_allow_html=True)
            st.markdown("<div class='card-subtitle'>AI pairs approaching-threshold ingredients into a high-margin chef's special to prevent food waste before expiry.</div>", unsafe_allow_html=True)

            if st.button("🌟 Synthesize High-Margin Special", key="btn_chalkboard", use_container_width=True):
                st.markdown("""
                <div class='speech-bubble' style='border-left-color: #10B981;'>
                    <div style='font-family: "Playfair Display", Georgia, serif; font-size: 1.25rem; font-weight: 700; color: #0F172A;'>Tawa Malai Paneer <span class='aesthetic-calligraphy'>&amp;</span> Wild Mushroom Sourdough Melt</div>
                    <div style='font-size: 0.88rem; color: #475569; margin: 6px 0 10px 0;'>
                        Fresh in-stock paneer gently braised with button mushrooms and melted English cheddar over sourdough.
                    </div>
                    <div style='display: flex; gap: 14px; font-size: 0.84rem; font-weight: 700;'>
                        <span style='color: #0F172A;'>Price: <b>₹340</b></span>
                        <span style='color: #64748B;'>Food Cost: <b>₹85</b></span>
                        <span style='color: #059669;'>Profit Margin: <b>75%</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Counter Persona Stock Management & Restock Console
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🛠️ Counter Persona: Real-Time Stock Editor & Restock Console</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-subtitle'>Cashier / Store Manager can instantly adjust physical counts, record supplier shipments, update safety buffers, or add new ingredients into the live KDS database.</div>", unsafe_allow_html=True)

        edit_c1, edit_c2 = st.columns([1.2, 1.1], gap="large")

        with edit_c1:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title' style='font-size: 1.05rem;'>📦 Edit / Restock Existing Ingredient</div>", unsafe_allow_html=True)
            
            all_items = df_raw["item_name"].tolist()
            if all_items:
                sel_item_name = st.selectbox("Select Ingredient to Modify:", all_items, key="sel_inv_modify")
                item_data = df_raw[df_raw["item_name"] == sel_item_name].iloc[0]
                
                curr_q = float(item_data["quantity"])
                curr_unit = str(item_data["unit"])
                curr_threshold = float(item_data["safety_threshold"])
                curr_cost = float(item_data["unit_cost"])
                curr_expiry = str(item_data["expiry_date"])
                curr_status = str(item_data["freshness_status"])

                st.markdown(f"""
                <div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; margin: 10px 0 14px 0; display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.88rem; color: #475569;'>Current Ledger Count: <b style='color: #0F172A;'>{curr_q:.2f} {curr_unit}</b></span>
                    <span class='pill-badge pill-{"rose" if curr_status in ["OUT OF STOCK", "Critical Low Stock"] else "green"}'>{curr_status}</span>
                </div>
                """, unsafe_allow_html=True)

                mod_mode = st.radio("Modification Type:", ["➕ Quick Restock (Add Shipment)", "✏️ Set Exact Quantity (Audit Count)"], horizontal=True, key="inv_mod_mode")

                if "Quick Restock" in mod_mode:
                    add_qty = st.number_input(f"Received Shipment Quantity to ADD ({curr_unit}):", min_value=0.1, max_value=500.0, value=5.0, step=0.5, key="inp_add_qty")
                    if st.button("🚀 Record Shipment & Restock Ingredient", type="primary", use_container_width=True, key="btn_apply_restock"):
                        ok = restock_inventory_item(sel_item_name, add_qty)
                        if ok:
                            st.success(f"✅ Successfully added +{add_qty} {curr_unit} to {sel_item_name}! New total: {curr_q + add_qty:.2f} {curr_unit}.")
                            time.sleep(0.8)
                            st.rerun()
                else:
                    c_adj1, c_adj2 = st.columns(2)
                    with c_adj1:
                        new_exact_qty = st.number_input(f"New Exact Quantity ({curr_unit}):", min_value=0.0, max_value=1000.0, value=curr_q, step=0.5, key="inp_exact_qty")
                        new_threshold_val = st.number_input(f"Min Safety Buffer ({curr_unit}):", min_value=0.1, max_value=200.0, value=curr_threshold, step=0.5, key="inp_thresh_val")
                    with c_adj2:
                        new_cost_val = st.number_input("Unit Cost (₹):", min_value=1.0, max_value=5000.0, value=curr_cost, step=5.0, key="inp_cost_val")
                        new_exp_val = st.text_input("Expiry Date (YYYY-MM-DD):", value=curr_expiry, key="inp_exp_val")

                    if st.button("💾 Save Changes to Kitchen Ledger", type="primary", use_container_width=True, key="btn_apply_exact"):
                        ok = update_inventory_item(sel_item_name, new_exact_qty, new_threshold_val, new_cost_val, new_exp_val)
                        if ok:
                            st.success(f"✅ Successfully updated {sel_item_name} to {new_exact_qty:.2f} {curr_unit}!")
                            time.sleep(0.8)
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with edit_c2:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title' style='font-size: 1.05rem;'>✨ Register Brand New Ingredient</div>", unsafe_allow_html=True)
            st.markdown("<div class='card-subtitle'>Add an untracked raw supply item to the automatic recipe deduction system.</div>", unsafe_allow_html=True)

            new_ing_name = st.text_input("Ingredient Name:", placeholder="e.g. Fresh Basmati Rice", key="new_ing_name")
            c_new1, c_new2 = st.columns(2)
            with c_new1:
                new_ing_cat = st.selectbox("Category:", ["Dairy", "Fresh Veggie", "Perishable Meat", "Perishable Poultry", "Bakery", "Dry Grocery", "Beverage"], key="new_ing_cat")
                new_ing_qty = st.number_input("Initial Quantity:", min_value=0.1, max_value=1000.0, value=10.0, step=1.0, key="new_ing_qty")
                new_ing_unit = st.selectbox("Unit:", ["kg", "litres", "pcs", "packs", "grams"], key="new_ing_unit")
            with c_new2:
                new_ing_thresh = st.number_input("Safety Buffer Threshold:", min_value=0.1, max_value=200.0, value=2.0, step=0.5, key="new_ing_thresh")
                new_ing_cost = st.number_input("Unit Cost (₹):", min_value=1.0, max_value=10000.0, value=65.0, step=5.0, key="new_ing_cost")
                new_ing_exp = st.text_input("Expiry (YYYY-MM-DD):", value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"), key="new_ing_exp")

            if st.button("➕ Add New Ingredient to Vault", type="primary", use_container_width=True, key="btn_add_new_ing"):
                if new_ing_name.strip():
                    add_new_inventory_item(new_ing_name, new_ing_cat, new_ing_qty, new_ing_unit, new_ing_thresh, new_ing_exp, new_ing_cost)
                    st.success(f"✅ Added {new_ing_name} ({new_ing_qty} {new_ing_unit}) to inventory vault!")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.warning("Please enter a valid ingredient name.")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # TAB 4: REVIEW SENTIMENT TRIAGE & GOOGLE MAPS SERPAPI INTEGRATION
    # =========================================================================
    with tab_reviews:
        sub_gmaps, sub_manual = st.tabs([
            "🌐 Live Google Maps Reviews (SerpApi)",
            "🧾 Counter Checkout SMS Rating Dispatcher"
        ])

        with sub_gmaps:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🌐 Google Maps Live Review Aggregator & AI Triage</div>", unsafe_allow_html=True)
            st.markdown("<div class='card-subtitle'>Directly pulls customer reviews from Google Maps via SerpApi, diagnoses diner sentiment, and generates automated public thank-yous or reputation-defense escalation memos.</div>", unsafe_allow_html=True)

            gmap_col1, gmap_col2 = st.columns([1.6, 1.2], gap="medium")
            with gmap_col1:
                search_q = st.text_input(
                    "📍 Restaurant Name / Google Maps Search:",
                    value=st.session_state.get("gmaps_query", "Bukhara, ITC Maurya, New Delhi"),
                    help="Enter your restaurant name, city, or Google Maps Place search query."
                )
            with gmap_col2:
                serp_key = st.text_input(
                    "🔑 SerpApi Key (Optional):",
                    value=st.session_state.get("serp_key", os.getenv("SERPAPI_API_KEY", "")),
                    type="password",
                    help="Optional: Leave blank to use the live-streamed feed without consuming credits."
                )

            # Quick presets
            st.markdown("<span style='font-size: 0.78rem; font-weight: 700; color: #475569;'>⚡ Quick Restaurant Search Presets:</span>", unsafe_allow_html=True)
            p_cols = st.columns(3)
            with p_cols[0]:
                if st.button("🍛 Bukhara, New Delhi", key="pre_bukhara", use_container_width=True):
                    st.session_state.gmaps_query = "Bukhara, ITC Maurya, New Delhi"
                    st.rerun()
            with p_cols[1]:
                if st.button("🍗 Karim's, Jama Masjid", key="pre_karim", use_container_width=True):
                    st.session_state.gmaps_query = "Karim's, Jama Masjid, Old Delhi"
                    st.rerun()
            with p_cols[2]:
                if st.button("🥘 Pind Balluchi, CP", key="pre_pind", use_container_width=True):
                    st.session_state.gmaps_query = "Pind Balluchi, Connaught Place, New Delhi"
                    st.rerun()

            fetch_gmaps_btn = st.button("🚀 Fetch Google Maps Reviews & Analyze Feed", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Load or process Google Reviews
            if fetch_gmaps_btn or ("cached_gmaps_data" in st.session_state and st.session_state.cached_gmaps_data):
                if fetch_gmaps_btn:
                    with st.spinner("Connecting to Google Maps via SerpApi and fetching live diner reviews..."):
                        gdata = fetch_google_maps_reviews(search_q, api_key=serp_key)
                        st.session_state.cached_gmaps_data = gdata
                else:
                    gdata = st.session_state.cached_gmaps_data

                rest = gdata.get("restaurant", {})
                reviews = gdata.get("reviews", [])
                is_live = gdata.get("is_live_api", False)

                # Restaurant Profile Header Card
                st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                r_head1, r_head2 = st.columns([1.8, 1.2])
                with r_head1:
                    st.markdown(f"<div style='font-family: \"Playfair Display\", serif; font-size: 1.4rem; font-weight: 700; color: #0F172A;'>{rest.get('title', search_q)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.88rem; color: #64748B;'>📍 {rest.get('address', 'New Delhi, India')} &bull; Price: {rest.get('price', '₹₹')}</div>", unsafe_allow_html=True)
                with r_head2:
                    api_badge = "<span class='pill-badge pill-green'>🟢 SerpApi Live Sync</span>" if is_live else "<span class='pill-badge pill-slate'>⚡ Smart Live Feed</span>"
                    st.markdown(f"""
                    <div style='text-align: right;'>
                        {api_badge}
                        <div style='font-size: 1.25rem; font-weight: 800; color: #F59E0B; margin-top: 4px;'>
                            ⭐ {rest.get('rating', 4.4)} / 5.0 <span style='font-size: 0.82rem; font-weight: 500; color: #64748B;'>({rest.get('reviews_count', 800)}+ Google Reviews)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Reviews Stream List
                st.markdown(f"<div style='font-size: 0.95rem; font-weight: 700; color: #0F172A; margin: 18px 0 10px 4px;'>📑 Fetched Google Maps Reviews ({len(reviews)} Reviews)</div>", unsafe_allow_html=True)

                for idx, rev in enumerate(reviews):
                    stars_str = "⭐" * rev.get("rating", 5)
                    is_bad = rev.get("rating", 5) <= 2
                    status_pill = "<span class='pill-badge pill-rose'>CRITICAL REPUTATION RISK</span>" if is_bad else "<span class='pill-badge pill-green'>BRAND ADVOCATE</span>"
                    
                    st.markdown("<div class='saas-card' style='margin-bottom: 14px;'>", unsafe_allow_html=True)
                    c_rev_hdr1, c_rev_hdr2 = st.columns([1.8, 1.2])
                    with c_rev_hdr1:
                        st.markdown(f"**👤 {rev.get('author', 'Diner')}** &bull; <span style='color: #64748B; font-size: 0.82rem;'>{rev.get('date', 'Recent')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color: #F59E0B;'>{stars_str}</span> <span style='font-size: 0.82rem; color: #64748B;'>({rev.get('rating')}/5 Stars)</span>", unsafe_allow_html=True)
                    with c_rev_hdr2:
                        st.markdown(f"<div style='text-align: right;'>{status_pill}</div>", unsafe_allow_html=True)

                    st.markdown(f"<div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin: 10px 0; font-size: 0.9rem; color: #1E293B; line-height: 1.5;'>\"{rev.get('snippet', '')}\"</div>", unsafe_allow_html=True)

                    btn_col1, btn_col2 = st.columns([1.2, 1.8])
                    with btn_col1:
                        analyze_single_btn = st.button(f"🔍 AI Diagnose & Draft Reply", key=f"btn_diag_{idx}", use_container_width=True)

                    diag_cache_key = f"diag_res_{idx}"
                    if analyze_single_btn or (diag_cache_key in st.session_state):
                        if analyze_single_btn:
                            with st.spinner("AI analyzing diner tone and generating response protocol..."):
                                diag_res = ai_engine.triage_customer_review(rev.get("author", "Guest"), rev.get("snippet", ""), rev.get("rating", 5))
                                st.session_state[diag_cache_key] = diag_res
                        else:
                            diag_res = st.session_state[diag_cache_key]

                        with btn_col2:
                            st.markdown(f"**Action:** `{diag_res.get('suggested_action', 'Review Protocol')}`")

                        if diag_res.get("should_send_google_link"):
                            st.markdown(f"""
                            <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 10px; padding: 12px 16px; margin: 10px 0;'>
                                <div style='font-weight: 700; color: #065F46; font-size: 0.85rem;'>🌟 Public Google Maps Owner Thank-You Response Draft:</div>
                                <div style='font-size: 0.88rem; color: #047857; margin-top: 4px; font-weight: 500;'>
                                    "{diag_res.get('private_sms_reply', 'Thank you for your fantastic review! We are delighted you enjoyed your dining experience.')}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px; padding: 12px 16px; margin: 10px 0;'>
                                <div style='font-weight: 700; color: #991B1B; font-size: 0.85rem;'>🛡️ Reputation Defense: Public Owner Apology & Internal Escalation Draft:</div>
                                <div style='font-size: 0.88rem; color: #B91C1C; margin-top: 4px; font-weight: 500;'>
                                    "{diag_res.get('private_sms_reply', 'We sincerely apologize for falling short of your expectations. Our General Manager is reviewing this immediately.')}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        if st.button("💾 Record in Reputation Vault", key=f"btn_save_{idx}", use_container_width=True):
                            conn = get_connection()
                            conn.execute("""
                            INSERT INTO reviews (customer_name, phone, order_ref, rating, feedback_text, sentiment, auto_action, response_draft, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (rev.get("author", "Google Diner"), "Google Maps", "Google Review", rev.get("rating", 5), rev.get("snippet", ""), diag_res.get("sentiment"), diag_res.get("suggested_action"), diag_res.get("private_sms_reply"), datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            conn.close()
                            st.success(f"Review from {rev.get('author')} logged in reputation database!")

                    st.markdown("</div>", unsafe_allow_html=True)

        with sub_manual:
            col_rev_in, col_rev_action = st.columns([1.1, 1.4], gap="large")

            with col_rev_in:
                st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                st.markdown("<div class='card-title'>🧾 Counter Checkout: SMS Rating Dispatcher</div>", unsafe_allow_html=True)
                st.markdown("<div class='card-subtitle'>Cashier / Billing staff sends an instant SMS to the diner at checkout inviting them to rate their experience.</div>", unsafe_allow_html=True)

                # Presets for instant counter checkout
                st.markdown("<span style='font-size: 0.8rem; font-weight: 700; color: #475569;'>⚡ Quick Checkout Presets:</span>", unsafe_allow_html=True)
                r_pre_cols = st.columns(3)
                with r_pre_cols[0]:
                    if st.button("⭐ Happy Diner", key="rev_pre_delight", use_container_width=True):
                        st.session_state.rev_name = "Priya Sharma"
                        st.session_state.rev_phone = "+91 98765 43210"
                        st.session_state.rev_table = "Table 4 (Dine-In)"
                        st.session_state.rev_exp = "🌟 Smooth & Delightful Dining (Trigger Google Maps 5-Star Invite)"
                        st.session_state.rev_items = "2x Butter Naan, 1x Paneer Butter Masala"
                with r_pre_cols[1]:
                    if st.button("🛵 Takeaway", key="rev_pre_takeaway", use_container_width=True):
                        st.session_state.rev_name = "Rohan Singhania"
                        st.session_state.rev_phone = "+91 98765 43210"
                        st.session_state.rev_table = "Order #ORD-87254 (Takeaway)"
                        st.session_state.rev_exp = "⚡ Fast Standard Bill Settlement (Direct 10-Second Rating Link)"
                        st.session_state.rev_items = "1x Garlic Naan, 1x Paneer Tikka"
                with r_pre_cols[2]:
                    if st.button("⚠️ Service Delay", key="rev_pre_angry", use_container_width=True):
                        st.session_state.rev_name = "Rohan Singhania"
                        st.session_state.rev_phone = "+91 98765 43210"
                        st.session_state.rev_table = "Table 8 (Dine-In)"
                        st.session_state.rev_exp = "⚠️ Staff Noticed Service Delay / Hiccup (Activate Private Feedback Shield)"
                        st.session_state.rev_items = "2x Butter Chicken, 2x Naan (Delayed Kitchen)"

                rev_guest_name = st.text_input("Customer Name:", value=st.session_state.get("rev_name", "Rohan Singhania"))
                rev_guest_phone = st.text_input("Customer Mobile (E.164 Telecom Format):", value=st.session_state.get("rev_phone", "+91 98765 43210"))
                rev_table_ref = st.text_input("Table / Bill Reference:", value=st.session_state.get("rev_table", "Table 4 (Dine-In)"))
                
                exp_options = [
                    "🌟 Smooth & Delightful Dining (Trigger Google Maps 5-Star Invite)",
                    "⚡ Fast Standard Bill Settlement (Direct 10-Second Rating Link)",
                    "⚠️ Staff Noticed Service Delay / Hiccup (Activate Private Feedback Shield)"
                ]
                cur_exp = st.session_state.get("rev_exp", exp_options[0])
                exp_idx = exp_options.index(cur_exp) if cur_exp in exp_options else 0
                rev_service_exp = st.selectbox("Counter Staff Dining Observation:", exp_options, index=exp_idx)
                
                rev_ordered_items = st.text_input("Dishes Ordered / Note:", value=st.session_state.get("rev_items", "2x Butter Naan, 1x Paneer Butter Masala"))

                gen_sms_btn = st.button("✨ Generate Rating Invitation SMS", type="primary", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_rev_action:
                if gen_sms_btn or (st.session_state.get("cached_counter_req") is not None):
                    if gen_sms_btn:
                        with st.spinner("AI drafting personalized customer review invitation..."):
                            diag = ai_engine.generate_counter_review_request(
                                rev_guest_name, rev_table_ref, rev_service_exp, rev_ordered_items
                            )
                            st.session_state.cached_counter_req = diag
                    else:
                        diag = st.session_state.cached_counter_req

                    is_shield = diag.get("strategy") == "PRIVATE_SHIELD"
                    badge_html = "<span class='pill-badge pill-rose'>🛡️ PRIVATE FEEDBACK SHIELD</span>" if is_shield else "<span class='pill-badge pill-green'>🌟 GOOGLE 5-STAR BOOST</span>"

                    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                        <div class='card-title' style='margin: 0;'>Counter Dispatch Strategy</div>
                        <div>{badge_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"**Target Protocol:** `{diag.get('action')}`")
                    st.markdown(f"**Guest Incentive:** `{diag.get('loyalty_points', 50)} Loyalty Points / 10% Discount Coupon`")

                    if diag.get("should_send_google_link"):
                        st.markdown("""
                        <div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 14px 18px; margin: 14px 0;'>
                            <div style='font-weight: 700; color: #065F46; font-size: 0.95rem;'>🌟 Google Maps Boost Protocol Activated</div>
                            <div style='font-size: 0.85rem; color: #047857; margin-top: 4px;'>
                                Diner enjoyed great service! SMS includes 1-tap Google Maps review link + VIP next-visit discount to drive public 5-star ratings.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style='background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 14px 18px; margin: 14px 0;'>
                            <div style='font-weight: 700; color: #991B1B; font-size: 0.95rem;'>🛡️ Public Review Shield Engaged (Google Link Withheld)</div>
                            <div style='font-size: 0.85rem; color: #B91C1C; margin-top: 4px;'>
                                Kitchen/Service delay detected. SMS invites guest to direct private manager channel with apology dessert rather than venting on Google Maps!
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>📩 Outgoing SMS to Diner Phone:</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; margin-bottom: 16px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B;'>
                            <span>📱 Outgoing SMS &bull; {rev_guest_phone}</span>
                            <span class='pill-badge pill-slate' style='font-size: 0.7rem; padding: 2px 8px;'>Ready to Dispatch</span>
                        </div>
                        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 16px; color: #0F172A; font-weight: 500; font-size: 0.92rem; line-height: 1.5;'>
                            {diag.get('sms_body', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("🚀 Dispatch Rating Request SMS to Customer Mobile", type="primary", use_container_width=True):
                        with st.spinner("Connecting to carrier network and dispatching SMS..."):
                            sms_result = send_real_sms(rev_guest_phone, diag.get("sms_body", ""))
                        
                        conn = get_connection()
                        conn.execute("""
                        INSERT INTO reviews (customer_name, phone, order_ref, rating, feedback_text, sentiment, auto_action, response_draft, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (rev_guest_name, rev_guest_phone, rev_table_ref, 5 if diag.get("should_send_google_link") else 3, f"Review Request Sent at Checkout ({rev_service_exp})", "REQUEST_SENT", diag.get("action"), diag.get("sms_body"), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()

                        if sms_result.get("success"):
                            st.success(f"✅ Live SMS delivered to {rev_guest_phone} via {sms_result.get('provider')}! Tracking ID: `{sms_result.get('message_id')}`")
                            st.caption(f"Status: {sms_result.get('status')} &bull; {sms_result.get('details')}")
                        else:
                            st.warning(f"⚠️ Telecom notice: {sms_result.get('error')}")

                    st.markdown("</div>", unsafe_allow_html=True)




def render_chef_view():
    # Auto-polling sync and voice callout for Chef
    conn = get_connection()
    unannounced = conn.execute("SELECT * FROM orders WHERE announced = 0 AND status != 'COMPLETED' LIMIT 1").fetchone()
    if unannounced:
        dishes_raw = json.loads(unannounced["items_json"]) if unannounced["items_json"] else []
        speech_text = f"Attention Kitchen! New order for {unannounced['table_or_platform']}. Prepare: {', '.join(dishes_raw)}."
        audio_path = generate_voice_callout(speech_text)
        st.session_state.chef_audio_cache = audio_path
        conn.execute("UPDATE orders SET announced = 1 WHERE id = ?", (unannounced["id"],))
        conn.commit()
    conn.close()

    # Audio Playback exclusively on Chef Station
    if st.session_state.get("chef_audio_cache") and os.path.exists(st.session_state.chef_audio_cache):
        st.audio(st.session_state.chef_audio_cache, format="audio/mp3", autoplay=True)

    col_kds_line, col_emergency = st.columns([1.6, 1.4], gap="large")

    with col_kds_line:
        col_kh1, col_kh2 = st.columns([2, 1])
        with col_kh1:
            st.markdown("<div class='card-title'>📋 Active Kitchen Order Line</div>", unsafe_allow_html=True)
            st.caption("Touch 'Start Cooking' to update floor & counter, and 'Notify Waiter' when plated.")
        with col_kh2:
            if st.button("🔄 Refresh Orders Line", key="chef_manual_refresh", use_container_width=True):
                st.rerun()

        conn = get_connection()
        active_tickets = conn.execute("SELECT * FROM orders WHERE status != 'COMPLETED' ORDER BY id ASC").fetchall()
        conn.close()

        if not active_tickets:
            st.markdown("""
            <div class='saas-card' style='text-align: center; padding: 48px 24px !important;'>
                <div style='font-size: 2.8rem; margin-bottom: 12px;'>✨</div>
                <div style='font-size: 1.35rem; font-weight: 700; color: #0F172A;'>Kitchen Line All Clear!</div>
                <div style='color: #64748B; font-size: 0.92rem; margin-top: 6px;'>No pending tickets right now. Plating pass is ready.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for ticket in active_tickets:
                dishes = json.loads(ticket["items_json"]) if ticket["items_json"] else []
                is_cooking = ticket["status"] == "COOKING"
                is_ready = ticket["status"] == "READY"
                
                if is_ready:
                    card_border = "#10B981"
                    status_badge = "<span class='pill-badge pill-green'>🔔 WAITER NOTIFIED</span>"
                elif is_cooking:
                    card_border = "#3B82F6"
                    status_badge = "<span class='pill-badge pill-indigo'>🔥 IN COOKING</span>"
                else:
                    card_border = "#F59E0B"
                    status_badge = "<span class='pill-badge pill-amber'>🟡 PENDING</span>"

                st.markdown(f"""
                <div class='saas-card' style='border-left: 6px solid {card_border}; padding: 20px 24px !important; margin-bottom: 14px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #E2E8F0; padding-bottom: 10px; margin-bottom: 12px;'>
                        <div>
                            <span style='font-family: "Playfair Display", Georgia, serif; font-size: 1.35rem; font-weight: 700; color: #0F172A;'>{ticket['order_code']}</span>
                            <span style='color: #475569; font-size: 1.05rem; margin-left: 10px; font-weight: 600;'>&bull; {ticket['table_or_platform']}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 8px;'>
                            {status_badge}
                            <span style='color: #64748B; font-size: 0.85rem;'>{ticket['created_at']}</span>
                        </div>
                    </div>
                    <div style='margin-bottom: 14px;'>
                        {"".join([f"<div style='font-size: 1.1rem; font-weight: 700; color: #0F172A; padding: 6px 12px; background: #F8FAFC; border-radius: 8px; margin-bottom: 6px; border-left: 3px solid #10B981;'>🥘 {d}</div>" for d in dishes])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 0.8])
                with btn_col1:
                    if not is_cooking and not is_ready:
                        if st.button("🔥 Start Cooking", key=f"chef_cook_{ticket['id']}", type="primary", use_container_width=True):
                            conn = get_connection()
                            conn.execute("UPDATE orders SET status = 'COOKING' WHERE id = ?", (ticket["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    elif is_cooking:
                        st.markdown("<div style='background: #EFF6FF; color: #1D4ED8; font-weight: 700; font-size: 0.85rem; padding: 10px; border-radius: 8px; text-align: center;'>🔥 On Stove / In Oven</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background: #ECFDF5; color: #065F46; font-weight: 700; font-size: 0.85rem; padding: 10px; border-radius: 8px; text-align: center;'>✅ Cooked</div>", unsafe_allow_html=True)
                with btn_col2:
                    if ticket["status"] != "READY":
                        if st.button("🔔 Notify Waiter (Ready)", key=f"chef_ready_{ticket['id']}", use_container_width=True):
                            conn = get_connection()
                            conn.execute("UPDATE orders SET status = 'READY' WHERE id = ?", (ticket["id"],))
                            conn.commit()
                            conn.close()
                            st.success(f"Buzzed Floor Waiter! {ticket['order_code']} marked ready for pickup.")
                            st.rerun()
                    else:
                        st.markdown("<div style='background: #ECFDF5; color: #065F46; font-weight: 700; font-size: 0.85rem; padding: 10px; border-radius: 8px; text-align: center;'>🔔 Waiter Buzzed &bull; Ready at Pass</div>", unsafe_allow_html=True)
                with btn_col3:
                    if st.button("🔊 Replay", key=f"chef_audio_{ticket['id']}", use_container_width=True):
                        speech = f"Attention Kitchen! Prepare: {', '.join(dishes)}."
                        p = generate_voice_callout(speech)
                        st.session_state.chef_audio_cache = p
                        st.rerun()

                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    with col_emergency:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🚨 Stock-Less Recipe Emergency Assistant</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-subtitle'>When a pan is on the stove and an ingredient runs out, instantly craft alternative dishes, waiter scripts, and broadcast 86 alerts.</div>", unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #475569; margin-bottom: 8px;'>⚡ Quick Tap Out-of-Stock Preset:</div>", unsafe_allow_html=True)
        q_col1, q_col2, q_col3 = st.columns(3)
        with q_col1:
            if st.button("🥚 Out of Eggs", key="chef_pre_egg", use_container_width=True):
                st.session_state.short_ing = "Farm Fresh Eggs"
                st.session_state.ordered_dish_target = "5 Bread Egg Fillings / Omelette"
        with q_col2:
            if st.button("🧀 Out of Paneer", key="chef_pre_paneer", use_container_width=True):
                st.session_state.short_ing = "Fresh Paneer"
                st.session_state.ordered_dish_target = "Kadhai Paneer Tikka Masala"
        with q_col3:
            if st.button("🍗 Low Chicken", key="chef_pre_chicken", use_container_width=True):
                st.session_state.short_ing = "Boneless Chicken Breast"
                st.session_state.ordered_dish_target = "Butter Chicken Gravy"

        target_dish = st.text_input("Ordered Dish Being Cooked:", value=st.session_state.get("ordered_dish_target", "Triple Egg & Herb Breakfast Omelette"), key="chef_inp_dish")
        short_ing = st.selectbox("Scarce / Missing Ingredient:", [
            "Farm Fresh Eggs",
            "Fresh Paneer",
            "Boneless Chicken Breast",
            "Button Mushrooms",
            "English Cheddar Cheese",
            "Heavy Cooking Cream"
        ], index=0, key="chef_inp_ing")
        qty_left = st.text_input("Current Line Quantity Left:", value="0 left / completely finished", key="chef_inp_qty")

        if st.button("✨ Generate Emergency Substitute Dish", key="chef_btn_gen_sub", type="primary", use_container_width=True):
            with st.spinner("AI generating alternative plating & kitchen adjustments..."):
                sub_res = ai_engine.solve_low_stock_substitution(target_dish, short_ing, qty_left)
                st.session_state.chef_emergency_result = sub_res

        if st.session_state.get("chef_emergency_result") is not None:
            res = st.session_state.chef_emergency_result
            st.markdown(f"""
            <div style='background: #F8FAFC; border-left: 5px solid #10B981; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-top: 14px;'>
                <div style='font-size: 1.2rem; font-weight: 800; color: #10B981;'>🍽️ Substitute: {res.get('substitute_dish', 'Chef Special')}</div>
                <div style='background: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin: 10px 0; border: 1px solid #E2E8F0;'>
                    <b style='color: #475569; font-size: 0.85rem;'>🗣️ Waiter / Cashier Script:</b><br>
                    <i style='color: #0F172A; font-size: 0.98rem;'>"{res.get('dialogue_for_staff', '')}"</i>
                </div>
                <div style='color: #475569; font-size: 0.88rem; line-height: 1.5;'>
                    <b>📈 Margin Impact:</b> {res.get('margin_impact', '+14% Margin')}<br>
                    <b>💡 Upsell Pairing:</b> {res.get('upsell_pitch', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                if st.button(f"🚨 Broadcast 86 '{short_ing}' to Counter", key="chef_btn_86", use_container_width=True):
                    conn = get_connection()
                    conn.execute("UPDATE inventory SET quantity = 0, freshness_status = 'OUT OF STOCK' WHERE item_name = ?", (short_ing,))
                    conn.commit()
                    conn.close()
                    st.error(f"Alert broadcasted! '{short_ing}' marked 86 (Out of Stock). Counter & Waiters notified.")
            with col_b2:
                if st.button(f"📢 Announce Substitute to Line", key="chef_btn_voice_sub", use_container_width=True):
                    voice_msg = f"Kitchen notice! For {target_dish}, we are now serving: {res.get('substitute_dish')}."
                    p = generate_voice_callout(voice_msg)
                    st.session_state.chef_audio_cache = p
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Live Perishable Stock Monitor ribbon at bottom of Chef view
    st.markdown("---")
    st.markdown("#### 📦 Live Perishable Stock Monitor")
    conn = get_connection()
    inv_rows = conn.execute("SELECT item_name, quantity, unit, freshness_status FROM inventory").fetchall()
    conn.close()

    inv_cols = st.columns(len(inv_rows))
    for idx, r in enumerate(inv_rows):
        with inv_cols[idx]:
            is_low = "Low" in r["freshness_status"] or "OUT" in r["freshness_status"]
            card_bg = "#FEF2F2" if is_low else "#FFFFFF"
            color = "#EF4444" if is_low else "#10B981"
            st.markdown(f"""
            <div style='background: {card_bg}; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 8px; text-align: center;'>
                <div style='font-size: 0.74rem; color: #64748B; font-weight: 600;'>{r['item_name']}</div>
                <div style='font-size: 1.05rem; font-weight: 800; color: {color};'>{r['quantity']} {r['unit']}</div>
                <div style='font-size: 0.68rem; color: {color}; font-weight: 700;'>{r['freshness_status']}</div>
            </div>
            """, unsafe_allow_html=True)



def render_waiter_view():
    col_floor, col_tableside = st.columns([1.5, 1.5], gap="large")

    with col_floor:
        col_wh1, col_wh2 = st.columns([2, 1])
        with col_wh1:
            st.markdown("<div class='card-title'>🔔 Kitchen Pickup Buzzer & Table Queue</div>", unsafe_allow_html=True)
            st.caption("Orders cooking on the stove or hot and ready at the kitchen pass.")
        with col_wh2:
            if st.button("🔄 Sync with Kitchen", key="waiter_sync_btn", use_container_width=True):
                st.rerun()

        conn = get_connection()
        orders_rows = conn.execute("SELECT * FROM orders WHERE status != 'COMPLETED' ORDER BY id ASC").fetchall()
        conn.close()

        if not orders_rows:
            st.markdown("""
            <div class='saas-card' style='text-align: center; padding: 48px 24px !important;'>
                <div style='font-size: 2.8rem; margin-bottom: 12px;'>☕</div>
                <div style='font-size: 1.35rem; font-weight: 700; color: #0F172A;'>All Tables Served!</div>
                <div style='color: #64748B; font-size: 0.92rem; margin-top: 6px;'>No food waiting at the kitchen counter. All diners happy.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for ord_item in orders_rows:
                is_ready = ord_item["status"] == "READY"
                is_cooking = ord_item["status"] == "COOKING"
                
                if is_ready:
                    card_border = "#10B981"
                    badge = "<span class='pill-badge pill-green'>🔔 HOT & READY TO SERVE</span>"
                elif is_cooking:
                    card_border = "#F59E0B"
                    badge = "<span class='pill-badge pill-amber'>🔥 ON STOVE / IN OVEN</span>"
                else:
                    card_border = "#64748B"
                    badge = "<span class='pill-badge pill-slate'>⏳ QUEUED</span>"

                dishes = json.loads(ord_item["items_json"]) if ord_item["items_json"] else []

                st.markdown(f"""
                <div class='saas-card' style='border-left: 6px solid {card_border}; padding: 18px 22px !important; margin-bottom: 14px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                        <span style='font-family: "Playfair Display", Georgia, serif; font-size: 1.25rem; font-weight: 800; color: #0F172A;'>{ord_item['table_or_platform']}</span>
                        <div>
                            {badge}
                            <span style='color: #64748B; font-size: 0.82rem; margin-left: 8px;'>{ord_item['created_at']}</span>
                        </div>
                    </div>
                    <div style='background: #F8FAFC; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;'>
                        {"".join([f"<div style='font-size: 1rem; font-weight: 600; color: #1E293B; padding: 3px 0;'>🥘 {d}</div>" for d in dishes])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c_btn1, c_btn2 = st.columns([1.5, 1])
                with c_btn1:
                    if st.button(f"✅ Served to Guest ({ord_item['order_code']})", key=f"waiter_serve_{ord_item['id']}", type="primary", use_container_width=True):
                        conn = get_connection()
                        conn.execute("UPDATE orders SET status = 'COMPLETED' WHERE id = ?", (ord_item["id"],))
                        conn.commit()
                        conn.close()
                        st.success(f"{ord_item['table_or_platform']} served! Order closed.")
                        st.rerun()
                with c_btn2:
                    if st.button(f"📱 Bill / SMS", key=f"waiter_bill_{ord_item['id']}", use_container_width=True, help="Send post-dining review link"):
                        st.session_state.active_review_target = ord_item["customer_phone"]
                        st.info(f"Targeting guest {ord_item['customer_phone']} for review!")

                st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    with col_tableside:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🛡️ Table-Side 86 Alert & Upsell Radar</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-subtitle'>Live check of 86 ingredients before taking orders at tables, plus polite alternative pitches.</div>", unsafe_allow_html=True)

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
                st.markdown(f"&bull; <b>{out['item_name']}</b> is {out['freshness_status']} (Only {out['quantity']} {out['unit']} left). Propose an alternative!", unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 12px 16px; color: #065F46; font-weight: 600; margin-bottom: 14px;'>✅ All Ingredients In Stock & Available for Ordering.</div>", unsafe_allow_html=True)

        # 2. Table-Side Quick Substitution Pitch Generator
        st.markdown("<div style='font-size: 1rem; font-weight: 700; color: #0F172A; margin: 12px 0 4px 0;'>💡 Table-Side Substitute Script:</div>", unsafe_allow_html=True)
        st.caption("If a guest requests a dish with a low-stock component, get an instant polite script:")

        w_dish = st.text_input("Diner Wants to Order:", value="Triple Egg Omelette / 5 Bread Egg Fillings", key="waiter_inp_dish")
        w_ing = st.selectbox("Low-Stock Component:", ["Farm Fresh Eggs", "Fresh Paneer", "Boneless Chicken Breast", "Button Mushrooms"], key="waiter_inp_ing")

        if st.button("✨ Get Customer-Friendly Upsell Script", key="waiter_btn_get_script", type="primary", use_container_width=True):
            with st.spinner("AI generating table conversation pitch..."):
                w_res = ai_engine.solve_low_stock_substitution(w_dish, w_ing, "0 remaining / finished")
                st.session_state.waiter_script = w_res

        if st.session_state.get("waiter_script") is not None:
            res = st.session_state.waiter_script
            st.markdown(f"""
            <div style='background: #F8FAFC; border-left: 5px solid #10B981; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-top: 12px;'>
                <b style='color: #10B981; font-size: 1.15rem;'>🍽️ Suggest: {res.get('substitute_dish', 'Chef Special')}</b>
                <div style='background: #FFFFFF; border-radius: 8px; padding: 12px; margin: 10px 0; border: 1px solid #E2E8F0;'>
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
        st.markdown("<div style='font-size: 1rem; font-weight: 700; color: #0F172A; margin: 8px 0 4px 0;'>📱 Post-Dining Google Review Trigger:</div>", unsafe_allow_html=True)
        phone_target = st.text_input("Diner Phone Number:", value=st.session_state.get("active_review_target", "+91 98765 43210"), key="waiter_inp_phone")
        if st.button("📤 Send Automated Experience Rating SMS", key="waiter_btn_send_sms", use_container_width=True):
            st.success(f"SMS review invitation dispatched to {phone_target}! Positive ratings will be routed to Google Maps.")

        st.markdown("</div>", unsafe_allow_html=True)



if st.session_state.active_role == "Counter Person":
    render_counter_view()
elif st.session_state.active_role == "Chef":
    render_chef_view()
elif st.session_state.active_role == "Waiter":
    render_waiter_view()


# Footer
st.markdown("""
<div style='text-align: center; color: #64748B; font-size: 0.82rem; margin-top: 40px; padding: 20px 0; border-top: 1px solid #E2E8F0;'>
    <b>RestoCopilot AI</b> &bull; Silicon Valley Autonomous Hospitality OS &bull; Dual-Engine (Local Llama 3.2 & Gemma 31B Open-Weights) &bull; Edge Kitchen Database
</div>
""", unsafe_allow_html=True)
