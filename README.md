# Golfzon Scorecard OCR Application

A Python + Streamlit application that extracts player data from Golfzon-style golf scorecard screenshots using OCR and calculates net scores based on handicaps.

## Features

- 📸 **Image Upload**: Upload screenshots of Golfzon scorecards (JPG, PNG)
- 🔍 **OCR Processing**: Automatic text extraction using pytesseract
- 📊 **Data Parsing**: Extracts player names, gross scores, and handicaps using regex
- 🧮 **Net Score Calculation**: Calculates net scores based on handicap and number of holes
- 🏆 **Winner Display**: Automatically identifies and displays the winner
- 📥 **CSV Export**: Download results as CSV file
- ⚙️ **Configurable**: Toggle between 9-hole and 18-hole rounds

## Installation

### Prerequisites

1. **Python 3.10+** installed on your system
2. **Tesseract OCR** installed:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   Or follow the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

2. Clone or download this repository:
   ```bash
   cd golfzon-ocr
   ```

3. Install Python dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Activate the Poetry virtual environment:
   ```bash
   poetry shell
   ```

5. Verify Tesseract installation:
   ```bash
   tesseract --version
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   poetry run streamlit run app.py
   ```
   Or if you're already in the Poetry shell:
   ```bash
   streamlit run app.py
   ```

2. The application will open in your default web browser (usually at `http://localhost:8501`)

3. Upload a screenshot of your Golfzon scorecard:
   - Click "Choose an image file"
   - Select a JPG or PNG image file
   - The image should clearly show player names, scores, and handicaps

4. Review the results:
   - Raw OCR text (expandable section)
   - Parsed player data table
   - Winner banner
   - Option to download results as CSV

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

### Scoring
- Players are sorted by net score (lowest wins)
- Results are displayed in a table format
- Winner is highlighted with a banner

## Project Structure

```
golfzon-ocr/
├── app.py              # Streamlit main application
├── ocr.py              # OCR text extraction
├── parser.py           # Regex parsing of OCR output
├── calculator.py       # Net score calculation logic
├── pyproject.toml      # Poetry dependencies and project configuration
└── README.md          # This file
```

## Example Output

```
Player      | Gross Score | Handicap (G-HCP) | Strokes Given | Net Score
------------|-------------|------------------|---------------|----------
Acorm       | 38          | -2.2             | -1.1          | 39.1
Cjdyer      | 41          | +16.1            | 8.1           | 32.9
Lcrostarosa | 43          | +11.4            | 5.7           | 37.3

🏆 Winner: Cjdyer (Net Score: 32.9)
```

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

### Import Errors
- Ensure all dependencies are installed: `poetry install`
- Verify Python version is 3.10 or higher: `python --version`
- Make sure you're using the Poetry environment: `poetry shell` or `poetry run streamlit run app.py`

## Dependencies

- **streamlit**: Web UI framework
- **pytesseract**: Python wrapper for Tesseract OCR
- **Pillow**: Image processing
- **opencv-python**: Image preprocessing (optional)
- **pandas**: Data manipulation and display
- **numpy**: Numerical operations

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests for improvements!

