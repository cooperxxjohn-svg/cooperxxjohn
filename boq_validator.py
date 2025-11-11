"""
BOQ Validator - CPWD Compliance Validation
Validates BOQ items against CPWD standards and specifications

This module ensures all BOQ items comply with CPWD norms, specifications,
and government contracting requirements.
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from enum import Enum
import logging

from boq_schema import (
    BOQLineItem, BOQSection, BOQDocument, WorkCategory,
    UnitType, MaterialGrade
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "ERROR"  # Must be fixed
    WARNING = "WARNING"  # Should be reviewed
    INFO = "INFO"  # Informational


class ValidationResult:
    """Result of a validation check"""

    def __init__(
        self,
        severity: ValidationSeverity,
        rule_code: str,
        message: str,
        item_no: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.severity = severity
        self.rule_code = rule_code
        self.message = message
        self.item_no = item_no
        self.suggestion = suggestion

    def __repr__(self):
        item_ref = f"[{self.item_no}] " if self.item_no else ""
        return f"{self.severity.value}: {item_ref}{self.message} (Rule: {self.rule_code})"

    def to_dict(self) -> dict:
        return {
            'severity': self.severity.value,
            'rule_code': self.rule_code,
            'message': self.message,
            'item_no': self.item_no,
            'suggestion': self.suggestion
        }


class CPWDValidator:
    """Main validator for CPWD compliance"""

    # CPWD limits and standards
    MAX_OVERHEAD_PERCENTAGE = Decimal("20.0")
    MAX_PROFIT_PERCENTAGE = Decimal("12.0")
    MIN_WASTAGE_PERCENTAGE = Decimal("0.0")
    MAX_WASTAGE_PERCENTAGE = Decimal("20.0")

    # Standard concrete grades for different applications
    CONCRETE_GRADE_APPLICATIONS = {
        'foundation': [MaterialGrade.M15, MaterialGrade.M20, MaterialGrade.M25],
        'column': [MaterialGrade.M20, MaterialGrade.M25, MaterialGrade.M30],
        'beam': [MaterialGrade.M20, MaterialGrade.M25, MaterialGrade.M30],
        'slab': [MaterialGrade.M20, MaterialGrade.M25, MaterialGrade.M30],
        'pcc': [MaterialGrade.M10, MaterialGrade.M15],
    }

    # Minimum quantities that require justification
    MIN_QUANTITY_THRESHOLDS = {
        UnitType.CUBIC_METER: Decimal("0.01"),
        UnitType.SQUARE_METER: Decimal("0.1"),
        UnitType.METER: Decimal("0.1"),
        UnitType.KILOGRAM: Decimal("0.5"),
    }

    def __init__(self):
        self.validation_results: List[ValidationResult] = []

    def validate_document(self, boq_doc: BOQDocument) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate entire BOQ document

        Returns:
            Tuple of (is_valid, validation_results)
        """
        self.validation_results = []

        # Document level validations
        self._validate_document_structure(boq_doc)
        self._validate_contract_details(boq_doc)

        # Section and item validations
        for section in boq_doc.sections:
            self._validate_section(section)
            for item in section.items:
                self._validate_item(item)

        # Check for errors
        has_errors = any(r.severity == ValidationSeverity.ERROR for r in self.validation_results)

        return (not has_errors, self.validation_results)

    def _validate_document_structure(self, boq_doc: BOQDocument):
        """Validate document structure and metadata"""

        # Check BOQ ID format
        if not boq_doc.boq_id:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="DOC001",
                message="BOQ document must have a unique BOQ ID",
                suggestion="Assign a unique identifier like 'BOQ-2024-001'"
            ))

        # Check sections exist
        if not boq_doc.sections:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="DOC002",
                message="BOQ document must contain at least one section",
                suggestion="Add work sections to the BOQ"
            ))

        # Validate GST percentage
        if boq_doc.gst_percentage < 0 or boq_doc.gst_percentage > 28:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="DOC003",
                message=f"GST percentage {boq_doc.gst_percentage}% seems unusual (standard is 18% for construction)",
                suggestion="Verify GST rate as per current tax laws"
            ))

    def _validate_contract_details(self, boq_doc: BOQDocument):
        """Validate contract metadata"""

        contract = boq_doc.contract

        # Check required fields
        if not contract.contract_name:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="CON001",
                message="Contract name is required",
                suggestion="Provide contract/project name"
            ))

        if not contract.location:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="CON002",
                message="Contract location should be specified",
                suggestion="Add project location for regional rate applicability"
            ))

        # Validate completion period
        if contract.completion_period_days:
            if contract.completion_period_days <= 0:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    rule_code="CON003",
                    message="Completion period must be positive",
                    suggestion="Specify valid completion period in days"
                ))
            elif contract.completion_period_days > 1825:  # 5 years
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    rule_code="CON004",
                    message=f"Completion period of {contract.completion_period_days} days (>5 years) seems unusually long",
                    suggestion="Verify completion period"
                ))

    def _validate_section(self, section: BOQSection):
        """Validate BOQ section"""

        # Check section has items
        if not section.items:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="SEC001",
                message=f"Section {section.section_no} '{section.title}' has no items",
                suggestion="Add items or remove empty section"
            ))

        # Check section numbering
        if not section.section_no:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="SEC002",
                message=f"Section '{section.title}' missing section number",
                suggestion="Assign section number (e.g., '1', '2.1')"
            ))

    def _validate_item(self, item: BOQLineItem):
        """Validate individual BOQ line item"""

        # Item number validation
        self._validate_item_number(item)

        # Description validation
        self._validate_description(item)

        # Quantity validation
        self._validate_quantity(item)

        # Rate validation
        self._validate_rates(item)

        # Material validation
        self._validate_materials(item)

        # Labour validation
        self._validate_labour(item)

        # Specification validation
        self._validate_specifications(item)

        # Category-specific validation
        self._validate_category_specific(item)

    def _validate_item_number(self, item: BOQLineItem):
        """Validate item numbering"""
        if not item.item_no:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="ITEM001",
                message="Item number is required",
                suggestion="Assign sequential item number"
            ))

    def _validate_description(self, item: BOQLineItem):
        """Validate item description"""
        if not item.description or len(item.description) < 10:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="ITEM002",
                message=f"Item description too short or missing",
                item_no=item.item_no,
                suggestion="Provide detailed description (minimum 10 characters)"
            ))

        # Check for complete specification
        if not item.specification:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="ITEM003",
                message="Item specification missing",
                item_no=item.item_no,
                suggestion="Add detailed specification referencing standards"
            ))

    def _validate_quantity(self, item: BOQLineItem):
        """Validate quantities"""

        # Check quantity is positive
        if item.quantity <= 0:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="QTY001",
                message=f"Quantity must be positive (found: {item.quantity})",
                item_no=item.item_no,
                suggestion="Correct quantity value"
            ))

        # Check for suspiciously small quantities
        threshold = self.MIN_QUANTITY_THRESHOLDS.get(item.unit, Decimal("0"))
        if threshold and item.quantity < threshold:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="QTY002",
                message=f"Quantity {item.quantity} {item.unit.value} is very small",
                item_no=item.item_no,
                suggestion="Verify quantity or combine with similar items"
            ))

        # Check for very large quantities (potential error)
        if item.quantity > 100000:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="QTY003",
                message=f"Quantity {item.quantity} seems unusually large",
                item_no=item.item_no,
                suggestion="Verify quantity calculation"
            ))

    def _validate_rates(self, item: BOQLineItem):
        """Validate rates and amounts"""

        # Unit rate should be positive
        if item.unit_rate <= 0:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="RATE001",
                message=f"Unit rate must be positive (found: {item.unit_rate})",
                item_no=item.item_no,
                suggestion="Calculate or assign unit rate"
            ))

        # Verify amount calculation
        calculated_amount = item.quantity * item.unit_rate
        if abs(calculated_amount - item.total_amount) > Decimal("0.01"):
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                rule_code="RATE002",
                message=f"Total amount mismatch: {item.total_amount} vs calculated {calculated_amount}",
                item_no=item.item_no,
                suggestion="Recalculate total amount = quantity × unit rate"
            ))

        # Check overhead percentage
        if item.overhead_percentage > self.MAX_OVERHEAD_PERCENTAGE:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="RATE003",
                message=f"Overhead {item.overhead_percentage}% exceeds typical CPWD limit of {self.MAX_OVERHEAD_PERCENTAGE}%",
                item_no=item.item_no,
                suggestion="Review overhead percentage"
            ))

        # Check profit percentage
        if item.profit_percentage > self.MAX_PROFIT_PERCENTAGE:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="RATE004",
                message=f"Profit {item.profit_percentage}% exceeds typical CPWD limit of {self.MAX_PROFIT_PERCENTAGE}%",
                item_no=item.item_no,
                suggestion="Review profit percentage"
            ))

    def _validate_materials(self, item: BOQLineItem):
        """Validate material specifications"""

        for material in item.materials:
            # Check wastage
            if material.wastage_percentage > self.MAX_WASTAGE_PERCENTAGE:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    rule_code="MAT001",
                    message=f"Material '{material.name}' wastage {material.wastage_percentage}% seems high",
                    item_no=item.item_no,
                    suggestion=f"Typical wastage is 2-10%, verify {material.wastage_percentage}%"
                ))

            # Check specification exists
            if not material.specification:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    rule_code="MAT002",
                    message=f"Material '{material.name}' missing specification/IS code",
                    item_no=item.item_no,
                    suggestion="Add IS code or standard specification"
                ))

            # Check quantity is positive
            if material.quantity <= 0:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    rule_code="MAT003",
                    message=f"Material '{material.name}' quantity must be positive",
                    item_no=item.item_no,
                    suggestion="Correct material quantity"
                ))

    def _validate_labour(self, item: BOQLineItem):
        """Validate labour specifications"""

        for labour_item in item.labour:
            if labour_item.quantity <= 0:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    rule_code="LAB001",
                    message=f"Labour '{labour_item.category}' quantity must be positive",
                    item_no=item.item_no,
                    suggestion="Correct labour quantity"
                ))

            # Check rate reasonableness (basic sanity check)
            if labour_item.rate and labour_item.rate > 5000:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    rule_code="LAB002",
                    message=f"Labour rate ₹{labour_item.rate} seems high",
                    item_no=item.item_no,
                    suggestion="Verify labour rate against DSR"
                ))

    def _validate_specifications(self, item: BOQLineItem):
        """Validate technical specifications"""

        # Check for reference standard
        if not item.reference_standard:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                rule_code="SPEC001",
                message="Reference standard/IS code not specified",
                item_no=item.item_no,
                suggestion="Add IS code or CPWD specification reference"
            ))

        # Check for drawing reference (for major items)
        if item.category in [WorkCategory.CONCRETE_WORK, WorkCategory.MASONRY, WorkCategory.EARTHWORK]:
            if not item.drawing_reference:
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    rule_code="SPEC002",
                    message="Drawing reference not provided",
                    item_no=item.item_no,
                    suggestion="Add drawing number for traceability"
                ))

    def _validate_category_specific(self, item: BOQLineItem):
        """Category-specific validations"""

        if item.category == WorkCategory.CONCRETE_WORK:
            self._validate_concrete_item(item)
        elif item.category == WorkCategory.EARTHWORK:
            self._validate_earthwork_item(item)
        elif item.category == WorkCategory.REINFORCEMENT:
            self._validate_reinforcement_item(item)

    def _validate_concrete_item(self, item: BOQLineItem):
        """Validate concrete work items"""

        # Check for cement in materials
        has_cement = any('cement' in m.name.lower() for m in item.materials)
        if not has_cement and 'concrete' in item.description.lower():
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="CONC001",
                message="Concrete item should include cement in material breakdown",
                item_no=item.item_no,
                suggestion="Add cement, sand, aggregate materials"
            ))

        # Check unit
        if item.unit != UnitType.CUBIC_METER:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="CONC002",
                message=f"Concrete work typically measured in {UnitType.CUBIC_METER.value}, found {item.unit.value}",
                item_no=item.item_no,
                suggestion="Verify unit of measurement"
            ))

    def _validate_earthwork_item(self, item: BOQLineItem):
        """Validate earthwork items"""

        # Check unit
        if item.unit not in [UnitType.CUBIC_METER, UnitType.SQUARE_METER]:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="EW001",
                message=f"Earthwork typically measured in cum or sqm, found {item.unit.value}",
                item_no=item.item_no,
                suggestion="Verify unit of measurement"
            ))

    def _validate_reinforcement_item(self, item: BOQLineItem):
        """Validate steel reinforcement items"""

        # Check unit
        if item.unit not in [UnitType.KILOGRAM, UnitType.METRIC_TON]:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="STEEL001",
                message=f"Steel reinforcement typically measured in kg or MT, found {item.unit.value}",
                item_no=item.item_no,
                suggestion="Verify unit of measurement"
            ))

        # Check for steel material
        has_steel = any('steel' in m.name.lower() or 'tmt' in m.name.lower() for m in item.materials)
        if not has_steel:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                rule_code="STEEL002",
                message="Reinforcement item should include steel/TMT in materials",
                item_no=item.item_no,
                suggestion="Add TMT steel material"
            ))

    def get_validation_summary(self) -> Dict[str, int]:
        """Get summary of validation results"""
        summary = {
            'total_issues': len(self.validation_results),
            'errors': sum(1 for r in self.validation_results if r.severity == ValidationSeverity.ERROR),
            'warnings': sum(1 for r in self.validation_results if r.severity == ValidationSeverity.WARNING),
            'info': sum(1 for r in self.validation_results if r.severity == ValidationSeverity.INFO),
        }
        return summary

    def print_validation_report(self):
        """Print formatted validation report"""
        summary = self.get_validation_summary()

        print("\n" + "=" * 80)
        print("BOQ VALIDATION REPORT (CPWD Compliance)")
        print("=" * 80)
        print(f"\nTotal Issues Found: {summary['total_issues']}")
        print(f"  - Errors:   {summary['errors']}")
        print(f"  - Warnings: {summary['warnings']}")
        print(f"  - Info:     {summary['info']}")
        print("\n" + "-" * 80)

        if self.validation_results:
            for result in self.validation_results:
                print(f"\n{result}")
                if result.suggestion:
                    print(f"  → Suggestion: {result.suggestion}")
        else:
            print("\n✓ All validations passed!")

        print("\n" + "=" * 80)
