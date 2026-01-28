"""
Intelligent Table Extractor
Extracts tables from construction documents with proper structure preservation
"""

import pandas as pd
import tabula
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTable:
    """Represents an extracted table with metadata"""
    page_num: int
    table_index: int  # Multiple tables per page
    headers: List[str]
    rows: List[List[str]]
    table_type: str  # 'boq', 'schedule', 'specification', 'unknown'
    confidence: float = 0.0
    row_count: int = 0
    column_count: int = 0

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame"""
        return pd.DataFrame(self.rows, columns=self.headers)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'page_num': self.page_num,
            'table_type': self.table_type,
            'headers': self.headers,
            'rows': self.rows,
            'confidence': self.confidence,
            'row_count': self.row_count,
            'column_count': self.column_count
        }


@dataclass
class BOQItem:
    """Structured BOQ item extracted from table"""
    item_no: str
    description: str
    unit: str
    quantity: float
    rate: float = 0.0
    amount: float = 0.0
    specification: Optional[str] = None
    cpwd_code: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'item': self.item_no,
            'description': self.description,
            'qty': self.quantity,
            'unit': self.unit,
            'rate': self.rate,
            'amount': self.amount,
            'specification': self.specification,
            'cpwd_code': self.cpwd_code
        }


class IntelligentTableExtractor:
    """
    Extracts tables from construction documents with intelligence
    Handles various BOQ formats and standardizes output
    """

    # Common BOQ column patterns
    BOQ_COLUMN_PATTERNS = {
        'item_no': r'(item\s*no|sr\.?\s*no|s\.?\s*no|item|no)',
        'description': r'(description|particulars|item\s*of\s*work|work\s*description|specification)',
        'unit': r'(unit|uom|u\.?o\.?m)',
        'quantity': r'(quantity|qty|nos)',
        'rate': r'(rate|unit\s*rate|rate\s*per)',
        'amount': r'(amount|total|value)'
    }

    # Common units in construction
    STANDARD_UNITS = ['cum', 'sqm', 'rmt', 'm', 'kg', 'nos', 'ls', 'each', 'set', 'tonne', 'litre']

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns"""
        return {key: re.compile(pattern, re.IGNORECASE)
                for key, pattern in self.BOQ_COLUMN_PATTERNS.items()}

    def extract_tables_from_pdf(self, pdf_path: str, pages: Optional[List[int]] = None) -> List[ExtractedTable]:
        """
        Extract all tables from PDF

        Args:
            pdf_path: Path to PDF file
            pages: Specific pages to extract from (None = all pages)

        Returns:
            List of ExtractedTable objects
        """
        extracted_tables = []

        try:
            # Use tabula to extract tables
            # Try multiple extraction methods for robustness

            # Method 1: Stream method (for tables with borders)
            tables_stream = self._extract_with_tabula(pdf_path, pages, method='stream')
            extracted_tables.extend(tables_stream)

            # Method 2: Lattice method (for tables without borders)
            if len(tables_stream) == 0:
                tables_lattice = self._extract_with_tabula(pdf_path, pages, method='lattice')
                extracted_tables.extend(tables_lattice)

            logger.info(f"Extracted {len(extracted_tables)} tables from PDF")

            # Classify each table
            for table in extracted_tables:
                table.table_type = self._classify_table(table)
                logger.debug(f"Page {table.page_num}, Table {table.table_index}: {table.table_type} ({table.row_count} rows)")

            return extracted_tables

        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []

    def _extract_with_tabula(self, pdf_path: str, pages: Optional[List[int]], method: str) -> List[ExtractedTable]:
        """Extract tables using tabula with specified method"""
        extracted = []

        try:
            # Read tables using tabula
            if pages:
                page_str = ','.join([str(p + 1) for p in pages])  # tabula uses 1-indexed pages
                dfs = tabula.read_pdf(pdf_path, pages=page_str, multiple_tables=True, lattice=(method == 'lattice'))
            else:
                dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, lattice=(method == 'lattice'))

            # Convert to ExtractedTable objects
            for idx, df in enumerate(dfs):
                if df.empty:
                    continue

                # Clean DataFrame
                df = self._clean_dataframe(df)

                # Extract headers and rows
                headers = [str(col).strip() for col in df.columns]
                rows = df.values.tolist()

                # Create ExtractedTable
                table = ExtractedTable(
                    page_num=0,  # tabula doesn't provide page number easily
                    table_index=idx,
                    headers=headers,
                    rows=rows,
                    table_type='unknown',
                    row_count=len(rows),
                    column_count=len(headers)
                )

                extracted.append(table)

        except Exception as e:
            logger.warning(f"Tabula extraction ({method}) failed: {e}")

        return extracted

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean extracted DataFrame"""
        # Remove completely empty rows
        df = df.dropna(how='all')

        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')

        # Fill NaN with empty strings
        df = df.fillna('')

        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        return df

    def _classify_table(self, table: ExtractedTable) -> str:
        """
        Classify table type based on headers and content

        Returns:
            'boq', 'schedule', 'specification', or 'unknown'
        """
        # Combine headers for analysis
        headers_text = ' '.join(table.headers).lower()

        # Check for BOQ indicators
        boq_score = 0
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern.search(headers_text):
                boq_score += 1

        # BOQ tables typically have at least 4-5 key columns
        if boq_score >= 4:
            return 'boq'

        # Check for schedule patterns
        if 'schedule' in headers_text or 'timeline' in headers_text:
            return 'schedule'

        # Check for specification patterns
        if 'specification' in headers_text or 'standard' in headers_text:
            return 'specification'

        return 'unknown'

    def parse_boq_table(self, table: ExtractedTable) -> List[BOQItem]:
        """
        Parse a BOQ table into structured BOQItem objects

        Args:
            table: ExtractedTable identified as BOQ type

        Returns:
            List of BOQItem objects
        """
        boq_items = []

        try:
            # Map columns to BOQ fields
            column_mapping = self._map_boq_columns(table.headers)

            logger.debug(f"Column mapping: {column_mapping}")

            # Parse each row
            for row_idx, row in enumerate(table.rows):
                try:
                    boq_item = self._parse_boq_row(row, column_mapping)
                    if boq_item:
                        boq_items.append(boq_item)
                except Exception as e:
                    logger.warning(f"Error parsing row {row_idx}: {e}")
                    continue

            logger.info(f"Parsed {len(boq_items)} BOQ items from table")

        except Exception as e:
            logger.error(f"Error parsing BOQ table: {e}")

        return boq_items

    def _map_boq_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        Map table columns to BOQ fields

        Returns:
            Dictionary mapping field_name -> column_index
        """
        mapping = {}

        for col_idx, header in enumerate(headers):
            header_lower = header.lower()

            # Try to match each BOQ field pattern
            for field_name, pattern in self.compiled_patterns.items():
                if pattern.search(header_lower):
                    mapping[field_name] = col_idx
                    break

        return mapping

    def _parse_boq_row(self, row: List[str], column_mapping: Dict[str, int]) -> Optional[BOQItem]:
        """Parse a single BOQ row"""

        # Extract values based on column mapping
        item_no = self._get_column_value(row, column_mapping, 'item_no', '')
        description = self._get_column_value(row, column_mapping, 'description', '')
        unit = self._get_column_value(row, column_mapping, 'unit', '')
        quantity_str = self._get_column_value(row, column_mapping, 'quantity', '0')
        rate_str = self._get_column_value(row, column_mapping, 'rate', '0')
        amount_str = self._get_column_value(row, column_mapping, 'amount', '0')

        # Skip if description is empty (likely header or total row)
        if not description or len(description) < 3:
            return None

        # Skip total/subtotal rows
        if re.match(r'(total|sub\s*total|grand\s*total)', description, re.IGNORECASE):
            return None

        # Parse numeric values
        quantity = self._parse_number(quantity_str)
        rate = self._parse_number(rate_str)
        amount = self._parse_number(amount_str)

        # Validate: quantity should be > 0
        if quantity <= 0:
            return None

        # Standardize unit
        unit = self._standardize_unit(unit)

        # Calculate amount if missing
        if amount == 0 and rate > 0 and quantity > 0:
            amount = quantity * rate

        return BOQItem(
            item_no=item_no,
            description=description,
            unit=unit,
            quantity=quantity,
            rate=rate,
            amount=amount
        )

    def _get_column_value(self, row: List[str], mapping: Dict[str, int], field: str, default: str) -> str:
        """Get value from row using column mapping"""
        if field in mapping:
            col_idx = mapping[field]
            if col_idx < len(row):
                return str(row[col_idx]).strip()
        return default

    def _parse_number(self, value: str) -> float:
        """Parse numeric value from string"""
        try:
            # Remove common separators and symbols
            cleaned = re.sub(r'[,\s₹$]', '', value)
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _standardize_unit(self, unit: str) -> str:
        """Standardize unit to common format"""
        unit_lower = unit.lower().strip()

        # Remove periods
        unit_lower = unit_lower.replace('.', '')

        # Common abbreviations
        unit_map = {
            'cubic meter': 'cum',
            'cu m': 'cum',
            'cum': 'cum',
            'square meter': 'sqm',
            'sq m': 'sqm',
            'sqm': 'sqm',
            'running meter': 'rmt',
            'rmt': 'rmt',
            'meter': 'm',
            'metre': 'm',
            'm': 'm',
            'kilogram': 'kg',
            'kg': 'kg',
            'number': 'nos',
            'nos': 'nos',
            'each': 'each',
            'lumpsum': 'ls',
            'ls': 'ls',
            'litre': 'litre',
            'ltr': 'litre'
        }

        return unit_map.get(unit_lower, unit_lower)

    def extract_boq_from_pdf(self, pdf_path: str, boq_pages: Optional[List[int]] = None) -> List[BOQItem]:
        """
        High-level function to extract BOQ from PDF

        Args:
            pdf_path: Path to PDF
            boq_pages: Specific pages with BOQ (None = auto-detect)

        Returns:
            List of BOQItem objects
        """
        # Extract tables
        tables = self.extract_tables_from_pdf(pdf_path, pages=boq_pages)

        # Filter BOQ tables
        boq_tables = [t for t in tables if t.table_type == 'boq']

        if not boq_tables:
            logger.warning("No BOQ tables found, trying all tables")
            boq_tables = tables  # Try all tables

        # Parse BOQ items from each table
        all_boq_items = []
        for table in boq_tables:
            items = self.parse_boq_table(table)
            all_boq_items.extend(items)

        logger.info(f"Total BOQ items extracted: {len(all_boq_items)}")

        return all_boq_items


# Convenience functions

def extract_boq(pdf_path: str) -> List[BOQItem]:
    """Quick extraction of BOQ from PDF"""
    extractor = IntelligentTableExtractor()
    return extractor.extract_boq_from_pdf(pdf_path)


def extract_tables(pdf_path: str, pages: Optional[List[int]] = None) -> List[ExtractedTable]:
    """Quick extraction of all tables"""
    extractor = IntelligentTableExtractor()
    return extractor.extract_tables_from_pdf(pdf_path, pages)
