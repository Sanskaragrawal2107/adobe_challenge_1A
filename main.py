import fitz  # PyMuPDF
import json
import os
import sys
import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import statistics
from collections import Counter, defaultdict
import argparse
import math

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPDFExtractor:
    def __init__(self, input_dir: str = "input", output_dir: str = "output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_text_with_metadata(self, pdf_path: str) -> List[Dict]:
        """Extract text with comprehensive metadata."""
        try:
            doc = fitz.open(pdf_path)
            text_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")
                page_height = page.rect.height
                page_width = page.rect.width
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 0:
                                    bbox = span["bbox"]
                                    text_data.append({
                                        "text": text,
                                        "font_size": span["size"],
                                        "font": span["font"],
                                        "flags": span["flags"],
                                        "page": page_num,  # 0-based indexing as required
                                        "bbox": bbox,
                                        "x_position": bbox[0],
                                        "y_position": bbox[1],
                                        "width": bbox[2] - bbox[0],
                                        "height": bbox[3] - bbox[1],
                                        "page_width": page_width,
                                        "page_height": page_height,
                                        "relative_x": bbox[0] / page_width,
                                        "relative_y": bbox[1] / page_height
                                    })
            
            doc.close()
            return text_data
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []

    def calculate_enhanced_font_statistics(self, text_data: List[Dict]) -> Dict:
        """Calculate comprehensive font statistics for better analysis."""
        if not text_data:
            return {"avg_size": 12, "median_size": 12, "max_size": 12, "mode_size": 12, "min_size": 12, "std_dev": 0, "font_families": {}, "size_distribution": Counter()}
        
        # Separate by content type for better analysis
        body_text_sizes = []
        all_sizes = []
        font_families = defaultdict(list)
        
        for item in text_data:
            size = item["font_size"]
            font = item["font"]
            text = item["text"]
            
            all_sizes.append(size)
            font_families[font].append(size)
            
            # Heuristic for body text (longer text, common sizes)
            if len(text) > 20 and not self.is_bold(item["flags"]):
                body_text_sizes.append(size)
        
        # Use body text for baseline if available, otherwise all text
        baseline_sizes = body_text_sizes if body_text_sizes else all_sizes
        
        # Find the most common font size (likely body text)
        size_counter = Counter(round(size, 1) for size in baseline_sizes)
        most_common_size = size_counter.most_common(1)[0][0] if size_counter else 12
        
        return {
            "avg_size": statistics.mean(baseline_sizes),
            "median_size": statistics.median(baseline_sizes),
            "mode_size": most_common_size,
            "max_size": max(all_sizes),
            "min_size": min(all_sizes),
            "std_dev": statistics.stdev(baseline_sizes) if len(baseline_sizes) > 1 else 0,
            "font_families": dict(font_families),
            "size_distribution": size_counter
        }

    def is_bold(self, flags: int) -> bool:
        """Check if text is bold based on flags."""
        return bool(flags & 2**4)

    def is_italic(self, flags: int) -> bool:
        """Check if text is italic based on flags."""
        return bool(flags & 2**1)

    def enhanced_heading_patterns(self, text: str) -> Tuple[bool, str]:
        """Enhanced pattern matching with pattern type identification."""
        text = text.strip()
        
        patterns = [
            # Chapter patterns
            (r'^(CHAPTER|Chapter|chapter)\s+(\d+|[IVXLCDMivxlcdm]+)', 'chapter'),
            (r'^(PART|Part|part)\s+(\d+|[IVXLCDMivxlcdm]+)', 'part'),
            (r'^(SECTION|Section|section)\s+(\d+|[IVXLCDMivxlcdm]+)', 'section'),
            
            # Numbered patterns
            (r'^\d+\.\s+[A-Z]', 'numbered'),
            (r'^\d+\.\d+\s+[A-Z]', 'numbered_sub'),
            (r'^\d+\.\d+\.\d+\s+[A-Z]', 'numbered_subsub'),
            (r'^\d+\s+[A-Z][a-z]', 'numbered_simple'),
            
            # All caps (but not too long)
            (r'^[A-Z][A-Z\s]{2,30}$', 'all_caps'),
            
            # Title case patterns
            (r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*$', 'title_case'),
            
            # Introduction, conclusion, etc.
            (r'^(INTRODUCTION|Introduction|CONCLUSION|Conclusion|ABSTRACT|Abstract|SUMMARY|Summary|OVERVIEW|Overview|BACKGROUND|Background|METHODOLOGY|Methodology|RESULTS|Results|DISCUSSION|Discussion|REFERENCES|References|APPENDIX|Appendix)', 'standard_heading'),
            
            # Table/Figure captions
            (r'^(Table|Figure|Chart|Diagram)\s+\d+', 'caption'),
            
            # Bullet/dash patterns
            (r'^[-•▪▫]\s+[A-Z]', 'bullet'),
        ]
        
        for pattern, pattern_type in patterns:
            if re.match(pattern, text):
                return True, pattern_type
        
        return False, 'none'

    def analyze_position_context(self, item: Dict, text_data: List[Dict], index: int) -> Dict:
        """Analyze positional context for better heading detection."""
        context = {
            'is_left_aligned': item['relative_x'] < 0.1,
            'is_centered': 0.3 < item['relative_x'] < 0.7,
            'is_top_of_page': item['relative_y'] < 0.2,
            'is_isolated': False,
            'has_space_before': False,
            'has_space_after': False,
            'line_count_in_paragraph': 1
        }
        
        # Check spacing before and after
        same_page_items = [t for t in text_data if t['page'] == item['page']]
        current_y = item['y_position']
        
        # Find items close in Y position (same paragraph)
        close_items = [t for t in same_page_items 
                      if abs(t['y_position'] - current_y) < item['height'] * 1.5]
        
        context['line_count_in_paragraph'] = len(close_items)
        context['is_isolated'] = len(close_items) == 1
        
        # Check for spacing
        items_before = [t for t in same_page_items if t['y_position'] < current_y]
        items_after = [t for t in same_page_items if t['y_position'] > current_y]
        
        if items_before:
            closest_before = max(items_before, key=lambda x: x['y_position'])
            context['has_space_before'] = (current_y - closest_before['y_position']) > item['height'] * 2
        
        if items_after:
            closest_after = min(items_after, key=lambda x: x['y_position'])
            context['has_space_after'] = (closest_after['y_position'] - current_y) > item['height'] * 2
        
        return context

    def is_likely_heading_enhanced(self, item: Dict, font_stats: Dict, context: Dict, pattern_info: Tuple[bool, str]) -> Tuple[bool, float]:
        """Enhanced heading detection with confidence scoring."""
        text = item["text"].strip()
        font_size = item["font_size"]
        
        # Basic filters
        if len(text) < 2 or len(text) > 200:
            return False, 0.0
        
        # Skip obvious non-headings
        if re.match(r'^\d+$', text) or re.match(r'^Page \d+', text, re.IGNORECASE):
            return False, 0.0
        
        # Skip if too many words (likely paragraph text)
        if len(text.split()) > 20:
            return False, 0.0
        
        confidence = 0.0
        
        # Font size analysis (more sophisticated)
        mode_size = font_stats["mode_size"]
        size_diff = font_size - mode_size
        std_dev = font_stats["std_dev"]
        
        if size_diff > 2 * std_dev:
            confidence += 0.4
        elif size_diff > std_dev:
            confidence += 0.2
        elif size_diff > 1:
            confidence += 0.1
        
        # Bold text
        if self.is_bold(item["flags"]):
            confidence += 0.3
        
        # Pattern matching
        matches_pattern, pattern_type = pattern_info
        if matches_pattern:
            pattern_weights = {
                'chapter': 0.5,
                'part': 0.5,
                'section': 0.4,
                'numbered': 0.4,
                'numbered_sub': 0.3,
                'all_caps': 0.2,
                'standard_heading': 0.4,
                'title_case': 0.1
            }
            confidence += pattern_weights.get(pattern_type, 0.1)
        
        # Position context
        if context['is_left_aligned'] or context['is_centered']:
            confidence += 0.1
        
        if context['is_isolated']:
            confidence += 0.2
        
        if context['has_space_before'] or context['has_space_after']:
            confidence += 0.1
        
        # Font family analysis
        common_fonts = Counter()
        for font_family, sizes in font_stats["font_families"].items():
            common_fonts[font_family] = len(sizes)
        
        if common_fonts and item["font"] != common_fonts.most_common(1)[0][0]:
            confidence += 0.1  # Different font family
        
        # Text characteristics
        if text.isupper() and 3 <= len(text) <= 50:
            confidence += 0.1
        
        if re.match(r'^[A-Z]', text) and not re.match(r'^[A-Z][a-z]', text):
            confidence += 0.05  # Starts with capital
        
        return confidence >= 0.3, confidence

    def determine_heading_level_enhanced(self, item: Dict, font_stats: Dict, pattern_info: Tuple[bool, str], confidence: float) -> str:
        """Enhanced heading level determination."""
        font_size = item["font_size"]
        mode_size = font_stats["mode_size"]
        size_diff = font_size - mode_size
        matches_pattern, pattern_type = pattern_info
        
        # Pattern-based level assignment
        if pattern_type in ['chapter', 'part']:
            return "H1"
        elif pattern_type == 'section':
            return "H2"
        elif pattern_type == 'numbered':
            return "H2"
        elif pattern_type in ['numbered_sub', 'numbered_subsub']:
            return "H3"
        
        # Size-based assignment (more nuanced)
        std_dev = font_stats["std_dev"]
        
        if size_diff > 3 * std_dev:
            return "H1"
        elif size_diff > 2 * std_dev:
            return "H2"
        elif size_diff > std_dev or self.is_bold(item["flags"]):
            return "H3"
        else:
            return "H3"  # Changed from H4 to H3 since we only go up to H3

    def clean_heading_text_enhanced(self, text: str) -> str:
        """Enhanced text cleaning with better artifact removal."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common PDF artifacts
        text = text.replace('\x00', '')  # Null characters
        text = text.replace('\ufeff', '')  # BOM
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # Control characters
        
        # Fix common OCR errors
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        
        # Remove trailing punctuation that's likely artifacts
        text = re.sub(r'[\.]{2,}$', '', text)
        
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])\s+', r'\1 ', text)
        
        return text.strip()

    def group_multiline_headings(self, text_data: List[Dict], headings: List[Dict]) -> List[Dict]:
        """Group headings that are split across multiple lines."""
        grouped_headings = []
        processed = set()
        
        for i, heading in enumerate(headings):
            if i in processed:
                continue
            
            combined_text = heading["text"]
            combined_level = heading["level"]
            page = heading["page"]
            
            # Look for continuation on next lines
            j = i + 1
            while j < len(headings):
                next_heading = headings[j]
                
                # If next heading is on same page and similar formatting
                if (next_heading["page"] == page and 
                    next_heading["level"] == combined_level and
                    len(next_heading["text"]) < 100 and  # Not too long
                    not re.match(r'^\d+\.', next_heading["text"])):  # Not numbered separately
                    
                    combined_text += " " + next_heading["text"]
                    processed.add(j)
                    j += 1
                else:
                    break
            
            grouped_headings.append({
                "level": combined_level,
                "text": self.clean_heading_text_enhanced(combined_text),
                "page": page
            })
            processed.add(i)
        
        return grouped_headings

    def extract_headings_enhanced(self, text_data: List[Dict]) -> List[Dict]:
        """Enhanced heading extraction with multi-criteria analysis."""
        if not text_data:
            return []
        
        font_stats = self.calculate_enhanced_font_statistics(text_data)
        potential_headings = []
        
        for i, item in enumerate(text_data):
            # Get pattern information
            pattern_info = self.enhanced_heading_patterns(item["text"])
            
            # Get position context
            context = self.analyze_position_context(item, text_data, i)
            
            # Determine if it's a heading
            is_heading, confidence = self.is_likely_heading_enhanced(
                item, font_stats, context, pattern_info
            )
            
            if is_heading:
                level = self.determine_heading_level_enhanced(
                    item, font_stats, pattern_info, confidence
                )
                
                potential_headings.append({
                    "level": level,
                    "text": item["text"],
                    "page": item["page"],
                    "confidence": confidence,
                    "font_size": item["font_size"],
                    "bbox": item["bbox"]
                })
        
        # Group multi-line headings
        grouped_headings = self.group_multiline_headings(text_data, potential_headings)
        
        # Remove duplicates and filter by confidence
        final_headings = self.remove_duplicates_enhanced(grouped_headings)
        
        return final_headings

    def remove_duplicates_enhanced(self, headings: List[Dict]) -> List[Dict]:
        """Enhanced duplicate removal with better similarity detection."""
        if not headings:
            return []
        
        unique_headings = []
        
        for heading in headings:
            is_duplicate = False
            clean_text = self.clean_heading_text_enhanced(heading["text"]).lower()
            
            for existing in unique_headings:
                existing_clean = self.clean_heading_text_enhanced(existing["text"]).lower()
                
                # Check for exact matches or very similar text
                if (clean_text == existing_clean or 
                    (len(clean_text) > 10 and clean_text in existing_clean) or
                    (len(existing_clean) > 10 and existing_clean in clean_text)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # Clean the text before adding
                heading["text"] = self.clean_heading_text_enhanced(heading["text"])
                unique_headings.append(heading)
        
        return unique_headings

    def find_document_title_enhanced(self, text_data: List[Dict], font_stats: Dict) -> str:
        """Enhanced document title detection."""
        if not text_data:
            return "Untitled Document"
        
        # Look at first few pages for title
        first_pages = [item for item in text_data if item["page"] <= 1]  # 0 and 1 (first two pages)
        
        if not first_pages:
            return "Untitled Document"
        
        candidates = []
        
        # Find large, prominent text on first pages
        for item in first_pages:
            text = item["text"].strip()
            
            # Skip very short or very long text
            if len(text) < 3 or len(text) > 150:
                continue
            
            # Skip obvious non-titles
            if (re.match(r'^\d+$', text) or 
                'page' in text.lower() or
                len(text.split()) > 20):
                continue
            
            font_size = item["font_size"]
            size_score = font_size - font_stats["mode_size"]
            
            # Position score (centered or left-aligned at top)
            position_score = 0
            if item["relative_y"] < 0.3:  # Top of page
                position_score += 2
            if 0.2 < item["relative_x"] < 0.8:  # Somewhat centered
                position_score += 1
            
            # Formatting score
            format_score = 0
            if self.is_bold(item["flags"]):
                format_score += 2
            
            total_score = size_score + position_score + format_score
            
            candidates.append({
                "text": text,
                "score": total_score,
                "page": item["page"]
            })
        
        if candidates:
            # Sort by score and return best candidate
            candidates.sort(key=lambda x: x["score"], reverse=True)
            best_candidate = candidates[0]
            
            # Clean and return title
            title = self.clean_heading_text_enhanced(best_candidate["text"])
            return title if title else "Untitled Document"
        
        return "Untitled Document"
    
    def process_pdf(self, pdf_path: Path) -> Dict:
        """Process a single PDF and return the result."""
        try:
            start_time = time.time()
            
            # Extract text with metadata
            text_data = self.extract_text_with_metadata(str(pdf_path))
            
            if not text_data:
                logger.warning(f"No text extracted from {pdf_path}")
                return {"title": "Untitled Document", "outline": []}
            
            # Calculate font statistics
            font_stats = self.calculate_enhanced_font_statistics(text_data)
            
            # Find document title
            title = self.find_document_title_enhanced(text_data, font_stats)
            
            # Extract headings
            headings = self.extract_headings_enhanced(text_data)
            
            # Clean output format (remove internal fields)
            clean_headings = []
            for heading in headings:
                clean_heading = {
                    "level": heading["level"],
                    "text": heading["text"],
                    "page": heading["page"]  # Already 0-based
                }
                clean_headings.append(clean_heading)
            
            result = {
                "title": title,
                "outline": clean_headings
            }
            
            processing_time = time.time() - start_time
            logger.info(f"Processed {pdf_path.name} in {processing_time:.2f}s - Found {len(clean_headings)} headings")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")
            return {"title": "Untitled Document", "outline": []}

    def process_all_pdfs(self):
        """Process all PDF files in the input directory."""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.error("No PDF files found in input directory")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                result = self.process_pdf(pdf_file)
                
                # Save result with same name as input file
                output_file = self.output_dir / f"{pdf_file.stem}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved results to {output_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")

    # Interactive methods for manual testing
    def display_banner(self):
        """Display professional contest banner."""
        print("\n" + "="*60)
        print("🏆 ADOBE INDIA HACKATHON 2025 - Round 1A")
        print("📄 PDF Outline Extractor - Connecting the Dots")
        print("🚀 Intelligent Document Structure Analysis")
        print("="*60)
        print("⚡ Performance Target: <10 seconds | 🎯 Max Accuracy")
        print("🌐 Multilingual Support | 🔧 AMD64 Optimized")
        print("-"*60)

    def get_file_input(self) -> str:
        """Get PDF file path with interactive input."""
        self.display_banner()
        print("\n📋 INPUT OPTIONS:")
        print("1️⃣  Enter full path to PDF file")
        print("2️⃣  Place PDF in 'input/' and enter filename only")
        print("3️⃣  Drag and drop PDF file path here")
        print("\n💡 Tip: Use quotes for paths with spaces")
        print("-"*60)
        
        while True:
            try:
                pdf_input = input("\n📂 Enter PDF file path: ").strip().strip('"')
                
                if not pdf_input:
                    print("❌ Please enter a file path")
                    continue
                
                # Check if it's just a filename (look in input directory)
                if not os.path.exists(pdf_input) and not '/' in pdf_input and not '\\' in pdf_input:
                    potential_path = self.input_dir / pdf_input
                    if potential_path.exists():
                        return str(potential_path)
                
                return pdf_input
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting PDF Extractor. Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Input error: {e}")
                continue

    def process_interactive(self):
        """Interactive processing mode for testing."""
        pdf_path = self.get_file_input()
        
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return
        
        if not pdf_path.lower().endswith('.pdf'):
            print(f"❌ Not a PDF file: {pdf_path}")
            return
        
        print(f"\n🚀 Processing: {os.path.basename(pdf_path)}")
        result = self.process_pdf(Path(pdf_path))
        
        # Save with timestamp for interactive mode
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{Path(pdf_path).stem}_outline_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        print(f"📋 Found {len(result['outline'])} headings in '{result['title']}'")

def main():
    """Main function for Adobe Hackathon evaluation."""
    parser = argparse.ArgumentParser(
        description='Adobe Hackathon 2025 - PDF Outline Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--input-dir', default='input', help='Input directory path')
    parser.add_argument('--output-dir', default='output', help='Output directory path')
    parser.add_argument('--interactive', action='store_true', help='Enable interactive mode for testing')
    parser.add_argument('pdf_file', nargs='?', help='Single PDF file to process (interactive mode)')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = EnhancedPDFExtractor(args.input_dir, args.output_dir)
    
    try:
        if args.interactive or args.pdf_file:
            # Interactive/single file mode for testing
            if args.pdf_file:
                # Process single file from command line
                pdf_path = Path(args.pdf_file)
                if not pdf_path.exists():
                    print(f"❌ File not found: {pdf_path}")
                    sys.exit(1)
                
                result = extractor.process_pdf(pdf_path)
                output_file = extractor.output_dir / f"{pdf_path.stem}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Processed {pdf_path.name} -> {output_file}")
            else:
                # Interactive mode
                extractor.process_interactive()
        else:
            # Automated batch processing (default for evaluation)
            extractor.process_all_pdfs()
            
    except KeyboardInterrupt:
        print("\n👋 Processing interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()