"""
Test to verify 1.png data extraction is correct.
"""
import pytest
from pathlib import Path
from PIL import Image
from golfzon_ocr.processing.ocr import extract_text
from golfzon_ocr.processing.parser import parse_players
from golfzon_ocr.processing.calculator import calculate_net_scores


def test_1png_data_extraction():
    """Test that 1.png extracts correct player data."""
    image_path = Path(__file__).parent.parent / "uploads" / "1.png"
    
    if not image_path.exists():
        pytest.skip("1.png not found in uploads directory")
    
    # Load and process image
    image = Image.open(image_path)
    ocr_text = extract_text(image)
    players = parse_players(ocr_text)
    
    # Should find 3 players
    assert len(players) == 3, f"Expected 3 players, found {len(players)}"
    
    # Find each player by name
    beachy = next((p for p in players if 'beachy' in p.get('name', '').lower()), None)
    firstorlast = next((p for p in players if 'first' in p.get('name', '').lower()), None)
    
    # Find Cdubs21 (might be unnamed or have OCR variations)
    cdubs = next((p for p in players 
                  if 'cdub' in p.get('name', '').lower() 
                  or 'dub' in p.get('name', '').lower()
                  or not p.get('name', '').strip()), None)
    
    # Verify Beachy's data
    assert beachy is not None, "Beachy not found"
    assert beachy['gross_score'] == 43, f"Beachy gross should be 43, got {beachy['gross_score']}"
    assert abs(beachy['handicap'] - 12.4) < 0.1, f"Beachy handicap should be 12.4, got {beachy['handicap']}"
    
    # Verify FirstOrLast's data
    assert firstorlast is not None, "FirstOrLast not found"
    assert firstorlast['gross_score'] == 40, f"FirstOrLast gross should be 40, got {firstorlast['gross_score']}"
    assert abs(firstorlast['handicap'] - 10.3) < 0.1, f"FirstOrLast handicap should be 10.3, got {firstorlast['handicap']}"
    
    # Verify Cdubs21's data (may be unnamed)
    assert cdubs is not None, "Cdubs21 data not found"
    assert cdubs['gross_score'] == 44, f"Cdubs21 gross should be 44, got {cdubs['gross_score']}"
    assert abs(cdubs['handicap'] - 18.2) < 0.1, f"Cdubs21 handicap should be 18.2, got {cdubs['handicap']}"


def test_1png_net_score_calculation():
    """Test that 1.png net scores are calculated correctly."""
    image_path = Path(__file__).parent.parent / "uploads" / "1.png"
    
    if not image_path.exists():
        pytest.skip("1.png not found in uploads directory")
    
    # Load and process image
    image = Image.open(image_path)
    ocr_text = extract_text(image)
    players = parse_players(ocr_text)
    
    # Calculate net scores (9 holes)
    results = calculate_net_scores(players, num_holes=9)
    
    # Par for this course is 35 (from the scorecard)
    par = 35
    
    # Find each player's result
    beachy_result = next((r for r in results if 'beachy' in r.get('name', '').lower()), None)
    firstorlast_result = next((r for r in results if 'first' in r.get('name', '').lower()), None)
    cdubs_result = next((r for r in results if not r.get('name', '').strip() or 'dub' in r.get('name', '').lower()), None)
    
    # Verify net score calculations (with rounding)
    # Beachy: handicap 12.4 → 12, strokes = 6, net = 43 - 6 = 37, net to par = 37 - 35 = +2
    assert beachy_result is not None
    assert beachy_result['net_score'] == 37
    assert beachy_result['strokes_given'] == 6
    assert (beachy_result['net_score'] - par) == 2
    
    # FirstOrLast: handicap 10.3 → 10, strokes = 5, net = 40 - 5 = 35, net to par = 35 - 35 = 0
    assert firstorlast_result is not None
    assert firstorlast_result['net_score'] == 35
    assert firstorlast_result['strokes_given'] == 5
    assert (firstorlast_result['net_score'] - par) == 0
    
    # Cdubs21: handicap 18.2 → 18, strokes = 9, net = 44 - 9 = 35, net to par = 35 - 35 = 0
    assert cdubs_result is not None
    assert cdubs_result['net_score'] == 35
    assert cdubs_result['strokes_given'] == 9
    assert (cdubs_result['net_score'] - par) == 0
    
    # Net scores relative to par: +2, 0, 0


