import streamlit as st
from streamlit_gsheets import GSheetsConnection
from google import genai
from google.genai import types
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Universal Node Vault", layout="wide")
st.title("🧠 Universal Second Memory Vault")

# Initialize connection to your cloud Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
ai_client = genai.Client()

# Split screen layout: Left side for logging, Right side for Visual Nodes
left_col, right_col = st.columns([1, 1.4])

with left_col:
    st.subheader("📌 Log a New Node")
    
    # 1. Top-Level Domain Selection
    domain = st.selectbox("Select Domain", ["Media", "Health", "Coding", "General"])
    
    user_input = st.text_input("Title / Topic", placeholder="e.g., Dune, Daily Workout, FastAPI Setup...")
    status = st.selectbox("Status", ["Want to Explore/Do", "In Progress", "Completed/Archived"])
    personal_notes = st.text_area("Your Notes / Context")
    
    if st.button("⚡ Process & Pin Node"):
        if user_input:
            with st.spinner("Processing entry details..."):
                # Standard prompt that respects the selected top-level Domain
                prompt = f"""
                The user wants to save this entry under the '{domain}' domain: "{user_input}"
                
                Use your built-in Google Search grounding tool to find:
                1. The official correct title or clear topic name.
                2. A sub-category tailored to the domain (e.g., if Media: Film/Game/Book; if Health: Workout/Nutrition; if Coding: Python/Database).
                3. The top 2 tags/keywords.
                4. A 1-sentence summary or definition.
                
                Format your response EXACTLY like this line, using '||' as a separator:
                Official Title || SubCategory || Tag1, Tag2 || Summary
                """
                
                try:
                    response = ai_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )
                    
                    ai_data = response.text.strip().split("||")
                    
                    if len(ai_data) == 4:
                        title, sub_category, tags, ai_summary = [x.strip() for x in ai_data]
                    else:
                        title, sub_category, tags, ai_summary = user_input, "General", "Unknown", "Could not verify details."
                    
                    # Append data to Google Sheets (including our top-level Domain column!)
                    new_row = pd.DataFrame([{
                        "Domain": domain,
                        "Title": title,
                        "Category": sub_category,
                        "Status": status,
                        "Tags": tags,
                        "Notes": personal_notes,
                        "AI Summary": ai_summary
                    }])
                    
                    df = conn.read()
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    st.success(f"Added node '{title}' to {domain} -> {sub_category}!")
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"API Error: {e}")
        else:
            st.warning("Please fill out the title.")

with right_col:
    st.subheader("🕸️ Structural Knowledge Graph")
    
    try:
        df = conn.read()
        if not df.empty:
            # Set up the canvas
            net = Network(height="550px", width="100%", bgcolor="#0F1623", font_color="#FFFFFF")
            net.barnes_hut(gravity=-2500, central_gravity=0.3, spring_length=110)
            
            # Tier 1: The Core Brain Root
            net.add_node("Root", label="MY BRAIN", color="#E8C547", size=26, shape="diamond")
            
            # Keep track of structural nodes we've already created to prevent overlap
            created_domains = set()
            created_subcats = set()
            
            # Color maps for the major Domain Hubs
            domain_colors = {
                "Media": "#7C3AED",   # Purple
                "Health": "#00C853",  # Green
                "Coding": "#00A8E8",  # Light Blue
                "General": "#94A3B8"  # Slate Gray
            }
            
            for idx, row in df.iterrows():
                # Read columns safely (handles old rows missing the 'Domain' column gracefully)
                dom = row.get("Domain", "Media") 
                title = row["Title"]
                subcat = row["Category"]
                status_val = row["Status"]
                
                # Tier 2: Create Domain Hub (e.g., "MEDIA", "HEALTH") and link to Core Root
                if dom not in created_domains:
                    net.add_node(dom, label=dom.upper(), color=domain_colors.get(dom, "#94A3B8"), size=22, shape="ellipse")
                    net.add_edge("Root", dom, color="#334155", width=3)
                    created_domains.add(dom)
                
                # Tier 3: Create Sub-Category Hub (e.g., "Film", "Workout") and link to Domain Hub
                subcat_id = f"{dom}_{subcat}" # Unique ID to prevent cross-domain collisions
                if subcat_id not in created_subcats:
                    net.add_node(subcat_id, label=subcat, color="#1E293B", size=16, shape="box", border_color=domain_colors.get(dom, "#94A3B8"))
                    net.add_edge(dom, subcat_id, color="#334155", width=2)
                    created_subcats.add(subcat_id)
                
                # Tier 4: Add the actual Data Item Node and link to its Sub-Category
                item_label = f"{title}\n({status_val})"
                net.add_node(title, label=item_label, color="#475569", size=12, title=row["AI Summary"])
                net.add_edge(subcat_id, title, color="#1A2235", width=1)
            
            # Render the canvas viewport
            html_content = net.generate_html()
            components.html(html_content, height=570, scrolling=False)
        else:
            st.info("Log your first entry to generate the connection graph.")
    except Exception as e:
        st.caption("Awaiting cloud framework serialization data...")
