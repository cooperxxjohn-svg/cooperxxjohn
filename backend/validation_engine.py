"""
Validation Engine
Confidence scoring, validation, and quality assurance for extracted BOQ data
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation issues"""
    MISSING_DATA = "missing_data"
    INVALID_FORMAT = "invalid_format"
    SUSPICIOUS_VALUE = "suspicious_value"
    CPWD_COMPLIANCE = "cpwd_compliance"
    CONSISTENCY = "consistency"
    DUPLICATE = "duplicate"


@dataclass
class ValidationIssue:
    """A single validation issue"""
    level: ValidationLevel
    category: ValidationCategory
    field: str
    message: str
    item_index: Optional[int] = None
    suggested_fix: Optional[str] = None
    confidence_impact: float = 0.1  # How much this affects confidence (0-1)

    def to_dict(self) -> Dict:
        return {
            'level': self.level.value,
            'category': self.category.value,
            'field': self.field,
            'message': self.message,
            'item_index': self.item_index,
            'suggested_fix': self.suggested_fix
        }


@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    overall_confidence: float  # 0-1
    field_confidences: Dict[str, float]
    issues: List[ValidationIssue]
    summary: Dict
    uncertain_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'is_valid': self.is_valid,
            'overall_confidence': self.overall_confidence,
            'field_confidences': self.field_confidences,
            'issues': [issue.to_dict() for issue in self.issues],
            'summary': self.summary,
            'uncertain_fields': self.uncertain_fields
        }


@dataclass
class ConfidenceScores:
    """Confidence scores for a BOQ item"""
    material_name: float
    specification: float
    quantity: float
    unit: float
    rate: float
    amount: float
    overall: float


class ValidationEngine:
    """
    Validates extracted BOQ data and assigns confidence scores
    """

    # CPWD standard units
    CPWD_UNITS = ['cum', 'sqm', 'rmt', 'm', 'kg', 'tonne', 'nos', 'ls', 'each', 'litre']

    # Reasonable ranges for common items
    QUANTITY_RANGES = {
        'excavation': (10, 10000),  # cum
        'concrete': (1, 5000),  # cum
        'brick masonry': (10, 5000),  # cum
        'plastering': (10, 10000),  # sqm
        'flooring': (10, 5000),  # sqm
        'painting': (10, 10000),  # sqm
        'steel': (100, 100000),  # kg
    }

    # Rate ranges (INR) for common items
    RATE_RANGES = {
        'excavation': (100, 500),  # per cum
        'concrete': (4000, 12000),  # per cum
        'brick masonry': (3000, 8000),  # per cum
        'plastering': (150, 400),  # per sqm
        'flooring': (200, 2000),  # per sqm
        'painting': (50, 300),  # per sqm
        'steel': (50, 150),  # per kg
    }

    # Common CPWD item codes
    CPWD_ITEM_PATTERNS = {
        'earthwork': r'^1\.\d+',
        'concrete': r'^10\.\d+',
        'formwork': r'^11\.\d+',
        'reinforcement': r'^12\.\d+',
        'masonry': r'^6\.\d+',
        'plastering': r'^13\.\d+',
        'flooring': r'^16\.\d+',
        'painting': r'^19\.\d+',
    }

    def __init__(self):
        pass

    def score_extraction_confidence(self, item: Dict) -> ConfidenceScores:
        """
        Score confidence for each field in a BOQ item

        Args:
            item: BOQ item dictionary

        Returns:
            ConfidenceScores object
        """
        scores = {
            'material_name': self._score_material_name(item.get('description', '')),
            'specification': self._score_specification(item.get('description', ''), item.get('specification', '')),
            'quantity': self._score_quantity(item.get('qty', 0), item.get('description', '')),
            'unit': self._score_unit(item.get('unit', '')),
            'rate': self._score_rate(item.get('rate', 0), item.get('description', ''), item.get('unit', '')),
            'amount': self._score_amount(item.get('qty', 0), item.get('rate', 0), item.get('amount', 0))
        }

        # Calculate overall confidence (weighted average)
        overall = (
            scores['material_name'] * 0.25 +
            scores['specification'] * 0.15 +
            scores['quantity'] * 0.20 +
            scores['unit'] * 0.15 +
            scores['rate'] * 0.15 +
            scores['amount'] * 0.10
        )

        return ConfidenceScores(
            material_name=scores['material_name'],
            specification=scores['specification'],
            quantity=scores['quantity'],
            unit=scores['unit'],
            rate=scores['rate'],
            amount=scores['amount'],
            overall=overall
        )

    def _score_material_name(self, description: str) -> float:
        """Score confidence in material name extraction"""
        if not description or len(description) < 5:
            return 0.2

        # Check if contains common construction terms
        construction_terms = [
            'excavation', 'concrete', 'cement', 'masonry', 'brick', 'plastering',
            'flooring', 'roofing', 'steel', 'reinforcement', 'painting', 'finishing',
            'plumbing', 'electrical', 'drainage', 'tile', 'marble', 'granite'
        ]

        terms_found = sum(1 for term in construction_terms if term in description.lower())

        if terms_found > 0:
            return min(0.7 + (terms_found * 0.1), 0.98)
        else:
            # Has reasonable length and structure
            if len(description) > 10 and len(description) < 200:
                return 0.6
            else:
                return 0.4

    def _score_specification(self, description: str, specification: str) -> float:
        """Score confidence in specification extraction"""
        spec_text = specification if specification else description

        if not spec_text:
            return 0.3

        # Check for detailed specification indicators
        indicators = [
            r'\d+mm',  # Dimensions (230mm)
            r'\d+:\d+',  # Ratios (1:4)
            r'grade',  # Material grade
            r'class',  # Classification
            r'fps',  # Strength (FPS)
            r'IS\s*\d+',  # IS codes
            r'specification',  # Explicit mention
        ]

        matches = sum(1 for pattern in indicators if re.search(pattern, spec_text, re.IGNORECASE))

        base_score = 0.5
        bonus = min(matches * 0.15, 0.45)

        return min(base_score + bonus, 0.95)

    def _score_quantity(self, quantity: float, description: str) -> float:
        """Score confidence in quantity value"""
        if quantity <= 0:
            return 0.1

        # Check if quantity is in reasonable range for the item type
        for item_type, (min_qty, max_qty) in self.QUANTITY_RANGES.items():
            if item_type in description.lower():
                if min_qty <= quantity <= max_qty:
                    return 0.92
                elif quantity < min_qty * 0.1 or quantity > max_qty * 10:
                    return 0.4  # Very suspicious
                else:
                    return 0.7  # Outside typical range but possible

        # Default: quantity present and reasonable magnitude
        if 0.1 <= quantity <= 1000000:
            return 0.75
        else:
            return 0.5

    def _score_unit(self, unit: str) -> float:
        """Score confidence in unit"""
        if not unit:
            return 0.2

        unit_lower = unit.lower().strip()

        # Exact match with CPWD units
        if unit_lower in self.CPWD_UNITS:
            return 0.99

        # Close match (common variations)
        variations = {
            'cubic meter': 'cum',
            'square meter': 'sqm',
            'running meter': 'rmt',
            'meter': 'm',
            'kilogram': 'kg',
            'number': 'nos',
            'lumpsum': 'ls'
        }

        if unit_lower in variations:
            return 0.95

        # Has unit but non-standard
        if len(unit) > 0:
            return 0.6
        else:
            return 0.2

    def _score_rate(self, rate: float, description: str, unit: str) -> float:
        """Score confidence in rate value"""
        if rate <= 0:
            return 0.3  # Rate might be determined later

        # Check against typical rates
        for item_type, (min_rate, max_rate) in self.RATE_RANGES.items():
            if item_type in description.lower():
                if min_rate <= rate <= max_rate:
                    return 0.90
                elif rate < min_rate * 0.1 or rate > max_rate * 10:
                    return 0.3  # Very suspicious
                else:
                    return 0.6  # Outside typical range

        # Default: rate present and reasonable
        if 10 <= rate <= 100000:
            return 0.70
        elif rate > 0:
            return 0.50
        else:
            return 0.3

    def _score_amount(self, quantity: float, rate: float, amount: float) -> float:
        """Score confidence in amount calculation"""
        if amount <= 0:
            return 0.3

        # Check if amount = qty × rate
        if quantity > 0 and rate > 0:
            expected_amount = quantity * rate
            difference = abs(amount - expected_amount) / expected_amount if expected_amount > 0 else 1

            if difference < 0.01:  # Within 1%
                return 0.99
            elif difference < 0.05:  # Within 5%
                return 0.90
            elif difference < 0.10:  # Within 10%
                return 0.75
            else:
                return 0.5

        # Amount present but can't verify
        return 0.70

    def validate_item(self, item: Dict, index: int) -> Tuple[ConfidenceScores, List[ValidationIssue]]:
        """
        Validate a single BOQ item

        Args:
            item: BOQ item dictionary
            index: Item index in the list

        Returns:
            Tuple of (ConfidenceScores, List[ValidationIssue])
        """
        issues = []

        # Score confidence
        confidence = self.score_extraction_confidence(item)

        # Check for missing required fields
        required_fields = ['description', 'qty', 'unit']
        for field in required_fields:
            if not item.get(field):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.MISSING_DATA,
                    field=field,
                    message=f"Missing required field: {field}",
                    item_index=index
                ))

        # Validate unit
        unit = item.get('unit', '').lower()
        if unit and unit not in self.CPWD_UNITS:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.CPWD_COMPLIANCE,
                field='unit',
                message=f"Non-standard unit: {unit}",
                item_index=index,
                suggested_fix=self._suggest_unit_fix(unit)
            ))

        # Validate quantity
        qty = item.get('qty', 0)
        if qty <= 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.INVALID_FORMAT,
                field='qty',
                message="Quantity must be greater than 0",
                item_index=index
            ))
        elif qty > 1000000:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SUSPICIOUS_VALUE,
                field='qty',
                message=f"Very large quantity: {qty}",
                item_index=index
            ))

        # Validate rate
        rate = item.get('rate', 0)
        if rate < 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.INVALID_FORMAT,
                field='rate',
                message="Rate cannot be negative",
                item_index=index
            ))
        elif rate > 1000000:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SUSPICIOUS_VALUE,
                field='rate',
                message=f"Very high rate: ₹{rate}",
                item_index=index
            ))

        # Validate amount calculation
        amount = item.get('amount', 0)
        if qty > 0 and rate > 0:
            expected = qty * rate
            if abs(amount - expected) / expected > 0.10 if expected > 0 else True:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.CONSISTENCY,
                    field='amount',
                    message=f"Amount ({amount}) doesn't match qty × rate ({expected:.2f})",
                    item_index=index,
                    suggested_fix=f"₹{expected:.2f}"
                ))

        return confidence, issues

    def _suggest_unit_fix(self, unit: str) -> Optional[str]:
        """Suggest standardized unit"""
        unit_map = {
            'cubic meter': 'cum',
            'cu.m': 'cum',
            'square meter': 'sqm',
            'sq.m': 'sqm',
            'running meter': 'rmt',
            'r.m': 'rmt',
            'meter': 'm',
            'kilogram': 'kg',
            'number': 'nos',
            'lumpsum': 'ls'
        }
        return unit_map.get(unit.lower())

    def validate_document(self, boq_items: List[Dict]) -> ValidationResult:
        """
        Validate complete BOQ document

        Args:
            boq_items: List of BOQ items

        Returns:
            ValidationResult with complete validation
        """
        all_issues = []
        all_confidences = []
        field_confidence_totals = {
            'material_name': [],
            'specification': [],
            'quantity': [],
            'unit': [],
            'rate': [],
            'amount': []
        }

        # Validate each item
        for idx, item in enumerate(boq_items):
            confidence, issues = self.validate_item(item, idx)
            all_issues.extend(issues)
            all_confidences.append(confidence.overall)

            # Collect field confidences
            field_confidence_totals['material_name'].append(confidence.material_name)
            field_confidence_totals['specification'].append(confidence.specification)
            field_confidence_totals['quantity'].append(confidence.quantity)
            field_confidence_totals['unit'].append(confidence.unit)
            field_confidence_totals['rate'].append(confidence.rate)
            field_confidence_totals['amount'].append(confidence.amount)

        # Check for duplicates
        duplicate_issues = self._detect_duplicates(boq_items)
        all_issues.extend(duplicate_issues)

        # Calculate overall confidence
        overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        # Calculate field confidences
        field_confidences = {
            field: sum(scores) / len(scores) if scores else 0.0
            for field, scores in field_confidence_totals.items()
        }

        # Identify uncertain fields
        uncertain_fields = [
            field for field, conf in field_confidences.items()
            if conf < 0.7
        ]

        # Generate summary
        summary = {
            'total_items': len(boq_items),
            'issues_found': len(all_issues),
            'critical_issues': len([i for i in all_issues if i.level == ValidationLevel.CRITICAL]),
            'errors': len([i for i in all_issues if i.level == ValidationLevel.ERROR]),
            'warnings': len([i for i in all_issues if i.level == ValidationLevel.WARNING]),
            'average_confidence': overall_confidence,
            'high_confidence_items': len([c for c in all_confidences if c > 0.8]),
            'low_confidence_items': len([c for c in all_confidences if c < 0.5])
        }

        # Determine if valid
        is_valid = (
            summary['critical_issues'] == 0 and
            summary['errors'] == 0 and
            overall_confidence > 0.6
        )

        return ValidationResult(
            is_valid=is_valid,
            overall_confidence=overall_confidence,
            field_confidences=field_confidences,
            issues=all_issues,
            summary=summary,
            uncertain_fields=uncertain_fields
        )

    def _detect_duplicates(self, boq_items: List[Dict]) -> List[ValidationIssue]:
        """Detect duplicate or very similar BOQ items"""
        issues = []
        seen_descriptions = {}

        for idx, item in enumerate(boq_items):
            desc = item.get('description', '').lower().strip()

            if desc in seen_descriptions:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.DUPLICATE,
                    field='description',
                    message=f"Duplicate item found (similar to item {seen_descriptions[desc]})",
                    item_index=idx
                ))
            else:
                seen_descriptions[desc] = idx

        return issues


# Convenience functions

def validate_boq(boq_items: List[Dict]) -> ValidationResult:
    """Quick validation of BOQ items"""
    engine = ValidationEngine()
    return engine.validate_document(boq_items)


def score_item_confidence(item: Dict) -> ConfidenceScores:
    """Quick confidence scoring for single item"""
    engine = ValidationEngine()
    return engine.score_extraction_confidence(item)
