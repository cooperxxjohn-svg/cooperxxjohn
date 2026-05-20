"""
Advanced export templates with customization
Professional proposal templates, bid forms, work orders
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from typing import Dict, List
import os


class ProposalTemplate:
    """Professional proposal template with company branding"""

    def __init__(self, company_info: Dict):
        self.company_info = company_info
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

    def generate_proposal(self, project: Dict, rooms: List[Dict], output_path: str):
        """Generate professional proposal PDF"""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []

        # Cover page
        story.extend(self._create_cover_page(project))
        story.append(PageBreak())

        # Table of contents
        story.extend(self._create_table_of_contents(project, rooms))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(project))
        story.append(PageBreak())

        # Detailed breakdown
        story.extend(self._create_detailed_breakdown(rooms))
        story.append(PageBreak())

        # Terms and conditions
        story.extend(self._create_terms_and_conditions())

        # Build PDF
        doc.build(story)

    def _create_cover_page(self, project: Dict) -> List:
        """Create cover page"""
        elements = []

        # Company logo (if available)
        logo_path = self.company_info.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            elements.append(Spacer(1, 1*inch))
            elements.append(Image(logo_path, width=2*inch, height=1*inch))
            elements.append(Spacer(1, 0.5*inch))

        # Title
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("PAINTING PROPOSAL", self.title_style))
        elements.append(Spacer(1, 0.5*inch))

        # Project info
        project_info = [
            ["Project:", project.get("name", "")],
            ["Customer:", project.get("customer", "")],
            ["Date:", datetime.now().strftime("%B %d, %Y")],
            ["Proposal #:", f"P-{datetime.now().strftime('%Y%m%d')}-001"]
        ]

        info_table = Table(project_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 1*inch))

        # Company info
        company_data = [
            [self.company_info.get('name', 'Your Company')],
            [self.company_info.get('address', '')],
            [self.company_info.get('phone', '')],
            [self.company_info.get('email', '')],
            [self.company_info.get('license', '')]
        ]

        company_table = Table(company_data, colWidths=[6*inch])
        company_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(company_table)

        return elements

    def _create_table_of_contents(self, project: Dict, rooms: List[Dict]) -> List:
        """Create table of contents"""
        elements = []

        elements.append(Paragraph("TABLE OF CONTENTS", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))

        toc_items = [
            "Executive Summary ............................. Page 3",
            "Scope of Work .................................. Page 4",
            "Room-by-Room Breakdown ......................... Page 5",
            "Materials Specifications ....................... Page 8",
            "Timeline ....................................... Page 9",
            "Terms & Conditions ............................. Page 10"
        ]

        for item in toc_items:
            elements.append(Paragraph(item, self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))

        return elements

    def _create_executive_summary(self, project: Dict) -> List:
        """Create executive summary"""
        elements = []

        elements.append(Paragraph("EXECUTIVE SUMMARY", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))

        summary_text = f"""
        This proposal outlines the scope and cost for painting services at {project.get('name', 'your facility')}.
        Our team will provide professional interior painting services including surface preparation,
        priming, and application of premium paint finishes.

        <br/><br/>

        <b>Project Highlights:</b><br/>
        • Total Rooms: {project.get('total_rooms', 0)}<br/>
        • Total Paintable Area: {project.get('total_sqft', 0):,.0f} square feet<br/>
        • Estimated Duration: {self._estimate_duration(project.get('total_sqft', 0))} working days<br/>
        • Total Investment: ${project.get('bid_amount', 0):,.2f}<br/>

        <br/><br/>

        We pride ourselves on quality workmanship, professional service, and competitive pricing.
        All work is guaranteed for 2 years against defects in materials and workmanship.
        """

        elements.append(Paragraph(summary_text, self.styles['Normal']))

        return elements

    def _create_detailed_breakdown(self, rooms: List[Dict]) -> List:
        """Create detailed room-by-room breakdown"""
        elements = []

        elements.append(Paragraph("ROOM-BY-ROOM BREAKDOWN", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))

        for room in rooms:
            # Room header
            room_header = Paragraph(
                f"<b>{room.get('name', '')}</b>",
                self.heading_style
            )

            # Room details table
            dimensions = room.get('dimensions', {})
            room_details = [
                ["Dimensions:", f"{dimensions.get('length', 0)}' × {dimensions.get('width', 0)}' × {dimensions.get('height', 0)}'"],
                ["Total Area:", f"{room.get('total_area', 0):,.0f} sqft"]
            ]

            details_table = Table(room_details, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            # Surface breakdown
            surfaces_data = [["Surface", "Area (sqft)", "Description"]]

            for surface_name, surface in room.get('surfaces', {}).items():
                surfaces_data.append([
                    surface_name.title(),
                    f"{surface.get('area', 0):,.0f}",
                    "Primer + 2 coats finish"
                ])

            surfaces_table = Table(surfaces_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            surfaces_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            # Combine elements for this room
            room_group = KeepTogether([
                room_header,
                Spacer(1, 0.1*inch),
                details_table,
                Spacer(1, 0.1*inch),
                surfaces_table,
                Spacer(1, 0.3*inch)
            ])

            elements.append(room_group)

        return elements

    def _create_terms_and_conditions(self) -> List:
        """Create terms and conditions"""
        elements = []

        elements.append(Paragraph("TERMS & CONDITIONS", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))

        terms = """
        <b>1. Payment Terms:</b><br/>
        • 50% deposit due upon contract signing<br/>
        • 50% due upon completion<br/>
        • Payment accepted via check, credit card, or bank transfer<br/>

        <br/><br/>

        <b>2. Scope of Work:</b><br/>
        • All labor and materials for painting as specified<br/>
        • Surface preparation including filling, sanding, and priming<br/>
        • Application of premium paint (2 coats minimum)<br/>
        • Daily cleanup and final site cleanup<br/>

        <br/><br/>

        <b>3. Exclusions:</b><br/>
        • Extensive drywall repair or replacement<br/>
        • Removal of wallpaper<br/>
        • Painting of ceilings with water damage<br/>
        • Furniture moving (customer responsible)<br/>

        <br/><br/>

        <b>4. Warranty:</b><br/>
        • 2-year warranty against defects in materials and workmanship<br/>
        • Does not cover damage from abuse, neglect, or normal wear<br/>

        <br/><br/>

        <b>5. Timeline:</b><br/>
        • Work to commence within 14 days of contract signing<br/>
        • Estimated completion as specified above<br/>
        • Delays due to weather or unforeseen circumstances exempt<br/>

        <br/><br/>

        <b>Customer Acceptance:</b><br/>
        By signing below, customer accepts the terms and conditions of this proposal.

        <br/><br/><br/>

        ___________________________ &nbsp;&nbsp;&nbsp;&nbsp; ___________<br/>
        Customer Signature &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date<br/>

        <br/><br/>

        ___________________________ &nbsp;&nbsp;&nbsp;&nbsp; ___________<br/>
        Contractor Signature &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date<br/>
        """

        elements.append(Paragraph(terms, self.styles['Normal']))

        return elements

    def _estimate_duration(self, total_sqft: float) -> int:
        """Estimate project duration in days"""
        # Assume 300 sqft per painter per day
        days = max(1, round(total_sqft / 300))
        return days


class BidFormTemplate:
    """Standardized bid form for GC submissions"""

    @staticmethod
    def generate_bid_form(project: Dict, output_path: str):
        """Generate standard bid form"""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []

        styles = getSampleStyleSheet()

        # Header
        story.append(Paragraph("CONTRACTOR BID FORM", styles['Title']))
        story.append(Spacer(1, 0.3*inch))

        # Project info
        project_data = [
            ["Project Name:", project.get('name', '')],
            ["Bid Number:", f"BID-{datetime.now().strftime('%Y%m%d')}"],
            ["Bid Date:", datetime.now().strftime("%B %d, %Y")],
            ["Bid Due Date:", project.get('bid_due_date', '').strftime("%B %d, %Y") if project.get('bid_due_date') else ''],
        ]

        project_table = Table(project_data, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(project_table)
        story.append(Spacer(1, 0.5*inch))

        # Cost breakdown
        cost_data = [
            ["Description", "Amount"],
            ["Material Cost", f"${project.get('material_cost', 0):,.2f}"],
            ["Labor Cost", f"${project.get('labor_cost', 0):,.2f}"],
            ["Subtotal", f"${(project.get('material_cost', 0) + project.get('labor_cost', 0)):,.2f}"],
            ["Markup (30%)", f"${project.get('estimated_cost', 0) * 0.30:,.2f}"],
            ["TOTAL BID AMOUNT", f"${project.get('bid_amount', 0):,.2f}"]
        ]

        cost_table = Table(cost_data, colWidths=[4*inch, 2*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(cost_table)

        doc.build(story)


# Usage
if __name__ == "__main__":
    # Test proposal generation
    company_info = {
        'name': 'Professional Painting Co.',
        'address': '123 Main St, City, State 12345',
        'phone': '(555) 123-4567',
        'email': 'contact@propaint.com',
        'license': 'License #12345'
    }

    test_project = {
        'name': 'Office Building Renovation',
        'customer': 'ABC Corp',
        'total_rooms': 10,
        'total_sqft': 5000,
        'bid_amount': 12500,
        'material_cost': 5000,
        'labor_cost': 5000,
        'estimated_cost': 10000
    }

    test_rooms = [
        {
            'name': 'Conference Room A',
            'dimensions': {'length': 20, 'width': 15, 'height': 9},
            'total_area': 900,
            'surfaces': {
                'walls': {'area': 600},
                'ceiling': {'area': 300}
            }
        }
    ]

    template = ProposalTemplate(company_info)
    template.generate_proposal(test_project, test_rooms, "test_proposal.pdf")

    print("✓ Proposal template generated")
