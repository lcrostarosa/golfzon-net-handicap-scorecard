"""
Test file for golfzon-ocr parser and calculator.
"""
import pytest
from parser import parse_players
from calculator import calculate_net_scores


def test_parse_players_complete_data():
    """Test parsing with complete player data."""
    ocr_text = """
    G Acorm 38(+2) -2.2
    G Cjdyer 41(+5) +16.1
    G Lcrostarosa 43(+7) +11.4
    """
    players = parse_players(ocr_text)
    assert len(players) == 3
    
    names = [p['name'].lower() for p in players]
    assert 'acorn' in names or 'acorm' in names
    assert 'gjdyer' in names or 'cjdyer' in names
    assert 'lcrostarosa' in names


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
    
    # Verify calculations
    assert acorn['strokes_given'] == -1.1
    assert abs(acorn['net_score'] - 39.1) < 0.01
    
    assert abs(gjdyer['strokes_given'] - 8.05) < 0.01
    assert abs(gjdyer['net_score'] - 32.95) < 0.01
    
    assert lcrostarosa['strokes_given'] == 5.7
    assert abs(lcrostarosa['net_score'] - 37.3) < 0.01
    
    # Verify sorting (lowest net score first)
    assert results[0]['net_score'] <= results[1]['net_score']
    assert results[1]['net_score'] <= results[2]['net_score']
    
    # Gjdyer should be the winner
    assert results[0]['name'] == 'Gjdyer'
    assert abs(results[0]['net_score'] - 32.95) < 0.01


def test_parse_ocr_with_noise():
    """Test parsing with OCR noise and misreads."""
    ocr_text = """
    m | \\lAcorm 513) 4141.4 \\G t 38(+2 Bo >
    2 |(Acidyer alslsilsiG lel sis] > 4I(+5, +16.
    3 |[llcrostarosa] 5) 4 [FN 4 IF ILE 4) 4 |e 43(+7) +iL.4
    """
    players = parse_players(ocr_text)
    
    # Should find at least 2 players (Gjdyer and Lcrostarosa)
    assert len(players) >= 2
    
    names = [p['name'].lower() for p in players]
    assert 'gjdyer' in names or 'cjdyer' in names
    assert 'lcrostarosa' in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

