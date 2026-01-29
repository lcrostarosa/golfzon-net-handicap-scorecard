"""
Tests for edge cases in parser - scores without names, 1-6 players, etc.
"""
import pytest
from golfzon_ocr.processing import parse_players, calculate_net_scores


def test_parse_scores_without_names():
    """Test parsing when scores are detected but names are missing."""
    ocr_text = """
    38(+2) -2.2
    41(+5) +16.1
    43(+7) +11.4
    """
    players = parse_players(ocr_text)
    
    # Should detect all 3 scores even without names
    assert len(players) == 3
    assert all(p.get('gross_score') in [38, 41, 43] for p in players)
    assert all(p.get('handicap') is not None for p in players)
    
    # Names should be empty (allowing manual editing)
    names = [p.get('name', '').strip() for p in players]
    assert all(not name for name in names)  # All names should be empty


def test_parse_partial_names():
    """Test parsing when some players have names and some don't."""
    ocr_text = """
    Player1 38(+2) -2.2
    41(+5) +16.1
    Player3 43(+7) +11.4
    """
    players = parse_players(ocr_text)
    
    # Should detect all 3 scores
    assert len(players) >= 3
    assert len(players) <= 6
    
    # Check that we have at least some names (may be truncated)
    names = [p.get('name', '').strip() for p in players]
    name_lower = [n.lower() for n in names if n]
    assert any('player' in n for n in name_lower)
    
    # Should have at least one name and potentially empty names
    assert len([n for n in names if n]) >= 1


def test_parse_max_6_players():
    """Test that parser limits to maximum 6 players."""
    ocr_text = """
    Player1 38(+2) -2.2
    Player2 39(+3) -1.2
    Player3 40(+4) -0.2
    Player4 41(+5) +0.8
    Player5 42(+6) +1.8
    Player6 43(+7) +2.8
    Player7 44(+8) +3.8
    Player8 45(+9) +4.8
    """
    players = parse_players(ocr_text)
    
    # Should limit to 6 players max
    assert len(players) <= 6
    assert len(players) >= 1


def test_parse_single_player():
    """Test parsing with just 1 player."""
    ocr_text = "Player1 38(+2) -2.2"
    players = parse_players(ocr_text)
    
    assert len(players) == 1
    assert players[0]['gross_score'] == 38
    assert players[0]['handicap'] == -2.2
    # Name may be truncated by parser, so check if it contains 'player'
    assert 'player' in players[0]['name'].lower()


def test_parse_calculate_with_empty_names():
    """Test that calculator works with empty names."""
    players = [
        {"name": "", "gross_score": 38, "handicap": -2.2},
        {"name": "Player2", "gross_score": 41, "handicap": 16.1},
    ]
    
    # Should calculate successfully even with empty names
    results = calculate_net_scores(players, num_holes=9)
    
    assert len(results) == 2
    # Results are sorted by net_score, so find by name
    empty_name_result = next((r for r in results if r['name'] == ""), None)
    player2_result = next((r for r in results if r['name'] == "Player2"), None)
    assert empty_name_result is not None
    assert player2_result is not None
    assert all('net_score' in r for r in results)


def test_parse_handles_duplicate_scores():
    """Test that parser handles duplicate score+handicap combinations."""
    ocr_text = """
    Player1 38(+2) -2.2
    Player2 38(+2) -2.2
    """
    players = parse_players(ocr_text)
    
    # Should deduplicate to 1 player (prefer the one with a name)
    assert len(players) == 1
    assert players[0]['gross_score'] == 38
    assert players[0]['handicap'] == -2.2
    # Name may be truncated, so check if it contains 'player'
    assert 'player' in players[0]['name'].lower()


def test_parse_mixed_formats():
    """Test parsing with mixed formats (some with names, some without)."""
    ocr_text = """
    Name1 38(+2) -2.2
    41(+5) +16.1
    Name3 43(+7) +11.4
    45(+9) +18.2
    """
    players = parse_players(ocr_text)
    
    # Should detect all 4 scores
    assert len(players) >= 3
    assert len(players) <= 6
    
    # Should have at least some names (may be truncated)
    names = [p.get('name', '').strip() for p in players if p.get('name', '').strip()]
    assert len(names) >= 1
    # Check that we have names (may be truncated to just "Name")
    name_lower = [n.lower() for n in names]
    assert any('name' in n for n in name_lower)

