"""
Streamlit application for Golfzon scorecard OCR and league management.
"""
import streamlit as st
from PIL import Image
import pandas as pd
from datetime import datetime

# Register HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    # pillow-heif not installed, HEIC files won't be supported
    pass

from golfzon_ocr.processing import extract_text, parse_players, calculate_net_scores, recalculate_net_scores
from golfzon_ocr.db import (
    get_db_context, create_league, get_league, list_leagues,
    get_league_by_name, list_teams, create_team,
    create_weekly_score, get_player_scores_by_week, get_all_weeks,
    get_top_two_scores_per_team, get_scores_by_week
)
from golfzon_ocr.services import match_ocr_players_to_existing, add_player_to_team, get_team_roster
from golfzon_ocr.services import get_leaderboard_summary, calculate_weekly_standings
from golfzon_ocr.export import export_full_league_data, export_weekly_summary, export_team_roster


# Page configuration
st.set_page_config(
    page_title="Golfzon League Manager",
    page_icon="⛳",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .winner-banner {
        background-color: #D4EDDA;
        color: #155724;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
        border: 1px solid #C3E6CB;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'selected_league_id' not in st.session_state:
        st.session_state.selected_league_id = None
    if 'original_results' not in st.session_state:
        st.session_state.original_results = None
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'current_image_id' not in st.session_state:
        st.session_state.current_image_id = None


def league_selection_sidebar():
    """League selection sidebar."""
    with st.sidebar:
        st.header("🏆 League Selection")
        
        with get_db_context() as db:
            leagues = list_leagues(db)
            league_names = [league.name for league in leagues]
            
            if league_names:
                selected_league_name = st.selectbox(
                    "Select League",
                    league_names,
                    index=0 if st.session_state.selected_league_id is None else None
                )
                
                selected_league = next(
                    (league for league in leagues
                     if league.name == selected_league_name),
                    None
                )
                if selected_league:
                    st.session_state.selected_league_id = selected_league.id
                    st.info(f"Selected: **{selected_league.name}**")
            else:
                st.info("No leagues yet. Create one below!")
            
            st.markdown("---")
            st.subheader("Create New League")
            new_league_name = st.text_input("League Name", key="new_league_input")
            if st.button("Create League", type="primary"):
                if new_league_name.strip():
                    try:
                        # Check if league already exists
                        existing = get_league_by_name(db, new_league_name.strip())
                        if existing:
                            st.error(f"League '{new_league_name}' already exists!")
                        else:
                            new_league = create_league(db, new_league_name.strip())
                            st.session_state.selected_league_id = new_league.id
                            st.success(f"Created league '{new_league.name}'!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating league: {e}")
                else:
                    st.warning("Please enter a league name")


def page_score_submission():
    """Score submission page with OCR and manual entry."""
    st.header("📸 Submit Scores")
    
    if not st.session_state.selected_league_id:
        st.warning("Please select or create a league first!")
        return
    
    with get_db_context() as db:
        league = get_league(db, st.session_state.selected_league_id)
        if not league:
            st.error("Selected league not found!")
            return
        
        st.info(f"Submitting scores for: **{league.name}**")
        
        # Week selection
        col1, col2 = st.columns(2)
        with col1:
            week_number = st.number_input("Week Number", min_value=1, value=1, step=1)
        with col2:
            num_holes = st.radio("Number of holes:", [9, 18], index=0, horizontal=True)
        
        # Submission method selection
        submission_method = st.radio(
            "Submission Method:",
            ["OCR from Image", "Manual Entry", "Bulk Entry (Multiple Weeks)"],
            horizontal=True
        )
        
        if submission_method == "OCR from Image":
            _ocr_score_submission(db, league, week_number, num_holes)
        elif submission_method == "Manual Entry":
            _manual_score_submission(db, league, week_number, num_holes)
        else:
            _bulk_score_submission(db, league, num_holes)


def _ocr_score_submission(db, league, week_number, num_holes):
    """OCR-based score submission."""
    # Settings
    auto_calculate_strokes = st.checkbox(
        "Auto-calculate strokes from handicap",
        value=True
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png', 'heic', 'heif'],
        help="Upload a screenshot of your Golfzon scorecard"
    )
    
    # Reset session state when new file is uploaded
    if uploaded_file is not None:
        current_file_id = id(uploaded_file)
        if st.session_state.current_image_id != current_file_id:
            st.session_state.current_image_id = current_file_id
            st.session_state.original_results = None
            st.session_state.current_results = None
    
    if uploaded_file is not None:
        # Display uploaded image
        try:
            image = Image.open(uploaded_file)
            # Convert HEIC to RGB if needed
            if image.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB for better OCR compatibility
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            st.image(image, caption="Uploaded Scorecard", use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")
            st.info("If this is a HEIC file, make sure pillow-heif is installed: pip install pillow-heif")
            return
        
        # Process the image
        with st.spinner("Processing image with OCR..."):
            try:
                # Extract text using OCR
                ocr_text = extract_text(image)
                
                # Backup OCR
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
                    except Exception:
                        enhanced = gray
                    backup_ocr_text = pytesseract.image_to_string(enhanced, config=r'--oem 3 --psm 11')
                except Exception:
                    backup_ocr_text = None
                
                # Show raw OCR text
                with st.expander("Raw OCR Text", expanded=False):
                    st.text(ocr_text)
                
                # Parse player data
                players = parse_players(ocr_text, backup_ocr_text=backup_ocr_text if 'backup_ocr_text' in locals() else None)
                
                if not players:
                    st.error("❌ No player data found in the image.")
                    return
                
                # Calculate net scores
                if st.session_state.original_results is None:
                    results = calculate_net_scores(players, num_holes)
                    st.session_state.original_results = results
                    st.session_state.current_results = results
                else:
                    results = st.session_state.current_results
                
                # Display results
                st.header("📊 Results")
                
                df = pd.DataFrame(results)
                df_display = df[['name', 'gross_score', 'handicap', 'strokes_given', 'net_score']].copy()
                df_display.columns = ['Player', 'Gross Score', 'Handicap (G-HCP)', 'Strokes Given', 'Net Score']
                
                # Replace empty names with placeholder text for display
                df_display['Player'] = df_display['Player'].replace('', 'Enter player name...')
                
                column_config = {
                    "Player": st.column_config.TextColumn("Player", disabled=False),  # Enable editing for manual name entry
                    "Gross Score": st.column_config.NumberColumn("Gross Score", min_value=1, max_value=200, step=1),
                    "Handicap (G-HCP)": st.column_config.NumberColumn("Handicap (G-HCP)", min_value=-50.0, max_value=50.0, step=0.1, format="%.1f"),
                    "Strokes Given": st.column_config.NumberColumn("Strokes Given", min_value=-50.0, max_value=50.0, step=0.1, format="%.2f", disabled=auto_calculate_strokes),
                    "Net Score": st.column_config.NumberColumn("Net Score", format="%.2f", disabled=True)
                }
                
                # Show warning if any players have empty names
                if any(r.get('name', '').strip() == '' for r in results):
                    empty_count = sum(1 for r in results if not r.get('name', '').strip())
                    st.warning(f"⚠️ {empty_count} player(s) have missing names. **Click on the 'Enter player name...' cells in the Player column below to edit them.**")
                    st.info("💡 **How to edit:** Click directly on the cell showing 'Enter player name...', delete that text, and type the actual player name.")
                
                edited_df = st.data_editor(
                    df_display,
                    column_config=column_config,
                    use_container_width=True,
                    hide_index=True,
                    key=f"results_editor_{num_holes}_{auto_calculate_strokes}"
                )
                
                # Convert back to results format
                edited_results = []
                for _, row in edited_df.iterrows():
                    player_name = row["Player"]
                    # Handle placeholder text - convert back to empty string
                    # Also handle NaN values that might come from pandas
                    if pd.isna(player_name) or str(player_name).strip() == "" or "Enter player name" in str(player_name):
                        player_name = ""
                    else:
                        player_name = str(player_name).strip()
                    
                    edited_results.append({
                        "name": player_name,
                        "gross_score": int(row["Gross Score"]),
                        "handicap": float(row["Handicap (G-HCP)"]),
                        "strokes_given": float(row["Strokes Given"])
                    })
                
                # Recalculate
                recalculated_results = recalculate_net_scores(
                    edited_results,
                    num_holes,
                    auto_calculate_strokes=auto_calculate_strokes
                )
                st.session_state.current_results = recalculated_results
                results = recalculated_results
                
                # Check for empty names after editing
                players_with_empty_names = [r for r in results if not r.get('name', '').strip()]
                has_empty_names = len(players_with_empty_names) > 0
                
                # Display winner (only if all players have names)
                if results:
                    winner = results[0]
                    if winner.get("name", "").strip():
                        st.markdown(
                            f'<div class="winner-banner">🏆 Winner: {winner["name"]} '
                            f'(Net Score: {winner["net_score"]:.1f})</div>',
                            unsafe_allow_html=True
                        )
                    elif not has_empty_names:
                        # All names filled but winner name check failed (shouldn't happen)
                        st.info("💡 Please enter player names above to see the winner.")
                    else:
                        st.info("💡 Please enter player names above to see the winner.")
                
                # Save to database
                st.markdown("---")
                st.subheader("💾 Save Scores")
                
                # Check if any players have empty names
                if has_empty_names:
                    st.error(f"⚠️ {len(players_with_empty_names)} players have missing names. Please click on the 'Enter player name...' cells in the table above and type the player names, then try saving again.")
                    st.info("💡 **Tip:** Click directly on the 'Enter player name...' text in the Player column to edit it.")
                    return
                
                # Match players to database
                matched_players = match_ocr_players_to_existing(db, results, st.session_state.selected_league_id)
                
                # Check if all players are matched
                unmatched = [m for m in matched_players if m['action'] == 'needs_team']
                if unmatched:
                    st.warning(f"⚠️ {len(unmatched)} players need team assignment before saving.")
                    st.write("Unmatched players:")
                    for match in unmatched:
                        st.write(f"- {match['ocr_data']['name']}")
                    st.info("Please assign these players to teams in the Team Management page first.")
                else:
                    # Show matching status
                    with st.expander("Player Matching", expanded=False):
                        for match in matched_players:
                            status_icon = "✅" if match['action'] == 'matched' else "🆕"
                            st.write(f"{status_icon} {match['ocr_data']['name']} → {match['player'].name} ({match['player'].team.name})")
                    
                    if st.button("Save Scores to Database", type="primary"):
                        saved_count = 0
                        error_count = 0
                        
                        # Create a mapping of player names to calculated results
                        results_dict = {r['name']: r for r in results}
                        
                        for match in matched_players:
                            player = match['player']
                            ocr_data = match['ocr_data']
                            
                            # Find matching calculated result
                            calculated_result = results_dict.get(ocr_data['name'])
                            if not calculated_result:
                                # Try to find by matching player name
                                calculated_result = next(
                                    (r for r in results
                                     if r['name'].lower() == player.name.lower()),
                                    None
                                )
                            
                            if not calculated_result:
                                st.warning(f"Could not find calculated result for {player.name}. Skipping.")
                                error_count += 1
                                continue
                            
                            # Check if score already exists for this week
                            existing_score = get_player_scores_by_week(db, player.id, week_number)
                            if existing_score:
                                st.warning(f"Score for {player.name} (Week {week_number}) already exists. Skipping.")
                                continue
                            
                            try:
                                create_weekly_score(
                                    db,
                                    player_id=player.id,
                                    league_id=st.session_state.selected_league_id,
                                    week_number=week_number,
                                    date=datetime.now(),
                                    gross_score=calculated_result['gross_score'],
                                    handicap=calculated_result['handicap'],
                                    strokes_given=calculated_result['strokes_given'],
                                    net_score=calculated_result['net_score'],
                                    num_holes=num_holes
                                )
                                saved_count += 1
                            except Exception as e:
                                st.error(f"Error saving score for {player.name}: {e}")
                                error_count += 1
                        
                        if saved_count > 0:
                            st.success(f"✅ Saved {saved_count} scores for Week {week_number}!")
                        if error_count > 0:
                            st.error(f"❌ Failed to save {error_count} scores.")
                        
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error processing image: {str(e)}")
                st.exception(e)


def _manual_score_submission(db, league, week_number, num_holes):
    """Manual score entry submission."""
    st.subheader("Manual Score Entry")
    
    # Get all teams and players
    teams = list_teams(db, league_id=league.id)
    
    if not teams:
        st.warning("No teams found. Please create teams first in the Team Management page.")
        return
    
    # Settings
    auto_calculate_strokes = st.checkbox(
        "Auto-calculate strokes from handicap",
        value=True
    )
    
    # Manual entry form
    st.markdown("### Enter Scores")
    
    # Create form for manual entry
    with st.form("manual_score_form"):
        # Player selection and score entry
        entries = []
        
        for team in teams:
            st.markdown(f"**{team.name}**")
            players = get_team_roster(db, team.id)
            
            if not players:
                st.write(f"*No players in {team.name}*")
                continue
            
            # Create entries for each player
            for player in players:
                # Check if score already exists
                existing_score = get_player_scores_by_week(db, player.id, week_number)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{player.name}**")
                    if existing_score:
                        st.caption(f"⚠️ Score exists: {existing_score.net_score:.2f} (Week {week_number})")
                
                with col2:
                    gross_score = st.number_input(
                        "Gross Score",
                        min_value=1,
                        max_value=200,
                        value=existing_score.gross_score if existing_score else 40,
                        key=f"gross_{player.id}"
                    )
                
                with col3:
                    handicap = st.number_input(
                        "Handicap",
                        min_value=-50.0,
                        max_value=50.0,
                        value=existing_score.handicap if existing_score else 10.0,
                        step=0.1,
                        format="%.1f",
                        key=f"handicap_{player.id}"
                    )
                
                # Calculate strokes and net score
                if auto_calculate_strokes:
                    if num_holes == 9:
                        strokes_given = handicap / 2
                    else:
                        strokes_given = handicap
                else:
                    strokes_given_input = st.number_input(
                        "Strokes Given",
                        min_value=-50.0,
                        max_value=50.0,
                        value=existing_score.strokes_given if existing_score else (handicap / 2 if num_holes == 9 else handicap),
                        step=0.1,
                        format="%.2f",
                        key=f"strokes_{player.id}"
                    )
                    strokes_given = strokes_given_input
                
                net_score = gross_score - strokes_given
                
                entries.append({
                    'player': player,
                    'gross_score': gross_score,
                    'handicap': handicap,
                    'strokes_given': strokes_given,
                    'net_score': net_score,
                    'existing_score': existing_score
                })
        
        submitted = st.form_submit_button("Save Scores", type="primary")
        
        if submitted:
            saved_count = 0
            updated_count = 0
            error_count = 0
            
            for entry in entries:
                player = entry['player']
                existing_score = entry['existing_score']
                
                try:
                    if existing_score:
                        # Update existing score
                        existing_score.gross_score = entry['gross_score']
                        existing_score.handicap = entry['handicap']
                        existing_score.strokes_given = entry['strokes_given']
                        existing_score.net_score = entry['net_score']
                        existing_score.num_holes = num_holes
                        db.commit()
                        updated_count += 1
                    else:
                        # Create new score
                        create_weekly_score(
                            db,
                            player_id=player.id,
                            league_id=league.id,
                            week_number=week_number,
                            date=datetime.now(),
                            gross_score=entry['gross_score'],
                            handicap=entry['handicap'],
                            strokes_given=entry['strokes_given'],
                            net_score=entry['net_score'],
                            num_holes=num_holes
                        )
                        saved_count += 1
                except Exception as e:
                    st.error(f"Error saving score for {player.name}: {e}")
                    error_count += 1
            
            if saved_count > 0 or updated_count > 0:
                msg = []
                if saved_count > 0:
                    msg.append(f"✅ Saved {saved_count} new scores")
                if updated_count > 0:
                    msg.append(f"✅ Updated {updated_count} scores")
                st.success(" ".join(msg) + f" for Week {week_number}!")
            if error_count > 0:
                st.error(f"❌ Failed to save {error_count} scores.")
            
            if saved_count > 0 or updated_count > 0:
                st.rerun()


def _bulk_score_submission(db, league, num_holes):
    """Bulk score entry for multiple weeks at team level."""
    st.subheader("Bulk Score Entry - Multiple Weeks")
    st.info("💡 Enter the team total score (sum of top 2 net scores) for each team per week. Perfect for catching up an in-progress league!")
    
    # Get all teams
    teams = list_teams(db, league_id=league.id)
    
    if not teams:
        st.warning("No teams found. Please create teams first in the Team Management page.")
        return
    
    # Week range selection
    st.markdown("### Select Weeks")
    col1, col2 = st.columns(2)
    with col1:
        start_week = st.number_input("Start Week", min_value=1, value=1, step=1)
    with col2:
        end_week = st.number_input("End Week", min_value=1, value=1, step=1)
    
    if start_week > end_week:
        st.error("Start week must be less than or equal to end week!")
        return
    
    weeks = list(range(start_week, end_week + 1))
    st.caption(f"Entering team totals for weeks: {', '.join(map(str, weeks))}")
    
    st.markdown("---")
    st.markdown("### Enter Team Total Scores")
    st.caption("Enter the team total (sum of top 2 net scores) for each team per week.")
    
    # Create form for bulk entry
    with st.form("bulk_score_form"):
        # Team-level entries
        team_entries = []
        
        for team in teams:
            st.markdown(f"**{team.name}**")
            players = get_team_roster(db, team.id)
            
            if not players:
                st.write(f"*No players in {team.name}*")
                continue
            
            if len(players) < 2:
                st.warning(f"⚠️ {team.name} needs at least 2 players to record team scores.")
                st.markdown("---")
                continue
            
            # Get existing top 2 scores for reference
            team_entry = {
                'team': team,
                'players': players[:2],  # Use first 2 players
                'weeks': {}
            }
            
            # Create columns for each week
            cols = st.columns(len(weeks))
            
            for idx, week_num in enumerate(weeks):
                with cols[idx]:
                    st.caption(f"Week {week_num}")
                    
                    # Get existing team total for this week
                    top_scores = get_top_two_scores_per_team(db, league.id, week_num)
                    existing_scores = top_scores.get(team.id, [])
                    
                    existing_total = None
                    if len(existing_scores) >= 2:
                        existing_total = sum(s.net_score for s in existing_scores[:2])
                        st.caption(f"Current: {existing_total:.2f} ({existing_scores[0].player.name} + {existing_scores[1].player.name})")
                    elif len(existing_scores) == 1:
                        existing_total = existing_scores[0].net_score
                        st.caption(f"Current: {existing_total:.2f} (incomplete)")
                    
                    # Input for team total
                    team_total = st.number_input(
                        "Team Total",
                        min_value=0.0,
                        max_value=400.0,
                        value=existing_total if existing_total else 70.0,
                        step=0.1,
                        format="%.2f",
                        key=f"bulk_team_{team.id}_week_{week_num}_total"
                    )
                    
                    team_entry['weeks'][week_num] = {
                        'team_total': team_total,
                        'existing_scores': existing_scores
                    }
            
            team_entries.append(team_entry)
            st.markdown("---")
        
        submitted = st.form_submit_button("Save All Team Scores", type="primary")
        
        if submitted:
            saved_count = 0
            updated_count = 0
            error_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_operations = sum(len(entry['weeks']) for entry in team_entries)
            current_op = 0
            
            for team_entry in team_entries:
                team = team_entry['team']
                players = team_entry['players']
                
                for week_num, week_data in team_entry['weeks'].items():
                    current_op += 1
                    progress_bar.progress(current_op / total_operations)
                    status_text.text(f"Processing {team.name} - Week {week_num}...")
                    
                    # Get existing scores for this team/week
                    existing_scores = week_data['existing_scores']
                    target_total = week_data['team_total']
                    
                    # Get all scores for this team/week
                    all_team_scores = get_scores_by_week(db, league.id, week_num)
                    team_player_scores = [s for s in all_team_scores if s.player.team_id == team.id]
                    team_player_scores.sort(key=lambda x: x.net_score)
                    
                    # Calculate target scores (split evenly, or use existing proportions)
                    if len(team_player_scores) >= 2:
                        # Update existing top 2 scores proportionally
                        score1_obj = team_player_scores[0]
                        score2_obj = team_player_scores[1]
                        
                        # Calculate current total and proportions
                        current_total = score1_obj.net_score + score2_obj.net_score
                        if current_total > 0:
                            # Maintain proportions
                            ratio1 = score1_obj.net_score / current_total
                            ratio2 = score2_obj.net_score / current_total
                            target_score1 = target_total * ratio1
                            target_score2 = target_total * ratio2
                        else:
                            # Split evenly
                            target_score1 = target_total / 2
                            target_score2 = target_total / 2
                        
                        try:
                            # Adjust gross_score to achieve target net_score
                            gross_diff1 = target_score1 - score1_obj.net_score
                            score1_obj.gross_score = int(score1_obj.gross_score + gross_diff1)
                            score1_obj.net_score = target_score1
                            db.commit()
                            updated_count += 1
                            
                            gross_diff2 = target_score2 - score2_obj.net_score
                            score2_obj.gross_score = int(score2_obj.gross_score + gross_diff2)
                            score2_obj.net_score = target_score2
                            db.commit()
                            updated_count += 1
                        except Exception as e:
                            st.error(f"Error updating scores for {team.name} (Week {week_num}): {e}")
                            error_count += 1
                    elif len(team_player_scores) == 1:
                        # Update existing score, create second
                        score1_obj = team_player_scores[0]
                        # Split: use existing score proportionally, or split evenly
                        if score1_obj.net_score > 0:
                            # Maintain player 1's score, calculate player 2's
                            target_score1 = score1_obj.net_score
                            target_score2 = target_total - target_score1
                        else:
                            # Split evenly
                            target_score1 = target_total / 2
                            target_score2 = target_total / 2
                        
                        # Update first score
                        gross_diff1 = target_score1 - score1_obj.net_score
                        score1_obj.gross_score = int(score1_obj.gross_score + gross_diff1)
                        score1_obj.net_score = target_score1
                        db.commit()
                        updated_count += 1
                        
                        # Create second score
                        player2 = players[1] if players[0].id == score1_obj.player_id else players[0]
                        estimated_gross = target_score2 + score1_obj.strokes_given
                        try:
                            create_weekly_score(
                                db,
                                player_id=player2.id,
                                league_id=league.id,
                                week_number=week_num,
                                date=datetime.now(),
                                gross_score=int(estimated_gross),
                                handicap=score1_obj.handicap,
                                strokes_given=score1_obj.strokes_given,
                                net_score=target_score2,
                                num_holes=num_holes
                            )
                            saved_count += 1
                        except Exception as e:
                            st.error(f"Error creating score for {player2.name} (Week {week_num}): {e}")
                            error_count += 1
                    else:
                        # No scores exist, create them - split evenly
                        default_handicap = 10.0
                        strokes = default_handicap / 2 if num_holes == 9 else default_handicap
                        
                        target_score1 = target_total / 2
                        target_score2 = target_total / 2
                        
                        try:
                            # Create first score
                            create_weekly_score(
                                db,
                                player_id=players[0].id,
                                league_id=league.id,
                                week_number=week_num,
                                date=datetime.now(),
                                gross_score=int(target_score1 + strokes),
                                handicap=default_handicap,
                                strokes_given=strokes,
                                net_score=target_score1,
                                num_holes=num_holes
                            )
                            saved_count += 1
                            
                            # Create second score
                            create_weekly_score(
                                db,
                                player_id=players[1].id,
                                league_id=league.id,
                                week_number=week_num,
                                date=datetime.now(),
                                gross_score=int(target_score2 + strokes),
                                handicap=default_handicap,
                                strokes_given=strokes,
                                net_score=target_score2,
                                num_holes=num_holes
                            )
                            saved_count += 1
                        except Exception as e:
                            st.error(f"Error creating scores for {team.name} (Week {week_num}): {e}")
                            error_count += 1
            
            progress_bar.empty()
            status_text.empty()
            
            # Show results
            if saved_count > 0 or updated_count > 0:
                msg = []
                if saved_count > 0:
                    msg.append(f"✅ Saved {saved_count} new scores")
                if updated_count > 0:
                    msg.append(f"✅ Updated {updated_count} scores")
                st.success(" ".join(msg) + f" across {len(weeks)} weeks!")
            if error_count > 0:
                st.error(f"❌ Failed to save {error_count} scores.")
            
            if saved_count > 0 or updated_count > 0:
                st.rerun()


def page_team_management():
    """Team management page."""
    st.header("👥 Team Management")
    
    if not st.session_state.selected_league_id:
        st.warning("Please select or create a league first!")
        return
    
    with get_db_context() as db:
        league = get_league(db, st.session_state.selected_league_id)
        if not league:
            st.error("Selected league not found!")
            return
        
        st.info(f"Managing teams for: **{league.name}**")
        
        # Create new team
        st.subheader("Create New Team")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_team_name = st.text_input("Team Name", key="new_team_input")
        with col2:
            if st.button("Create Team", type="primary"):
                if new_team_name.strip():
                    try:
                        create_team(db, st.session_state.selected_league_id, new_team_name.strip())
                        st.success(f"Created team '{new_team_name}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating team: {e}")
                else:
                    st.warning("Please enter a team name")
        
        st.markdown("---")
        
        # List teams
        teams = list_teams(db, league_id=st.session_state.selected_league_id)
        
        if not teams:
            st.info("No teams yet. Create one above!")
        else:
            for team in teams:
                with st.expander(f"🏌️ {team.name}", expanded=False):
                    players = get_team_roster(db, team.id)
                    
                    st.write(f"**Players:** {len(players)}")
                    if players:
                        for player in players:
                            st.write(f"- {player.name}")
                    else:
                        st.write("*(no players)*")
                    
                    # Add player
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_player_name = st.text_input(f"Add Player", key=f"player_input_{team.id}")
                    with col2:
                        if st.button("Add", key=f"add_player_{team.id}"):
                            if new_player_name.strip():
                                try:
                                    add_player_to_team(db, team.id, new_player_name.strip())
                                    st.success(f"Added {new_player_name} to {team.name}!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            else:
                                st.warning("Please enter a player name")


def page_leaderboard():
    """Leaderboard page."""
    st.header("📊 Leaderboard")
    
    if not st.session_state.selected_league_id:
        st.warning("Please select or create a league first!")
        return
    
    with get_db_context() as db:
        league = get_league(db, st.session_state.selected_league_id)
        if not league:
            st.error("Selected league not found!")
            return
        
        summary = get_leaderboard_summary(db, st.session_state.selected_league_id)
        
        if not summary['weeks']:
            st.info("No scores yet. Submit scores in the Score Submission page!")
            return
        
        # Week selector
        selected_week = st.selectbox(
            "View Week",
            summary['weeks'],
            index=len(summary['weeks']) - 1 if summary['weeks'] else 0
        )
        
        # Current week standings
        if selected_week:
            st.subheader(f"Week {selected_week} Standings")
            standings = calculate_weekly_standings(db, st.session_state.selected_league_id, selected_week)
            
            if standings:
                standings_data = []
                for rank, standing in enumerate(standings, 1):
                    score_display = standing['score']
                    if standing['score'] is None:
                        score_display = 'No scores'
                    elif not standing.get('is_complete', False):
                        score_display = f"{standing['score']:.2f}* (1 of 2)"
                    else:
                        score_display = f"{standing['score']:.2f}"
                    
                    players_str = ', '.join([f"{s['player_name']} ({s['net_score']:.2f})" 
                                            for s in standing['top_two_scores']])
                    if not standing['top_two_scores']:
                        players_str = 'No scores'
                    
                    standings_data.append({
                        'Rank': rank,
                        'Team': standing['team_name'],
                        'Score': score_display,
                        'Status': 'Complete' if standing.get('is_complete', False) else 'Incomplete',
                        'Top Players': players_str
                    })
                
                df = pd.DataFrame(standings_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                if any(not s.get('is_complete', False) for s in standings):
                    st.caption("* Teams with 1 score shown - need 2 scores for complete standings")
            else:
                st.info("No scores for this week yet.")
        
        st.markdown("---")
        
        # Cumulative standings
        st.subheader("Cumulative Standings")
        cumulative = summary['cumulative_standings']
        
        if cumulative:
            cumulative_data = []
            for rank, standing in enumerate(cumulative, 1):
                cumulative_data.append({
                    'Rank': rank,
                    'Team': standing['team_name'],
                    'Total Score': f"{standing['total_score']:.2f}",
                    'Weeks Played': standing['weeks_played'],
                    'Average Score': f"{standing['average_score']:.2f}" if standing['average_score'] else 'N/A'
                })
            
            df_cumulative = pd.DataFrame(cumulative_data)
            st.dataframe(df_cumulative, use_container_width=True, hide_index=True)
        else:
            st.info("No cumulative standings yet.")


def page_export():
    """Export page."""
    st.header("📥 Export Data")
    
    if not st.session_state.selected_league_id:
        st.warning("Please select or create a league first!")
        return
    
    with get_db_context() as db:
        league = get_league(db, st.session_state.selected_league_id)
        if not league:
            st.error("Selected league not found!")
            return
        
        st.info(f"Exporting data for: **{league.name}**")
        
        # Export options
        export_type = st.radio(
            "Export Type",
            ["Full League Data", "Weekly Summary", "Team Rosters"],
            horizontal=True
        )
        
        if export_type == "Full League Data":
            if st.button("Export Full League Data", type="primary"):
                try:
                    csv_data = export_full_league_data(db, st.session_state.selected_league_id)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"{league.name}_full_export.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error exporting: {e}")
        
        elif export_type == "Weekly Summary":
            weeks = get_all_weeks(db, st.session_state.selected_league_id)
            if weeks:
                selected_week = st.selectbox("Select Week", weeks)
                if st.button("Export Weekly Summary", type="primary"):
                    try:
                        csv_data = export_weekly_summary(db, st.session_state.selected_league_id, selected_week)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=f"{league.name}_week_{selected_week}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"Error exporting: {e}")
            else:
                st.info("No weeks with scores yet.")
        
        elif export_type == "Team Rosters":
            if st.button("Export Team Rosters", type="primary"):
                try:
                    csv_data = export_team_roster(db, st.session_state.selected_league_id)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"{league.name}_rosters.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error exporting: {e}")


def main():
    """Main application."""
    initialize_session_state()
    
    st.title("⛳ Golfzon League Manager")
    
    # League selection sidebar
    league_selection_sidebar()
    
    if not st.session_state.selected_league_id:
        st.info("👈 Please select or create a league in the sidebar to get started!")
        return
    
    # Page navigation
    page = st.tabs(["📸 Submit Scores", "👥 Team Management", "📊 Leaderboard", "📥 Export"])
    
    with page[0]:
        page_score_submission()
    with page[1]:
        page_team_management()
    with page[2]:
        page_leaderboard()
    with page[3]:
        page_export()


if __name__ == "__main__":
    main()
