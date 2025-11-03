"""
Tests for CSV export functions.
"""
import csv
import io

from golfzon_ocr.export import export_full_league_data, export_weekly_summary, export_team_roster


def test_export_full_league_data(db_session, sample_league, sample_teams, sample_players, sample_scores):
    """Test exporting full league data."""
    csv_data = export_full_league_data(db_session, sample_league.id)
    
    assert csv_data is not None
    assert len(csv_data) > 0
    
    # Verify it's valid CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    assert len(rows) > 0
    assert "League" in rows[0][0]


def test_export_weekly_summary(db_session, sample_league, sample_scores):
    """Test exporting weekly summary."""
    csv_data = export_weekly_summary(db_session, sample_league.id, 1)
    
    assert csv_data is not None
    assert len(csv_data) > 0
    
    # Verify it's valid CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    assert len(rows) > 0


def test_export_team_roster(db_session, sample_league, sample_teams, sample_players):
    """Test exporting team rosters."""
    csv_data = export_team_roster(db_session, sample_league.id)
    
    assert csv_data is not None
    assert len(csv_data) > 0
    
    # Verify it's valid CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    assert len(rows) > 0

