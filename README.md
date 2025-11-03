# Golfzon League Manager

A Python + Streamlit application that extracts player data from Golfzon-style golf scorecard screenshots using OCR, calculates net scores based on handicaps, and manages multi-league team competitions with weekly scoring and leaderboards.

## Features

### Core OCR Functionality
- 📸 **Image Upload**: Upload screenshots of Golfzon scorecards (JPG, PNG)
- 🔍 **OCR Processing**: Automatic text extraction using pytesseract
- 📊 **Data Parsing**: Extracts player names, gross scores, and handicaps using regex
- 🧮 **Net Score Calculation**: Calculates net scores based on handicap and number of holes
- 🏆 **Winner Display**: Automatically identifies and displays the winner
- ⚙️ **Configurable**: Toggle between 9-hole and 18-hole rounds

### Multi-League Management
- 🏆 **Multiple Leagues**: Create and manage multiple golf leagues
- 👥 **Team Management**: Create teams and assign players within each league
- 📅 **Weekly Scoring**: Track scores by week number for mid-season entry
- 📊 **Leaderboards**: View weekly and cumulative standings based on top 2 net scores per team
- 📥 **CSV Export**: Export league data, weekly summaries, and team rosters

### Database & Persistence
- 💾 **SQLite Database**: Persistent storage for all league data
- 🔄 **Alembic Migrations**: Version-controlled database schema migrations
- 📈 **Historical Data**: Track all weekly scores and calculate cumulative standings

### Scoring System
- **Team Scoring**: Each team's score is the sum of the top 2 net scores from team members
- **Weekly Standings**: See which team won each week
- **Cumulative Standings**: Track overall league performance across all weeks
- **Mid-Season Entry**: Add scores for any week number, perfect for joining leagues mid-season

## Installation

### Prerequisites

1. **Python 3.10+** installed on your system
2. **Tesseract OCR** installed:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
3. **Poetry** for dependency management:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

### Setup

1. Clone or download this repository:
   ```bash
   cd golfzon-ocr
   ```

2. Install Python dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Initialize the database:
   ```bash
   poetry run python bootstrap_db.py
   ```

4. Activate the Poetry virtual environment (optional):
   ```bash
   poetry shell
   ```

5. Verify Tesseract installation:
   ```bash
   tesseract --version
   ```

## Usage

### Starting the Application

1. Start the Streamlit application:
   ```bash
   poetry run streamlit run app.py
   ```
   Or if you're already in the Poetry shell:
   ```bash
   streamlit run app.py
   ```

2. The application will open in your default web browser (usually at `http://localhost:8501`)

### Using the Application

#### 1. Create or Select a League
- Use the sidebar to select an existing league or create a new one
- All operations are scoped to the selected league

#### 2. Team Management
- Navigate to the "Team Management" tab
- Create teams within your league
- Add players to teams
- View team rosters

#### 3. Submit Scores
- Navigate to the "Submit Scores" tab
- Select the week number (for mid-season entry, use the appropriate week)
- Upload a screenshot of your Golfzon scorecard
- The OCR will extract player data automatically
- Review and edit scores if needed
- Match players to existing players in the database
- Save scores to the database

#### 4. View Leaderboards
- Navigate to the "Leaderboard" tab
- View weekly standings for any week
- View cumulative standings across all weeks
- Standings are calculated using the top 2 net scores per team

#### 5. Export Data
- Navigate to the "Export" tab
- Choose export type:
  - **Full League Data**: Complete league export with all teams, players, scores, and standings
  - **Weekly Summary**: Export standings and scores for a specific week
  - **Team Rosters**: Export all teams and their players
- Download CSV files for offline analysis

## How It Works

### OCR Extraction
The application uses pytesseract to extract text from the uploaded image. The image is preprocessed with:
- Grayscale conversion
- Contrast enhancement (CLAHE)

### Data Parsing
Player data is extracted using regex pattern matching:
- **Pattern**: `PlayerName GrossScore(+/-X) Handicap`
- **Example**: `Acorm 38(+2) -2.2`

The parser:
- Removes "G" prefix from player names (common in Golfzon scorecards)
- Validates score ranges
- Handles duplicate players
- Handles OCR errors and misreads

### Net Score Calculation

For **9-hole rounds**:
```
strokes_given = handicap / 2
net_score = gross_score - strokes_given
```

For **18-hole rounds**:
```
strokes_given = handicap
net_score = gross_score - strokes_given
```

### Team Scoring

Each team's weekly score is calculated as:
1. Get all player scores for the team in that week
2. Sort by net score (lowest first)
3. Take the top 2 net scores
4. Sum those two scores = team score for the week

The team with the **lowest** total score wins the week.

### Cumulative Standings

Cumulative standings are calculated by:
1. Summing each team's weekly scores across all weeks
2. Teams are ranked by total score (lowest wins)
3. Shows average score per week and total weeks played

## Database Schema

The application uses SQLite with the following tables:

- **leagues**: League information (id, name, created_at)
- **teams**: Team information (id, league_id, name, created_at)
- **players**: Player information (id, team_id, name, created_at)
- **weekly_scores**: Score records (id, player_id, league_id, week_number, date, gross_score, handicap, strokes_given, net_score, num_holes, created_at)

## Project Structure

```
golfzon-ocr/
├── app.py              # Main Streamlit application
├── database.py         # Database connection and CRUD operations
├── models.py           # SQLAlchemy models
├── teams.py            # Team management functions
├── leaderboard.py      # Leaderboard calculation and display
├── export.py           # CSV export functions
├── ocr.py              # OCR text extraction
├── parser.py           # Regex parsing of OCR output
├── calculator.py       # Net score calculation logic
├── bootstrap_db.py     # Database initialization script
├── alembic/            # Alembic migration directory
│   ├── versions/       # Migration files
│   └── env.py          # Alembic environment config
├── alembic.ini         # Alembic configuration
├── tests/              # Test suite
│   ├── conftest.py     # pytest fixtures
│   ├── test_database.py
│   ├── test_teams.py
│   ├── test_leaderboard.py
│   ├── test_export.py
│   └── test_integration.py
├── pyproject.toml      # Poetry dependencies and project configuration
└── README.md          # This file
```

## Testing

Run the test suite:
```bash
poetry run pytest tests/ -v
```

The test suite includes:
- Database CRUD operations
- Team management functions
- Leaderboard calculations
- CSV export functionality
- Integration tests for full workflows

## Example Workflow

1. **Create a League**: "Summer 2024 League"
2. **Create Teams**: "Team A", "Team B", "Team C"
3. **Add Players**: Assign players to teams (e.g., "John Doe" → Team A)
4. **Submit Week 1 Scores**: Upload scorecard image, OCR extracts players, save scores
5. **View Week 1 Leaderboard**: See which team won based on top 2 net scores
6. **Submit Week 2 Scores**: Repeat for subsequent weeks
7. **View Cumulative Standings**: See overall league standings across all weeks
8. **Export Data**: Download CSV for record keeping

## Troubleshooting

### OCR Returns Empty Text
- Ensure the image is clear and readable
- Check that text is not obscured by glare or reflections
- Verify the image format is supported (JPG, PNG)

### No Player Data Found
- Verify the scorecard format matches Golfzon style
- Check that player names, scores, and handicaps are visible
- Review the raw OCR text output to see what was extracted

### Tesseract Not Found
- Ensure Tesseract is installed and in your system PATH
- On macOS/Linux, verify with: `which tesseract`
- On Windows, add Tesseract installation directory to PATH

### Database Errors
- Run `poetry run python bootstrap_db.py` to initialize/reset the database
- Check that `golfzon_league.db` file exists and is writable
- Verify Alembic migrations are up to date: `poetry run alembic upgrade head`

### Import Errors
- Ensure all dependencies are installed: `poetry install`
- Verify Python version is 3.10 or higher: `python --version`
- Make sure you're using the Poetry environment: `poetry shell` or `poetry run streamlit run app.py`

## Dependencies

### Core Dependencies
- **streamlit**: Web UI framework
- **pytesseract**: Python wrapper for Tesseract OCR
- **Pillow**: Image processing
- **opencv-python**: Image preprocessing
- **pandas**: Data manipulation and display
- **numpy**: Numerical operations
- **sqlalchemy**: ORM for database operations
- **alembic**: Database migration tool

### Development Dependencies
- **pytest**: Testing framework

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests for improvements!
