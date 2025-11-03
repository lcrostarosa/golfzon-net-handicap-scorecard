"""
Streamlit application for Golfzon scorecard OCR and net score calculation.
"""
import streamlit as st
from PIL import Image
import pandas as pd
import io

from ocr import extract_text
from parser import parse_players
from calculator import calculate_net_scores


# Page configuration
st.set_page_config(
    page_title="Golfzon Scorecard OCR",
    page_icon="⛳",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .winner-banner {
        background-color: #FFD700;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.title("⛳ Golfzon Scorecard OCR")
    st.markdown("Upload a screenshot of your Golfzon scorecard to calculate net scores based on handicaps.")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        num_holes = st.radio(
            "Number of holes:",
            [9, 18],
            index=0,
            help="Select 9-hole or 18-hole round"
        )
        
        st.markdown("---")
        st.markdown("### How it works:")
        st.markdown("""
        1. Upload a screenshot of your scorecard
        2. OCR extracts player data
        3. Net scores are calculated using:
           - **9-hole**: strokes = handicap / 2
           - **18-hole**: strokes = handicap
        4. Results sorted by net score (lowest wins)
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a screenshot of your Golfzon scorecard"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Scorecard", use_container_width=True)
        
        # Process the image
        with st.spinner("Processing image with OCR..."):
            try:
                # Extract text using OCR
                ocr_text = extract_text(image)
                
                # Also get backup OCR with PSM 11 for missing handicaps
                try:
                    import pytesseract
                    import cv2
                    import numpy as np
                    img_array = np.array(image)
                    if len(img_array.shape) == 3:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                    try:
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                        enhanced = clahe.apply(gray)
                    except:
                        enhanced = gray
                    backup_ocr_text = pytesseract.image_to_string(enhanced, config=r'--oem 3 --psm 11')
                except:
                    backup_ocr_text = None
                
                # Show raw OCR text in expandable section
                with st.expander("Raw OCR Text", expanded=False):
                    st.text(ocr_text)
                
                # Parse player data (with backup OCR for missing handicaps)
                players = parse_players(ocr_text, backup_ocr_text=backup_ocr_text if 'backup_ocr_text' in locals() else None)
                
                if not players:
                    st.error("❌ No player data found in the image. Please check:")
                    st.markdown("""
                    - Ensure the image is clear and readable
                    - Verify the scorecard format matches Golfzon style
                    - Check that player names, scores, and handicaps are visible
                    """)
                    st.text("OCR Output:")
                    st.text(ocr_text)
                else:
                    # Calculate net scores
                    results = calculate_net_scores(players, num_holes)
                    
                    # Display results
                    st.header("📊 Results")
                    
                    # Create DataFrame for display
                    df = pd.DataFrame(results)
                    
                    # Reorder columns for better display
                    df_display = df[['name', 'gross_score', 'handicap', 'strokes_given', 'net_score']].copy()
                    df_display.columns = ['Player', 'Gross Score', 'Handicap (G-HCP)', 'Strokes Given', 'Net Score']
                    
                    # Display table
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Display winner
                    if results:
                        winner = results[0]
                        st.markdown(
                            f'<div class="winner-banner">🏆 Winner: {winner["name"]} '
                            f'(Net Score: {winner["net_score"]:.1f})</div>',
                            unsafe_allow_html=True
                        )
                    
                    # CSV export
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name="golf_scorecard_results.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"❌ Error processing image: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()

