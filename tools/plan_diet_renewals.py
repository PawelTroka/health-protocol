"""Read-only quantity audit of diet/DIET_RENEWAL_MODEL.json.

This offline tool never opens a retailer, edits a subscription, assumes a delivery,
or purchases food. Default output is Markdown; --json emits the complete analysis.
--self-test checks the exact arithmetic and inventory simulator.
Only --update-analysis writes the derived analysis back into the model file.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "diet" / "DIET_RENEWAL_MODEL.json"
CYCLES = (7, 14, 21, 28, 30, 60, 90)


def number(value):
    return round(float(value), 6)


def rate(streams):
    return sum((Fraction(s["quantity"], s["days"]) for s in streams), Fraction())


def inventory(streams, demand, demand_period=1):
    """Minimum synthetic opening buffer and peak; arrivals precede daily meals.

    Quantities must use a common unit. This is a quantity calculation, not an
    expiry model. Positive drift is reported rather than disguised as a buffer.
    demand is a callable on the day index or a constant Fraction/int.
    """
    horizon = math.lcm(demand_period, *(s["days"] for s in streams))
    total = Fraction()
    minimum = Fraction()
    high = Fraction()
    end_balances = []
    supplied = Fraction()
    consumed = Fraction()
    for day in range(horizon):
        delivery = sum(s["quantity"] for s in streams
                       if day % s["days"] == s.get("phase", 0) % s["days"])
        supplied += delivery
        total += delivery
        high = max(high, total)
        eaten = demand(day) if callable(demand) else demand
        consumed += eaten
        total -= eaten
        minimum = min(minimum, total)
        end_balances.append(total)
    buffer = -minimum
    return {
        "period_days": horizon,
        "supply": number(supplied),
        "demand": number(consumed),
        "net_change_per_period": number(total),
        "quantity_balanced": total == 0,
        "minimum_synthetic_opening_buffer": number(buffer),
        "peak_after_delivery_with_that_buffer": number(high + buffer),
        "mean_end_of_day_stock_with_that_buffer": number(
            sum(end_balances, Fraction()) / horizon + buffer),
        "limitations": "No expiry, age-state recurrence, price or courier proof. The synthetic buffer is not credited as owned stock.",
    }


def stream(quantity, days, phase=0, food=None):
    value = {"quantity": quantity, "days": days, "phase": phase}
    if food:
        value["food"] = food
    return value


def egg_demand(day, tempeh_phase=8):
    # Two identical 14-day rotations: 3 Tempeh, 6 Egg and 5 Fish dinners.
    # Fish: 2 Salmon, 2 Mackerel, 1 Sardine; Lunch Fish remains separate.
    return 4 if (day - tempeh_phase) % 14 in (3, 5, 7, 9, 11, 13) else 0


def phase_candidates(anchor):
    """Keep active357 at day0 and361 at day8; search two added phases.

    Add /28 Egg and Oat lines to357 only as a proposed future composition.
    The /21 Egg+Oat lines can share a basket; /60 Eggs need their own qualifying
    mixed basket. Shipping and stock transition remain explicit release gates.
    """
    candidates = []
    for p21 in range(21):
        oat_streams = [stream(300, 28, 0), stream(300, 21, p21)]
        oats = inventory(oat_streams, 25)
        for p60 in range(60):
            eggs = [stream(10, 14, 8), stream(10, 28, 0),
                    stream(10, 21, p21), stream(10, 60, p60)]
            check = inventory(eggs, egg_demand, 14)
            candidates.append((check["peak_after_delivery_with_that_buffer"],
                               oats["peak_after_delivery_with_that_buffer"],
                               check["mean_end_of_day_stock_with_that_buffer"],
                               p21, p60, check, oats))
    # An explicit practical ranking, not the full normalized-freshness objective.
    best = min(candidates, key=lambda c: c[:5])
    _, _, _, p21, p60, eggs, oats = best
    return {
        "selection_rule": "Lowest modeled Egg peak, then Oat peak, then Egg mean stock; preserve both active delivery phases. Not a global freshness optimum.",
        "phase_search_count": len(candidates),
        "anchor_date": anchor.isoformat(),
        "phase_21_days": p21,
        "phase_60_days": p60,
        "illustrative_21_day_date": (anchor + timedelta(days=p21)).isoformat(),
        "illustrative_60_day_date": (anchor + timedelta(days=p60)).isoformat(),
        "date_status": "Relative steady-state model only; no first date is booked or released against estimated opening stock.",
        "eggs": eggs,
        "oats": oats,
        "proposed_baskets": [
            {"id": "A28-amendment", "days": 28, "phase": 0,
             "additions": {"eggs_10": 1, "oats_300": 1},
             "status": "Not saved; Oat price gate must pass; existing357 contents/quote must be reverified after any change."},
            {"id": "C21", "days": 21, "phase": p21,
             "contents": {"eggs_10": 1, "oats_300": 1},
             "status": "Test basket only. Add only separately due approved food; never shipping filler. Free courier unverified."},
            {"id": "D60", "days": 60, "phase": p60,
             "contents": {"eggs_10": 1},
             "status": "A core to share with genuinely due60-day food, not a free-delivery Egg-only promise."},
        ],
    }


def nut_scenarios(operational=None):
    operational = operational or {}
    current = [stream(800, 90, 0), stream(1000, 90, 40)]
    old = [stream(g, 90, p) for g, p in zip(
        (300, 500, 300, 350, 150, 200), (0, 15, 30, 45, 60, 75))]
    # Same exact90-day food mix, each pack separate. Integer-day phases near its
    # consumption midpoint; model is aggregate mass and flags species remnants.
    packs = [stream(300, 90, 0, "walnuts"), stream(150, 90, 15, "pistachios"),
             stream(350, 90, 22, "almonds"), stream(300, 90, 40, "walnuts"),
             stream(150, 90, 55, "pistachios"), stream(200, 90, 62, "macadamias"),
             stream(200, 90, 72, "macadamias"), stream(150, 90, 82, "pistachios")]
    four = []
    for periods in itertools.product(CYCLES, repeat=4):
        ss = [stream(g, d) for g, d in zip((300, 150, 350, 200), periods)]
        if rate(ss) == 20:
            four.append({"periods_walnut_pistachio_almond_macadamia": periods,
                         "daily_grams": [number(Fraction(s["quantity"], s["days"])) for s in ss],
                         "status": "Quantity alternative only; changes the prior variety shares and is not selected."})
    return {
        "current_two_groups_90_days": {
            "streams": current,
            "inventory_g": inventory(current, 20),
            "nut_grams_per_90_days": {"walnuts": 600, "pistachios": 450, "almonds": 350, "macadamias": 400},
            "A_contents_g": {"walnuts": 300, "pistachios": 300, "macadamias": 200},
            "B_contents_g": {"walnuts": 300, "pistachios": 150, "almonds": 350, "macadamias": 200},
            "dated_checkout_evidence": operational.get("nut_groups", {}),
            "accepted_for_activation": False,
            "status": "Current preparation candidate. Both repeat every90days, B40days after A. Exact aggregate20g/day and preserved90day species shares; not an activated subscription or a species-level usable-life proof.",
            "portion_caveat": "150g Pistachio and350g Almond packs leave10g at20g portions. Verify same-food remainder use and opened life; unknown combined opening Nuts do not establish species-specific coverage.",
        },
        "existing_proposal_six_groups": {"streams": old, "inventory_g": inventory(old, 20),
                                         "status": "Historical arithmetic comparison; not the current activation proposal."},
        "same_mix_eight_pack_phases": {
            "streams": packs, "inventory_g": inventory(packs, 20),
            "status": "Historical lower-stock arithmetic comparison; no standalone Nut orders authorized or shipping verified. Co-group only with genuinely due food on the same cycle.",
            "portion_caveat": "150g Pistachio and350g Almond packs leave10g at20g portions. The report is a mass lower bound, not a species-level eating plan. Resolve the same-food remainder and its opened life; never combine different Nuts into a CHOOSE ONE serving.",
        },
        "four_one_pack_stream_alternatives": four,
    }


def practical_alternatives(model):
    operational = model.get("operational_evidence", {})
    pantry_b_quote = operational.get("pantry_B_checkout", {})
    pantry_b_rejected = pantry_b_quote.get("native_plan_status") in {
        "rejected_paid_home_courier", "retired_paid_courier_and_excess_macadamia_rate"}
    monthly = []
    for phase in range(10):
        streams = [stream(10, 14, 8)] + [stream(10, 30, phase + p) for p in (0, 10, 20)]
        check = inventory(streams, egg_demand, 14)
        monthly.append((check["peak_after_delivery_with_that_buffer"],
                        check["mean_end_of_day_stock_with_that_buffer"], phase, check))
    best = min(monthly)
    oat500 = []
    for phase in range(60):
        check = inventory([stream(500, 30), stream(500, 60, phase)], 25)
        oat500.append((check["peak_after_delivery_with_that_buffer"],
                       check["mean_end_of_day_stock_with_that_buffer"], phase, check))
    best500 = min(oat500)
    return {
        "monthly_egg_clusters": {
            "streams": [stream(10, 14, 8)] + [stream(10, 30, best[2] + p) for p in (0, 10, 20)],
            "inventory_eggs": best[3],
            "benefit": "Three new monthly fresh cores10days apart, retaining361. More evenly spaced new grocery cores than21/28/60, but dates drift across weekdays and free delivery remains unverified.",
            "status": "Alternative to the21/28/60 additions, not additional to them."
        },
        "oats_500_30_plus_60": {
            "streams": [stream(500, 30), stream(500, 60, best500[2])],
            "inventory_g": best500[3],
            "verified_new_product": model["new_verified_oat500"],
            "status": "Exact25g/day. Two native rate cores; dates/composition/courier need checkout."
        },
        "two_pantry_groups_60_days": {
            "retired": True,
            "accepted_for_activation": False,
            "status": "Retired historical composition:600g Macadamia/90days exceeds the intended400g by200g, despite aggregate Nut mass balancing. The tested B also failed free home courier. Do not revive as a current proposal.",
            "A": {"phase": 0, "days": 60,
                  "contents": {"oats_1000": 1, "walnuts_300": 1, "pistachios_150": 1, "almonds_350": 1},
                  "first_goods_reference_pln": 113.46,
                  "illustrative_ten_percent_goods_pln": 102.11},
            "B": {"phase": 40, "days": 60,
                  "contents": {"oats_500": 1, "macadamias_200": 2},
                  "first_goods_reference_pln": 79.27,
                  "illustrative_ten_percent_goods_pln": 71.34,
                  "live_checkout": pantry_b_quote,
                  "accepted_for_activation": False},
            "oats_inventory_g": inventory([stream(1000, 60), stream(500, 60, 40)], 25),
            "nuts_inventory_g": inventory([stream(800, 60), stream(400, 60, 40)], 20),
            "nut_grams_per_60_days": {"walnuts": 300, "pistachios": 150, "almonds": 350, "macadamias": 400},
            "tradeoff": "Historical arithmetic only: exact aggregate25g Oats/day and20g Nuts/day, but600g Macadamia/90days instead of the intended400g, plus altered shares of the other Nuts. This composition does not preserve the agreed rotation.",
            "shipping": (
                "Standalone B rejected:79.27zł goods +9.49zł GLS home courier =88.76zł; only pickup is free. A remains unquoted. Arithmetic balance does not make this pair an accepted schedule. No filler or assumed fee waiver."
                if pantry_b_rejected else
                "Both groups unquoted. Group B's79.27zł cannot inherit free shipping. Do not add filler; if no genuinely due compatible items qualify, keep this alternative unaccepted."
            ),
            "transition": "Retired: do not configure this pair. The current NutA/B90day candidate is separate from the outstanding Oat route."
        }
    }


def forecast_reviews(model):
    opening_date = date.fromisoformat(model["opening_stock"]["reported_on"])
    today = date.fromisoformat(model["as_of"])
    latest = {}
    for observation in model.get("stock_observations", []):
        reported_on = date.fromisoformat(observation["reported_on"])
        if reported_on > today or reported_on < opening_date:
            continue
        key = (observation["group"], observation["unit"])
        if key not in latest or reported_on >= latest[key][0]:
            latest[key] = (reported_on, observation)
    values = [
        ("combined Nuts", Fraction(500), Fraction(20), 7),
        ("combined Flax/Chia", Fraction(650), Fraction(7), 14),
        ("Pumpkin", Fraction(350), Fraction(7), 7),
        ("Matcha", Fraction(200), Fraction(2), 14),
        ("Phileos", Fraction(250) * Fraction(915, 1000), Fraction(27, 2), 7),
        ("Soy Milk if chosen every day", Fraction(2000), Fraction(200), 7),
        # There is no observed opening Oat balance in the historical register.
        # A paid/incoming bag is not stock available to consume.
        ("Rolled Oats", None, Fraction(25), 7),
    ]
    result = []
    for name, initial, daily, lead in values:
        unit = "ml" if name == "Soy Milk if chosen every day" else "g"
        start = opening_date
        source = "Original opening-stock estimate"
        if (name, unit) in latest:
            start, observation = latest[(name, unit)]
            initial = Fraction(str(observation["quantity"]))
            source = observation.get("source", "Dated stock observation")
        if initial is None:
            continue
        if initial < 0:
            raise ValueError(f"Negative stock observation for {name}")
        days = (today - start).days
        complete = initial // daily
        next_need = start + timedelta(days=int(complete))
        result.append({
            "food": name,
            "stock_reported_on": start.isoformat(),
            "stock_reference_quantity": number(initial),
            "unit": unit,
            "stock_source": source,
            "forecast_remaining_before_today_use": number(max(0, initial - days * daily)),
            "first_forecast_not_fully_supplied_day": next_need.isoformat(),
            "review_no_later_than": max(today, next_need - timedelta(days=lead)).isoformat(),
            "forecast_only": True,
        })
    observations_without_depletion = []
    if ("Eggs", "count") in latest:
        reported_on, eggs = latest[("Eggs", "count")]
        observations_without_depletion.append({
            "food": "Eggs",
            "stock_reported_on": reported_on.isoformat(),
            "reported_quantity": eggs["quantity"],
            "unit": "count",
            "stock_source": eggs.get("source", "Dated stock observation"),
            "forecast_depletion_date": None,
            "reason": "Apply the actual dinner rotation and edible weights; no daily-average depletion or incoming carton is assumed.",
        })
    return {
        "assumptions": "Use the latest dated stock observation on or before as_of for each exact group/unit; otherwise retain the original opening-stock estimate. Forecast daily use from that reference, assuming the balance precedes that day's serving. Before/after-serving timing, measured quantities, consumption and expiry remain unverified. Combined Nut mass does not identify species or guarantee complete same-food portions. Incoming orders are excluded until receipt is established.",
        "reviews": result,
        "observations_without_depletion_forecast": observations_without_depletion,
        "oat_rule": "Forecast currently reported Oats separately from incoming food. The paid1kg supplies40 written servings only after actual receipt and consumption begin; those dates remain unknown. An empty current balance is an immediate coverage gap, not covered by a dispatch estimate.",
        "fresh_stock": "357 parcel arrived18September, reported by root's live review. Use its Kiwi/Tomatoes/Mushrooms by actual condition, measured yield and label dates; do not infer today's consumption.",
        "native_only": "Forecasts inform initial retailer configuration. No routine skips, date corrections, manual bridge purchases or Codex-managed reorder cycle count as an accepted solution."
    }


def premium(subscription_price, pack_g, manual_price, manual_g, cap):
    ratio = Fraction(str(subscription_price)) / pack_g / (
        Fraction(str(manual_price)) / manual_g)
    pct = (ratio - 1) * 100
    return {"premium_percent": number(pct), "within_goods_only_cap": pct <= cap,
            "limitations": "Goods-only screen; current matching delivered prices, compulsory fees and tax still require checkout verification."}


def derive(model):
    eggs_current = [stream(10, 14, 8)]
    six_tempeh = 3 * 28 // 14
    portions = model["protocol_requirements"]
    anchor = date.fromisoformat(model["steady_state_anchor"])
    prices = model["dated_price_references"]
    oat_price = prices["oats_300_first_pln"]
    manual = prices["oats_equivalent_1000_manual_pln"]
    return {
        "as_of": model["as_of"],
        "operational_evidence_separate_from_arithmetic": model.get("operational_evidence", {}),
        "active_coverage_per_28_days": {
            "recurring_food_count": 9,
            "tempeh_dinners": {"supplied": six_tempeh, "required": 6},
            "nominal_eggs": {"supplied": number(rate(eggs_current) * 28), "required": 48, "gap": 28},
            "egg_dinners_approximate": {"supplied": 5, "required": 12, "gap": 7},
            "fish_dinners": {"supplied": 0, "required": 10},
            "lunch_protein_choices": {"supplied": 0, "required": 28},
            "berries": {"strawberry_g_gross": 900, "maximum_portion_equivalents_before_hulling": 6, "required": 28, "minimum_gap": 22},
            "mushrooms": {"full_75g_choices": 4, "separate_oyster_remainder_g": 50, "separate_shiitake_remainder_g": 50, "required": 28},
            "whole_fruit": {"gross_g": 3200, "upper_150g_equivalents_before_peeling": number(Fraction(3200, 150)), "required": 28},
            "mediterranean_vegetable_choices": {"nominal_tomato_choices": 10, "required": 28},
            "colorful_vegetable_choices": {"butternut_gross_g": 2000, "upper_choices_before_preparation": 20, "required": 28},
            "other_categories": portions["not_supplied_by_active_renewals"],
        },
        "egg_oat_minimum_new_interval_proposal": phase_candidates(anchor),
        "oat_price_screen": {
            "first": premium(oat_price, 300, manual, 1000, 25),
            "ten_percent_example": premium(round(oat_price * .9, 2), 300, manual, 1000, 25),
            "fifteen_percent_example": premium(round(oat_price * .85, 2), 300, manual, 1000, 25),
            "decision": "Hold300g route if current delivered comparison confirms more than25% premium. Do not compensate using savings on unrelated foods.",
        },
        "nut_comparisons": nut_scenarios(model.get("operational_evidence", {})),
        "activation_rollout": model.get("activation_rollout", {}),
        "practical_additional_alternatives": practical_alternatives(model),
        "forecast_stock_reviews": forecast_reviews(model),
        "restricted_native_impossibilities": [
            {"food": "each7g/day Seed category", "native_period_lcm_days": 1260,
             "required_g": 8820, "pack_quantum_g": 50, "remainder_g": 20,
             "scope": "Only if all usable pack sizes are multiples of50g and only the seven documented intervals exist. A new pack/cycle/native variable pattern can change the result."},
            {"food": "25g/day Oats using only1kg bags", "native_period_lcm_days": 1260,
             "required_g": 31500, "pack_quantum_g": 1000, "remainder_g": 500,
             "scope": "Same restricted intervals; mixed smaller packs or a verified40-day1kg native cycle can solve quantity without changing the diet."},
        ],
        "native_only_verdict": "Current whole-Diet candidate is not feasible with demonstrated routes. Exact subcategory rates below are candidates only: remaining exact-food native routes, free courier, price caps, first starts and usable lives are unresolved. Restricted Seed/1kg-Oat arithmetic impossibilities are not claims about every possible future retailer offer.",
        "not_proven": ["Full diet automation", "New-basket free home courier", "Actual usable lives", "Food-specific opening-stock depletion", "Future discount tiers", "Global freshness optimality"],
    }


def markdown(result):
    p = result["egg_oat_minimum_new_interval_proposal"]
    stock = result["forecast_stock_reviews"]
    practical = result["practical_additional_alternatives"]
    current_nuts = result["nut_comparisons"]["current_two_groups_90_days"]
    operational = result.get("operational_evidence_separate_from_arithmetic", {})
    rollout = result.get("activation_rollout", {})
    nut_a = operational.get("nut_A_final_checkout", {})
    nut_status = (f"Nut A subscription{nut_a['subscription_id']}: {nut_a['status']}; Nut B remains unactivated."
                  if nut_a.get("order_submitted") else
                  "Unactivated; renewal courier, usable life and remainder allocation remain to verify.")
    lines = ["# Diet subscription rollout: stock and native candidates", "",
             f"As of {result['as_of']}. Offline analysis; no retailer changes or new activations.", "",
             "| Latest stock reference | Reported balance | Estimated first uncovered day |",
             "| --- | --- | --- |"]
    for item in stock["reviews"]:
        if item["food"] in {"combined Nuts", "Rolled Oats"}:
            lines.append(f"| {item['food']} ({item['stock_reported_on']}) | {item['stock_reference_quantity']:g}{item['unit']} | {item['first_forecast_not_fully_supplied_day']} |")
    for item in stock["observations_without_depletion_forecast"]:
        lines.append(f"| {item['food']} ({item['stock_reported_on']}) | {item['reported_quantity']} {item['unit']} | Unassigned: actual dinner rotation and edible weight required |")
    lines += ["", "Stock dates assume the reported balance precedes that day's serving. Estimates are not observed depletion; incoming food is not credited before receipt. Combined Nut mass does not establish complete same-food portions.", "",
              "| Current native candidate | Quantity model and readiness |", "| --- | --- |",
              f"| NutA800g + NutB1000g, each every90days | B40days after A; exact20g/day; aggregate peak{current_nuts['inventory_g']['peak_after_delivery_with_that_buffer']:g}g. {nut_status} |",
              f"| Oats500g/30days +500g/60days | Exact25g/day; aggregate peak{practical['oats_500_30_plus_60']['inventory_g']['peak_after_delivery_with_that_buffer']:g}g. Qualifying shipments and first starts unverified. |",
              f"| Existing Eggs10/14days + three10/30day cores | Exact48 nominal Eggs/28days; extra monthly cores10days apart; modeled peak{practical['monthly_egg_clusters']['inventory_eggs']['peak_after_delivery_with_that_buffer']:g}. Free courier and usable life unverified. |"]
    nut_quote = current_nuts["dated_checkout_evidence"]
    if nut_quote:
        lines += ["", f"Historical NutA/B first-checkout evidence ({nut_quote['observed_on']}): {nut_quote['A']['first_goods_pln']:.2f} / {nut_quote['B']['first_goods_pln']:.2f}zł goods, {nut_quote['first_home_courier_pln']:.2f}zł {nut_quote['first_home_courier']} home courier. These earlier first quotes alone do not establish discounted renewals."]
    if nut_a.get("order_submitted"):
        lines += ["", f"Nut A order{nut_a['order_id']}: {nut_a['first_total_pln']:.2f}zł after coupon{nut_a.get('coupon', '')}; initial payment verified: {nut_a.get('initial_payment_verified', False)}; recurring card verified: {nut_a.get('card_on_profile', False)}. Current renewal quote{nut_a['displayed_recurring_charge_pln']:.2f}zł with{nut_a['home_courier_pln']:.2f}zł home courier. Delivery/consumption are not inferred from payment."]
    if rollout:
        lines += ["", f"NutA activation target: {rollout.get('nut_A_activation_target', 'unassigned')} ({rollout.get('nut_A_status', 'not released')}). NutB timing: {rollout.get('nut_B_arrival_rule', 'unassigned')}.",
                  "Full-automation completion date: " + (rollout.get("full_automation_completion_date") or "unassigned; qualifying routes and repeated whole-diet coverage are not yet established.")]
    lines += ["", "| Existing recurring coverage | Result |", "| --- | --- |",
             "| Active Tempeh |6/6 dinners per28days |",
             "| Active Eggs |20/48 nominal Eggs; approximately7 Egg dinners still uncovered |",
             "| Active Berries |At most6/28 portions before hulling |"]
    lines += ["", "Historical arithmetic comparisons (not activation instructions):", "",
              f"- Earlier Eggs10/14/21/28/60days: peak{p['eggs']['peak_after_delivery_with_that_buffer']:g}, synthetic buffer{p['eggs']['minimum_synthetic_opening_buffer']:g}. The buffer is not owned stock.",
              f"- Earlier Oats300g/21days +300g/28days: peak{p['oats']['peak_after_delivery_with_that_buffer']:g}g; dated price benchmark fails the cap. Relative phases21day:{p['phase_21_days']},60day:{p['phase_60_days']} against{p['anchor_date']} are not booked dates.",
              "- Retired mixed60-day PantryA/B: " + practical['two_pantry_groups_60_days']['tradeoff'] + " " + practical['two_pantry_groups_60_days']['shipping']]
    for name, scenario in result["nut_comparisons"].items():
        if name != "current_two_groups_90_days" and isinstance(scenario, dict) and "inventory_g" in scenario:
            inv = scenario["inventory_g"]
            lines.append(f"- {name}: peak {inv['peak_after_delivery_with_that_buffer']:g}g; net drift {inv['net_change_per_period']:g}g/{inv['period_days']}days. Aggregate only; species remnants and courier require checks.")
    selected_eggs = operational.get("selected_organic_eggs", operational.get("egg_product", {}))
    if selected_eggs.get("available_for_new_checkout") is False:
        lines.append(f"- Selected Egg SKU{selected_eggs.get('sku', 'unverified')} is unavailable for a new checkout. Additional Egg streams cannot be treated as purchasable; this does not establish a problem with paid361's reserved carton.")
    elif selected_eggs.get("available_for_new_checkout") is True:
        lines.append(f"- Selected Egg SKU{selected_eggs.get('sku', 'unverified')} is listed available; its own matched delivered-price, free-courier and remaining-life checks still control activation. Paid361's original carton remains separate.")
    lines += ["", "Retailer subscriptions only: no managed routine skipping, manual bridge shopping or Codex reordering is counted as coverage.", "New baskets do not inherit existing free delivery. Never add unused food to reach a threshold. More than25% matched delivered premium is not permitted."]
    return "\n".join(lines)


def self_test():
    balanced = inventory([stream(300, 21), stream(300, 28, 4)], 25)
    assert balanced["quantity_balanced"] and balanced["supply"] == 2100
    assert rate([stream(10, p) for p in (14, 21, 28, 60)]) * 28 == 48
    assert sum(egg_demand(d) for d in range(28)) == 48
    bad = inventory([stream(1000, 90), stream(1000, 90, 30), stream(300, 90, 60)], 25)
    assert bad["net_change_per_period"] == 50
    for value in nut_scenarios().values():
        if isinstance(value, dict) and "inventory_g" in value:
            assert value["inventory_g"]["quantity_balanced"]
    nut_pair = nut_scenarios()["current_two_groups_90_days"]
    assert nut_pair["inventory_g"]["supply"] == 1800
    assert nut_pair["inventory_g"]["peak_after_delivery_with_that_buffer"] == 1000
    assert nut_pair["nut_grams_per_90_days"]["macadamias"] == 400
    assert sum(nut_pair["nut_grams_per_90_days"].values()) == 1800
    assert not premium(4.85, 300, 11.92, 1000, 25)["within_goods_only_cap"]
    probe = {"new_verified_oat500": {}, "operational_evidence": {
        "pantry_B_checkout": {"native_plan_status": "rejected_paid_home_courier"}}}
    options = practical_alternatives(probe)
    pair = options["two_pantry_groups_60_days"]
    assert pair["B"]["accepted_for_activation"] is False
    assert "Standalone B rejected" in pair["shipping"]
    assert pair["oats_inventory_g"]["quantity_balanced"]
    assert options["monthly_egg_clusters"]["inventory_eggs"]["quantity_balanced"]
    probe["operational_evidence"]["pantry_B_checkout"]["native_plan_status"] = "retired_paid_courier_and_excess_macadamia_rate"
    retired_pair = practical_alternatives(probe)["two_pantry_groups_60_days"]
    assert retired_pair["retired"] and not retired_pair["accepted_for_activation"]
    assert "Standalone B rejected" in retired_pair["shipping"]
    assert "Both groups unquoted" not in retired_pair["shipping"]
    assert "200g" in retired_pair["status"]
    stock_probe = {
        "opening_stock": {"reported_on": "2026-09-14"},
        "as_of": "2026-09-23",
        "stock_observations": [
            {"reported_on": "2026-09-23", "group": "combined Nuts", "quantity": 100, "unit": "g", "source": "user estimate"},
            {"reported_on": "2026-09-20", "group": "combined Nuts", "quantity": 180, "unit": "g"},
            {"reported_on": "2026-09-24", "group": "combined Nuts", "quantity": 800, "unit": "g"},
            {"reported_on": "2026-09-23", "group": "Rolled Oats", "quantity": 0, "unit": "g"},
            {"reported_on": "2026-09-23", "group": "Eggs", "quantity": 10, "unit": "count"},
        ],
    }
    stock_check = forecast_reviews(stock_probe)
    by_food = {item["food"]: item for item in stock_check["reviews"]}
    assert by_food["combined Nuts"]["stock_reported_on"] == "2026-09-23"
    assert by_food["combined Nuts"]["forecast_remaining_before_today_use"] == 100
    assert by_food["combined Nuts"]["first_forecast_not_fully_supplied_day"] == "2026-09-28"
    assert by_food["combined Nuts"]["stock_source"] == "user estimate"
    assert by_food["Rolled Oats"]["first_forecast_not_fully_supplied_day"] == "2026-09-23"
    assert by_food["Rolled Oats"]["forecast_remaining_before_today_use"] == 0
    assert by_food["Matcha"]["stock_reported_on"] == "2026-09-14"
    assert "Eggs" not in by_food
    assert stock_check["observations_without_depletion_forecast"][0]["forecast_depletion_date"] is None
    stock_probe["stock_observations"] = []
    fallback = {item["food"]: item for item in forecast_reviews(stock_probe)["reviews"]}
    assert fallback["combined Nuts"]["first_forecast_not_fully_supplied_day"] == "2026-10-09"
    assert "Rolled Oats" not in fallback
    print("Exact rates, discrete Egg pattern, Oat drift, Nut balance, price-cap and dated stock forecast checks passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--update-analysis", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    model = json.loads(args.model.read_text(encoding="utf-8"))
    result = derive(model)
    if args.update_analysis:
        model["derived_analysis"] = result
        args.model.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else markdown(result))


if __name__ == "__main__":
    main()
