"""
Test OCR processing on actual image files.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image
from src.golfzon_ocr.processing import extract_text, parse_players, calculate_net_scores


def test_image(image_path):
    """Test OCR on a single image file."""
    print(f"\n{'='*80}")
    print(f"Testing: {image_path}")
    print(f"{'='*80}")
    
    try:
        # Load image
        image = Image.open(image_path)
        print(f"Image size: {image.size}, Mode: {image.mode}")
        
        # Extract text using OCR
        print("\n--- Extracting text with OCR...")
        ocr_text = extract_text(image)
        
        # Show raw OCR text (truncated if too long)
        print(f"\n--- Raw OCR Text (first 500 chars):")
        print(ocr_text[:500])
        if len(ocr_text) > 500:
            print(f"... (truncated, total length: {len(ocr_text)} chars)")
        
        # Parse players
        print(f"\n--- Parsing players...")
        players = parse_players(ocr_text)
        
        if players:
            print(f"✅ Found {len(players)} players:")
            for i, player in enumerate(players, 1):
                print(f"  {i}. {player['name']} - Score: {player['gross_score']}, Handicap: {player['handicap']}")
            
            # Calculate net scores
            print(f"\n--- Calculating net scores (9 holes)...")
            results = calculate_net_scores(players, num_holes=9)
            
            print(f"\n--- Results (sorted by net score):")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['name']}: Gross={result['gross_score']}, "
                      f"Handicap={result['handicap']:.1f}, "
                      f"Strokes={result['strokes_given']:.2f}, "
                      f"Net={result['net_score']:.2f}")
            
            if results:
                print(f"\n🏆 Winner: {results[0]['name']} (Net Score: {results[0]['net_score']:.2f})")
        else:
            print("❌ No players found in OCR text")
            print("\n--- Full OCR text for debugging:")
            print(ocr_text)
        
        return {
            'success': True,
            'players_found': len(players) if players else 0,
            'ocr_length': len(ocr_text),
            'players': players
        }
        
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'players_found': 0
        }


def main():
    """Run tests on all images."""
    print("="*80)
    print("OCR Image Testing")
    print("="*80)
    
    results = []
    
    # Test test.jpeg
    test_jpeg = "test.jpeg"
    if os.path.exists(test_jpeg):
        result = test_image(test_jpeg)
        result['file'] = test_jpeg
        results.append(result)
    else:
        print(f"\n⚠️  {test_jpeg} not found, skipping...")
    
    # Test all PNGs in uploads folder
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        png_files = sorted([f for f in os.listdir(uploads_dir) if f.lower().endswith('.png')])
        
        if png_files:
            print(f"\n{'='*80}")
            print(f"Found {len(png_files)} PNG files in uploads/")
            print(f"{'='*80}")
            
            for png_file in png_files:
                image_path = os.path.join(uploads_dir, png_file)
                result = test_image(image_path)
                result['file'] = png_file
                results.append(result)
        else:
            print(f"\n⚠️  No PNG files found in {uploads_dir}/")
    else:
        print(f"\n⚠️  {uploads_dir} directory not found")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total_files = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    total_players = sum(r.get('players_found', 0) for r in results)
    
    print(f"Total files tested: {total_files}")
    print(f"Successfully processed: {successful}")
    print(f"Total players found: {total_players}")
    
    if results:
        print(f"\n--- Results by file:")
        for result in results:
            status = "✅" if result.get('success') else "❌"
            players = result.get('players_found', 0)
            file_name = result.get('file', 'unknown')
            print(f"  {status} {file_name}: {players} players found")


if __name__ == "__main__":
    main()

