import streamlit as st
import scraper
from scraper import get_pinterest_data
from scraper import get_driver
import pandas as pd
from io import BytesIO
import time

def start_scraping():
    st.session_state.scraping = True

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pinterest Data")
    return output.getvalue()

def update_scrape_status(term, n_boards, scroll_count):
    status_box.info(f"Scraping '{term}'. Boards found: {n_boards}")

if "scraping" not in st.session_state:
    st.session_state.scraping = False


st.set_page_config(page_title="Pinterest Scraper", layout="centered")

st.title("Pinterest Scraper")
st.markdown("Enter pinterest board search terms ")
terms_input = st.text_area("Enter terms (one per line):", height=200)
st.button(
    "Begin Scrape",
    on_click=start_scraping,
    disabled=st.session_state.scraping,
    help="Scraping already in progress." if st.session_state.scraping else None
)

with st.expander("❓ Help / Debug Instructions"):
    st.markdown("""
**Taking too long to get results?**  
There might be a large number of Pinterest boards for certain keywords, and the page loads via infinite scroll. Be patient or try a more niche keyword to speed things up.

**Getting 0 pins and boards?**  
That might actually be true! But if you've **verified manually** that the keyword shows results on Pinterest, let the team know in the `#data-team-checks` Slack channel.

**❌ Error in the scraper?**  
If you're seeing an error message (usually shown in red with a traceback), please:
- Take a **screenshot** of the error
- Include the **keyword(s)** you used
- Share it with the team so we can replicate and fix it.
    """)

if st.session_state.scraping and terms_input.strip():
    strip_split_terms = terms_input.strip().split('\n')
    terms = [term.strip() for term in strip_split_terms]
    file_name = "pinterest_data_" + "_".join(strip_split_terms) + '.xlsx'

    status_box = st.empty()
    progress_bar = st.progress(0, text="Scraping in progress. Please wait.")
    df_results = pd.DataFrame(columns=["keyword", "total_pins", "n_boards", "errors"])
    live_table = st.empty()

    with st.spinner("Scraping data from Pinterest..."):
        for i, term in enumerate(terms):
            progress_bar.progress((i) / len(terms), text=f"Processing: ({i+1}/{len(terms)})")
            time.sleep(0.5)
            with get_driver() as driver:
                df_term = get_pinterest_data(term, driver=driver, update_callback=update_scrape_status)
            df_results = pd.concat([df_results, df_term], ignore_index=True)
            live_table.dataframe(df_results)

    progress_bar.empty()
    st.success("✅ Scraping complete!")
    status_box.empty()
    st.session_state.scraping = False

    excel_data = to_excel(df_results)
    st.download_button(
        label="📥 Download as Excel",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )