"""
Advanced OCR Processor
Handles scanned documents with validation, error correction, and confidence scoring
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
import logging
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float  # 0-1
    language: str
    line_confidences: List[float]
    corrected_errors: int
    needs_manual_review: bool
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'corrected_errors': self.corrected_errors,
            'needs_manual_review': self.needs_manual_review,
            'metadata': self.metadata or {}
        }


class AdvancedOCREngine:
    """
    Advanced OCR with error correction and validation
    Optimized for construction documents
    """

    # Common OCR errors in construction documents
    OCR_ERROR_PATTERNS = {
        # Number confusions
        r'\bO\b': '0',  # O -> 0
        r'\bl\b': '1',  # l -> 1
        r'\bS\b(?=\s*\d)': '5',  # S -> 5 (when followed by numbers)
        r'\bB\b(?=\s*\d)': '8',  # B -> 8

        # Unit corrections
        r'\bcurn\b': 'cum',
        r'\bsqrn\b': 'sqm',
        r'\bkq\b': 'kg',
        r'\bnos\.?\s': 'nos ',

        # Common material names
        r'\bccment\b': 'cement',
        r'\bconcrctc\b': 'concrete',
        r'\bstccl\b': 'steel',
        r'\brnasonry\b': 'masonry',
        r'\bplastcring\b': 'plastering',
    }

    # Construction terminology dictionary
    CONSTRUCTION_TERMS = [
        'excavation', 'foundation', 'concrete', 'cement', 'sand', 'aggregate',
        'masonry', 'brick', 'block', 'plastering', 'flooring', 'roofing',
        'steel', 'reinforcement', 'shuttering', 'formwork', 'curing',
        'painting', 'finishing', 'plumbing', 'electrical', 'drainage',
        'earthwork', 'filling', 'compaction', 'waterproofing',
        'cpwd', 'dsr', 'schedule', 'specification'
    ]

    # Standard units
    STANDARD_UNITS = ['cum', 'sqm', 'rmt', 'm', 'kg', 'nos', 'ls', 'each', 'tonne', 'litre']

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

        # Configure Tesseract (if custom path needed)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

    def _compile_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """Compile error correction patterns"""
        return [(re.compile(pattern, re.IGNORECASE), replacement)
                for pattern, replacement in self.OCR_ERROR_PATTERNS.items()]

    def process_scanned_document(self, pdf_path: str) -> OCRResult:
        """
        Process a scanned PDF document

        Args:
            pdf_path: Path to PDF file

        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            import fitz  # PyMuPDF

            # Check if PDF is already searchable
            doc = fitz.open(pdf_path)

            # Try to extract text first
            text = ""
            for page in doc:
                text += page.get_text()

            # If we got substantial text, it's already searchable
            if len(text.strip()) > 100:
                logger.info("PDF is already searchable, skipping OCR")
                doc.close()
                return OCRResult(
                    text=text,
                    confidence=0.95,
                    language='en',
                    line_confidences=[],
                    corrected_errors=0,
                    needs_manual_review=False,
                    metadata={'method': 'direct_extraction'}
                )

            # PDF is scanned, need OCR
            logger.info("PDF appears to be scanned, performing OCR...")

            # Process each page
            all_text = []
            all_confidences = []
            total_corrections = 0

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Convert page to image
                pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
                img_data = pix.tobytes("png")

                # Process image with OCR
                page_result = self._ocr_image_from_bytes(img_data)

                all_text.append(f"--- Page {page_num + 1} ---\n{page_result.text}")
                all_confidences.extend(page_result.line_confidences)
                total_corrections += page_result.corrected_errors

                logger.info(f"Page {page_num + 1}: confidence={page_result.confidence:.2f}, "
                          f"corrections={page_result.corrected_errors}")

            doc.close()

            # Combine results
            combined_text = '\n\n'.join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

            # Detect language
            language = self._detect_language(combined_text)

            # Determine if manual review needed
            needs_manual_review = avg_confidence < 0.7

            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                language=language,
                line_confidences=all_confidences,
                corrected_errors=total_corrections,
                needs_manual_review=needs_manual_review,
                metadata={'method': 'ocr', 'pages': len(doc)}
            )

        except Exception as e:
            logger.error(f"Error processing scanned document: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                language='unknown',
                line_confidences=[],
                corrected_errors=0,
                needs_manual_review=True,
                metadata={'error': str(e)}
            )

    def _ocr_image_from_bytes(self, img_bytes: bytes) -> OCRResult:
        """Perform OCR on image bytes"""
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return self.ocr_image(img)

    def ocr_image(self, image: np.ndarray) -> OCRResult:
        """
        Perform OCR on an image with confidence scoring

        Args:
            image: OpenCV image (numpy array)

        Returns:
            OCRResult with text and confidence
        """
        try:
            # Preprocess image for better OCR
            preprocessed = self._preprocess_for_ocr(image)

            # Perform OCR with detailed data
            ocr_data = pytesseract.image_to_data(
                preprocessed,
                output_type=pytesseract.Output.DICT,
                lang='eng',
                config='--psm 1'  # Automatic page segmentation with OSD
            )

            # Extract text and confidence per line
            lines = []
            line_confidences = []
            current_line = []
            current_line_confs = []

            for i, word in enumerate(ocr_data['text']):
                conf = float(ocr_data['conf'][i])

                if conf > 0:  # Valid word
                    current_line.append(word)
                    current_line_confs.append(conf)

                # Check if end of line
                if i < len(ocr_data['text']) - 1:
                    next_block = ocr_data['block_num'][i + 1]
                    curr_block = ocr_data['block_num'][i]
                    if next_block != curr_block and current_line:
                        # End of line
                        line_text = ' '.join(current_line)
                        line_conf = sum(current_line_confs) / len(current_line_confs) if current_line_confs else 0

                        lines.append(line_text)
                        line_confidences.append(line_conf)

                        current_line = []
                        current_line_confs = []

            # Add last line
            if current_line:
                line_text = ' '.join(current_line)
                line_conf = sum(current_line_confs) / len(current_line_confs) if current_line_confs else 0
                lines.append(line_text)
                line_confidences.append(line_conf)

            # Combine text
            raw_text = '\n'.join(lines)

            # Fix OCR errors
            corrected_text, num_corrections = self.fix_ocr_errors(raw_text)

            # Calculate overall confidence
            avg_confidence = sum(line_confidences) / len(line_confidences) if line_confidences else 0.0
            normalized_confidence = avg_confidence / 100.0  # Tesseract gives 0-100

            # Detect language
            language = self._detect_language(corrected_text)

            return OCRResult(
                text=corrected_text,
                confidence=normalized_confidence,
                language=language,
                line_confidences=[c / 100.0 for c in line_confidences],
                corrected_errors=num_corrections,
                needs_manual_review=normalized_confidence < 0.7,
                metadata={'lines': len(lines)}
            )

        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                language='unknown',
                line_confidences=[],
                corrected_errors=0,
                needs_manual_review=True,
                metadata={'error': str(e)}
            )

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for optimal OCR"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Binarization (Otsu's method)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to remove small noise
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    def fix_ocr_errors(self, text: str) -> Tuple[str, int]:
        """
        Fix common OCR errors in construction documents

        Args:
            text: Raw OCR text

        Returns:
            Tuple of (corrected_text, num_corrections)
        """
        corrected = text
        num_corrections = 0

        # Apply pattern-based corrections
        for pattern, replacement in self.compiled_patterns:
            matches = pattern.findall(corrected)
            if matches:
                corrected = pattern.sub(replacement, corrected)
                num_corrections += len(matches)

        # Context-based corrections
        corrected, context_corrections = self._context_based_corrections(corrected)
        num_corrections += context_corrections

        logger.debug(f"Fixed {num_corrections} OCR errors")

        return corrected, num_corrections

    def _context_based_corrections(self, text: str) -> Tuple[str, int]:
        """Apply context-aware corrections"""
        corrections = 0
        lines = text.split('\n')
        corrected_lines = []

        for line in lines:
            original = line
            # Fix numbers before units
            # Example: "5O cum" -> "50 cum"
            for unit in self.STANDARD_UNITS:
                pattern = rf'(\d+)[Oo](\s+{unit})'
                if re.search(pattern, line, re.IGNORECASE):
                    line = re.sub(pattern, r'\g<1>0\g<2>', line, flags=re.IGNORECASE)

            # Fix "l" to "1" in numeric contexts
            # Example: "l23" -> "123"
            line = re.sub(r'\bl(\d+)', r'1\g<1>', line)
            line = re.sub(r'(\d+)l\b', r'\g<1>1', line)

            if line != original:
                corrections += 1

            corrected_lines.append(line)

        return '\n'.join(corrected_lines), corrections

    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            if len(text.strip()) < 50:
                return 'en'  # Default to English for short text

            lang = detect(text)
            return lang
        except LangDetectException:
            return 'en'

    def validate_extraction(self, ocr_result: OCRResult) -> Dict:
        """
        Validate OCR extraction quality

        Returns:
            Validation report
        """
        text = ocr_result.text

        # Check for construction terminology presence
        terms_found = sum(1 for term in self.CONSTRUCTION_TERMS if term in text.lower())
        terminology_score = min(terms_found / 10.0, 1.0)  # At least 10 terms = full score

        # Check for numeric data presence (BOQ should have lots of numbers)
        numbers = re.findall(r'\d+\.?\d*', text)
        numeric_density = len(numbers) / max(len(text.split()), 1)
        numeric_score = min(numeric_density * 10, 1.0)

        # Check for table-like structure
        lines = text.split('\n')
        structured_lines = sum(1 for line in lines if len(re.findall(r'\s{2,}', line)) >= 2)
        structure_score = structured_lines / max(len(lines), 1)

        # Overall validation score
        validation_score = (
            ocr_result.confidence * 0.4 +
            terminology_score * 0.3 +
            numeric_score * 0.2 +
            structure_score * 0.1
        )

        return {
            'validation_score': validation_score,
            'ocr_confidence': ocr_result.confidence,
            'terminology_score': terminology_score,
            'numeric_score': numeric_score,
            'structure_score': structure_score,
            'is_valid': validation_score > 0.6,
            'recommendation': 'Use for processing' if validation_score > 0.7 else 'Manual review recommended' if validation_score > 0.5 else 'Low quality - consider re-scanning'
        }


# Convenience functions

def ocr_pdf(pdf_path: str) -> OCRResult:
    """Quick OCR processing of a PDF"""
    engine = AdvancedOCREngine()
    return engine.process_scanned_document(pdf_path)


def ocr_image_file(image_path: str) -> OCRResult:
    """Quick OCR processing of an image file"""
    engine = AdvancedOCREngine()
    img = cv2.imread(image_path)
    return engine.ocr_image(img)
