# Hole-by-Hole Scores Feature

## Overview
This document describes the new hole-by-hole score extraction and editing feature added to the Golfzon League Manager.

## What Was Implemented

### 1. **Parser Enhancements** (`src/golfzon_ocr/processing/parser.py`)
- Added `extract_hole_scores()` function to extract individual hole scores from OCR text
- Added `parse_players_with_holes()` function to parse both player summaries and hole-by-hole scores
- The parser looks for table-like structures in the scorecard with hole numbers and player rows
- Handles both 9-hole and 18-hole rounds

### 2. **Calculator Enhancements** (`src/golfzon_ocr/processing/calculator.py`)
- Added `calculate_gross_from_holes()` to calculate gross score from hole scores
- Added `recalculate_from_hole_scores()` to recalculate all player stats from edited hole scores
- Supports automatic recalculation when hole scores are modified in the UI

### 3. **UI Integration** (`app.py`)
- Added **⛳ Hole-by-Hole Scores** section after the player results table
- Displays an editable data grid with:
  - Player names in the first column
  - Individual hole scores (H1, H2, H3, etc.) in subsequent columns
  - All hole scores are editable (1-15 range)
- Auto-recalculates gross score and net score when hole scores are edited
- Session state management to preserve hole scores across UI updates

## How It Works

### OCR Processing Flow
1. Upload a Golfzon scorecard image
2. Extract OCR text from the image
3. Parse player summaries (name, gross score, handicap)
4. Extract hole-by-hole scores from the scorecard table
5. Match hole scores to players by name
6. Display both player summaries and hole scores in editable tables

### Data Structure
- **Hole Scores Dictionary**: `{player_name: [score1, score2, ..., score9]}`
- Scores are integers (1-15) or `None` for missing data
- Stored in Streamlit session state (`st.session_state.hole_scores`)

### User Interaction
1. **View OCR Results**: See extracted player summaries with totals
2. **Edit Player Names**: Click on "Enter player name..." cells to edit
3. **Edit Hole Scores**: Click on individual hole score cells to modify
4. **Auto-Recalculation**: Gross score and net score update automatically
5. **Save to Database**: Save the final results (currently stores totals only)

## Features

### ✅ Implemented
- [x] Extract hole-by-hole scores from OCR text
- [x] Display hole scores in an editable data grid
- [x] Auto-recalculate gross score from hole scores
- [x] Auto-recalculate net score from gross score
- [x] Support for both 9-hole and 18-hole rounds
- [x] Handle missing/incomplete hole score data gracefully
- [x] Session state management for hole scores

### 🔮 Future Enhancements
- [ ] Store hole scores in the database (currently only stores totals)
- [ ] Add Par row to show expected score for each hole
- [ ] Show over/under par for each hole (+1, -1, E)
- [ ] Color-code holes (green for under par, red for over par)
- [ ] Add hole-by-hole statistics (birdies, pars, bogeys)
- [ ] Improve OCR accuracy for hole score detection
- [ ] Support for "OUT" and "IN" nine splits in 18-hole rounds

## Testing

### Test Results
- ✅ Parser successfully extracts hole scores from sample scorecards
- ✅ Calculator correctly recalculates gross scores from hole scores
- ✅ UI displays and updates hole scores correctly
- ⚠️ Some edge cases in OCR detection (e.g., partial names, ambiguous numbers)

### Known Limitations
1. **OCR Accuracy**: Hole score extraction depends on OCR quality
   - Works best with clear, well-lit screenshots
   - May miss scores if table structure is unclear
2. **Name Matching**: Partial name matches may cause incorrect associations
3. **Missing Scores**: If OCR doesn't detect hole scores, table shows zeros
   - Users can manually enter scores in this case

## Usage Example

### Before (Old Behavior)
```
Player Results:
- Beachy: Gross 48, Net 37.7
- FirstOrLast: Gross 40, Net 31.9
```

### After (New Feature)
```
Player Results:
- Beachy: Gross 48, Net 37.7
- FirstOrLast: Gross 40, Net 31.9

⛳ Hole-by-Hole Scores:
Player      H1  H2  H3  H4  H5  H6  H7  H8  H9
Beachy       4   4   4   5   6   6   6   6   7
FirstOrLast  5   6   3   3   5   5   5   4   4
```

## Technical Details

### File Changes
1. **`parser.py`**: +300 lines (new functions for hole extraction)
2. **`calculator.py`**: +80 lines (recalculation from holes)
3. **`__init__.py`**: Updated exports
4. **`app.py`**: +150 lines (UI for hole scores editor)

### Dependencies
- No new dependencies required
- Uses existing Streamlit `st.data_editor()` component
- Compatible with pandas DataFrames

## Conclusion

The hole-by-hole scores feature provides users with detailed visibility into individual hole performance. Users can now:
1. See exactly how each player performed on each hole
2. Manually correct OCR errors at the hole level
3. Understand scoring patterns and trends

This addresses the issue of the empty div that should contain "all of the holes from the OCR text" - it now displays a fully functional, editable table of hole-by-hole scores.

