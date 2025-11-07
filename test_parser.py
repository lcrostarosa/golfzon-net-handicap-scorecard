"""
Test file for golfzon-ocr parser and calculator.
"""
import pytest
from golfzon_ocr.processing import parse_players, calculate_net_scores, recalculate_net_scores


def test_parse_players_complete_data():
    """Test parsing with complete player data."""
    ocr_text = """
    G Acorm 38(+2) -2.2
    G Cjdyer 41(+5) +16.1
    G Lcrostarosa 43(+7) +11.4
    """
    players = parse_players(ocr_text)
    # Should find at least 3 players (may have duplicates or unmatched scores)
    assert len(players) >= 3
    assert len(players) <= 6  # Max 6 players
    
    # Check that we have the expected scores
    scores = {p['gross_score'] for p in players}
    assert 38 in scores
    assert 41 in scores
    assert 43 in scores
    
    # Check that we have at least some names (may have empty names for unmatched scores)
    names = [p['name'].lower() for p in players if p.get('name', '').strip()]
    assert len(names) >= 2  # At least 2 should have names


def test_calculate_net_scores_9_holes():
    """Test net score calculation for 9-hole round."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2},
        {"name": "Gjdyer", "gross_score": 41, "handicap": 16.1},
        {"name": "Lcrostarosa", "gross_score": 43, "handicap": 11.4},
    ]
    
    results = calculate_net_scores(players, num_holes=9)
    
    assert len(results) == 3
    
    # Find each player in results
    acorn = next((r for r in results if r['name'] == 'Acorn'), None)
    gjdyer = next((r for r in results if r['name'] == 'Gjdyer'), None)
    lcrostarosa = next((r for r in results if r['name'] == 'Lcrostarosa'), None)
    
    assert acorn is not None
    assert gjdyer is not None
    assert lcrostarosa is not None
    
    # Verify calculations (with rounding)
    # Acorn: -2.2 → -2, strokes = -1, net = 38 - (-1) = 39
    assert acorn['strokes_given'] == -1
    assert acorn['net_score'] == 39
    
    # Gjdyer: 16.1 → 16, strokes = 8, net = 41 - 8 = 33
    assert gjdyer['strokes_given'] == 8
    assert gjdyer['net_score'] == 33
    
    # Lcrostarosa: 11.4 → 11, strokes = 6, net = 43 - 6 = 37
    assert lcrostarosa['strokes_given'] == 6
    assert lcrostarosa['net_score'] == 37
    
    # Verify sorting (lowest net score first)
    assert results[0]['net_score'] <= results[1]['net_score']
    assert results[1]['net_score'] <= results[2]['net_score']
    
    # Gjdyer should be the winner
    assert results[0]['name'] == 'Gjdyer'
    assert results[0]['net_score'] == 33


def test_parse_ocr_with_noise():
    """Test parsing with OCR noise and misreads."""
    ocr_text = """
    m | \\lAcorm 513) 4141.4 \\G t 38(+2 Bo >
    2 |(Acidyer alslsilsiG lel sis] > 4I(+5, +16.
    3 |[llcrostarosa] 5) 4 [FN 4 IF ILE 4) 4 |e 43(+7) +iL.4
    """
    players = parse_players(ocr_text)
    
    # Should find at least 2 players despite OCR noise
    assert len(players) >= 2
    
    # Parser should extract names from noisy text (no longer applies player-specific corrections)
    names = [p['name'].lower() for p in players]
    # Check that we extracted names (even if OCR misread them)
    assert any('acorm' in n or 'acorn' in n for n in names), f"Expected Acorm/Acorn in {names}"
    assert any('acidyer' in n or 'dyer' in n for n in names), f"Expected Acidyer/dyer in {names}"


def test_recalculate_net_scores_auto_calculate_9_holes():
    """Test recalculation with auto_calculate_strokes=True for 9-hole round."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2},
        {"name": "Gjdyer", "gross_score": 41, "handicap": 16.1},
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=True)
    
    assert len(results) == 2
    
    acorn = next((r for r in results if r['name'] == 'Acorn'), None)
    gjdyer = next((r for r in results if r['name'] == 'Gjdyer'), None)
    
    assert acorn is not None
    assert gjdyer is not None
    
    # With auto_calculate, strokes should be calculated from handicap (with rounding)
    # Acorn: -2.2 → -2, strokes = -1, net = 38 - (-1) = 39
    assert acorn['strokes_given'] == -1
    assert acorn['net_score'] == 39
    
    # Gjdyer: 16.1 → 16, strokes = 8, net = 41 - 8 = 33
    assert gjdyer['strokes_given'] == 8
    assert gjdyer['net_score'] == 33


def test_recalculate_net_scores_auto_calculate_18_holes():
    """Test recalculation with auto_calculate_strokes=True for 18-hole round."""
    players = [
        {"name": "Acorn", "gross_score": 76, "handicap": -2.2},
        {"name": "Gjdyer", "gross_score": 82, "handicap": 16.1},
    ]
    
    results = recalculate_net_scores(players, num_holes=18, auto_calculate_strokes=True)
    
    assert len(results) == 2
    
    acorn = next((r for r in results if r['name'] == 'Acorn'), None)
    gjdyer = next((r for r in results if r['name'] == 'Gjdyer'), None)
    
    assert acorn is not None
    assert gjdyer is not None
    
    # With auto_calculate for 18 holes, strokes = rounded handicap
    # Acorn: -2.2 → -2, strokes = -2, net = 76 - (-2) = 78
    assert acorn['strokes_given'] == -2
    assert acorn['net_score'] == 78
    
    # Gjdyer: 16.1 → 16, strokes = 16, net = 82 - 16 = 66
    assert gjdyer['strokes_given'] == 16
    assert gjdyer['net_score'] == 66


def test_recalculate_net_scores_manual_strokes():
    """Test recalculation with auto_calculate_strokes=False (manual strokes)."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2, "strokes_given": -2.0},
        {"name": "Gjdyer", "gross_score": 41, "handicap": 16.1, "strokes_given": 7.5},
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=False)
    
    assert len(results) == 2
    
    acorn = next((r for r in results if r['name'] == 'Acorn'), None)
    gjdyer = next((r for r in results if r['name'] == 'Gjdyer'), None)
    
    assert acorn is not None
    assert gjdyer is not None
    
    # With manual strokes, should use the provided strokes_given (rounded)
    assert acorn['strokes_given'] == -2
    assert acorn['net_score'] == 40  # 38 - (-2)
    
    assert gjdyer['strokes_given'] == 8  # 7.5 rounded to 8
    assert gjdyer['net_score'] == 33  # 41 - 8


def test_recalculate_net_scores_edited_values():
    """Test recalculation after editing handicap and gross_score."""
    # Initial players
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2, "strokes_given": -1.1},
        {"name": "Gjdyer", "gross_score": 41, "handicap": 16.1, "strokes_given": 8.05},
    ]
    
    # Edit Acorn's handicap and Gjdyer's gross_score
    edited_players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -3.0, "strokes_given": -1.1},
        {"name": "Gjdyer", "gross_score": 40, "handicap": 16.1, "strokes_given": 8.05},
    ]
    
    results = recalculate_net_scores(edited_players, num_holes=9, auto_calculate_strokes=True)
    
    assert len(results) == 2
    
    acorn = next((r for r in results if r['name'] == 'Acorn'), None)
    gjdyer = next((r for r in results if r['name'] == 'Gjdyer'), None)
    
    assert acorn is not None
    assert gjdyer is not None
    
    # Acorn's strokes should be recalculated from new handicap (with rounding)
    # -3.0 → -3, strokes = -2, net = 38 - (-2) = 40
    assert acorn['strokes_given'] == -2
    assert acorn['net_score'] == 40
    
    # Gjdyer's net score should reflect new gross_score
    # 16.1 → 16, strokes = 8, net = 40 - 8 = 32
    assert gjdyer['strokes_given'] == 8
    assert gjdyer['net_score'] == 32


def test_recalculate_net_scores_sorting():
    """Test that recalculation properly sorts results by net score."""
    players = [
        {"name": "Player1", "gross_score": 45, "handicap": 10.0},
        {"name": "Player2", "gross_score": 40, "handicap": 5.0},
        {"name": "Player3", "gross_score": 43, "handicap": 8.0},
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=True)
    
    assert len(results) == 3
    
    # Verify sorting (lowest net score first)
    assert results[0]['net_score'] <= results[1]['net_score']
    assert results[1]['net_score'] <= results[2]['net_score']
    
    # Player2 should win (5.0 → 5, strokes = 2, 40 - 2 = 38)
    assert results[0]['name'] == 'Player2'
    assert results[0]['net_score'] == 38


def test_recalculate_net_scores_auto_calculate_overrides_manual():
    """Test that auto_calculate=True ignores manual strokes_given."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2, "strokes_given": 999.0},
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=True)
    
    assert len(results) == 1
    acorn = results[0]
    
    # Should ignore manual strokes_given (999.0) and calculate from handicap (with rounding)
    # -2.2 → -2, strokes = -1, net = 38 - (-1) = 39
    assert acorn['strokes_given'] == -1
    assert acorn['net_score'] == 39


def test_recalculate_net_scores_no_strokes_given():
    """Test recalculation when strokes_given is missing (should calculate)."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2},
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=False)
    
    assert len(results) == 1
    acorn = results[0]
    
    # Should calculate strokes_given even when auto_calculate=False if missing (with rounding)
    # -2.2 → -2, strokes = -1
    assert acorn['strokes_given'] == -1


def test_recalculate_net_scores_invalid_data():
    """Test that recalculation skips invalid player data."""
    players = [
        {"name": "Valid", "gross_score": 38, "handicap": -2.2},
        {"name": "InvalidScore", "gross_score": 250, "handicap": 10.0},  # Invalid score > 200
        {"name": "MissingScore", "handicap": 10.0},  # Missing gross_score
        {"name": "MissingHandicap", "gross_score": 40},  # Missing handicap
    ]
    
    results = recalculate_net_scores(players, num_holes=9, auto_calculate_strokes=True)
    
    # Should only include valid player (handicap validation not implemented in recalculate)
    assert len(results) == 1
    assert results[0]['name'] == 'Valid'


def test_recalculate_net_scores_empty_list():
    """Test that recalculation raises ValueError for empty list."""
    with pytest.raises(ValueError, match="Players list is empty"):
        recalculate_net_scores([], num_holes=9, auto_calculate_strokes=True)


def test_recalculate_net_scores_invalid_holes():
    """Test that recalculation raises ValueError for invalid num_holes."""
    players = [
        {"name": "Acorn", "gross_score": 38, "handicap": -2.2},
    ]
    
    with pytest.raises(ValueError, match="Invalid number of holes"):
        recalculate_net_scores(players, num_holes=27, auto_calculate_strokes=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

