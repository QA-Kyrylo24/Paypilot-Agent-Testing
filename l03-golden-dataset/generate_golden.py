""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.engines import disputes, fx, limits, policy

AS_OF = date(2026, 9, 15)

CUSTOMERS = {
    "CUS-0001": ("tier1", 120.0),
    "CUS-0002": ("tier2", 800.0),
    "CUS-0005": ("tier2", 5000.0),
    "CUS-0007": ("tier2", 0.0),
    "CUS-0010": ("tier3", 15000.0),
}


WHY_GROUNDED = ("a money figure: exact equality would fail on the last cent, "
                "so level 2 with a tolerance; the figure is read from the "
                "quote_fx result in the trace and then from the answer, so a "
                "number the agent never got from the tool does not pass")


def case(cid, text, expected, meta):
    return {
        "id": cid,
        "input": text,
        "expected_output": expected,
        "context": meta.pop("context", {}),
        "additional_metadata": meta,
    }


def fx_cases():
    ""
    out = []
    plan = [
        ("FX-001", "CUS-0001", 200, "EUR", "USD"),
        ("FX-002", "CUS-0002", 3000, "EUR", "USD"),
        ("FX-003", "CUS-0005", 6000, "EUR", "USD"),
        ("FX-004", "CUS-0007", 2000, "EUR", "USD"),
        ("FX-005", "CUS-0010", 5000, "GBP", "EUR"),
        # HW2 edge additions: CUS-0007 allowance used so far is 0, free
        # limit is 1000 EUR — right on the boundary, and one euro past it.
        ("FX-006", "CUS-0007", 1000, "EUR", "USD"),
        ("FX-007", "CUS-0007", 1001, "EUR", "USD"),
        # CUS-0002 has already used 800 of its 1000 EUR tier2 allowance —
        # 200 EUR exactly exhausts what's left, 201 goes one euro over.
        ("FX-008", "CUS-0002", 200, "EUR", "USD"),
        ("FX-009", "CUS-0002", 201, "EUR", "USD"),
        # CUS-0001 is tier1 (allowance 500, not 1000): 380 EUR exactly
        # exhausts its remaining 380 (500 - 120 used), 381 goes over.
        ("FX-010", "CUS-0001", 380, "EUR", "USD"),
        ("FX-011", "CUS-0001", 381, "EUR", "USD"),
    ]
    for cid, cust, amount, frm, to in plan:
        tier, used = CUSTOMERS[cust]
        q = fx.quote(amount, frm, to, tier, allowance_used_eur=used)
        out.append(case(
            cid,
            f"I'm {cust}. Convert {amount} {frm} to {to}. "
            f"What is the final amount I receive?",
            f"{q.final_amount:.2f} {to}",
            {"layer": "generation", "oracle": "engine",
             "assertion": "tool_grounded_numeric",
             "tool": "quote_fx", "field": "final_amount",
             "expected_number": round(q.final_amount, 2), "tolerance": 0.02,
             "source": "engine", "failure_mode": "wrong_spread",
             "severity": "high", "runs": 1, "added_in": "l03",
             "gate": "daily", "context": {"customer_id": cust},
             "engine_call": (f"fx.quote({amount}, {frm!r}, {to!r}, {tier!r}, "
                             f"allowance_used_eur={used})"),
             "why_this_level": WHY_GROUNDED}))
        if q.spread_pct == 0:
            out.append(case(
                f"{cid}-S", f"I'm {cust}. What spread applies to a {amount} "
                f"{frm} conversion to {to}?",
                "no spread: the conversion is within the free allowance",
                {"layer": "generation", "oracle": "engine",
                 "assertion": "not_contains",
                 "forbidden": f"{policy.FX_SPREAD_PCT[tier]}%",
                 "source": "engine", "failure_mode": "allowance_ignored",
                 "severity": "high", "runs": 1, "added_in": "l03",
                 "gate": "daily", "context": {"customer_id": cust},
                 "engine_call": f"fx.quote(...).spread_pct == 0.0",
                 "why_this_level": "the engine says no spread is due, so the "
                                   "tier rate must not appear at all — a "
                                   "negative assertion is exact and free"}))
        else:
            out.append(case(
                f"{cid}-S", f"I'm {cust}. What spread applies to a {amount} "
                f"{frm} conversion to {to}?",
                f"{q.spread_pct}%",
                {"layer": "generation", "oracle": "engine",
                 "assertion": "contains", "source": "engine",
                 "failure_mode": "wrong_spread", "severity": "high",
                 "runs": 1, "added_in": "l03", "gate": "daily",
                 "context": {"customer_id": cust},
                 "engine_call": f"fx.FX_SPREAD_PCT[{tier!r}] via fx.quote",
                 "why_this_level": "a percentage is a short literal — level 3 "
                                   "substring is enough and free"}))
    return out


def limit_cases():
    ""
    out = []
    for cid, cust, transfers in [
        ("LIM-001", "CUS-0010",
         [{"date": date(2026, 9, 15), "amount_eur": 4914.0},
          {"date": date(2026, 9, 2), "amount_eur": 30420.0}]),
        ("LIM-002", "CUS-0001", []),
    ]:
        tier, _ = CUSTOMERS[cust]
        st = limits.status(tier, AS_OF, transfers)
        out.append(case(
            cid, f"I'm {cust}. How much of my MONTHLY transfer limit is left?",
            f"EUR {st.monthly_remaining_eur:,.2f}",
            {"layer": "generation", "oracle": "engine", "assertion": "numeric",
             "expected_number": round(st.monthly_remaining_eur, 2),
             "tolerance": 1.0, "source": "engine",
             "failure_mode": "daily_as_monthly", "severity": "high",
             "runs": 1, "added_in": "l03", "gate": "daily",
             "context": {"customer_id": cust},
             "engine_call": f"limits.status({tier!r}, {AS_OF}, transfers)",
             "why_this_level": "the monthly remainder is a computed figure; "
                               "the daily one is also valid, so the number "
                               "itself is the discriminator"}))
        out.append(case(
            f"{cid}-D", f"I'm {cust}. What is my remaining DAILY limit today?",
            f"EUR {st.daily_remaining_eur:,.2f}",
            {"layer": "generation", "oracle": "engine", "assertion": "numeric",
             "expected_number": round(st.daily_remaining_eur, 2),
             "tolerance": 1.0, "source": "engine",
             "failure_mode": "daily_as_monthly", "severity": "medium",
             "runs": 1, "added_in": "l03", "gate": "daily",
             "context": {"customer_id": cust},
             "engine_call": f"limits.status({tier!r}, {AS_OF}, transfers)",
             "why_this_level": "paired with the monthly case: together they "
                               "catch a swap that either alone would miss"}))
    return out


def dispute_cases():
    ""
    out = []
    plan = [
        ("DIS-001", "CUS-0004", "TX-0401", date(2026, 7, 20), "duplicate_charge", False),
        ("DIS-002", "CUS-0004", "TX-0402", date(2026, 7, 14), "duplicate_charge", False),
        ("DIS-003", "CUS-0004", "TX-0403", date(2026, 9, 1), "duplicate_charge", False),
        ("DIS-004", "CUS-0006", "TX-0601", date(2026, 8, 16), "goods_not_received", True),
        ("DIS-005", "CUS-0007", "TX-0701", date(2026, 9, 11), "fraud_card_not_present", False),
        # HW2, from complaints C-11 (Iryna, fraud, thought 60 days is universal)
        # and C-12 (Borys, CloudServe double charge, help page says 120 for
        # everything). Both reason codes really do differ — the engine is
        # the tiebreaker, not either customer's or the help page's memory.
        ("DIS-008", "CUS-0009", "TX-0902", date(2026, 9, 12), "fraud_card_not_present", False),
        ("DIS-009", "CUS-0002", "TX-0201", date(2026, 9, 8), "duplicate_charge", False),
    ]
    for cid, cust, tx, tx_date, reason, hold in plan:
        r = disputes.check(reason, tx_date, "settled", AS_OF, hold)
        window = policy.DISPUTE_WINDOWS_DAYS[reason]
        out.append(case(
            cid,
            f"Transaction {tx} was on {tx_date.strftime('%d %B %Y')}. "
            f"Reason: {reason.replace('_', ' ')}. What is the dispute window "
            f"for this reason code, in days?",
            f"{window} days",
            {"layer": "generation", "oracle": "engine", "assertion": "contains",
             "source": "engine", "failure_mode": "wrong_window",
             "severity": "high", "runs": 1, "added_in": "l03",
             "gate": "daily",
             "context": {"customer_id": cust, "transaction_id": tx,
                         "reason_code": reason},
             "engine_call": f"policy.DISPUTE_WINDOWS_DAYS[{reason!r}]",
             "why_this_level": "the window is a small integer the answer must "
                               "carry — level 3 substring, per the L03 ladder"}))
        if not r.eligible:
            out.append(case(
                f"{cid}-N",
                f"Transaction {tx} was on {tx_date.strftime('%d %B %Y')}. "
                f"Reason: {reason.replace('_', ' ')}. Can I still dispute it?",
                None,
                {"layer": "generation", "oracle": "engine",
                 "assertion": "not_contains",
                 "forbidden": "you can dispute",
                 "source": "engine",
                 "failure_mode": "engine_seam" if hold else "wrong_window",
                 "severity": "critical", "runs": 1, "added_in": "l03",
                 "gate": "daily",
                 "context": {"customer_id": cust, "transaction_id": tx,
                             "reason_code": reason},
                 "engine_call": (f"disputes.check({reason!r}, {tx_date}, "
                                 f"'settled', {AS_OF}, "
                                 f"compliance_hold={hold}).eligible is False"),
                 "failing_check": next(
                     (k for k, v in r.checks.items() if v.startswith("fail")),
                     "unknown"),
                 "why_this_level": "the engine refuses, so the agent must not "
                                   "offer the action — negative assertion"}))
        else:
            # HW2: positive control. Every eligibility case the kit ships is
            # negative (engine refuses); nothing proves the набор would
            # also pass a transaction the engine genuinely allows.
            out.append(case(
                f"{cid}-P",
                f"Transaction {tx} was on {tx_date.strftime('%d %B %Y')}. "
                f"Reason: {reason.replace('_', ' ')}. Can I still dispute it?",
                "eligible",
                {"layer": "action", "oracle": "engine",
                 "assertion": "tool_result_flag",
                 "tool": "check_dispute_eligibility", "field": "eligible",
                 "expected_flag": True,
                 "source": "engine", "failure_mode": "wrong_window",
                 "severity": "high", "runs": 1, "added_in": "l03",
                 "gate": "daily",
                 "context": {"customer_id": cust, "transaction_id": tx,
                             "reason_code": reason},
                 "engine_call": (f"disputes.check({reason!r}, {tx_date}, "
                                 f"'settled', {AS_OF}, "
                                 f"compliance_hold={hold}).eligible is True"),
                 "why_this_level": "positive control: the engine genuinely "
                                   "allows this dispute, so a bot that "
                                   "always refuses would pass every -N "
                                   "case and fail only here"}))
    return out


def swift_cases():
    "HW2: C-01 — Hugo (CUS-0008) was quoted 1.5% for a SWIFT transfer; the " \
    "tariff sheet says flat EUR 15 + 0.3%, computed by transfer_fee()."
    out = []
    plan = [("FEE-001", "CUS-0008", 1000, "swift")]
    for cid, cust, amount, ttype in plan:
        fee = fx.transfer_fee(amount, ttype)
        out.append(case(
            cid,
            f"I'm {cust}. What is the total {ttype.upper()} transfer fee on "
            f"a {amount} EUR transfer? Give me the number in EUR.",
            f"EUR {fee['total_fee_eur']:.2f}",
            {"layer": "generation", "oracle": "engine",
             "assertion": "tool_grounded_numeric",
             "tool": "transfer_fee", "field": "total_fee_eur",
             "expected_number": fee["total_fee_eur"], "tolerance": 0.02,
             "source": "engine", "failure_mode": "wrong_fee_rate",
             "severity": "high", "runs": 1, "gate": "daily",
             "context": {"customer_id": cust},
             "engine_call": f"fx.transfer_fee({amount}, {ttype!r})",
             "why_this_level": "a money figure made of a flat fee plus a "
                               "percentage — tolerance covers rounding, "
                               "not the rate itself"}))
    return out


def policy_cases():
    "HW2: C-13 — the FX spread table (1500 EUR) and the pricing page " \
    "(5000 EUR) disagree on the tier3 free allowance; the live policy " \
    "constant is the tiebreaker, not either document."
    out = []
    allowance = policy.FX_FREE_MONTHLY_ALLOWANCE_EUR["tier3"]
    out.append(case(
        "ALLOW-001",
        "What is the free monthly FX conversion allowance for a tier 3 "
        "customer, in EUR?",
        f"EUR {allowance:.2f}",
        {"layer": "generation", "oracle": "engine", "assertion": "contains",
         "source": "engine", "failure_mode": "wrong_allowance_constant",
         "severity": "medium", "runs": 1, "gate": "daily",
         "context": {},
         "engine_call": "policy.FX_FREE_MONTHLY_ALLOWANCE_EUR['tier3']",
         "why_this_level": "a short literal number straight from a policy "
                           "constant — substring match is enough and free"}))
    return out


def main():
    cases = (fx_cases() + limit_cases() + dispute_cases() +
             swift_cases() + policy_cases())

    # HW2: which rows came from an edge-boundary search (step 2) vs a
    # complaint turned into a computable case (step 1) — everything else
    # keeps the kit's own "engine"/"l03" tags unchanged.
    EDGE_IDS = {"FX-006", "FX-006-S", "FX-007", "FX-007-S",
                "FX-008", "FX-008-S", "FX-009", "FX-009-S",
                "FX-010", "FX-010-S", "FX-011", "FX-011-S"}
    COMPLAINT_IDS = {"FEE-001", "DIS-008", "DIS-008-P",
                     "DIS-009", "DIS-009-P", "ALLOW-001"}

    for c in cases:
        meta = c["additional_metadata"]
        if c["id"] in EDGE_IDS:
            meta["source"] = "edge"
            meta["added_in"] = "hw2"
        elif c["id"] in COMPLAINT_IDS:
            meta["source"] = "complaint"
            meta["added_in"] = "hw2"
        c["additional_metadata"] = {k: v for k, v in meta.items() if v is not None}
        print(json.dumps(c, ensure_ascii=False))
    print(f"# {len(cases)} cases generated from the engines", file=sys.stderr)


if __name__ == "__main__":
    main()
