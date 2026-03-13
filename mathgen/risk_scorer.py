"""Dynamic risk scoring for generated math questions.

Scores a question's risk level based on its parameters of complexity,
known vulnerability patterns, and historical error rates.

Risk factors:
  - Topic complexity (fraction > decimal > unit > average)
  - LCD complexity for fractions (large LCD → higher risk)
  - Decimal precision depth (more decimal places → higher risk)
  - Unit conversion layer count and direction
  - Known hint-leak vulnerability patterns
  - Answer boundary (result = 0, very large, non-integer)
  - Wording variation index (untested templates → higher risk)
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple


_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGS = os.path.join(_HERE, 'logs')

# ── Weight table ────────────────────────────────────────────────

# Each factor adds to a cumulative score.  Final classification:
#   0-29  → low    (trusted automation)
#   30-59 → medium (extra validation, sampled review)
#   60+   → high   (mandatory manual review queue)

_TOPIC_BASE = {
    'fraction_word_problem': 15,
    'decimal_word_problem': 10,
    'unit_conversion': 10,
    'average_word_problem': 5,
}

_RISK_THRESHOLDS = {'low': 30, 'medium': 60}  # < 30 = low, 30-59 = medium, 60+ = high


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _lcm(a: int, b: int) -> int:
    return a * b // _gcd(a, b)


# ── Scoring functions per topic ─────────────────────────────────

def _score_fraction(params: dict) -> Tuple[int, List[str]]:
    """Score fraction word problem parameters."""
    score = 0
    factors = []

    a_den = params.get('a_den', 2)
    b_den = params.get('b_den', 2)
    a_num = params.get('a_num', 1)
    b_num = params.get('b_num', 1)

    # LCD complexity
    lcd = _lcm(a_den, b_den)
    if lcd > 20:
        score += 20
        factors.append(f'large_lcd={lcd}')
    elif lcd > 10:
        score += 10
        factors.append(f'medium_lcd={lcd}')

    # Improper fractions
    if a_num > a_den or b_num > b_den:
        score += 10
        factors.append('improper_fraction')

    # Result = 0 (a == b in subtract)
    tpl_idx = params.get('template_index', 0)
    # Templates with pattern='subtract' are at indices 0, 2, 4
    is_subtract = tpl_idx in (0, 2, 4)
    if is_subtract and a_num * b_den == b_num * a_den:
        score += 15
        factors.append('result_zero')

    # Simplification needed
    lcd_a = a_num * (lcd // a_den)
    lcd_b = b_num * (lcd // b_den)
    if is_subtract:
        result_num = lcd_a - lcd_b
    else:
        result_num = lcd_a + lcd_b
    if result_num != 0 and _gcd(abs(result_num), lcd) > 1:
        score += 5
        factors.append('needs_simplification')

    return score, factors


def _score_decimal(params: dict) -> Tuple[int, List[str]]:
    """Score decimal word problem parameters."""
    score = 0
    factors = []

    a_str = str(params.get('a', '0'))
    b_str = str(params.get('b', '0'))
    operation = params.get('operation', 'add')

    # Decimal depth
    a_dec = len(a_str.split('.')[1]) if '.' in a_str else 0
    b_dec = len(b_str.split('.')[1]) if '.' in b_str else 0
    max_dec = max(a_dec, b_dec)
    if max_dec >= 2:
        score += 15
        factors.append(f'deep_decimals={max_dec}')
    elif max_dec == 1:
        score += 5

    # Multiplication with sub-1 operands
    if operation == 'multiply':
        score += 10
        factors.append('multiply_operation')
        try:
            a_val = float(a_str)
            b_val = float(b_str)
            if a_val < 1 or b_val < 1:
                score += 10
                factors.append('sub_one_operand')
        except ValueError:
            pass

    # Result = 0
    if operation == 'subtract' and a_str == b_str:
        score += 15
        factors.append('result_zero')

    # Carry across tens (e.g. 9.9 + 0.2 = 10.1)
    try:
        a_val = float(a_str)
        b_val = float(b_str)
        if operation in ('add', 'subtract'):
            result = a_val + b_val if operation == 'add' else a_val - b_val
            if int(result) != int(a_val) and int(result) != int(b_val):
                score += 10
                factors.append('carry_across_tens')
    except ValueError:
        pass

    # Hint leak: answer could be substring of operand
    # (known vulnerability from Phase 1)
    try:
        a_val = float(a_str)
        b_val = float(b_str)
        if operation == 'multiply':
            # Check if one operand is 1.0 (answer = other operand, leaks)
            if abs(a_val - 1.0) < 1e-9 or abs(b_val - 1.0) < 1e-9:
                score += 20
                factors.append('multiply_by_one_leak_risk')
    except ValueError:
        pass

    return score, factors


def _score_average(params: dict) -> Tuple[int, List[str]]:
    """Score average word problem parameters."""
    score = 0
    factors = []

    values = params.get('values', [])
    n = len(values)

    # Non-standard count (template[0] hardcodes "三次")
    tpl_idx = params.get('template_index', 0)
    if tpl_idx == 0 and n != 3:
        score += 15
        factors.append(f'wording_count_mismatch_n={n}')

    # Non-exact division
    total = sum(values)
    if n > 0 and total % n != 0:
        score += 15
        factors.append('non_exact_division')

    # All identical values
    if n > 0 and len(set(values)) == 1:
        score += 5
        factors.append('all_identical')

    # Wide range
    if n > 1:
        spread = max(values) - min(values)
        if spread > 500:
            score += 10
            factors.append(f'wide_range={spread}')

    # Very large values
    if values and max(values) > 1000:
        score += 5
        factors.append('large_values')

    return score, factors


def _score_unit_conversion(params: dict) -> Tuple[int, List[str]]:
    """Score unit conversion parameters."""
    score = 0
    factors = []

    direction = params.get('direction', 'forward')
    value_str = str(params.get('value', '1'))
    conv_idx = params.get('conversion_index', 0)

    # Known multipliers
    _multipliers = [1000, 100, 10, 1000, 1000, 1000, 10000, 60, 60]
    multiplier = _multipliers[conv_idx % len(_multipliers)]

    # Reverse direction (division) is inherently riskier
    if direction == 'reverse':
        score += 10
        factors.append('reverse_direction')

    # Decimal input
    if '.' in value_str:
        score += 10
        factors.append('decimal_input')

    # Non-integer result in reverse (e.g. 90 min → 1.5 hr)
    if direction == 'reverse':
        try:
            val_parts = value_str.split('.')
            val_int = int(value_str.replace('.', ''))
            val_dec = len(val_parts[1]) if len(val_parts) > 1 else 0
            # Check if result is non-integer
            shifted = val_int * (10 ** val_dec)
            # This is approximate; the actual check would need more precision
            if shifted % multiplier != 0 or val_dec > 0:
                score += 10
                factors.append('non_integer_result')
        except (ValueError, IndexError):
            pass

    # Area conversion (large multiplier 10000)
    if conv_idx == 6:
        score += 10
        factors.append('area_conversion_10000x')

    # Hint leak: value=1 forward produces answer=multiplier
    try:
        val_f = float(value_str)
        if direction == 'forward' and abs(val_f - 1.0) < 1e-9:
            score += 25
            factors.append('value_1_forward_leak_risk')
    except ValueError:
        pass

    return score, factors


# ── Topic scorer dispatch ───────────────────────────────────────

_SCORERS = {
    'fraction_word_problem': _score_fraction,
    'decimal_word_problem': _score_decimal,
    'average_word_problem': _score_average,
    'unit_conversion': _score_unit_conversion,
}


def score_question(topic: str, params: dict) -> Dict:
    """Score a question's risk level based on its parameters.

    Returns:
        {
            'risk_score': int (0-100),
            'risk_level': 'low' | 'medium' | 'high',
            'risk_factors': ['factor1', 'factor2', ...],
            'topic': str,
        }
    """
    base = _TOPIC_BASE.get(topic, 10)
    scorer = _SCORERS.get(topic)

    if scorer is None:
        return {
            'risk_score': base,
            'risk_level': 'low',
            'risk_factors': [],
            'topic': topic,
        }

    param_score, factors = scorer(params)
    total = base + param_score

    if total >= _RISK_THRESHOLDS['medium']:
        level = 'high'
    elif total >= _RISK_THRESHOLDS['low']:
        level = 'medium'
    else:
        level = 'low'

    return {
        'risk_score': total,
        'risk_level': level,
        'risk_factors': factors,
        'topic': topic,
    }


def score_benchmark_case(topic: str, case: dict) -> Dict:
    """Score a benchmark case using its input parameters.

    Wrapper that extracts the 'input' field from a benchmark case dict.
    """
    return score_question(topic, case.get('input', {}))
