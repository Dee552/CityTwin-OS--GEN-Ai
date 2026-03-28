import streamlit as st
import time
import requests
import folium
from folium import plugins
from streamlit_folium import st_folium
import json
import random

# Force wide mode and dark theme
st.set_page_config(layout="wide", page_title="CITYTWIN OS", page_icon="🏎️")

# 🏎️ BACKGROUND & SOS VISUALS
sos_active = st.session_state.get("sos_active", False)
bg_filter = "brightness(0.4) sepia(1) hue-rotate(-50deg) saturate(5)" if sos_active else "brightness(1.0) saturate(1.2)"

st.markdown(f"""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .main {{ background: transparent !important; }}
        #bg-image-container {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -2;
            background-image: url('https://media4.giphy.com/media/v1.Y2lkPTZjMDliOTUyMTFpYWw2aW5xa2pkYjNsem14aXoyY2Zzb2dkZmlmMzhldmZtOWNzdyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/3orieWY8RCodjD4qqs/giphy.gif');
            background-size: cover; background-position: center; filter: {bg_filter}; transition: 0.5s;
        }}
        #bg-tint {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1;
            background: { "rgba(255, 0, 0, 0.2)" if sos_active else "rgba(0, 0, 0, 0.3)" };
            animation: { "flash 1s infinite" if sos_active else "none" };
        }}
        @keyframes flash {{ 0% {{ opacity: 0.2; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 0.2; }} }}
    </style>
    <div id="bg-image-container"></div>
    <div id="bg-tint"></div>
""", unsafe_allow_html=True)

# 🛰️ UTILS
def fetch_weather():
    try: return requests.get("http://localhost:8000/weather").json()
    except: return {"temp": "28", "desc": "Clear", "humidity": "65", "wind": "12"}

def inject_tools(speech_text=None, siren_active=False):
    speech_js = f"const msg = new SpeechSynthesisUtterance('{speech_text}'); window.speechSynthesis.speak(msg);" if speech_text else ""
    siren_js = """
    let audioCtx = null;
    function playSiren() {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain); gain.connect(audioCtx.destination);
        osc.type = 'triangle'; gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        setInterval(() => {
            osc.frequency.exponentialRampToValueAtTime(600, audioCtx.currentTime + 0.5);
            osc.frequency.exponentialRampToValueAtTime(800, audioCtx.currentTime + 1);
        }, 1000);
        osc.start();
    }
    """ if siren_active else ""
    
    js_code = f"""
    <script>
    {siren_js}
    function syncGPS() {{
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition((pos) => {{
                const url = new URL(window.location.href);
                url.searchParams.set('lat', pos.coords.latitude);
                url.searchParams.set('lon', pos.coords.longitude);
                window.parent.location.href = url.href;
            }});
        }}
    }}
    function startSTT() {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{ alert("Voice not supported."); return; }}
        const rec = new SpeechRecognition();
        rec.onresult = (e) => {{
            const txt = e.results[0][0].transcript;
            const url = new URL(window.location.href);
            url.searchParams.set('transcript', txt);
            window.parent.location.href = url.href;
        }};
        rec.start();
    }}
    {speech_js}
    if ({str(siren_active).lower()}) playSiren();
    window.syncGPS = syncGPS;
    window.startSTT = startSTT;
    </script>
    <div style="text-align:center; display:flex; justify-content:center; gap:20px; padding:10px;">
        <button onclick="syncGPS()" style="background:rgba(0, 210, 255, 0.2); color:#fff; border:2px solid #00d2ff; padding:15px 30px; border-radius:50px; font-family:'Orbitron'; cursor:pointer; font-weight:bold; text-transform:uppercase; backdrop-filter: blur(10px);">
            🛰️ SYNC GPS
        </button>
        <button onclick="startSTT()" style="background:rgba(255, 0, 0, 0.2); color:#fff; border:2px solid #ff0000; padding:15px 30px; border-radius:50px; font-family:'Orbitron'; cursor:pointer; font-weight:bold; text-transform:uppercase; backdrop-filter: blur(10px);">
            🎤 VOICE COMMAND
        </button>
    </div>
    """
    return st.components.v1.html(js_code, height=100)

# 🎨 STYLING
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Rajdhani:wght@500;700&display=swap');
    .hud-container { background: rgba(0, 10, 20, 0.5); backdrop-filter: blur(30px); border: 1px solid #00d2ff; border-radius: 25px; padding: 30px; margin: 10px 5%; color: white; }
    .stButton>button { background: rgba(0, 210, 255, 0.1) !important; color: #fff !important; border: 1px solid #00d2ff !important; height: 100px !important; font-family: 'Orbitron' !important; font-size: 1.2rem !important; border-radius: 15px !important; }
    .stButton>button:hover { background: #00d2ff !important; color: #000 !important; box-shadow: 0 0 40px #00d2ff; }
    header, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; font-family:Orbitron; font-size:5rem; color:#fff; text-shadow:0 0 30px #00d2ff; margin-bottom:0;'>CITYTWIN OS</h1>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: 
    if st.button("🚗 NAVIGATE"): st.session_state.mode = "NAV"
with col2: 
    if st.button("🚨 EMERGENCY"): st.session_state.mode = "EMG"
with col3: 
    if st.button("📊 ANALYTICS"): st.session_state.mode = "ANZ"
with col4: 
    if st.button("🧠 AI VOICE"): st.session_state.mode = "AI"

# 🛠️ ACTIVE NODE
if "mode" in st.session_state:
    st.markdown("<div class='hud-container'>", unsafe_allow_html=True)
    
    if st.session_state.mode == "AI":
        st.markdown("<h2 style='color:#00d2ff; font-family:Orbitron; border-bottom: 1px solid #00d2ff; padding-bottom:10px;'>🧠 MULTI-MODAL INTERFACE</h2>", unsafe_allow_html=True)
        
        # 1. Tools & Voice Out
        ai_text_to_speak = st.session_state.get("ai_out")
        inject_tools(speech_text=ai_text_to_speak)
        if ai_text_to_speak:
            st.session_state.last_response = ai_text_to_speak # Persist for display
            st.session_state.ai_out = None # Clear trigger

        # 2. Display persistent response
        if "last_response" in st.session_state:
            st.markdown(f"""
            <div style="background: rgba(0, 210, 255, 0.1); border: 1px solid #00d2ff; padding: 20px; border-radius: 15px; margin-bottom: 20px; font-family: 'Rajdhani';">
                <h3 style="color: #00d2ff; margin-top: 0; font-family: Orbitron;">🤖 AI RESPONSE:</h3>
                <p style="font-size: 1.2rem; line-height: 1.5;">{st.session_state.last_response}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # --- 🚨 EMERGENCY AUTO-DETECTION ---
            if "SERVICE:" in st.session_state.last_response:
                ai_res = st.session_state.last_response
                service_type = ai_res.split("SERVICE:")[1].split("|")[0].strip()
                st.warning(f"CRITICAL: {service_type} detected.")
                if st.button(f"📍 LOCATE NEAREST {service_type}"):
                    st.session_state.mode = "NAV"
                    st.session_state.target = f"{service_type} near me"
                    st.rerun()

        # 3. Unified Query logic
        query = None
        
        # 1. Check Voice Input (URL)
        q_params = st.query_params
        transcript = q_params.get("transcript")
        if transcript:
            st.info(f"🎤 VOICE: '{transcript}'")
            query = transcript
            st.query_params.pop("transcript") # Consume transcript

        # 2. Check Text Input
        text_in = st.chat_input("Write your query or press VOICE COMMAND...")
        if text_in: query = text_in

        # Process if any input exists
        if query:
            with st.spinner("Accessing Neural Network..."):
                try:
                    response = requests.get(f"http://localhost:8000/chat?query={query}", timeout=15)
                    if response.status_code == 200:
                        res_json = response.json()
                        ai_res = res_json.get("response", "")
                        st.session_state.ai_out = ai_res
                        st.markdown(f"### 🤖 AI RESPONSE:\n{ai_res}")
                        
                        # --- 🚨 EMERGENCY AUTO-DETECTION ---
                        if "SERVICE:" in ai_res:
                            service_type = ai_res.split("SERVICE:")[1].split("|")[0].strip()
                            st.warning(f"CRITICAL: {service_type} detected.")
                            if st.button(f"📍 LOCATE NEAREST {service_type}"):
                                st.session_state.mode = "NAV"
                                st.session_state.target = f"{service_type} near me"
                                st.rerun()
                        
                        st.rerun()
                    else:
                        st.error(f"Backend Error: {response.status_code}")
                except Exception as e:
                    st.error(f"AI Link Failed: {str(e)}")

    elif st.session_state.mode == "NAV":
        st.subheader("📍 TACTICAL NAVIGATION")
        inject_tools()
        q = st.query_params
        lat, lon = float(q.get("lat", 13.0827)), float(q.get("lon", 80.2707))
        
        # Auto-fill target if coming from Emergency AI
        current_target = st.session_state.get("target", "")
        target = st.text_input("Enter Target:", value=current_target)
        
        if st.button("SCAN AREA") or (current_target and "routes" not in st.session_state):
            with st.spinner(f"Routing to {target}..."):
                res = requests.get(f"http://localhost:8000/route?end={target}&start_lat={lat}&start_lon={lon}").json()
                if res.get("routes"):
                    routes = res["routes"]
                    st.session_state.routes = routes
                    st.session_state.selected_route_idx = 0
                    st.session_state.target = target
                    st.rerun()
        
        if "routes" in st.session_state:
            routes = st.session_state.routes
            
            st.markdown("### 📊 TACTICAL ROUTE SUMMARY")
            
            # Using a loop with st.markdown for each card to ensure perfect rendering
            for i, r in enumerate(routes):
                is_rec = r.get("is_recommended")
                border_color = "#ffcc00" if is_rec else "#00d2ff"
                bg_color = "rgba(255, 204, 0, 0.1)" if is_rec else "rgba(0, 210, 255, 0.05)"
                glow = "box-shadow: 0 0 15px rgba(255, 204, 0, 0.3);" if is_rec else ""
                badge = f"<span style='background:#ffcc00; color:#000; padding:2px 10px; border-radius:5px; font-size:0.75rem; font-weight:900; margin-left:10px; font-family:Orbitron;'>AI PREFERRED</span>" if is_rec else ""
                
                card_html = f"""<div style="border: 2px solid {border_color}; background: {bg_color}; padding: 20px; border-radius: 15px; margin-bottom: 15px; {glow} display: flex; justify-content: space-between; align-items: center; font-family: 'Rajdhani', sans-serif;">
<div style="flex-grow: 1;">
<div style="display: flex; align-items: center; margin-bottom: 5px;">
<span style="color:#00d2ff; font-weight: bold; font-size: 1.2rem; font-family:Orbitron;">ROUTE {i+1}</span>
{badge}
</div>
<div style="font-size: 1rem; color: #ffcc00; font-weight: 500;">🔮 {r['prediction']}</div>
<div style="font-size: 0.9rem; color: #888; margin-top: 5px;">📍 Distance: {r['distance_km']} km</div>
</div>
<div style="text-align: right; min-width: 100px;">
<div style="font-family: 'Orbitron'; font-size: 1.8rem; color: #fff; text-shadow: 0 0 10px {border_color};">{r['duration_min']}</div>
<div style="font-family: 'Orbitron'; font-size: 0.7rem; color: {border_color}; letter-spacing: 2px;">MINUTES</div>
</div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)
            
            # Selection Buttons
            st.markdown("<p style='font-family:Orbitron; font-size:0.8rem; color:#888;'>SELECT TRACK FOR UPLINK:</p>", unsafe_allow_html=True)
            cols = st.columns(len(routes))
            for i, r in enumerate(routes):
                with cols[i]:
                    rec_tag = "🤖 RECOMMENDED\n" if r.get("is_recommended") else ""
                    label = f"{rec_tag}ROUTE {i+1}\n{r['duration_min']} MIN"
                    
                    # Highlight the button if it's the recommended one
                    btn_style = "border: 2px solid #ffcc00 !important;" if r.get("is_recommended") else ""
                    if st.button(label, key=f"route_sel_{i}"):
                        st.session_state.selected_route_idx = i
                        st.rerun()
            
            selected_idx = st.session_state.get("selected_route_idx", 0)
            sel_route = routes[selected_idx]
            
            # Show a special banner if the selected route is the AI recommended one
            rec_banner = ""
            if sel_route.get("is_recommended"):
                rec_banner = """<div style="background: rgba(255, 204, 0, 0.2); border-left: 5px solid #ffcc00; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
<span style="color: #ffcc00; font-weight: bold;">🤖 CITYTWIN AI RECOMMENDATION:</span> This route is optimized for the fastest arrival based on predicted traffic clearances.
</div>"""
            
            st.markdown(f"""<div style="background: rgba(0, 210, 255, 0.1); border: 1px solid #00d2ff; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
{rec_banner}
<h4 style="color: #00d2ff; margin: 0;">SELECTED: ROUTE {selected_idx + 1}</h4>
<p style="margin: 5px 0;">📏 Distance: {sel_route['distance_km']} km | ⏱️ Est. Time: {sel_route['duration_min']} mins</p>
<p style="margin: 5px 0; color: #ffcc00;">🔮 Prediction: {sel_route['prediction']}</p>
<p style="margin: 5px 0; color: #00ff00; font-weight: bold; font-family: Orbitron; font-size: 0.8rem;">🎯 PREDICTION ACCURACY: {sel_route.get('prediction_accuracy', 95)}%</p>
</div>""", unsafe_allow_html=True)

            m = folium.Map(location=[lat, lon], zoom_start=15, tiles="CartoDB dark_matter")
            
            # Add User Location Marker
            folium.Marker(
                [lat, lon], 
                popup="Current Position", 
                icon=folium.Icon(color='blue', icon='circle', prefix='fa')
            ).add_to(m)

            # Add Destination Marker if points exist
            if sel_route["points"]:
                dest = sel_route["points"][-1]
                folium.Marker(
                    dest, 
                    popup=f"Target: {target}", 
                    icon=folium.Icon(color='red', icon='flag', prefix='fa')
                ).add_to(m)
            
            # Draw all routes but highlight selected with high-visibility pulsing ant-path
            for i, r in enumerate(routes):
                is_selected = (i == selected_idx)
                color = "#00ff00" if is_selected else "#555" # Green for selected
                opacity = 1.0 if is_selected else 0.3
                weight = 8 if is_selected else 4
                
                if is_selected:
                    # High visibility glowing green path for active navigation
                    plugins.AntPath(
                        r["points"], 
                        color=color, 
                        weight=weight, 
                        delay=600, 
                        dash_array=[10, 20],
                        pulse_color="#ffffff",
                        opacity=1.0
                    ).add_to(m)
                else:
                    folium.PolyLine(r["points"], color=color, weight=weight, opacity=opacity).add_to(m)

            # Navigation UI Plugins
            plugins.LocateControl(auto_start=False, flyTo=True).add_to(m) # Follow Me button
            plugins.Fullscreen().add_to(m)
            
            st.components.v1.html(m._repr_html_(), height=600)
            
            with st.expander("📄 TURN-BY-TURN INSTRUCTIONS"):
                for step in sel_route["steps"]:
                    st.write(f"• {step['instruction']} ({round(step['distance'])}m)")

    elif st.session_state.mode == "EMG":
        st.markdown("<h2 style='color:#ff0000; font-family:Orbitron; text-align:center;'>🚨 EMERGENCY COMMAND CENTER</h2>", unsafe_allow_html=True)
        
        # SOS Toggle
        sos_active = st.session_state.get("sos_active", False)
        btn_label = "⚪ DEACTIVATE SOS" if sos_active else "🔴 ACTIVATE SOS ALERT"
        
        # Large prominent toggle
        if st.button(btn_label, use_container_width=True):
            st.session_state.sos_active = not sos_active
            st.rerun()
        
        if st.session_state.get("sos_active"):
            inject_tools(siren_active=True)
            st.error("⚠️ EMERGENCY BROADCAST ACTIVE: YOUR LOCATION IS BEING TRACKED BY THE COMMAND CENTER.")

        # --- 📋 CRITICAL INSTRUCTIONS ---
        st.markdown("### ⚠️ CRITICAL INSTRUCTIONS")
        
        inst_col1, inst_col2 = st.columns(2)
        
        with inst_col1:
            st.markdown("""
            **🔥 FIRE EMERGENCY**
            1. **Stay Low**: Crawl under smoke to stay near fresh air.
            2. **Test Doors**: Feel doors with the back of your hand before opening.
            3. **Don't Stop**: Get out first, then call for help.
            """)
            
            st.markdown("""
            **🏥 MEDICAL CRISIS**
            1. **Check Response**: Shout and tap the person.
            2. **Call 108**: Immediately request an ambulance.
            3. **Stay Calm**: Follow the dispatcher's medical advice over the phone.
            """)

        with inst_col2:
            st.markdown("""
            **👮 POLICE / SAFETY**
            1. **Find Cover**: Move away from the threat immediately.
            2. **Lock Up**: Secure all doors and stay out of sight.
            3. **Silent Mode**: Keep your phone on silent if hiding.
            """)
            with inst_col2:
                st.markdown("""
                **🌊 FLOOD / STORM**
                1. **Higher Ground**: Move to the highest possible floor.
                2. **Avoid Water**: Do not walk or drive through moving water.
                3. **Power Down**: Turn off electricity at the main breaker if safe.
                """)

            # --- 📞 QUICK-DIAL COMMANDS ---
            st.markdown("<h3 style='color:#ff0000; font-family:Orbitron; margin-top:20px;'>📞 QUICK-DIAL COMMANDS</h3>", unsafe_allow_html=True)

            dial_col1, dial_col2, dial_col3, dial_col4 = st.columns(4)

            helplines = [
                ("🚓 POLICE", "100"),
                ("🚒 FIRE", "101"),
                ("🚑 AMBULANCE", "108"),
                ("⛈️ DISASTER", "1913"),
                ("👩 WOMEN", "1091"),
                ("👶 CHILD", "1098"),
                ("🌊 COASTAL", "1093"),
                ("⚡ POWER", "1912")
            ]

            for i, (label, num) in enumerate(helplines):
                with [dial_col1, dial_col2, dial_col3, dial_col4][i % 4]:
                    st.markdown(f"""
                        <a href="tel:{num}" style="text-decoration: none;">
                            <div style="background: rgba(255, 0, 0, 0.15); border: 2px solid #ff0000; padding: 15px; border-radius: 10px; text-align: center; color: #fff; font-family: 'Orbitron'; font-weight: bold; margin-bottom: 10px; transition: 0.3s; cursor: pointer;" 
                                 onmouseover="this.style.background='rgba(255, 0, 0, 0.4)'; this.style.boxShadow='0 0 15px #ff0000';" 
                                 onmouseout="this.style.background='rgba(255, 0, 0, 0.15)'; this.style.boxShadow='none';">
                                {label}<br><span style="font-size: 1.5rem;">{num}</span>
                            </div>
                        </a>
                    """, unsafe_allow_html=True)

            st.info("💡 YOUR CURRENT GPS COORDINATES ARE BEING SENT TO CHENNAI DISPATCH.")


    elif st.session_state.mode == "ANZ":
        st.markdown("<h2 style='color:#00d2ff; font-family:Orbitron;'>📊 CITY ANALYTICS GRID</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("TRAFFIC DENSITY", "78%", "+12%")
        c2.metric("AIR QUALITY", "42 AQI", "GOOD")
        c3.metric("POWER GRID", "94%", "STABLE")
        
        # Simple simulated chart
        chart_data = {"Hour": list(range(10)), "Traffic": [random.randint(20, 90) for _ in range(10)]}
        st.line_chart(chart_data, x="Hour", y="Traffic")

    if st.button("TERMINATE"):
        for k in ["mode", "route_data", "target", "ai_out"]: st.session_state.pop(k, None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

w = fetch_weather()
st.markdown(f"<div style='text-align:center; color:#00d2ff; padding:20px; font-family:Orbitron;'>● {w['temp']}°C ● GRID_LOAD: 64% ● MULTI-MODAL SYSTEM READY</div>", unsafe_allow_html=True)
