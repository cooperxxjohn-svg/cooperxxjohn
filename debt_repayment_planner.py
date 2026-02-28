#!/usr/bin/env python3
"""
Debt Repayment Planner for College Students

A practical tool to plan debt repayment, track payments, and find
realistic paths out of debt — especially for F1 visa students with
limited work authorization.

Usage:
    python debt_repayment_planner.py
"""

import json
import os
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class DebtAccount:
    """A single debt account (credit card, personal loan, etc.)."""
    name: str
    principal: float
    annual_interest_rate: float  # as percentage, e.g. 5.0 for 5%
    minimum_payment: float
    negotiated_monthly_payment: Optional[float] = None
    notes: str = ""

    @property
    def monthly_rate(self) -> float:
        return self.annual_interest_rate / 100 / 12

    @property
    def monthly_payment(self) -> float:
        return self.negotiated_monthly_payment or self.minimum_payment


@dataclass
class Payment:
    """Record of a payment made."""
    date: str  # ISO format YYYY-MM-DD
    account_name: str
    amount: float
    note: str = ""


@dataclass
class MonthlyBudget:
    """Monthly income and expense breakdown."""
    # Income sources (F1-legal)
    on_campus_job: float = 0.0
    cpt_income: float = 0.0
    opt_income: float = 0.0
    freelance_authorized: float = 0.0  # only if on OPT/CPT
    scholarships_stipends: float = 0.0
    family_support: float = 0.0
    other_income: float = 0.0

    # Fixed expenses
    rent: float = 0.0
    utilities: float = 0.0
    phone: float = 0.0
    insurance: float = 0.0
    subscriptions: float = 0.0

    # Variable expenses
    groceries: float = 0.0
    transportation: float = 0.0
    personal: float = 0.0
    other_expenses: float = 0.0

    @property
    def total_income(self) -> float:
        return (self.on_campus_job + self.cpt_income + self.opt_income +
                self.freelance_authorized + self.scholarships_stipends +
                self.family_support + self.other_income)

    @property
    def total_expenses(self) -> float:
        return (self.rent + self.utilities + self.phone + self.insurance +
                self.subscriptions + self.groceries + self.transportation +
                self.personal + self.other_expenses)

    @property
    def available_for_debt(self) -> float:
        return max(0, self.total_income - self.total_expenses)


@dataclass
class DebtPlan:
    """Complete debt repayment plan."""
    debts: list = field(default_factory=list)
    payments: list = field(default_factory=list)
    budget: MonthlyBudget = field(default_factory=MonthlyBudget)
    created_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    name: str = "My Debt Repayment Plan"


# ---------------------------------------------------------------------------
# Core Calculations
# ---------------------------------------------------------------------------

def calculate_payoff_schedule(
    principal: float,
    annual_rate: float,
    monthly_payment: float,
    extra_payment: float = 0.0,
) -> list[dict]:
    """
    Calculate month-by-month payoff schedule for a single debt.

    Returns list of dicts with: month, payment, principal_paid,
    interest_paid, remaining_balance.
    """
    balance = principal
    monthly_rate = annual_rate / 100 / 12
    schedule = []
    month = 0

    while balance > 0.01 and month < 600:  # cap at 50 years
        month += 1
        interest = balance * monthly_rate
        payment = min(monthly_payment + extra_payment, balance + interest)
        principal_paid = payment - interest

        if principal_paid <= 0:
            # Payment doesn't even cover interest — debt grows forever
            schedule.append({
                "month": month,
                "payment": payment,
                "principal_paid": 0,
                "interest_paid": payment,
                "remaining_balance": balance + (interest - payment),
            })
            if month >= 3:
                # Signal that this payment plan won't work
                schedule.append({
                    "month": -1,
                    "payment": 0,
                    "principal_paid": 0,
                    "interest_paid": 0,
                    "remaining_balance": balance + (interest - payment),
                    "warning": "Payment doesn't cover interest. Debt will grow.",
                })
                break
            balance = balance + (interest - payment)
            continue

        balance -= principal_paid
        balance = max(0, balance)

        schedule.append({
            "month": month,
            "payment": round(payment, 2),
            "principal_paid": round(principal_paid, 2),
            "interest_paid": round(interest, 2),
            "remaining_balance": round(balance, 2),
        })

    return schedule


def total_interest_paid(schedule: list[dict]) -> float:
    """Sum of all interest across the payoff schedule."""
    return round(sum(entry["interest_paid"] for entry in schedule if entry["month"] > 0), 2)


def total_paid(schedule: list[dict]) -> float:
    """Sum of all payments across the payoff schedule."""
    return round(sum(entry["payment"] for entry in schedule if entry["month"] > 0), 2)


def months_to_payoff(schedule: list[dict]) -> int:
    """Number of months until debt is paid off."""
    valid = [e for e in schedule if e["month"] > 0]
    if not valid:
        return 0
    return valid[-1]["month"]


# ---------------------------------------------------------------------------
# Repayment Strategies
# ---------------------------------------------------------------------------

def avalanche_order(debts: list[DebtAccount]) -> list[DebtAccount]:
    """
    Avalanche method: pay highest interest rate first.
    Mathematically optimal — saves the most money.
    """
    return sorted(debts, key=lambda d: d.annual_interest_rate, reverse=True)


def snowball_order(debts: list[DebtAccount]) -> list[DebtAccount]:
    """
    Snowball method: pay smallest balance first.
    Psychologically motivating — quick wins build momentum.
    """
    return sorted(debts, key=lambda d: d.principal)


def calculate_multi_debt_payoff(
    debts: list[DebtAccount],
    total_monthly_budget: float,
    strategy: str = "avalanche",
) -> dict:
    """
    Simulate paying off multiple debts with a fixed monthly budget.

    Strategy: 'avalanche' (highest rate first) or 'snowball' (smallest balance first)

    Returns timeline, total interest, total paid, and per-debt breakdown.
    """
    if strategy == "avalanche":
        ordered = avalanche_order(debts)
    else:
        ordered = snowball_order(debts)

    # Track balances
    balances = {d.name: d.principal for d in ordered}
    rates = {d.name: d.monthly_rate for d in ordered}
    minimums = {d.name: d.minimum_payment for d in ordered}

    timeline = []
    month = 0
    total_interest = 0.0

    while any(b > 0.01 for b in balances.values()) and month < 600:
        month += 1
        month_detail = {"month": month, "accounts": {}}
        remaining_budget = total_monthly_budget

        # First: pay minimums on all active debts
        for name in balances:
            if balances[name] <= 0.01:
                continue
            interest = balances[name] * rates[name]
            total_interest += interest
            min_pay = min(minimums[name], balances[name] + interest)
            balances[name] = balances[name] + interest - min_pay
            remaining_budget -= min_pay
            month_detail["accounts"][name] = {
                "payment": round(min_pay, 2),
                "interest": round(interest, 2),
                "balance": round(balances[name], 2),
            }

        # Then: throw remaining budget at target debt (first in ordered list still active)
        for debt in ordered:
            if balances[debt.name] <= 0.01 or remaining_budget <= 0:
                continue
            extra = min(remaining_budget, balances[debt.name])
            balances[debt.name] -= extra
            remaining_budget -= extra
            month_detail["accounts"][debt.name]["payment"] = round(
                month_detail["accounts"][debt.name]["payment"] + extra, 2
            )
            month_detail["accounts"][debt.name]["balance"] = round(
                balances[debt.name], 2
            )

        timeline.append(month_detail)

    return {
        "strategy": strategy,
        "months_to_freedom": month,
        "total_interest": round(total_interest, 2),
        "total_paid": round(sum(d.principal for d in debts) + total_interest, 2),
        "timeline": timeline,
    }


# ---------------------------------------------------------------------------
# Income Strategy Advisor (F1 Visa Specific)
# ---------------------------------------------------------------------------

F1_INCOME_STRATEGIES = [
    {
        "strategy": "On-Campus Employment",
        "legal_status": "ALLOWED during F1 status",
        "hours": "Up to 20 hrs/week during school, 40 hrs/week during breaks",
        "estimated_monthly": "$800 - $1,500",
        "details": (
            "Work at your university — dining halls, libraries, IT help desk, "
            "research assistant, tutoring center, rec center, admin offices. "
            "No special authorization needed beyond valid F1 status. "
            "Pay ranges from minimum wage to $15-20/hr for specialized roles."
        ),
        "action_steps": [
            "Check your university's student employment portal TODAY",
            "Visit the career center and ask about on-campus openings",
            "Email professors in your department about RA/TA positions",
            "Apply to the library, IT help desk, and dining services",
            "Ask about summer full-time on-campus positions (40 hrs/week)",
        ],
    },
    {
        "strategy": "Curricular Practical Training (CPT)",
        "legal_status": "ALLOWED with DSO authorization",
        "hours": "Part-time (20 hrs/week) or full-time during breaks",
        "estimated_monthly": "$1,500 - $4,000+",
        "details": (
            "Work off-campus in a job directly related to your major. "
            "Must be part of your curriculum (internship, co-op, practicum). "
            "Requires authorization from your Designated School Official (DSO). "
            "Tech/engineering students can earn significantly more."
        ),
        "action_steps": [
            "Talk to your DSO (international student office) about CPT eligibility",
            "Check if your program offers co-op or internship courses",
            "Apply to internships on LinkedIn, Handshake, and company career pages",
            "Some universities allow CPT after completing one academic year",
        ],
    },
    {
        "strategy": "Scholarships & Grants",
        "legal_status": "ALLOWED — not employment",
        "hours": "Application time only",
        "estimated_monthly": "Varies — $500 to full tuition",
        "details": (
            "Free money that reduces your overall financial burden. "
            "Many scholarships are available to international students. "
            "Departmental scholarships, need-based grants, and merit awards."
        ),
        "action_steps": [
            "Apply to EVERY scholarship your university offers",
            "Check: internationalscholarships.com, iefa.org, fastweb.com",
            "Ask your department about TA/RA positions with tuition waivers",
            "Look for scholarships from organizations in your home country",
            "Apply for emergency financial aid from your university",
        ],
    },
    {
        "strategy": "Severe Economic Hardship Work Authorization",
        "legal_status": "ALLOWED with USCIS approval",
        "hours": "Up to 20 hrs/week (school), 40 hrs/week (breaks)",
        "estimated_monthly": "$1,200 - $3,000",
        "details": (
            "If you can demonstrate unforeseen economic hardship (currency "
            "devaluation, loss of financial support, unexpected expenses), "
            "you may apply for off-campus work authorization through USCIS. "
            "Requires DSO recommendation and USCIS approval."
        ),
        "action_steps": [
            "Document your financial hardship thoroughly",
            "Meet with your DSO to discuss eligibility",
            "Prepare Form I-765 with supporting documents",
            "Processing takes 3-6 months — start NOW if eligible",
        ],
    },
    {
        "strategy": "Expense Reduction (Immediate Impact)",
        "legal_status": "N/A",
        "hours": "N/A",
        "estimated_monthly": "Save $200 - $800",
        "details": (
            "Every dollar saved is a dollar toward debt. This has IMMEDIATE "
            "impact unlike income strategies that take time to start."
        ),
        "action_steps": [
            "Audit EVERY subscription — cancel anything non-essential",
            "Switch to a cheaper phone plan (Mint Mobile, visible: $15-30/mo)",
            "Cook all meals — rice, beans, eggs, frozen vegetables ($150-200/mo for food)",
            "Use the university gym, library, free campus events for entertainment",
            "Get a roommate or move to cheaper housing if lease allows",
            "Use student discounts for EVERYTHING (UNiDAYS, Student Beans)",
            "Sell things you don't need (textbooks, electronics, clothes)",
            "Use campus food banks — no shame, that's what they're for",
        ],
    },
    {
        "strategy": "Skills-Based Side Income (On-Campus / Allowed)",
        "legal_status": "CHECK with DSO — some may require authorization",
        "hours": "Flexible",
        "estimated_monthly": "$200 - $1,000",
        "details": (
            "Leverage skills you already have within what's legally permitted. "
            "IMPORTANT: Always verify with your DSO before starting any "
            "income-generating activity to ensure F1 compliance."
        ),
        "action_steps": [
            "Tutor other students (through university tutoring center = on-campus work)",
            "Offer to be a study group leader or supplemental instruction leader",
            "Apply for grading positions in your department",
            "Participate in paid research studies at your university",
            "Enter hackathons and competitions with cash prizes",
            "Check if your university has a startup incubator (some allow F1 students)",
        ],
    },
]


def get_income_strategies() -> list[dict]:
    """Return F1-visa-compliant income strategies."""
    return F1_INCOME_STRATEGIES


def estimate_realistic_monthly_income(
    on_campus_hours_per_week: float = 0,
    hourly_rate: float = 12.0,
    cpt_monthly: float = 0,
    scholarships_monthly: float = 0,
    other_monthly: float = 0,
) -> dict:
    """Estimate realistic monthly income given F1 constraints."""
    # On-campus: capped at 20 hrs/week during school
    effective_hours = min(on_campus_hours_per_week, 20)
    on_campus_monthly = effective_hours * hourly_rate * 4.33  # avg weeks/month

    total = on_campus_monthly + cpt_monthly + scholarships_monthly + other_monthly

    return {
        "on_campus": round(on_campus_monthly, 2),
        "cpt": cpt_monthly,
        "scholarships": scholarships_monthly,
        "other": other_monthly,
        "total_monthly": round(total, 2),
        "total_annual": round(total * 12, 2),
    }


# ---------------------------------------------------------------------------
# Progress Tracking & Visualization (Terminal-Based)
# ---------------------------------------------------------------------------

def render_progress_bar(current: float, total: float, width: int = 40) -> str:
    """Render a text-based progress bar."""
    if total <= 0:
        return "[" + "=" * width + "] 100%"
    pct = min(current / total, 1.0)
    filled = int(width * pct)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {pct * 100:.1f}%"


def render_debt_dashboard(plan: DebtPlan) -> str:
    """Render a complete debt dashboard to the terminal."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  DEBT REPAYMENT DASHBOARD — {plan.name}")
    lines.append(f"  Started: {plan.created_date}")
    lines.append("=" * 70)

    # Summary
    total_debt = sum(d.principal for d in plan.debts)
    total_payments_made = sum(p.amount for p in plan.payments)
    remaining = max(0, total_debt - total_payments_made)

    lines.append("")
    lines.append(f"  Total Original Debt:    ${total_debt:>12,.2f}")
    lines.append(f"  Total Paid So Far:      ${total_payments_made:>12,.2f}")
    lines.append(f"  Remaining Balance:      ${remaining:>12,.2f}")
    lines.append("")
    lines.append(f"  Overall Progress: {render_progress_bar(total_payments_made, total_debt)}")
    lines.append("")

    # Per-account breakdown
    lines.append("-" * 70)
    lines.append("  ACCOUNTS")
    lines.append("-" * 70)

    for debt in plan.debts:
        payments_for_account = sum(
            p.amount for p in plan.payments if p.account_name == debt.name
        )
        account_remaining = max(0, debt.principal - payments_for_account)
        lines.append("")
        lines.append(f"  {debt.name}")
        lines.append(f"    Principal: ${debt.principal:,.2f}  |  "
                      f"Rate: {debt.annual_interest_rate}%  |  "
                      f"Payment: ${debt.monthly_payment:,.2f}/mo")
        lines.append(f"    Paid: ${payments_for_account:,.2f}  |  "
                      f"Remaining: ${account_remaining:,.2f}")
        lines.append(f"    {render_progress_bar(payments_for_account, debt.principal)}")

    # Budget summary
    budget = plan.budget
    if budget.total_income > 0:
        lines.append("")
        lines.append("-" * 70)
        lines.append("  MONTHLY BUDGET")
        lines.append("-" * 70)
        lines.append(f"    Income:              ${budget.total_income:>10,.2f}")
        lines.append(f"    Expenses:            ${budget.total_expenses:>10,.2f}")
        lines.append(f"    Available for Debt:  ${budget.available_for_debt:>10,.2f}")

        if budget.available_for_debt > 0 and remaining > 0:
            months_left = math.ceil(remaining / budget.available_for_debt)
            target_date = datetime.now() + timedelta(days=months_left * 30)
            lines.append(f"    Estimated Payoff:    ~{months_left} months "
                          f"({target_date.strftime('%B %Y')})")

    # Recent payments
    if plan.payments:
        lines.append("")
        lines.append("-" * 70)
        lines.append("  RECENT PAYMENTS")
        lines.append("-" * 70)
        recent = sorted(plan.payments, key=lambda p: p.date, reverse=True)[:10]
        for p in recent:
            lines.append(f"    {p.date}  |  {p.account_name:<25}  |  ${p.amount:>10,.2f}")
            if p.note:
                lines.append(f"              Note: {p.note}")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def render_payoff_comparison(debts: list[DebtAccount], monthly_budget: float) -> str:
    """Compare avalanche vs snowball strategies."""
    avalanche = calculate_multi_debt_payoff(debts, monthly_budget, "avalanche")
    snowball = calculate_multi_debt_payoff(debts, monthly_budget, "snowball")

    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  STRATEGY COMPARISON")
    lines.append(f"  Monthly Budget for Debt: ${monthly_budget:,.2f}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  {'':30} {'AVALANCHE':>15}  {'SNOWBALL':>15}")
    lines.append(f"  {'':30} {'(highest rate)':>15}  {'(smallest bal)':>15}")
    lines.append(f"  {'-' * 62}")
    lines.append(f"  {'Months to debt-free':30} {avalanche['months_to_freedom']:>12}mo  "
                  f"{snowball['months_to_freedom']:>12}mo")
    lines.append(f"  {'Total interest paid':30} ${avalanche['total_interest']:>11,.2f}  "
                  f"${snowball['total_interest']:>11,.2f}")
    lines.append(f"  {'Total amount paid':30} ${avalanche['total_paid']:>11,.2f}  "
                  f"${snowball['total_paid']:>11,.2f}")

    interest_saved = snowball["total_interest"] - avalanche["total_interest"]
    if interest_saved > 0:
        lines.append("")
        lines.append(f"  >> Avalanche saves you ${interest_saved:,.2f} in interest!")
    elif interest_saved < 0:
        lines.append("")
        lines.append(f"  >> Snowball saves you ${abs(interest_saved):,.2f} in interest!")

    months_diff = snowball["months_to_freedom"] - avalanche["months_to_freedom"]
    if months_diff > 0:
        lines.append(f"  >> Avalanche gets you debt-free {months_diff} months sooner!")
    elif months_diff < 0:
        lines.append(f"  >> Snowball gets you debt-free {abs(months_diff)} months sooner!")

    lines.append("")
    lines.append("  TIP: Avalanche is mathematically optimal. Snowball gives quick")
    lines.append("  psychological wins. Pick what keeps you motivated.")
    lines.append("=" * 70)
    return "\n".join(lines)


def render_income_strategies() -> str:
    """Render F1-visa income strategies guide."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  F1 VISA - LEGAL INCOME STRATEGIES")
    lines.append("  IMPORTANT: Always verify with your DSO before starting any work")
    lines.append("=" * 70)

    for i, s in enumerate(F1_INCOME_STRATEGIES, 1):
        lines.append("")
        lines.append(f"  {i}. {s['strategy'].upper()}")
        lines.append(f"     Legal Status: {s['legal_status']}")
        lines.append(f"     Hours: {s['hours']}")
        lines.append(f"     Estimated Monthly: {s['estimated_monthly']}")
        lines.append(f"     {s['details']}")
        lines.append("")
        lines.append("     Action Steps:")
        for step in s["action_steps"]:
            lines.append(f"       -> {step}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("  REMEMBER: Working illegally on F1 = deportation risk.")
    lines.append("  ALWAYS check with your international student office first.")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save / Load Plan
# ---------------------------------------------------------------------------

DATA_FILE = Path("debt_plan_data.json")


def save_plan(plan: DebtPlan, filepath: Path = DATA_FILE):
    """Save debt plan to JSON file."""
    data = {
        "name": plan.name,
        "created_date": plan.created_date,
        "debts": [
            {
                "name": d.name,
                "principal": d.principal,
                "annual_interest_rate": d.annual_interest_rate,
                "minimum_payment": d.minimum_payment,
                "negotiated_monthly_payment": d.negotiated_monthly_payment,
                "notes": d.notes,
            }
            for d in plan.debts
        ],
        "payments": [
            {
                "date": p.date,
                "account_name": p.account_name,
                "amount": p.amount,
                "note": p.note,
            }
            for p in plan.payments
        ],
        "budget": {
            "on_campus_job": plan.budget.on_campus_job,
            "cpt_income": plan.budget.cpt_income,
            "opt_income": plan.budget.opt_income,
            "freelance_authorized": plan.budget.freelance_authorized,
            "scholarships_stipends": plan.budget.scholarships_stipends,
            "family_support": plan.budget.family_support,
            "other_income": plan.budget.other_income,
            "rent": plan.budget.rent,
            "utilities": plan.budget.utilities,
            "phone": plan.budget.phone,
            "insurance": plan.budget.insurance,
            "subscriptions": plan.budget.subscriptions,
            "groceries": plan.budget.groceries,
            "transportation": plan.budget.transportation,
            "personal": plan.budget.personal,
            "other_expenses": plan.budget.other_expenses,
        },
    }
    filepath.write_text(json.dumps(data, indent=2))
    print(f"\n  Plan saved to {filepath}")


def load_plan(filepath: Path = DATA_FILE) -> Optional[DebtPlan]:
    """Load debt plan from JSON file."""
    if not filepath.exists():
        return None
    data = json.loads(filepath.read_text())
    plan = DebtPlan(
        name=data.get("name", "My Plan"),
        created_date=data.get("created_date", datetime.now().strftime("%Y-%m-%d")),
    )
    for d in data.get("debts", []):
        plan.debts.append(DebtAccount(**d))
    for p in data.get("payments", []):
        plan.payments.append(Payment(**p))
    b = data.get("budget", {})
    plan.budget = MonthlyBudget(**b)
    return plan


# ---------------------------------------------------------------------------
# Interactive CLI
# ---------------------------------------------------------------------------

def input_float(prompt: str, default: float = 0.0) -> float:
    """Get a float from user input with a default value."""
    raw = input(f"  {prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print("  Invalid number, using default.")
        return default


def input_str(prompt: str, default: str = "") -> str:
    """Get a string from user input with a default value."""
    raw = input(f"  {prompt} [{default}]: ").strip()
    return raw if raw else default


def add_debt_interactive(plan: DebtPlan):
    """Interactively add a debt account."""
    print("\n  --- Add New Debt Account ---")
    name = input_str("Account name (e.g., 'Chase Credit Card')")
    if not name:
        print("  Cancelled.")
        return
    principal = input_float("Total amount owed ($)")
    rate = input_float("Annual interest rate (%)", 0.0)
    minimum = input_float("Minimum monthly payment ($)")
    negotiated = input_float("Negotiated monthly payment ($ or 0 for minimum)", 0.0)
    notes = input_str("Notes (optional)")

    debt = DebtAccount(
        name=name,
        principal=principal,
        annual_interest_rate=rate,
        minimum_payment=minimum,
        negotiated_monthly_payment=negotiated if negotiated > 0 else None,
        notes=notes,
    )
    plan.debts.append(debt)
    print(f"\n  Added: {name} — ${principal:,.2f} at {rate}%")


def record_payment_interactive(plan: DebtPlan):
    """Interactively record a payment."""
    if not plan.debts:
        print("\n  No debt accounts yet. Add one first.")
        return

    print("\n  --- Record Payment ---")
    print("  Accounts:")
    for i, d in enumerate(plan.debts, 1):
        print(f"    {i}. {d.name} (${d.principal:,.2f})")

    try:
        choice = int(input("  Select account number: ")) - 1
        if choice < 0 or choice >= len(plan.debts):
            print("  Invalid selection.")
            return
    except ValueError:
        print("  Invalid input.")
        return

    amount = input_float("Payment amount ($)")
    date = input_str("Date (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
    note = input_str("Note (optional)")

    payment = Payment(
        date=date,
        account_name=plan.debts[choice].name,
        amount=amount,
        note=note,
    )
    plan.payments.append(payment)
    print(f"\n  Recorded: ${amount:,.2f} to {plan.debts[choice].name} on {date}")


def setup_budget_interactive(plan: DebtPlan):
    """Interactively set up monthly budget."""
    print("\n  --- Monthly Budget Setup ---")
    print("  INCOME (F1-Legal Sources):")
    b = plan.budget
    b.on_campus_job = input_float("On-campus job ($/month)", b.on_campus_job)
    b.cpt_income = input_float("CPT income ($/month)", b.cpt_income)
    b.opt_income = input_float("OPT income ($/month)", b.opt_income)
    b.scholarships_stipends = input_float("Scholarships/stipends ($/month)", b.scholarships_stipends)
    b.family_support = input_float("Family support ($/month)", b.family_support)
    b.other_income = input_float("Other income ($/month)", b.other_income)

    print("\n  FIXED EXPENSES:")
    b.rent = input_float("Rent ($/month)", b.rent)
    b.utilities = input_float("Utilities ($/month)", b.utilities)
    b.phone = input_float("Phone ($/month)", b.phone)
    b.insurance = input_float("Insurance ($/month)", b.insurance)
    b.subscriptions = input_float("Subscriptions ($/month)", b.subscriptions)

    print("\n  VARIABLE EXPENSES:")
    b.groceries = input_float("Groceries ($/month)", b.groceries)
    b.transportation = input_float("Transportation ($/month)", b.transportation)
    b.personal = input_float("Personal/misc ($/month)", b.personal)
    b.other_expenses = input_float("Other expenses ($/month)", b.other_expenses)

    print(f"\n  Total Income:          ${b.total_income:,.2f}")
    print(f"  Total Expenses:        ${b.total_expenses:,.2f}")
    print(f"  Available for Debt:    ${b.available_for_debt:,.2f}")


def run_interactive():
    """Main interactive CLI loop."""
    print("\n" + "=" * 70)
    print("  DEBT REPAYMENT PLANNER")
    print("  Your path from $30k in debt to financial freedom")
    print("=" * 70)

    # Load existing plan or create new
    plan = load_plan()
    if plan:
        print(f"\n  Loaded existing plan: {plan.name}")
        print(f"  {len(plan.debts)} debt accounts, {len(plan.payments)} payments recorded")
    else:
        plan = DebtPlan()
        plan.name = input_str("Name your plan", "My Debt Freedom Plan")

    while True:
        print("\n  ---- MENU ----")
        print("  1. View Dashboard")
        print("  2. Add Debt Account")
        print("  3. Record Payment")
        print("  4. Setup/Update Budget")
        print("  5. Compare Payoff Strategies")
        print("  6. View F1 Visa Income Strategies")
        print("  7. View Payoff Schedule (single debt)")
        print("  8. Save Plan")
        print("  9. Emergency Action Plan")
        print("  0. Save & Exit")
        print("")

        choice = input("  Choose [0-9]: ").strip()

        if choice == "1":
            print(render_debt_dashboard(plan))

        elif choice == "2":
            add_debt_interactive(plan)

        elif choice == "3":
            record_payment_interactive(plan)

        elif choice == "4":
            setup_budget_interactive(plan)

        elif choice == "5":
            if not plan.debts:
                print("\n  Add debt accounts first.")
                continue
            budget = plan.budget.available_for_debt
            if budget <= 0:
                budget = input_float("Monthly amount for debt payments ($)")
            if budget <= 0:
                print("  Need a positive amount.")
                continue
            print(render_payoff_comparison(plan.debts, budget))

        elif choice == "6":
            print(render_income_strategies())

        elif choice == "7":
            if not plan.debts:
                print("\n  Add debt accounts first.")
                continue
            print("\n  Select debt:")
            for i, d in enumerate(plan.debts, 1):
                print(f"    {i}. {d.name}")
            try:
                idx = int(input("  Number: ")) - 1
                debt = plan.debts[idx]
            except (ValueError, IndexError):
                print("  Invalid selection.")
                continue

            extra = input_float("Extra monthly payment above minimum ($)", 0)
            schedule = calculate_payoff_schedule(
                debt.principal, debt.annual_interest_rate,
                debt.monthly_payment, extra
            )
            months = months_to_payoff(schedule)
            interest = total_interest_paid(schedule)
            total = total_paid(schedule)

            print(f"\n  --- Payoff Schedule: {debt.name} ---")
            print(f"  Monthly payment: ${debt.monthly_payment + extra:,.2f}")
            print(f"  Months to pay off: {months}")
            print(f"  Total interest: ${interest:,.2f}")
            print(f"  Total paid: ${total:,.2f}")

            if months > 0:
                payoff_date = datetime.now() + timedelta(days=months * 30)
                print(f"  Debt-free by: {payoff_date.strftime('%B %Y')}")

            # Show first 12 months and last 3
            print(f"\n  {'Month':>6} {'Payment':>10} {'Principal':>10} "
                  f"{'Interest':>10} {'Balance':>12}")
            print(f"  {'-' * 50}")
            show = schedule[:12]
            if len(schedule) > 15:
                show += [{"month": "...", "payment": "", "principal_paid": "",
                          "interest_paid": "", "remaining_balance": ""}]
                show += schedule[-3:]

            for entry in show:
                if entry["month"] == "...":
                    print(f"  {'...':>6}")
                elif entry["month"] == -1:
                    print(f"\n  WARNING: {entry.get('warning', 'Payment too low!')}")
                else:
                    print(f"  {entry['month']:>6} ${entry['payment']:>9,.2f} "
                          f"${entry['principal_paid']:>9,.2f} "
                          f"${entry['interest_paid']:>9,.2f} "
                          f"${entry['remaining_balance']:>11,.2f}")

        elif choice == "8":
            save_plan(plan)

        elif choice == "9":
            print(render_emergency_action_plan())

        elif choice == "0":
            save_plan(plan)
            print("\n  Keep going. Every payment gets you closer to freedom.")
            print("  You've got this.\n")
            break

        else:
            print("  Invalid choice. Try again.")


# ---------------------------------------------------------------------------
# Emergency Action Plan
# ---------------------------------------------------------------------------

def render_emergency_action_plan() -> str:
    """Render an immediate action plan for someone in financial crisis."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  EMERGENCY ACTION PLAN — DO THIS NOW")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  WEEK 1: STOP THE BLEEDING")
    lines.append("  " + "-" * 40)
    lines.append("  [ ] List every single debt with balance, rate, and minimum payment")
    lines.append("  [ ] Cancel ALL non-essential subscriptions (Netflix, Spotify, etc.)")
    lines.append("  [ ] Call each creditor — ask for hardship programs or lower rates")
    lines.append("  [ ] Check if your university has emergency financial aid")
    lines.append("  [ ] Visit the campus food bank")
    lines.append("  [ ] Apply to 5+ on-campus jobs TODAY")
    lines.append("")
    lines.append("  WEEK 2: BUILD YOUR INCOME")
    lines.append("  " + "-" * 40)
    lines.append("  [ ] Follow up on all job applications")
    lines.append("  [ ] Meet with your DSO about CPT eligibility")
    lines.append("  [ ] Apply for every scholarship you qualify for")
    lines.append("  [ ] Sell items you don't need (textbooks, electronics)")
    lines.append("  [ ] Set up a bare-bones budget (this tool can help)")
    lines.append("")
    lines.append("  WEEK 3-4: EXECUTE YOUR PLAN")
    lines.append("  " + "-" * 40)
    lines.append("  [ ] Start your on-campus job (or keep applying)")
    lines.append("  [ ] Make minimum payments on ALL debts (never miss one)")
    lines.append("  [ ] Put every extra dollar toward highest-rate debt")
    lines.append("  [ ] Track every expense for one month")
    lines.append("  [ ] Revisit this planner and set up your full debt plan")
    lines.append("")
    lines.append("  ONGOING: STAY THE COURSE")
    lines.append("  " + "-" * 40)
    lines.append("  [ ] Review budget weekly (15 min every Sunday)")
    lines.append("  [ ] Increase income whenever possible (more hours, CPT, etc.)")
    lines.append("  [ ] Celebrate milestones (every $1,000 paid off)")
    lines.append("  [ ] Don't take on ANY new debt")
    lines.append("  [ ] Remember: this is temporary. You WILL get through it.")
    lines.append("")
    lines.append("  RESOURCES:")
    lines.append("  " + "-" * 40)
    lines.append("  - Your university's financial aid office")
    lines.append("  - Your DSO (international student office)")
    lines.append("  - National Foundation for Credit Counseling: nfcc.org")
    lines.append("  - r/personalfinance and r/povertyfinance on Reddit")
    lines.append("  - 211.org — connects you to local assistance programs")
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick Demo / Example Usage
# ---------------------------------------------------------------------------

def run_demo():
    """Run a demo showing the tool's capabilities with example $30k debt."""
    print("\n" + "=" * 70)
    print("  DEBT REPAYMENT PLANNER — DEMO")
    print("  Example: $30,000 debt, college student on F1 visa")
    print("=" * 70)

    # Example debt breakdown
    debts = [
        DebtAccount(
            name="Credit Card 1",
            principal=8000,
            annual_interest_rate=6.0,  # negotiated down
            minimum_payment=200,
            negotiated_monthly_payment=250,
            notes="Negotiated from 22% to 6%",
        ),
        DebtAccount(
            name="Credit Card 2",
            principal=5000,
            annual_interest_rate=4.0,
            minimum_payment=150,
            negotiated_monthly_payment=175,
            notes="Negotiated from 19% to 4%",
        ),
        DebtAccount(
            name="Personal Loan",
            principal=12000,
            annual_interest_rate=8.0,
            minimum_payment=300,
            negotiated_monthly_payment=350,
            notes="Negotiated from 12% to 8%",
        ),
        DebtAccount(
            name="Medical Bill",
            principal=5000,
            annual_interest_rate=0.0,
            minimum_payment=200,
            negotiated_monthly_payment=200,
            notes="0% interest payment plan",
        ),
    ]

    # Example budget (realistic for F1 student)
    budget = MonthlyBudget(
        on_campus_job=1100,      # ~15 hrs/week at $17/hr
        scholarships_stipends=200,
        family_support=300,
        rent=650,                # shared apartment
        utilities=60,
        phone=25,                # budget plan
        insurance=0,             # covered by school
        groceries=200,           # cooking at home
        transportation=50,      # bus pass
        personal=50,
    )

    plan = DebtPlan(
        debts=debts,
        budget=budget,
        name="Demo: F1 Student $30k Debt Freedom Plan",
    )

    # Add some example payments
    plan.payments = [
        Payment("2026-01-15", "Credit Card 1", 250, "January payment"),
        Payment("2026-01-15", "Credit Card 2", 175, "January payment"),
        Payment("2026-01-15", "Personal Loan", 350, "January payment"),
        Payment("2026-01-15", "Medical Bill", 200, "January payment"),
        Payment("2026-02-15", "Credit Card 1", 250, "February payment"),
        Payment("2026-02-15", "Credit Card 2", 175, "February payment"),
        Payment("2026-02-15", "Personal Loan", 350, "February payment"),
        Payment("2026-02-15", "Medical Bill", 200, "February payment"),
    ]

    # Show dashboard
    print(render_debt_dashboard(plan))

    # Show strategy comparison
    monthly_for_debt = budget.available_for_debt
    print(f"\n  Available for debt payments: ${monthly_for_debt:,.2f}/month")
    print(render_payoff_comparison(debts, monthly_for_debt))

    # Show income strategies
    print(render_income_strategies())

    # Show emergency action plan
    print(render_emergency_action_plan())

    # Show income estimation
    print("\n" + "=" * 70)
    print("  REALISTIC INCOME ESTIMATE")
    print("=" * 70)
    income = estimate_realistic_monthly_income(
        on_campus_hours_per_week=15,
        hourly_rate=17,
        scholarships_monthly=200,
        other_monthly=300,  # family support
    )
    print(f"  On-campus (15 hrs/wk @ $17/hr):  ${income['on_campus']:>10,.2f}")
    print(f"  Scholarships:                     ${income['scholarships']:>10,.2f}")
    print(f"  Other (family):                   ${income['other']:>10,.2f}")
    print(f"  TOTAL MONTHLY:                    ${income['total_monthly']:>10,.2f}")
    print(f"  TOTAL ANNUAL:                     ${income['total_annual']:>10,.2f}")

    # Show a single debt payoff schedule
    print("\n" + "=" * 70)
    print("  PAYOFF SCHEDULE: Personal Loan ($12,000 @ 8%)")
    print("=" * 70)
    schedule = calculate_payoff_schedule(12000, 8.0, 350, extra_payment=0)
    months = months_to_payoff(schedule)
    interest = total_interest_paid(schedule)
    print(f"  Months to pay off: {months}")
    print(f"  Total interest: ${interest:,.2f}")
    print(f"  Total paid: ${total_paid(schedule):,.2f}")
    if months > 0:
        payoff_date = datetime.now() + timedelta(days=months * 30)
        print(f"  Debt-free by: {payoff_date.strftime('%B %Y')}")

    return plan


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
    else:
        run_interactive()
