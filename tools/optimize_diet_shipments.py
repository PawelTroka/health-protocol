"""Offline shipment-cost and Egg-age comparison; never touches retailer accounts.

Prices are a dated public snapshot, not checkout quotes. The search preserves the
specified180-day pack demand and explores nine Pistachio/Cumin cadence choices.
It is not a solver for unavailable merchant capabilities or the entire Diet.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import deque
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'diet' / 'DIET_SHIPMENT_REOPTIMIZATION.json'
CATALOG = {
    '44492': ('Walnuts300g', 300, 2299, 1954),
    '53019': ('Pistachios150g', 150, 4369, 3714),
    '45420': ('Almonds350g', 350, 2839, 2413),
    '44472': ('Macadamias200g', 200, 3409, 2898),
    '46956': ('Rolled Oats1kg', 1000, 1459, 1240),
    '52572': ('Rolled Oats500g', 500, 1189, 1011),
    '46308': ('Coriander Seed30g', 30, 599, 509),
    '46323': ('Rosemary30g', 30, 719, 611),
    '46593': ('Cumin Seed30g', 30, 829, 705),
    '44499': ('White Quinoa500g', 500, 1759, 1495),
    '44959': ('Beluga Lentils400g', 400, 1629, 1385),
    '49356': ('Black Beans500g', 500, 1179, 1002),
    '46317': ('Oregano20g', 20, 669, 569),
    '46325': ('Thyme20g', 20, 599, 509),
}
CORE60 = {'46956': 1, '52572': 1, '46308': 1, '46323': 1,
          '46317': 1, '46325': 1}
CORE90 = {'44492': 2, '45420': 1, '44472': 2, '44499': 1,
          '44959': 1, '49356': 1}


def money(cents):
    return round(cents / 100, 2)


def shipping(goods_cents, logistics_cents, target_cents=10000):
    return {
        'goods_pln': money(goods_cents),
        'logistics_pln': money(logistics_cents),
        'logistics_percent': round(100 * logistics_cents / goods_cents, 4),
        'at_least_100_goods': goods_cents >= target_cents,
        'logistics_at_most_10_percent': 10 * logistics_cents <= goods_cents,
        'minimum_goods_for_ratio_pln': money(10 * logistics_cents),
        'maximum_logistics_pln': money(goods_cents // 10),
    }


def group_summary(days, packs):
    regular = sum(CATALOG[sku][3] * n for sku, n in packs.items())
    ordinary = sum(CATALOG[sku][2] * n for sku, n in packs.items())
    return {
        'days': days,
        'packs': packs,
        'pack_count': sum(packs.values()),
        'ordinary_goods_pln': money(ordinary),
        'advertised_later_goods_pln': money(regular),
        'net_food_mass_g': sum(CATALOG[sku][1] * n for sku, n in packs.items()),
        'shipping_scenarios': [shipping(regular, fee) for fee in (0, 949, 1299, 1499)],
        'maximum_logistics_pln': money(regular // 10),
    }


def pantry_search():
    candidates = []
    for pistachio_days, cumin_days in itertools.product((30, 60, 90), repeat=2):
        groups = {60: dict(CORE60), 90: dict(CORE90)}
        for sku, days in [('53019', pistachio_days), ('46593', cumin_days)]:
            groups.setdefault(days, {})[sku] = days // 30
        summaries = [group_summary(d, p) for d, p in sorted(groups.items())]
        feasible = all(g['advertised_later_goods_pln'] >= 100 for g in summaries)
        # All candidates deliver six of each flexible pack per180days. The score
        # is the mean delivery cycle, a transparent tie-breaker for these foods;
        # no batch shelf life is inferred from it.
        mean_cycle = Fraction(pistachio_days + cumin_days, 2)
        candidates.append({
            'pistachio_days': pistachio_days, 'cumin_days': cumin_days,
            'all_shipments_at_least_100_goods': feasible,
            'shipments_per_180_days': sum(180 // g['days'] for g in summaries),
            'flexible_food_mean_delivery_cycle_days': float(mean_cycle),
            'groups': summaries,
            'goods_per_180_days_pln': round(sum(g['advertised_later_goods_pln'] * 180 / g['days'] for g in summaries), 2),
        })
    accepted = [x for x in candidates if x['all_shipments_at_least_100_goods']]
    selected = min(accepted, key=lambda x: (x['shipments_per_180_days'], x['flexible_food_mean_delivery_cycle_days']))
    # Compare against the previously saved three-interval plan, including both
    # optional herbs when showing the old small60-day group's cost.
    old = [group_summary(30, {'46593': 1}), group_summary(60, CORE60),
           group_summary(90, {**CORE90, '53019': 3})]
    return {
        'search_scope': 'Nine cadence assignments for Pistachios and Cumin among30/60/90days, holding every180-day pack quantity fixed. Strict100PLN goods screen; actual fees, per-product premium, native changes and batch usability still require verification.',
        'candidate_count': len(candidates), 'accepted_count': len(accepted),
        'candidates': candidates, 'selected': selected,
        'old_separate_renewals': old,
        'selected_180_day_food_quantities': {
            'walnut_g': 1200, 'pistachio_g': 900, 'almond_g': 700,
            'macadamia_g': 800, 'oats_g': 4500, 'cumin_g': 180,
            'coriander_g': 90, 'rosemary_g': 90,
            'oregano_g': 60, 'thyme_g': 60,
        },
        'transition_warning': 'The selected groups replace/restructure370 and the old NutB/cart design. They are not extra subscriptions to place beside them. NutA already received and current stock offset the first orders.',
    }


def egg_age(streams):
    """One steady-state FIFO cycle, beginning just after minimum inventory.

    Twelve200g dinners/28days follow the saved A/B calendar: Monday/Thursday/
    Sunday in A weeks, Monday/Wednesday/Sunday in B weeks. No actual Egg size,
    expiry or owned stock is assumed.
    """
    horizon = math.lcm(28, *(days for _, days, _ in streams))
    delivery = [0] * horizon
    for quantity, days, phase in streams:
        for day in range(phase % days, horizon, days):
            delivery[day] += quantity
    meal_days = {0, 3, 6, 7, 9, 13, 14, 17, 20, 21, 23, 27}
    demand = [4 if day % 28 in meal_days else 0 for day in range(horizon)]
    if sum(delivery) != sum(demand):
        raise ValueError('Unbalanced Egg rate')
    balance = minimum = 0
    start = 0
    for day in range(horizon):
        balance += delivery[day] - demand[day]
        if balance < minimum:
            minimum, start = balance, day + 1
    queue = deque()
    maximum_age = age_mass = peak = stock = 0
    for day in range(start, start + horizon):
        q = delivery[day % horizon]
        if q:
            queue.append([day, q])
            stock += q
        peak = max(peak, stock)
        need = demand[day % horizon]
        while need:
            if not queue:
                raise AssertionError('Minimum-inventory rotation must not run out')
            arrived, available = queue[0]
            eaten = min(need, available)
            age = day - arrived
            maximum_age = max(maximum_age, age)
            age_mass += eaten * age
            available -= eaten
            stock -= eaten
            need -= eaten
            if available:
                queue[0][1] = available
            else:
                queue.popleft()
    assert stock == 0
    return (maximum_age, age_mass / sum(demand), peak)


def egg_phase_search():
    best_small = None
    best_large = None
    small_count = large_count = 0
    for p14 in range(14):
        for base in range(10):
            streams = [(10, 14, p14)] + [(10, 30, (base + k * 10) % 30) for k in range(3)]
            score = egg_age(streams)
            small_count += 1
            if best_small is None or score < best_small[0]:
                best_small = (score, streams)
        for p30 in range(30):
            for p60 in range(60):
                streams = [(10, 14, p14), (20, 30, p30), (20, 60, p60)]
                score = egg_age(streams)
                large_count += 1
                if best_large is None or score < best_large[0]:
                    best_large = (score, streams)
    def result(best, count):
        score, streams = best
        return {'searched_phases': count,
                'arrival_and_meal_horizon_days': math.lcm(28, *(d for _, d, _ in streams)),
                'streams': [{'eggs': q, 'days': d, 'phase_day': p} for q, d, p in streams],
                'maximum_delivery_to_consumption_days': score[0],
                'mean_delivery_to_consumption_days': round(score[1], 4),
                'peak_eggs_in_stock': score[2]}
    return {
        'objective': 'Minimize oldest Egg age at consumption, then mean age, then peak stock, using the complete28-day A/B meal calendar over420days. Compare140 evenly spaced monthly-carton candidates with25200 phases of the20-Egg parcel alternative.',
        'small_cartons': result(best_small, small_count),
        'larger_parcels': result(best_large, large_count),
        'limitations': 'Synthetic repeating meal/arrival model, not a booking, delivered-life guarantee, observed stock or proof of minimum shipping on all fresh groups. Four nominal Eggs may differ from200g shell-free. Ages require an additional supplier/delay margin; the6October old-carton11-day remaining life is not transferable to selected green-legged Eggs.',
    }


def self_test():
    assert shipping(9490, 949)['logistics_at_most_10_percent']
    assert not shipping(9489, 949)['logistics_at_most_10_percent']
    p = pantry_search()
    assert p['candidate_count'] == 9 and p['accepted_count'] == 2
    selected = p['selected']
    assert selected['pistachio_days'] == selected['cumin_days'] == 60
    assert [g['advertised_later_goods_pln'] for g in selected['groups']] == [132.87, 159.99]
    assert selected['goods_per_180_days_pln'] == 718.59
    for candidate in p['candidates']:
        for sku in CATALOG:
            packs = sum(Fraction(g['packs'].get(sku, 0) * 180, g['days']) for g in candidate['groups'])
            wanted = sum(Fraction(g['packs'].get(sku, 0) * 180, g['days']) for g in selected['groups'])
            assert packs == wanted
    score = egg_age([(12, 7, 0)])
    assert score[0] == 6 and math.isclose(score[1], 17 / 6) and score[2] == 12
    print('Shipping boundary, all nine fixed-demand candidates and FIFO Egg-age checks passed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--write-analysis', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    data = {
        'as_of': '2026-10-27', 'status': 'offline_reoptimization_not_activated',
        'price_scope': 'Current public Bioshi ordinary/advertised later15% prices, unit-rounded, from27October manifest/source ledger. Not locked prices or destination checkout.',
        'requirements': {'target_goods_per_actual_shipment_pln': 100,
                         'maximum_logistics_fraction': 0.10,
                         'logistics_includes_compulsory_packing': True,
                         'maximum_comparable_product_delivered_premium_fraction': 0.25,
                         'tempeh_and_tofu_allowed': False},
        'pantry': pantry_search(), 'eggs': egg_phase_search(),
        'full_diet_verified': False,
        'full_diet_scope': 'Complete meal/category ledger is inDIET_COMPLETE_SHIPMENT_PLAN.md. This script verifies pantry grouping and Egg-age arithmetic only; it does not make unavailable products, native grocery autoship or unopened/opened shelf lives available.',
    }
    if args.write_analysis:
        OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'selected_pantry': data['pantry']['selected'], 'eggs': data['eggs'],
                      'saved_to': str(OUTPUT) if args.write_analysis else None}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
