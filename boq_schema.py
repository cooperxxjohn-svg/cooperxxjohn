"""
BOQ (Bill of Quantities) Schema Definitions
Based on CPWD standards for Indian Government Contracts

This module defines the core data structures and JSON schemas for BOQ estimation.
"""

from typing import Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class UnitType(str, Enum):
    """Standard measurement units as per CPWD"""
    # Length
    METER = "m"
    CENTIMETER = "cm"
    KILOMETER = "km"

    # Area
    SQUARE_METER = "sqm"
    SQUARE_FOOT = "sqft"
    HECTARE = "ha"

    # Volume
    CUBIC_METER = "cum"
    CUBIC_FOOT = "cft"
    LITRE = "ltr"

    # Weight
    KILOGRAM = "kg"
    QUINTAL = "qtl"
    METRIC_TON = "MT"

    # Count
    NUMBER = "nos"
    PAIR = "pair"
    SET = "set"

    # Special
    RUNNING_METER = "rmt"
    SQUARE_METER_HORIZONTAL = "sqm(h)"
    SQUARE_METER_VERTICAL = "sqm(v)"
    JOB = "job"
    LUMP_SUM = "LS"


class WorkCategory(str, Enum):
    """Major work categories as per CPWD classification"""
    EARTHWORK = "EARTHWORK"
    CONCRETE_WORK = "CONCRETE_WORK"
    FORMWORK = "FORMWORK"
    REINFORCEMENT = "REINFORCEMENT"
    MASONRY = "MASONRY"
    PLASTERING = "PLASTERING"
    FLOORING = "FLOORING"
    ROOFING = "ROOFING"
    DOORS_WINDOWS = "DOORS_WINDOWS"
    FINISHING = "FINISHING"
    PAINTING = "PAINTING"
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    SANITARY = "SANITARY"
    DRAINAGE = "DRAINAGE"
    ROAD_WORK = "ROAD_WORK"
    WATERPROOFING = "WATERPROOFING"
    MISCELLANEOUS = "MISCELLANEOUS"


class MaterialGrade(str, Enum):
    """Standard material grades"""
    # Concrete grades
    M10 = "M10"
    M15 = "M15"
    M20 = "M20"
    M25 = "M25"
    M30 = "M30"
    M35 = "M35"
    M40 = "M40"

    # Steel grades
    FE415 = "Fe415"
    FE500 = "Fe500"
    FE550 = "Fe550"

    # Brick grades
    FIRST_CLASS = "First_Class"
    SECOND_CLASS = "Second_Class"
    ENGINEERING_BRICK = "Engineering_Brick"


class Material(BaseModel):
    """Material specification"""
    name: str
    grade: Optional[str] = None
    specification: str
    unit: UnitType
    quantity: Decimal = Field(ge=0)
    rate: Optional[Decimal] = Field(None, ge=0)
    amount: Optional[Decimal] = Field(None, ge=0)
    wastage_percentage: Decimal = Field(default=Decimal("5.0"), ge=0, le=100)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    @validator('amount', always=True)
    def calculate_amount(cls, v, values):
        if 'quantity' in values and 'rate' in values and values['rate'] is not None:
            qty_with_wastage = values['quantity'] * (1 + values.get('wastage_percentage', Decimal(5)) / 100)
            return qty_with_wastage * values['rate']
        return v


class Labour(BaseModel):
    """Labour specification"""
    category: str  # e.g., Mason, Helper, Skilled, Unskilled
    unit: UnitType
    quantity: Decimal = Field(ge=0)
    rate: Optional[Decimal] = Field(None, ge=0)
    amount: Optional[Decimal] = Field(None, ge=0)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    @validator('amount', always=True)
    def calculate_amount(cls, v, values):
        if 'quantity' in values and 'rate' in values and values['rate'] is not None:
            return values['quantity'] * values['rate']
        return v


class BOQLineItem(BaseModel):
    """
    Single line item in BOQ
    Represents one work item with complete specifications
    """
    item_no: str  # e.g., "1.1", "2.3.4"
    description: str
    category: WorkCategory
    sub_category: Optional[str] = None

    # Specifications
    specification: str
    reference_standard: Optional[str] = None  # e.g., "IS 456:2000", "CPWD DSR 2023"

    # Quantities
    unit: UnitType
    quantity: Decimal = Field(ge=0)

    # Rates and amounts
    unit_rate: Decimal = Field(ge=0)
    material_cost: Optional[Decimal] = Field(None, ge=0)
    labour_cost: Optional[Decimal] = Field(None, ge=0)
    equipment_cost: Optional[Decimal] = Field(None, ge=0)
    overhead_percentage: Decimal = Field(default=Decimal("15.0"), ge=0)
    profit_percentage: Decimal = Field(default=Decimal("10.0"), ge=0)

    total_amount: Decimal = Field(ge=0)

    # Breakdown
    materials: List[Material] = []
    labour: List[Labour] = []

    # Metadata
    remarks: Optional[str] = None
    drawing_reference: Optional[str] = None
    location: Optional[str] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

    @validator('total_amount', always=True)
    def calculate_total_amount(cls, v, values):
        if 'quantity' in values and 'unit_rate' in values:
            return values['quantity'] * values['unit_rate']
        return v


class BOQSection(BaseModel):
    """
    Section/group of related BOQ items
    """
    section_no: str  # e.g., "1", "2.1"
    title: str
    description: Optional[str] = None
    items: List[BOQLineItem] = []

    @property
    def total_amount(self) -> Decimal:
        return sum(item.total_amount for item in self.items)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ContractDetails(BaseModel):
    """Contract metadata"""
    contract_name: str
    contract_no: Optional[str] = None
    department: str = "CPWD"
    location: str
    client: str

    # Dates
    tender_date: Optional[datetime] = None
    completion_period_days: Optional[int] = None

    # Financial
    estimated_cost: Optional[Decimal] = None
    contract_value: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class BOQDocument(BaseModel):
    """
    Complete BOQ document
    Root data structure for entire Bill of Quantities
    """
    # Metadata
    boq_id: str
    version: str = "1.0"
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)

    # Contract details
    contract: ContractDetails

    # BOQ structure
    sections: List[BOQSection] = []

    # Summary
    total_quantity_summary: Dict[str, Decimal] = {}
    total_amount: Decimal = Field(default=Decimal("0"))

    # Terms and conditions
    gst_percentage: Decimal = Field(default=Decimal("18.0"), ge=0)
    price_escalation_clause: Optional[str] = None
    payment_terms: Optional[str] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

    @validator('total_amount', always=True)
    def calculate_total(cls, v, values):
        if 'sections' in values:
            return sum(section.total_amount for section in values['sections'])
        return v

    def to_json_schema(self) -> dict:
        """Export as JSON schema"""
        return self.schema()

    def get_summary_by_category(self) -> Dict[WorkCategory, Decimal]:
        """Get cost summary grouped by work category"""
        summary = {}
        for section in self.sections:
            for item in section.items:
                if item.category not in summary:
                    summary[item.category] = Decimal("0")
                summary[item.category] += item.total_amount
        return summary


# JSON Schema export
BOQ_JSON_SCHEMA = BOQDocument.schema_json(indent=2)


if __name__ == "__main__":
    # Example usage and schema export
    print("BOQ Data Structure Schema:")
    print("=" * 80)
    print(BOQ_JSON_SCHEMA)
