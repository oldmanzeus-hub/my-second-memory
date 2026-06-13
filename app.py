import streamlit as st
from streamlit_gsheets import GSheetsConnection
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Personal Memory Vault", layout="wide")
st.title("🧠 Personal Memory Vault & Mind Map")

# Initialize connection to your cloud Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Split screen layout: Left side for inputs, Right side for Mind Map
left_col, right_col = st.columns([1, 1.5])

with left_col:
    st.subheader("[+] Quick Log Entry")
    user_input = st.text_input("Log something new", placeholder="e.g., Shutter Island movie")
    status = st.selectbox("Current Status", ["Want to Explore", "In Progress", "Completed"])
    notes = st.text_area("Initial thoughts or keywords")
    
    if st.button("⚡ Quick Save"):
        # Local mock save sequence (Appends straight to Google Sheet DataFrame)
        new_row = pd.DataFrame([{"Title": user_input, "Category": "Film", "Status": status, "Notes": notes}])
        df = conn.read()
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success(f"Log updated!")
        st.cache_data.clear()

with right_col:
    st.subheader("🕸️ Dynamic Knowledge Graph")
    
    try:
        df = conn.read()
        if not df.empty:
            # Initialize PyVis network canvas
            net = Network(height="500px", width="100%", bgcolor="#0F1623", font_color="#FFFFFF")
            
            # Central anchor point of your brain
            net.add_node("Root", label="My Memory Vault", color="#E8C547", size=25)
            
            # Dynamically pull distinct categories and connect individual nodes
            unique_categories = df["Category"].dropna().unique()
            for cat in unique_categories:
                # Add category hub nodes
                net.add_node(cat, label=cat, color="#7C3AED", size=20)
                net.add_edge("Root", cat, color="#1A2235")
                
                # Filter down to specific items matching this branch
                items_in_cat = df[df["Category"] == cat]
                for idx, row in items_in_cat.iterrows():
                    item_title = row["Title"]
                    net.add_node(item_title, label=item_title, color="#94A3B8", size=12)
                    net.add_edge(cat, item_title, color="#1A2235")
            
            # Compile graph physics parameters into static HTML
            net.toggle_physics(True)
            html_content = net.generate_html()
            
            # Embed the canvas directly as a running script inside the webapp viewport
            components.html(html_content, height=520, scrolling=False)
        else:
            st.info("Log your first entry to generate the connection graph.")
    except Exception as e:
        st.caption("Waiting for database rows to build connectivity framework.")
