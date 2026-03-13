"""Mutation testing — systematically mutate question parameters to find weaknesses.

Applies small perturbations to benchmark case inputs and checks if the
generator still produces valid, correct output. Mutations that cause
failures reveal fragile boundary conditions.

Mutation strategies:
  - Boundary nudge: ±1 to numeric params
  - Zero injection: set params to 0 or 1
  - Swap: exchange a/b operands
  - Extremes: use max/min allowed values
  - Template shift: use different template_index
"""
from __future__ import annotations

import copy
import json
import os
from typing import Dict, List, Optional, Tuple

from mathgen.question_templates import ALL_GENERATORS
from mathgen.validators.schema_validator import validate_question_schema
from mathgen.validators.hint_validator import validate_hint_ladder
from mathgen.scripts.run_benchmarks import load_benchmark


_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGS = os.path.join(_HERE, 'logs')
_REPORTS = os.path.join(_HERE, 'reports')


# ── Mutation operators ──────────────────────────────────────────

def _mutate_fraction(params: dict) -> List[Tuple[str, dict]]:
    """Generate mutations for fraction word problem params."""
    mutations = []
    p = copy.deepcopy(params)

    # Boundary nudge: denominators
    for key in ('a_den', 'b_den'):
        if key in p and p[key] > 1:
            m = copy.deepcopy(p)
            m[key] = p[key] - 1
            mutations.append((f'{key}_minus1', m))
        m = copy.deepcopy(p)
        m[key] = p.get(key, 2) + 1
        mutations.append((f'{key}_plus1', m))

    # Equal fractions (result = 0 for subtract)
    m = copy.deepcopy(p)
    m['b_num'] = p.get('a_num', 1)
    m['b_den'] = p.get('a_den', 2)
    mutations.append(('equal_fractions', m))

    # Swap a/b
    m = copy.deepcopy(p)
    m['a_num'], m['b_num'] = p.get('b_num', 1), p.get('a_num', 1)
    m['a_den'], m['b_den'] = p.get('b_den', 2), p.get('a_den', 2)
    mutations.append(('swap_ab', m))

    # Large denominator
    m = copy.deepcopy(p)
    m['a_den'] = 12
    m['b_den'] = 8
    mutations.append(('large_denoms', m))

    # Template shift
    tpl = p.get('template_index', 0)
    m = copy.deepcopy(p)
    m['template_index'] = (tpl + 1) % 5
    mutations.append(('template_shift', m))

    return mutations


def _mutate_decimal(params: dict) -> List[Tuple[str, dict]]:
    """Generate mutations for decimal word problem params."""
    mutations = []
    p = copy.deepcopy(params)

    # Zero operand
    m = copy.deepcopy(p)
    m['b'] = '0.0'
    mutations.append(('b_zero', m))

    # Very small values
    m = copy.deepcopy(p)
    m['a'] = '0.01'
    m['b'] = '0.01'
    mutations.append(('tiny_values', m))

    # Equal operands (result = 0 for subtract)
    m = copy.deepcopy(p)
    m['b'] = p.get('a', '1.0')
    mutations.append(('equal_operands', m))

    # Operation shift
    ops = ['add', 'subtract', 'multiply']
    current = p.get('operation', 'add')
    for op in ops:
        if op != current:
            m = copy.deepcopy(p)
            m['operation'] = op
            mutations.append((f'op_{op}', m))
            break

    # Template shift
    tpl = p.get('template_index', 0)
    m = copy.deepcopy(p)
    m['template_index'] = (tpl + 1) % 5
    mutations.append(('template_shift', m))

    return mutations


def _mutate_average(params: dict) -> List[Tuple[str, dict]]:
    """Generate mutations for average word problem params."""
    mutations = []
    p = copy.deepcopy(params)

    values = p.get('values', [80, 90, 100])

    # All zeros
    m = copy.deepcopy(p)
    m['values'] = [0] * len(values)
    mutations.append(('all_zeros', m))

    # All same
    m = copy.deepcopy(p)
    m['values'] = [values[0]] * len(values)
    mutations.append(('all_same', m))

    # Single extreme
    m = copy.deepcopy(p)
    m['values'] = values[:]
    m['values'][0] = 9999
    mutations.append(('extreme_first', m))

    # Add/remove value
    m = copy.deepcopy(p)
    m['values'] = values[:2] if len(values) > 2 else values + [50]
    mutations.append(('change_count', m))

    # Template shift
    tpl = p.get('template_index', 0)
    m = copy.deepcopy(p)
    m['template_index'] = (tpl + 1) % 4
    mutations.append(('template_shift', m))

    return mutations


def _mutate_unit_conversion(params: dict) -> List[Tuple[str, dict]]:
    """Generate mutations for unit conversion params."""
    mutations = []
    p = copy.deepcopy(params)

    # Value = 1 (known leak risk)
    m = copy.deepcopy(p)
    m['value'] = '1'
    mutations.append(('value_one', m))

    # Value = 0
    m = copy.deepcopy(p)
    m['value'] = '0'
    mutations.append(('value_zero', m))

    # Very large value
    m = copy.deepcopy(p)
    m['value'] = '99999'
    mutations.append(('value_huge', m))

    # Direction flip
    m = copy.deepcopy(p)
    m['direction'] = 'reverse' if p.get('direction') == 'forward' else 'forward'
    mutations.append(('direction_flip', m))

    # Conversion index shift
    idx = p.get('conversion_index', 0)
    m = copy.deepcopy(p)
    m['conversion_index'] = (idx + 1) % 9
    mutations.append(('conv_shift', m))

    # Decimal value
    m = copy.deepcopy(p)
    m['value'] = '0.5'
    mutations.append(('decimal_value', m))

    return mutations


_MUTATORS = {
    'fraction_word_problem': _mutate_fraction,
    'decimal_word_problem': _mutate_decimal,
    'average_word_problem': _mutate_average,
    'unit_conversion': _mutate_unit_conversion,
}


# ── Mutation runner ─────────────────────────────────────────────

def run_mutation_test(topic: str, case_index: int, case: dict) -> List[Dict]:
    """Run all mutations for a single benchmark case.

    Returns list of mutation results:
        [{
            'case_id': 'topic[i]',
            'mutation': 'mutation_name',
            'survived': bool,  # True = mutation didn't cause failure (bad)
            'killed': bool,    # True = mutation was detected (good)
            'errors': [...],
        }]
    """
    mutator = _MUTATORS.get(topic)
    if not mutator:
        return []

    gen_cls = ALL_GENERATORS.get(topic)
    if not gen_cls:
        return []

    gen = gen_cls()
    mutations = mutator(case.get('input', {}))
    results = []

    for mut_name, mut_params in mutations:
        case_id = f'{topic}[{case_index}]'
        errors = []

        try:
            q = gen.generate(params=mut_params)
        except Exception as e:
            # Mutation killed by exception — detected
            results.append({
                'case_id': case_id,
                'mutation': mut_name,
                'survived': False,
                'killed': True,
                'errors': [f'exception:{e}'],
            })
            continue

        # Schema check
        valid, schema_errs = validate_question_schema(q)
        errors.extend(schema_errs)

        # Hint check
        hint_valid, hint_errs = validate_hint_ladder(q)
        errors.extend(hint_errs)

        # Answer leak check
        answer = q.get('correct_answer', '')
        if answer and len(answer) > 1:
            for lvl in ['level_1', 'level_2', 'level_3', 'level_4']:
                hint_text = q.get('hint_ladder', {}).get(lvl, '')
                if answer in hint_text:
                    errors.append(f'hint_leaks_answer:{lvl}')

        survived = len(errors) == 0
        results.append({
            'case_id': case_id,
            'mutation': mut_name,
            'survived': survived,
            'killed': not survived,
            'errors': errors,
        })

    return results


def run_all_mutations(max_cases_per_topic: int = 5) -> Dict:
    """Run mutation testing across all topics.

    Args:
        max_cases_per_topic: Limit mutations to first N cases per topic
            to keep runtime reasonable.

    Returns:
        {
            'total_mutations': int,
            'killed': int,
            'survived': int,
            'mutation_score': float,  # killed / total (higher = better)
            'by_topic': {topic: {killed, survived, total}},
            'survivors': [surviving mutation details],
            'killed_details': [killed mutation details],
        }
    """
    all_results = []
    by_topic = {}

    for topic in ALL_GENERATORS:
        cases = load_benchmark(topic)
        if not cases:
            continue

        topic_killed = 0
        topic_survived = 0

        for i, case in enumerate(cases[:max_cases_per_topic]):
            muts = run_mutation_test(topic, i, case)
            for m in muts:
                all_results.append(m)
                if m['killed']:
                    topic_killed += 1
                else:
                    topic_survived += 1

        by_topic[topic] = {
            'killed': topic_killed,
            'survived': topic_survived,
            'total': topic_killed + topic_survived,
        }

    total = len(all_results)
    killed = sum(1 for r in all_results if r['killed'])
    survived = total - killed
    score = killed / total if total > 0 else 0.0

    survivors = [r for r in all_results if r['survived']]
    killed_details = [r for r in all_results if r['killed']]

    return {
        'total_mutations': total,
        'killed': killed,
        'survived': survived,
        'mutation_score': score,
        'by_topic': by_topic,
        'survivors': survivors,
        'killed_details': killed_details,
    }


# ── Auto-promotion candidates ──────────────────────────────────

def find_promotion_candidates(
    mutation_results: Dict,
    min_kill_rate: float = 0.8,
) -> List[Dict]:
    """Identify benchmark cases suitable for gold bank promotion.

    A case is a promotion candidate if:
    1. It passes all benchmarks (assumed — only called after full pass)
    2. Its mutations achieve ≥ min_kill_rate
    3. It's not in a known vulnerability pattern

    Returns list of candidate dicts.
    """
    # Group kills/survives by case_id
    case_stats = {}
    for topic_data in mutation_results['by_topic'].items():
        pass  # We need per-case data, not per-topic

    case_kills = {}
    case_total = {}
    for r in mutation_results.get('survivors', []) + mutation_results.get('killed_details', []):
        cid = r['case_id']
        case_total[cid] = case_total.get(cid, 0) + 1
        if r['killed']:
            case_kills[cid] = case_kills.get(cid, 0) + 1

    candidates = []
    for cid in case_total:
        total = case_total[cid]
        kills = case_kills.get(cid, 0)
        kill_rate = kills / total if total > 0 else 0
        if kill_rate >= min_kill_rate:
            candidates.append({
                'case_id': cid,
                'kill_rate': kill_rate,
                'mutations_tested': total,
                'mutations_killed': kills,
                'eligible_for_gold': True,
            })

    candidates.sort(key=lambda x: x['kill_rate'], reverse=True)
    return candidates


# ── Report ──────────────────────────────────────────────────────

def generate_mutation_report(
    mutation_results: Dict,
    candidates: List[Dict],
) -> str:
    """Generate a markdown report of mutation testing results."""
    lines = [
        '# Mutation Testing Report',
        '',
    ]

    total = mutation_results['total_mutations']
    killed = mutation_results['killed']
    survived = mutation_results['survived']
    score = mutation_results['mutation_score']

    lines.append('## Summary')
    lines.append('')
    lines.append(f'| Metric | Value |')
    lines.append(f'|--------|-------|')
    lines.append(f'| Total mutations | {total} |')
    lines.append(f'| Killed (detected) | {killed} |')
    lines.append(f'| Survived (undetected) | {survived} |')
    lines.append(f'| Mutation score | {score:.1%} |')
    lines.append('')

    # Per-topic
    lines.append('## Per-Topic Results')
    lines.append('')
    lines.append('| Topic | Killed | Survived | Total | Score |')
    lines.append('|-------|--------|----------|-------|-------|')
    for topic, stats in sorted(mutation_results['by_topic'].items()):
        t_total = stats['total']
        t_killed = stats['killed']
        t_score = t_killed / t_total if t_total > 0 else 0
        lines.append(f"| {topic} | {t_killed} | {stats['survived']} | {t_total} | {t_score:.1%} |")
    lines.append('')

    # Survivors (weaknesses)
    survivors = mutation_results.get('survivors', [])
    if survivors:
        lines.append('## Surviving Mutations (Weaknesses)')
        lines.append('')
        lines.append('These mutations were NOT detected — potential blind spots:')
        lines.append('')
        lines.append('| Case | Mutation | Notes |')
        lines.append('|------|----------|-------|')
        for s in survivors[:20]:
            lines.append(f"| {s['case_id']} | {s['mutation']} | survived |")
        if len(survivors) > 20:
            lines.append(f'| ... | +{len(survivors) - 20} more | |')
        lines.append('')

    # Promotion candidates
    if candidates:
        lines.append('## Gold Bank Promotion Candidates')
        lines.append('')
        lines.append('Cases with high mutation kill rates (robust validations):')
        lines.append('')
        lines.append('| Case | Kill Rate | Tested | Killed |')
        lines.append('|------|-----------|--------|--------|')
        for c in candidates[:10]:
            lines.append(
                f"| {c['case_id']} | {c['kill_rate']:.0%} | "
                f"{c['mutations_tested']} | {c['mutations_killed']} |"
            )
        lines.append('')

    return '\n'.join(lines)
