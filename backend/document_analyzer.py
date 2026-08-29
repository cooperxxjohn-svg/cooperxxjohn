"""
Document Structure Analyzer
Detects document structure, identifies content types, and prioritizes pages for processing
"""

import PyPDF2
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content found in construction documents"""
    TITLE_PAGE = "title_page"
    TABLE_OF_CONTENTS = "table_of_contents"
    SPECIFICATION = "specification"
    BOQ_TABLE = "boq_table"
    SCHEDULE = "schedule"
    DRAWING = "drawing"
    GENERAL_CONDITIONS = "general_conditions"
    TECHNICAL_SPEC = "technical_spec"
    RATE_ANALYSIS = "rate_analysis"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Processing priority levels"""
    SKIP = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PageInfo:
    """Information about a single page"""
    page_num: int
    content_type: ContentType
    priority: Priority
    text_length: int
    has_tables: bool
    has_images: bool
    section_name: Optional[str] = None
    keywords_found: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1 confidence in content_type detection


@dataclass
class DocumentMap:
    """Complete map of document structure"""
    total_pages: int
    pages: List[PageInfo]
    sections: Dict[str, List[int]]  # section_name -> page_numbers
    boq_pages: List[int]
    drawing_pages: List[int]
    specification_pages: List[int]
    processing_order: List[int]  # Pages ordered by priority


class DocumentStructureAnalyzer:
    """
    Analyzes construction documents to understand structure and content
    """

    # Keywords for content type detection
    KEYWORDS = {
        'title': ['project', 'tender', 'contract', 'notice inviting tender', 'nit', 'bill of quantities'],
        'toc': ['table of contents', 'contents', 'index'],
        'specification': ['specification', 'work description', 'scope of work', 'technical specifications'],
        'boq': ['bill of quantities', 'boq', 'schedule of quantities', 'priced schedule', 'item no', 'description', 'unit', 'quantity', 'rate', 'amount'],
        'schedule': ['schedule', 'time schedule', 'payment schedule'],
        'drawing': ['drawing', 'plan', 'elevation', 'section', 'detail', 'architectural', 'structural'],
        'general_conditions': ['general conditions', 'terms and conditions', 'special conditions', 'conditions of contract'],
        'rate_analysis': ['rate analysis', 'analysis of rates', 'dsr', 'schedule of rates']
    }

    # Common construction sections
    COMMON_SECTIONS = [
        'earthwork', 'foundation', 'concrete', 'masonry', 'plastering',
        'flooring', 'roofing', 'doors', 'windows', 'painting', 'plumbing',
        'electrical', 'hvac', 'drainage', 'finishing', 'mep'
    ]

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for faster matching"""
        patterns = {}
        for key, keywords in self.KEYWORDS.items():
            patterns[key] = [re.compile(kw, re.IGNORECASE) for kw in keywords]
        return patterns

    def analyze_document_structure(self, pdf_path: str) -> DocumentMap:
        """
        Analyze complete document structure

        Args:
            pdf_path: Path to PDF file

        Returns:
            DocumentMap with complete structure analysis
        """
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            logger.info(f"Analyzing document structure: {total_pages} pages")

            # Analyze each page
            pages: List[PageInfo] = []
            for page_num in range(total_pages):
                page_info = self._analyze_page(doc, page_num)
                pages.append(page_info)
                logger.debug(f"Page {page_num + 1}: {page_info.content_type.value} (priority: {page_info.priority.value})")

            # Identify sections
            sections = self._identify_sections(pages)

            # Find special pages
            boq_pages = [p.page_num for p in pages if p.content_type == ContentType.BOQ_TABLE]
            drawing_pages = [p.page_num for p in pages if p.content_type == ContentType.DRAWING]
            spec_pages = [p.page_num for p in pages if p.content_type in [ContentType.SPECIFICATION, ContentType.TECHNICAL_SPEC]]

            # Determine processing order
            processing_order = self._determine_processing_order(pages)

            doc.close()

            doc_map = DocumentMap(
                total_pages=total_pages,
                pages=pages,
                sections=sections,
                boq_pages=boq_pages,
                drawing_pages=drawing_pages,
                specification_pages=spec_pages,
                processing_order=processing_order
            )

            self._log_analysis_summary(doc_map)

            return doc_map

        except Exception as e:
            logger.error(f"Error analyzing document structure: {e}")
            # Return minimal document map
            return DocumentMap(
                total_pages=0,
                pages=[],
                sections={},
                boq_pages=[],
                drawing_pages=[],
                specification_pages=[],
                processing_order=[]
            )

    def _analyze_page(self, doc: fitz.Document, page_num: int) -> PageInfo:
        """Analyze a single page"""
        page = doc[page_num]

        # Extract text
        text = page.get_text().lower()
        text_length = len(text)

        # Check for images
        images = page.get_images()
        has_images = len(images) > 0

        # Check for tables (rough heuristic)
        has_tables = self._detect_table_in_text(text)

        # Detect content type
        content_type, keywords_found, confidence = self._detect_content_type(text, page_num, text_length, has_images)

        # Determine priority
        priority = self._determine_priority(content_type, page_num, text_length)

        # Try to identify section
        section_name = self._identify_section_name(text)

        return PageInfo(
            page_num=page_num,
            content_type=content_type,
            priority=priority,
            text_length=text_length,
            has_tables=has_tables,
            has_images=has_images,
            section_name=section_name,
            keywords_found=keywords_found,
            confidence=confidence
        )

    def _detect_content_type(self, text: str, page_num: int, text_length: int, has_images: bool) -> Tuple[ContentType, List[str], float]:
        """
        Detect the content type of a page

        Returns:
            (ContentType, keywords_found, confidence)
        """
        # Title page detection (usually first 2 pages)
        if page_num < 2 and any(pattern.search(text) for pattern in self.compiled_patterns['title']):
            return ContentType.TITLE_PAGE, ['title'], 0.9

        # BOQ detection (high priority)
        boq_keywords = [kw for pattern in self.compiled_patterns['boq'] for kw in [pattern.pattern] if pattern.search(text)]
        if len(boq_keywords) >= 3:  # At least 3 BOQ keywords
            return ContentType.BOQ_TABLE, boq_keywords, 0.95

        # Specification detection
        spec_keywords = [kw for pattern in self.compiled_patterns['specification'] for kw in [pattern.pattern] if pattern.search(text)]
        if len(spec_keywords) >= 1 and text_length > 500:
            return ContentType.SPECIFICATION, spec_keywords, 0.85

        # Drawing detection (usually has images and minimal text)
        if has_images and text_length < 200:
            drawing_keywords = [kw for pattern in self.compiled_patterns['drawing'] for kw in [pattern.pattern] if pattern.search(text)]
            if drawing_keywords:
                return ContentType.DRAWING, drawing_keywords, 0.8

        # Rate analysis
        rate_keywords = [kw for pattern in self.compiled_patterns['rate_analysis'] for kw in [pattern.pattern] if pattern.search(text)]
        if rate_keywords:
            return ContentType.RATE_ANALYSIS, rate_keywords, 0.8

        # General conditions
        gc_keywords = [kw for pattern in self.compiled_patterns['general_conditions'] for kw in [pattern.pattern] if pattern.search(text)]
        if gc_keywords:
            return ContentType.GENERAL_CONDITIONS, gc_keywords, 0.75

        # Schedule
        schedule_keywords = [kw for pattern in self.compiled_patterns['schedule'] for kw in [pattern.pattern] if pattern.search(text)]
        if schedule_keywords:
            return ContentType.SCHEDULE, schedule_keywords, 0.75

        # Table of contents
        toc_keywords = [kw for pattern in self.compiled_patterns['toc'] for kw in [pattern.pattern] if pattern.search(text)]
        if toc_keywords:
            return ContentType.TABLE_OF_CONTENTS, toc_keywords, 0.9

        # Default: unknown
        return ContentType.UNKNOWN, [], 0.3

    def _detect_table_in_text(self, text: str) -> bool:
        """Detect if text contains table-like structure"""
        lines = text.split('\n')

        # Look for patterns that indicate tables
        # - Multiple aligned columns
        # - Repeated use of numbers
        # - Consistent spacing

        table_indicators = 0

        for line in lines:
            # Check for multiple numbers with spacing
            if re.findall(r'\d+\s+\d+\s+\d+', line):
                table_indicators += 1

            # Check for common table headers
            if re.search(r'(sr\.?\s*no|item\s*no|description|quantity|unit|rate|amount)', line, re.IGNORECASE):
                table_indicators += 2

        return table_indicators >= 3

    def _determine_priority(self, content_type: ContentType, page_num: int, text_length: int) -> Priority:
        """Determine processing priority for a page"""

        priority_map = {
            ContentType.BOQ_TABLE: Priority.CRITICAL,
            ContentType.SPECIFICATION: Priority.HIGH,
            ContentType.TECHNICAL_SPEC: Priority.HIGH,
            ContentType.RATE_ANALYSIS: Priority.MEDIUM,
            ContentType.DRAWING: Priority.MEDIUM,
            ContentType.SCHEDULE: Priority.MEDIUM,
            ContentType.GENERAL_CONDITIONS: Priority.LOW,
            ContentType.TITLE_PAGE: Priority.SKIP,
            ContentType.TABLE_OF_CONTENTS: Priority.SKIP,
            ContentType.UNKNOWN: Priority.LOW if text_length > 200 else Priority.SKIP
        }

        return priority_map.get(content_type, Priority.LOW)

    def _identify_section_name(self, text: str) -> Optional[str]:
        """Try to identify which construction section this page belongs to"""
        text_lower = text.lower()

        for section in self.COMMON_SECTIONS:
            if section in text_lower:
                return section

        return None

    def _identify_sections(self, pages: List[PageInfo]) -> Dict[str, List[int]]:
        """Group pages by construction section"""
        sections: Dict[str, List[int]] = {}

        for page in pages:
            if page.section_name:
                if page.section_name not in sections:
                    sections[page.section_name] = []
                sections[page.section_name].append(page.page_num)

        return sections

    def _determine_processing_order(self, pages: List[PageInfo]) -> List[int]:
        """
        Determine optimal processing order based on priority

        Strategy:
        1. Process BOQ pages first (CRITICAL)
        2. Process specification pages (HIGH)
        3. Process drawings and schedules (MEDIUM)
        4. Process other content (LOW)
        5. Skip title pages and TOC (SKIP)
        """
        # Sort pages by priority (descending) and page number (ascending)
        sorted_pages = sorted(
            pages,
            key=lambda p: (p.priority.value, -p.page_num),
            reverse=True
        )

        # Return page numbers, excluding SKIP priority
        processing_order = [
            p.page_num for p in sorted_pages
            if p.priority != Priority.SKIP
        ]

        return processing_order

    def prioritize_pages(self, document_map: DocumentMap, max_pages: Optional[int] = None) -> List[int]:
        """
        Get prioritized list of pages to process

        Args:
            document_map: DocumentMap from analyze_document_structure()
            max_pages: Maximum number of pages to return (None = all)

        Returns:
            List of page numbers in priority order
        """
        if max_pages:
            return document_map.processing_order[:max_pages]
        return document_map.processing_order

    def get_section_pages(self, document_map: DocumentMap, section_name: str) -> List[int]:
        """Get all pages for a specific section"""
        return document_map.sections.get(section_name, [])

    def _log_analysis_summary(self, doc_map: DocumentMap):
        """Log summary of analysis"""
        logger.info(f"Document Analysis Summary:")
        logger.info(f"  Total pages: {doc_map.total_pages}")
        logger.info(f"  BOQ pages: {len(doc_map.boq_pages)} - {doc_map.boq_pages}")
        logger.info(f"  Specification pages: {len(doc_map.specification_pages)}")
        logger.info(f"  Drawing pages: {len(doc_map.drawing_pages)}")
        logger.info(f"  Sections identified: {list(doc_map.sections.keys())}")
        logger.info(f"  Processing order (first 10): {doc_map.processing_order[:10]}")

        # Count by content type
        type_counts = {}
        for page in doc_map.pages:
            content_type = page.content_type.value
            type_counts[content_type] = type_counts.get(content_type, 0) + 1

        logger.info(f"  Content type distribution: {type_counts}")


# Convenience functions

def analyze_pdf(pdf_path: str) -> DocumentMap:
    """Quick analysis of a PDF document"""
    analyzer = DocumentStructureAnalyzer()
    return analyzer.analyze_document_structure(pdf_path)


def get_priority_pages(pdf_path: str, max_pages: int = 20) -> List[int]:
    """Get top priority pages from a document"""
    doc_map = analyze_pdf(pdf_path)
    return doc_map.processing_order[:max_pages]


def find_boq_pages(pdf_path: str) -> List[int]:
    """Find all BOQ pages in a document"""
    doc_map = analyze_pdf(pdf_path)
    return doc_map.boq_pages
