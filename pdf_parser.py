import pymupdf
import os
from typing import List, Dict
from extract_outline_ultra_precise import (
    PrecisionFontAnalyzer,
    AdvancedFuzzyHeadingClassifier,
    extract_all_text_with_positions,
    extract_outline_ultra_precise
)

def get_sections_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract sections with their content from a PDF using heading information.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        List of dictionaries containing section metadata and content.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"❌ Error opening {pdf_path}: {str(e)}")
        return []
    
    # Step 1: Get headings using existing Round 1A function
    font_analyzer = PrecisionFontAnalyzer()
    body_size, size_to_level, _ = font_analyzer.analyze_document_fonts(doc)
    heading_candidates = []
    fuzzy_classifier = AdvancedFuzzyHeadingClassifier()
    seen_texts = set()
    
    for font_info in font_analyzer.font_data:
        text = font_info['text']
        normalized_text = fuzzy_classifier.normalize_text(text)
        if normalized_text in seen_texts:
            continue
        seen_texts.add(normalized_text)
        
        # Skip obvious non-headings
        if (len(text.split()) > 25 or len(text) > 300 or
            text.count('.') > 3 or text.lower().startswith(('the ', 'this ', 'these ', 'those ', 'a ', 'an '))):
            continue
        
        fuzzy_score, score_breakdown = fuzzy_classifier.calculate_fuzzy_heading_score(
            text=text, font_size=font_info['size'], avg_font_size=body_size,
            position_y=font_info['position_y'], page_height=font_info['page_height'],
            font_flags=font_info['flags'], line_spacing=font_info['line_spacing'],
            is_isolated=font_info['is_isolated'], prev_line_spacing=font_info['prev_spacing'],
            next_line_spacing=font_info['next_spacing']
        )
        
        heading_level = None
        if font_info['size'] in size_to_level:
            heading_level = size_to_level[font_info['size']]
        elif fuzzy_score > 0.7:
            size_ratio = font_info['size'] / body_size
            heading_level = 'H1' if size_ratio > 1.3 else 'H2' if size_ratio > 1.15 else 'H3'
        
        if heading_level and fuzzy_score > 0.6:
            heading_candidates.append({
                'text': text,
                'level': heading_level,
                'page': font_info['page'],
                'y_pos': font_info['position_y'],
                'score': fuzzy_score
            })
    
    # Sort headings by page and position
    heading_candidates.sort(key=lambda x: (x['page'], x['y_pos']))
    
    # Step 2: Extract all text blocks
    text_blocks = extract_all_text_with_positions(doc)
    
    # Step 3: Map text to sections (FIXED LOGIC)
    sections = []
    for i, heading in enumerate(heading_candidates):
        start_page = heading['page']
        start_y = heading['y_pos']
        
        # Determine end boundary (next heading or end of document)
        end_page = doc.page_count
        end_y = float('inf')  # Use infinity for last section
        
        if i + 1 < len(heading_candidates):
            next_heading = heading_candidates[i + 1]
            end_page = next_heading['page']
            end_y = next_heading['y_pos']
        
        # Collect text between current and next heading
        section_content = []
        heading_text_normalized = fuzzy_classifier.normalize_text(heading['text'])
        
        for block in text_blocks:
            # Check if block is within section boundaries
            block_in_range = False
            
            if block['page'] > start_page and block['page'] < end_page:
                # Block is on a page between start and end
                block_in_range = True
            elif block['page'] == start_page and block['page'] == end_page:
                # Start and end on same page
                if block['y_pos'] > start_y and block['y_pos'] < end_y:
                    block_in_range = True
            elif block['page'] == start_page:
                # Block on start page
                if block['y_pos'] > start_y:
                    block_in_range = True
            elif block['page'] == end_page:
                # Block on end page
                if block['y_pos'] < end_y:
                    block_in_range = True
            
            if block_in_range:
                # CRITICAL FIX: Skip the heading text itself
                block_text_normalized = fuzzy_classifier.normalize_text(block['text'])
                if block_text_normalized != heading_text_normalized:
                    section_content.append(block['text'])
        
        # Only create section if there's actual content (not just the heading)
        if section_content:
            sections.append({
                "document": os.path.basename(pdf_path),
                "page_number": heading['page'],
                "section_title": heading['text'],  # This should be the heading, not content
                "content": "\n".join(section_content).strip()
            })
    
    doc.close()
    print(f"   📄 Extracted {len(sections)} sections from {os.path.basename(pdf_path)}")
    
    # Debug: Print first few sections to verify
    for i, section in enumerate(sections[:3]):
        print(f"   Section {i+1}: '{section['section_title'][:50]}...'")
    
    return sections
