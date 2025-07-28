import pymupdf  # PyMuPDF, imported as fitz
import os
import json
import re
import math
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import time
import tracemalloc
import unicodedata

class AdvancedFuzzyHeadingClassifier:    
    def __init__(self):
        # Comprehensive heading patterns with priority weights
        self.heading_patterns = [
            (r'^\d+\.?\s+(.+)', 3.0),  # "1. Introduction"
            (r'^(\d+\.\d+\.?\s+.+)', 2.8),  # "1.1 Subsection"
            (r'^(\d+\.\d+\.\d+\.?\s+.+)', 2.5),  # "1.1.1 Sub-subsection"
            (r'^([A-Z][A-Z\s]{2,50}[^a-z])$', 2.3),  # "ALL CAPS HEADING"
            (r'^(Chapter\s+\d+.*)', 2.9),  # "Chapter 1"
            (r'^(Section\s+\d+.*)', 2.7),  # "Section 1"
            (r'^(Part\s+[A-Z0-9]+.*)', 2.6),  # "Part A"
            (r'^(Appendix\s+[A-Z0-9]*.*)', 2.4),  # "Appendix A"
            (r'^([IVX]+\.\s+.+)', 2.7),  # Roman numerals: "I. Introduction"
            (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$', 2.0),  # Title Case
            (r'^(Article\s+\d+\.?\s+.+)', 2.6),  # "Article 1"
            (r'^([A-Z]\.\s+.+)', 2.3),  # "A. Appendix"
            (r'^[a-z]\.\s+.+', 2.0),  # "a. Subsection"
        ]
        
        # Enhanced semantic heading indicators
        self.semantic_indicators = {
            'introduction': 2.5, 'conclusion': 2.5, 'abstract': 2.8, 'summary': 2.3,
            'overview': 2.2, 'background': 2.1, 'methodology': 2.4, 'results': 2.4,
            'discussion': 2.3, 'analysis': 2.2, 'literature': 2.1, 'review': 2.0,
            'objectives': 2.2, 'scope': 2.1, 'limitations': 2.0, 'future': 1.9,
            'acknowledgements': 2.6, 'references': 2.7, 'bibliography': 2.6,
            'appendix': 2.5, 'contents': 2.8, 'index': 2.4, 'preface': 2.3,
            'foreword': 2.2, 'glossary': 2.1, 'notation': 2.0, 'definitions': 2.2,
            'executive summary': 2.7, 'methods': 2.4, 'findings': 2.4, 
            'recommendations': 2.3, 'contributions': 2.2, 'related work': 2.3,
            'experimental setup': 2.2, 'evaluation': 2.3, 'concluding remarks': 2.4
        }

        # Typography weight factors
        self.typography_weights = {
            'bold': 1.5,
            'italic': 0.8,
            'underline': 1.3,
            'all_caps': 1.4,
            'title_case': 1.2,
            'centered': 1.3
        }

    def normalize_text(self, text: str) -> str:
        """Normalize text for reliable comparison"""
        text = unicodedata.normalize('NFKC', text)
        text = re.sub(r'\s+', ' ', text).strip().lower()
        return text

    def sigmoid(self, x: float, steepness: float = 1.0, midpoint: float = 0.5) -> float:
        """Sigmoid activation function for smooth scoring"""
        return 1 / (1 + math.exp(-steepness * (x - midpoint)))
    
    def gaussian_membership(self, x: float, center: float, width: float) -> float:
        """Gaussian membership function for fuzzy logic"""
        return math.exp(-0.5 * ((x - center) / width) ** 2)
    
    def trapezoidal_membership(self, x: float, a: float, b: float, c: float, d: float) -> float:
        """Trapezoidal membership function"""
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        elif b < x <= c:
            return 1.0
        elif c < x < d:
            return (d - x) / (d - c)
        return 0.0

    def calculate_fuzzy_heading_score(self, text: str, font_size: float, avg_font_size: float,
                                    position_y: float, page_height: float, font_flags: int,
                                    line_spacing: float, is_isolated: bool, 
                                    prev_line_spacing: float, next_line_spacing: float) -> Tuple[float, Dict]:
        """Ultra-precise fuzzy logic scoring with mathematical models"""
        
        text_clean = text.strip()
        if not text_clean or len(text_clean) > 300:
            return 0.0, {}
        
        word_count = len(text_clean.split())
        char_count = len(text_clean)
        
        # Initialize score components
        scores = {}
        
        # 1. FONT SIZE ANALYSIS (25% weight)
        if avg_font_size > 0:
            size_ratio = font_size / avg_font_size
            # Gaussian membership for optimal size ratio
            scores['font_size'] = self.gaussian_membership(size_ratio, 1.3, 0.3)
            # Boost for significantly larger fonts
            if size_ratio > 1.5:
                scores['font_size'] = min(1.0, scores['font_size'] * 1.2)
        else:
            scores['font_size'] = 0.5
            
        # 2. LENGTH OPTIMIZATION (20% weight)
        # Trapezoidal membership: ideal 2-8 words, acceptable 1-15 words
        scores['length'] = self.trapezoidal_membership(word_count, 1, 2, 8, 15)
        
        # Penalty for very long text
        if char_count > 150:
            scores['length'] *= 0.7
        
        # 3. PATTERN MATCHING (25% weight)
        pattern_score = 0.0
        matched_pattern = None
        
        for pattern, weight in self.heading_patterns:
            if re.match(pattern, text_clean, re.IGNORECASE):
                pattern_score = weight / 3.0  # Normalize to 0-1 range
                matched_pattern = pattern
                break
        
        scores['pattern'] = min(1.0, pattern_score)
        
        # 4. SEMANTIC ANALYSIS (15% weight)
        semantic_score = 0.0
        text_lower = self.normalize_text(text_clean)
        
        for indicator, weight in self.semantic_indicators.items():
            if indicator in text_lower:
                semantic_score = max(semantic_score, weight / 3.0)
        
        scores['semantic'] = min(1.0, semantic_score)
        
        # 5. TYPOGRAPHY ANALYSIS (10% weight)
        typography_score = 0.5  # Base score
        
        # Check font flags for bold, italic, etc.
        if font_flags & 16:  # Bold
            typography_score *= self.typography_weights['bold']
        if font_flags & 2:   # Italic
            typography_score *= self.typography_weights['italic']
        
        # Case analysis
        if text_clean.isupper() and word_count <= 10:
            typography_score *= self.typography_weights['all_caps']
        elif text_clean.istitle():
            typography_score *= self.typography_weights['title_case']
        
        scores['typography'] = min(1.0, typography_score)
        
        # 6. POSITION ANALYSIS (5% weight)
        if page_height > 0:
            position_ratio = position_y / page_height
            # Higher score for top of page, lower for bottom
            scores['position'] = self.gaussian_membership(position_ratio, 0.2, 0.3)
        else:
            scores['position'] = 0.5
            
        # 7. WHITESPACE ANALYSIS (10% weight)
        whitespace_score = 0.5
        
        if is_isolated:  # Single line in block
            whitespace_score += 0.3
        
        # Analyze line spacing
        total_spacing = prev_line_spacing + next_line_spacing
        if total_spacing > 20:  # Significant whitespace
            whitespace_score += 0.2
        
        scores['whitespace'] = min(1.0, whitespace_score)
        
        # FUZZY AGGREGATION with weighted combination
        weights = {
            'font_size': 0.25,
            'length': 0.20,
            'pattern': 0.25,
            'semantic': 0.15,
            'typography': 0.10,
            'position': 0.05,
            'whitespace': 0.10
        }
        
        # Calculate weighted sum
        final_score = sum(scores[key] * weights[key] for key in scores)
        
        # CONFIDENCE BOOSTERS
        confidence_multiplier = 1.0
        
        # Strong pattern match boost
        if pattern_score > 2.5:
            confidence_multiplier *= 1.15
            
        # Multiple positive indicators
        positive_indicators = sum(1 for score in scores.values() if score > 0.7)
        if positive_indicators >= 3:
            confidence_multiplier *= 1.1
        
        # Apply confidence multiplier
        final_score = min(1.0, final_score * confidence_multiplier)
        
        # Add metadata
        scores['final_score'] = final_score
        scores['matched_pattern'] = matched_pattern
        scores['confidence_multiplier'] = confidence_multiplier
        
        return final_score, scores

class PrecisionFontAnalyzer:
    """Advanced font analysis with statistical clustering"""
    
    def __init__(self):
        self.font_data = []
        self.statistical_threshold = 0.1  # 10% variance tolerance
        
    def analyze_document_fonts(self, doc) -> Tuple[float, Dict[float, str], Dict]:
        """Comprehensive font analysis with statistical methods"""
        
        font_metrics = []
        font_contexts = defaultdict(list)
        
        # Collect comprehensive font data
        for page_num, page in enumerate(doc):
            try:
                blocks = page.get_text("dict")["blocks"]
                page_height = page.rect.height
                
                for block_idx, block in enumerate(blocks):
                    if "lines" in block:
                        for line_idx, line in enumerate(block["lines"]):
                            
                            # Calculate line spacing
                            prev_spacing = 0
                            next_spacing = 0
                            
                            if line_idx > 0:
                                prev_line = block["lines"][line_idx - 1]
                                if prev_line["spans"]:
                                    prev_spacing = line["bbox"][1] - prev_line["bbox"][3]
                            
                            if line_idx < len(block["lines"]) - 1:
                                next_line = block["lines"][line_idx + 1]
                                if next_line["spans"]:
                                    next_spacing = next_line["bbox"][1] - line["bbox"][3]
                            
                            for span in line["spans"]:
                                clean_text = span['text'].strip()
                                if clean_text:
                                    
                                    font_info = {
                                        'size': span['size'],
                                        'font_name': span['font'],
                                        'flags': span['flags'],
                                        'text': clean_text,
                                        'page': page_num + 1,
                                        'position_y': line["bbox"][1],
                                        'page_height': page_height,
                                        'line_spacing': prev_spacing + next_spacing,
                                        'prev_spacing': prev_spacing,
                                        'next_spacing': next_spacing,
                                        'is_isolated': len(block["lines"]) == 1 and len(line["spans"]) == 1,
                                        'word_count': len(clean_text.split()),
                                        'char_count': len(clean_text)
                                    }
                                    
                                    font_metrics.append(font_info)
                                    font_contexts[span['size']].append(font_info)
            except Exception as e:
                print(f"⚠️ Error processing page {page_num+1}: {str(e)}")
                continue
        
        if not font_metrics:
            return 12.0, {}, {}
        
        # Statistical analysis of font sizes
        sizes = [fm['size'] for fm in font_metrics]
        
        try:
            # Calculate statistical measures
            size_counter = Counter(sizes)
            size_stats = {
                'mean': statistics.mean(sizes),
                'median': statistics.median(sizes),
                'mode': size_counter.most_common(1)[0][0],
                'std_dev': statistics.stdev(sizes) if len(sizes) > 1 else 0,
                'unique_sizes': len(set(sizes))
            }
            
            # Identify body text size (most frequent)
            body_size = size_stats['mode']
            
            # Advanced clustering for heading sizes
            unique_sizes = sorted(set(sizes), reverse=True)
            
            # Calculate relative size thresholds
            size_thresholds = {
                'H1': body_size * 1.4,  # At least 40% larger
                'H2': body_size * 1.25, # At least 25% larger  
                'H3': body_size * 1.15  # At least 15% larger
            }
            
            size_to_level = {}
            
            # Assign heading levels based on size and context
            for size in unique_sizes:
                if size > size_thresholds['H1']:
                    if 'H1' not in size_to_level.values():
                        size_to_level[size] = 'H1'
                    elif 'H2' not in size_to_level.values():
                        size_to_level[size] = 'H2'
                    else:
                        size_to_level[size] = 'H3'
                elif size > size_thresholds['H2']:
                    if 'H2' not in size_to_level.values():
                        size_to_level[size] = 'H2'
                    else:
                        size_to_level[size] = 'H3'
                elif size > size_thresholds['H3']:
                    if 'H3' not in size_to_level.values():
                        size_to_level[size] = 'H3'
            
            # Validate assignments with context
            validated_mapping = {}
            for size, level in size_to_level.items():
                contexts = font_contexts[size]
                
                # Check if contexts support heading classification
                heading_like_contexts = 0
                for context in contexts:
                    if (context['word_count'] <= 15 and 
                        context['is_isolated'] and
                        context['char_count'] < 200):
                        heading_like_contexts += 1
                
                # Require at least 30% of contexts to be heading-like
                if heading_like_contexts / len(contexts) >= 0.3:
                    validated_mapping[size] = level
            
            analysis_metadata = {
                'total_fonts': len(font_metrics),
                'size_stats': size_stats,
                'size_thresholds': size_thresholds,
                'validation_passed': len(validated_mapping),
                'font_contexts': dict(font_contexts)
            }
            
            self.font_data = font_metrics
            
            return body_size, validated_mapping, analysis_metadata
        
        except statistics.StatisticsError:
            # Fallback if statistics fail
            return 12.0, {}, {'error': 'Statistics calculation failed'}

def extract_title_from_first_page(doc) -> str:
    """Extract title candidate from first page using heuristics"""
    if doc.page_count == 0:
        return ""
    
    try:
        first_page = doc[0]
        blocks = first_page.get_text("dict")["blocks"]
        title_candidates = []
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        clean_text = span['text'].strip()
                        if clean_text:
                            # Position and size heuristics
                            y_pos = line["bbox"][1]
                            page_height = first_page.rect.height
                            page_width = first_page.rect.width
                            x_center = (line["bbox"][0] + line["bbox"][2]) / 2
                            
                            # Score based on position, size, and content
                            position_score = max(0, 1.0 - (y_pos / (page_height * 0.3)))
                            center_score = max(0, 1.0 - abs(x_center - page_width/2) / (page_width * 0.4))
                            length_score = 1.0 if 2 <= len(clean_text.split()) <= 10 else 0.5
                            
                            total_score = (position_score * 0.4 + 
                                          center_score * 0.3 + 
                                          length_score * 0.3)
                            
                            title_candidates.append({
                                'text': clean_text,
                                'score': total_score,
                                'size': span['size']
                            })
        
        # Select best candidate
        if title_candidates:
            title_candidates.sort(key=lambda x: (-x['score'], -x['size']))
            return title_candidates[0]['text']
    except Exception:
        pass
    
    return ""

def extract_outline_ultra_precise(pdf_path: str) -> Dict:
    """Robust outline extraction using advanced fuzzy logic"""
    
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return {"title": "", "outline": []}
    
    result = {
        "title": doc.metadata.get('title', '').strip(),
        "outline": []
    }
    
    # 1. Enhanced TOC Analysis
    toc = doc.get_toc()
    if toc:
        print(f"✅ Found Table of Contents for {os.path.basename(pdf_path)}")
        
        for level, text, page_num in toc:
            if level <= 6:  # Support H1-H6
                clean_text = text.strip()
                if clean_text and len(clean_text.split()) <= 25:
                    result["outline"].append({
                        "level": f"H{level}",
                        "text": clean_text,
                        "page": max(1, page_num)  # Ensure valid page number
                    })
        
        # Return if we found valid TOC entries
        if result["outline"]:
            # Use first H1 as title if title is missing
            if not result['title']:
                for item in result['outline']:
                    if item['level'] == 'H1':
                        result['title'] = item['text']
                        break
            
            # Fallback title extraction
            if not result['title']:
                result['title'] = extract_title_from_first_page(doc)
                
            doc.close()
            return result
    
    # 2. Advanced Content Analysis
    print(f"⚠️ No valid TOC found for {os.path.basename(pdf_path)}. Running content analysis...")
    
    # Initialize analyzers
    font_analyzer = PrecisionFontAnalyzer()
    fuzzy_classifier = AdvancedFuzzyHeadingClassifier()
    
    # Comprehensive font analysis
    body_size, size_to_level, font_metadata = font_analyzer.analyze_document_fonts(doc)
    
    print(f"   📊 Font analysis: Body size = {body_size:.1f}pt, Found {len(size_to_level)} heading sizes")
    
    # Collect heading candidates
    heading_candidates = []
    seen_texts = set()
    
    for font_info in font_analyzer.font_data:
        text = font_info['text']
        normalized_text = fuzzy_classifier.normalize_text(text)
        
        # Skip duplicates
        if normalized_text in seen_texts:
            continue
        seen_texts.add(normalized_text)
        
        # Skip obvious non-headings
        if (len(text.split()) > 25 or 
            len(text) > 300 or
            text.count('.') > 3 or  # Likely paragraph text
            text.lower().startswith(('the ', 'this ', 'these ', 'those ', 'a ', 'an '))):
            continue
        
        # Calculate fuzzy heading score
        fuzzy_score, score_breakdown = fuzzy_classifier.calculate_fuzzy_heading_score(
            text=text,
            font_size=font_info['size'],
            avg_font_size=body_size,
            position_y=font_info['position_y'],
            page_height=font_info['page_height'],
            font_flags=font_info['flags'],
            line_spacing=font_info['line_spacing'],
            is_isolated=font_info['is_isolated'],
            prev_line_spacing=font_info['prev_spacing'],
            next_line_spacing=font_info['next_spacing']
        )
        
        # Determine heading level
        heading_level = None
        confidence_boost = 0.0
        
        # Font-based level assignment
        if font_info['size'] in size_to_level:
            heading_level = size_to_level[font_info['size']]
            confidence_boost += 0.15
        
        # Pattern-based level assignment fallback
        elif fuzzy_score > 0.7:
            if score_breakdown.get('matched_pattern'):
                pattern = score_breakdown['matched_pattern']
                if r'^\d+\.' in pattern:  # Main sections
                    heading_level = 'H1'
                elif r'^\d+\.\d+' in pattern:  # Subsections
                    heading_level = 'H2'
                elif r'^\d+\.\d+\.\d+' in pattern:  # Sub-subsections
                    heading_level = 'H3'
                else:
                    # Default based on font size
                    size_ratio = font_info['size'] / body_size
                    if size_ratio > 1.3:
                        heading_level = 'H1'
                    elif size_ratio > 1.15:
                        heading_level = 'H2'
                    else:
                        heading_level = 'H3'
        
        # Apply minimum threshold with confidence boosting
        final_score = fuzzy_score + confidence_boost
        
        if heading_level and final_score > 0.6:
            heading_candidates.append({
                'text': text,
                'level': heading_level,
                'page': font_info['page'],
                'score': final_score,
                'size': font_info['size'],
                'breakdown': score_breakdown
            })
    
    # 3. Post-processing and Validation
    # Sort by page then by score (descending)
    heading_candidates.sort(key=lambda x: (x['page'], -x['score']))
    
    # Remove duplicates while preserving order
    unique_candidates = []
    seen_pages = set()
    
    for candidate in heading_candidates:
        key = (candidate['page'], candidate['text'][:50].lower())
        if key not in seen_pages:
            unique_candidates.append(candidate)
            seen_pages.add(key)
    
    # Build final outline
    for candidate in unique_candidates:
        result["outline"].append({
            "level": candidate['level'],
            "text": candidate['text'],
            "page": candidate['page']
        })
    
    # 4. Title Extraction
    if not result['title']:
        # First try to find title from first H1
        for item in result['outline']:
            if item['level'] == 'H1':
                result['title'] = item['text']
                break
        
        # Then try highest scoring candidate
        if not result['title'] and unique_candidates:
            unique_candidates.sort(key=lambda x: -x['score'])
            result['title'] = unique_candidates[0]['text']
        
        # Finally, extract from first page
        if not result['title']:
            result['title'] = extract_title_from_first_page(doc)
    
    doc.close()
    
    print(f"   ✅ Extracted {len(result['outline'])} headings")
    
    return result

def process_all_pdfs(input_dir: str, output_dir: str) -> Dict:
    """Process all PDF files with robust error handling"""
    os.makedirs(output_dir, exist_ok=True)
    
    processing_stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'total_headings': 0,
        'processing_times': [],
        'failed_files': []
    }
    
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    for file in pdf_files:
        file_path = os.path.join(input_dir, file)
        print(f"\n🔍 Processing {file}...")
        
        start_time = time.time()
        
        try:
            document_outline = extract_outline_ultra_precise(file_path)
            
            output_filename = os.path.splitext(file)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(document_outline, f, indent=4, ensure_ascii=False)
            
            processing_time = time.time() - start_time
            processing_stats['processing_times'].append(processing_time)
            processing_stats['successful'] += 1
            processing_stats['total_headings'] += len(document_outline['outline'])
            
            print(f"✅ Success: {output_path}")
            print(f"   Title: {document_outline['title'][:50]}{'...' if len(document_outline['title']) > 50 else ''}")
            print(f"   Headings: {len(document_outline['outline'])}")
            print(f"   Time: {processing_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error processing {file}: {str(e)}")
            processing_stats['failed'] += 1
            processing_stats['failed_files'].append(file)
        
        processing_stats['total_files'] += 1
    
    return processing_stats


#  Round 1b 
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
    outline_data = extract_outline_ultra_precise(pdf_path)
    outline = outline_data["outline"]
    
    # Add y-position to outline entries (requires modifying extract_outline_ultra_precise)
    # Modify extract_outline_ultra_precise to include y_pos in heading_candidates
    # For simplicity, re-run font analysis to get y-positions
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
    
    heading_candidates.sort(key=lambda x: (x['page'], x['y_pos']))
    
    # Step 2: Extract all text blocks
    text_blocks = extract_all_text_with_positions(doc)
    
    # Step 3: Map text to sections
    sections = []
    for i, heading in enumerate(heading_candidates):
        start_page = heading['page']
        start_y = heading['y_pos']
        
        # Determine end boundary
        end_page = doc.page_count
        end_y = doc[end_page - 1].rect.height
        if i + 1 < len(heading_candidates):
            next_heading = heading_candidates[i + 1]
            end_page = next_heading['page']
            end_y = next_heading['y_pos']
        
        # Collect text between current and next heading
        section_content = ""
        for block in text_blocks:
            if (block['page'] > start_page or
                (block['page'] == start_page and block['y_pos'] >= start_y)) and \
               (block['page'] < end_page or
                (block['page'] == end_page and block['y_pos'] < end_y)):
                section_content += block['text'] + "\n"
        
        sections.append({
            "document": os.path.basename(pdf_path),
            "page_number": heading['page'],
            "section_title": heading['text'],
            "content": section_content.strip()
        })
    
    doc.close()
    return sections

# --- Main Execution ---
if __name__ == "__main__":
    INPUT_DIRECTORY = "input"
    OUTPUT_DIRECTORY = "output-deepseek"
    
    if not os.path.exists(INPUT_DIRECTORY):
        os.makedirs(INPUT_DIRECTORY)
        print(f"📁 Created '{INPUT_DIRECTORY}' folder. Add PDF files there.")
        exit()
    
    print("🚀 Starting Robust PDF Outline Extraction")
    print("📈 Features: Fuzzy Logic, Statistical Analysis, Advanced Pattern Recognition")
    
    start_time = time.time()
    tracemalloc.start()
    
    stats = process_all_pdfs(INPUT_DIRECTORY, OUTPUT_DIRECTORY)
    
    # Memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Final Report
    print("\n" + "="*60)
    print("📊 EXTRACTION REPORT")
    print("="*60)
    print(f"📁 Total PDFs: {stats['total_files']}")
    print(f"✅ Successful: {stats['successful']}")
    print(f"❌ Failed: {stats['failed']}")
    
    if stats['failed_files']:
        print(f"   Failed files: {', '.join(stats['failed_files'])}")
    
    print(f"📋 Total headings: {stats['total_headings']}")
    
    if stats['processing_times']:
        avg_time = sum(stats['processing_times']) / len(stats['processing_times'])
        print(f"⏱️ Avg time: {avg_time:.2f}s per PDF")
    
    print(f"⏱️ Total time: {total_time:.2f}s")
    print(f"💾 Peak memory: {peak / 1024 / 1024:.1f} MB")
    
    success_rate = (stats['successful'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
    print(f"🎯 Success rate: {success_rate:.1f}%")
    
    if stats['successful'] > 0:
        avg_headings = stats['total_headings'] / stats['successful']
        print(f"📈 Avg headings: {avg_headings:.1f} per document")
    
    print("\n🎉 Extraction complete!")
from typing import List, Dict
import pymupdf

def extract_all_text_with_positions(doc: pymupdf.Document) -> List[Dict]:
    """
    Extract all text blocks from a PDF document with positional metadata.
    
    Args:
        doc: PyMuPDF document object.
    
    Returns:
        List of dictionaries containing text and metadata for each text block.
    """
    text_blocks = []
    
    for page_num in range(doc.page_count):
        try:
            page = doc[page_num]
            page_height = page.rect.height
            page_width = page.rect.width
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            clean_text = span["text"].strip()
                            if clean_text:
                                line_text += clean_text + " "
                        
                        if line_text.strip():
                            # Calculate line spacing
                            prev_spacing = 0
                            next_spacing = 0
                            line_idx = block["lines"].index(line)
                            
                            if line_idx > 0:
                                prev_line = block["lines"][line_idx - 1]
                                if prev_line["spans"]:
                                    prev_spacing = line["bbox"][1] - prev_line["bbox"][3]
                            
                            if line_idx < len(block["lines"]) - 1:
                                next_line = block["lines"][line_idx + 1]
                                if next_line["spans"]:
                                    next_spacing = next_line["bbox"][1] - line["bbox"][3]
                            
                            x_center = (line["bbox"][0] + line["bbox"][2]) / 2
                            
                            text_blocks.append({
                                "page": page_num + 1,
                                "text": line_text.strip(),
                                "y_pos": line["bbox"][1],  # Top y-coordinate
                                "page_height": page_height,
                                "page_width": page_width,
                                "x_center": x_center,
                                "line_spacing": prev_spacing + next_spacing,
                                "font_size": span["size"] if line["spans"] else 0,
                                "font_flags": span["flags"] if line["spans"] else 0,
                                "is_isolated": len(block["lines"]) == 1 and len(line["spans"]) == 1
                            })
        except Exception as e:
            print(f"⚠️ Error processing page {page_num + 1}: {str(e)}")
            continue
    
    return text_blocks
