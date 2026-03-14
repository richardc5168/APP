"""Independent answer verifier — recomputes expected answer from params.

This module provides a second, independent computation path for every
topic.  When the generator's `correct_answer` disagrees with the
verifier's result, something is wrong.

Key design decisions:
  - ALL arithmetic uses integer operations (IEEE 754 avoidance).
  - Replicates the same rounding/formatting conventions as the generators.
  - Returns a VerifyResult with match status + details.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from math import gcd
from typing import Dict, List, Optional, Tuple


# ── Conversion table (must mirror unit_conversion.py) ──────────
_CONVERSIONS = [
    ('公里', '公尺', 1000),
    ('公尺', '公分', 100),
    ('公分', '公釐', 10),
    ('公斤', '公克', 1000),
    ('公噸', '公斤', 1000),
    ('公升', '毫升', 1000),
    ('平方公尺', '平方公分', 10000),
    ('小時', '分鐘', 60),
    ('分鐘', '秒', 60),
]


@dataclass
class VerifyResult:
    """Result of answer verification."""
    topic: str
    match: bool
    expected: str
    actual: str
    errors: List[str] = field(default_factory=list)
    invariants_checked: int = 0
    invariants_passed: int = 0


# ── Pure integer helpers (independent of BaseGenerator) ────────

def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def _simplify(n: int, d: int) -> Tuple[int, int]:
    g = _gcd(abs(n), abs(d))
    return n // g, d // g


def _frac_str(n: int, d: int) -> str:
    n, d = _simplify(n, d)
    return str(n) if d == 1 else f'{n}/{d}'


def _decimal_mul(a_str: str, b_str: str) -> str:
    """Exact decimal multiplication via integer arithmetic."""
    a_parts = a_str.split('.')
    b_parts = b_str.split('.')
    a_dec = len(a_parts[1]) if len(a_parts) > 1 else 0
    b_dec = len(b_parts[1]) if len(b_parts) > 1 else 0
    total_dec = a_dec + b_dec
    a_int = int(a_str.replace('.', ''))
    b_int = int(b_str.replace('.', ''))
    result = a_int * b_int
    if total_dec == 0:
        return str(result)
    s = str(abs(result)).zfill(total_dec + 1)
    sign = '-' if result < 0 else ''
    integer_part = s[:-total_dec]
    decimal_part = s[-total_dec:].rstrip('0')
    if not decimal_part:
        return sign + integer_part
    return sign + integer_part + '.' + decimal_part


def _decimal_add(a_str: str, b_str: str) -> str:
    """Exact decimal addition via integer arithmetic."""
    a_parts = a_str.split('.')
    b_parts = b_str.split('.')
    a_dec = len(a_parts[1]) if len(a_parts) > 1 else 0
    b_dec = len(b_parts[1]) if len(b_parts) > 1 else 0
    max_dec = max(a_dec, b_dec)
    a_int = int(a_str.replace('.', '')) * (10 ** (max_dec - a_dec))
    b_int = int(b_str.replace('.', '')) * (10 ** (max_dec - b_dec))
    result = a_int + b_int
    if max_dec == 0:
        return str(result)
    s = str(abs(result)).zfill(max_dec + 1)
    sign = '-' if result < 0 else ''
    integer_part = s[:-max_dec]
    decimal_part = s[-max_dec:].rstrip('0')
    if not decimal_part:
        return sign + integer_part
    return sign + integer_part + '.' + decimal_part


def _decimal_sub(a_str: str, b_str: str) -> str:
    """Exact decimal subtraction via integer arithmetic."""
    a_parts = a_str.split('.')
    b_parts = b_str.split('.')
    a_dec = len(a_parts[1]) if len(a_parts) > 1 else 0
    b_dec = len(b_parts[1]) if len(b_parts) > 1 else 0
    max_dec = max(a_dec, b_dec)
    a_int = int(a_str.replace('.', '')) * (10 ** (max_dec - a_dec))
    b_int = int(b_str.replace('.', '')) * (10 ** (max_dec - b_dec))
    result = a_int - b_int
    if max_dec == 0:
        return str(result)
    s = str(abs(result)).zfill(max_dec + 1)
    sign = '-' if result < 0 else ''
    integer_part = s[:-max_dec]
    decimal_part = s[-max_dec:].rstrip('0')
    if not decimal_part:
        return sign + integer_part
    return sign + integer_part + '.' + decimal_part


def _reverse_division(value_str: str, multiplier: int) -> str:
    """Exact reverse division for unit conversion."""
    val_parts = value_str.split('.')
    val_dec = len(val_parts[1]) if len(val_parts) > 1 else 0
    val_int = int(value_str.replace('.', ''))
    scale = 1
    while (val_int * scale) % multiplier != 0:
        scale *= 10
    result_int = (val_int * scale) // multiplier
    total_dec = val_dec + len(str(scale)) - 1
    if total_dec == 0:
        return str(result_int)
    s = str(result_int).zfill(total_dec + 1)
    integer_part = s[:-total_dec]
    decimal_part = s[-total_dec:].rstrip('0')
    return integer_part + ('.' + decimal_part if decimal_part else '')


# ── Fraction templates (must mirror fraction_word_problem.py) ──
_FRACTION_TEMPLATES = [
    {'pattern': 'subtract'},
    {'pattern': 'add'},
    {'pattern': 'subtract'},
    {'pattern': 'add'},
    {'pattern': 'subtract'},
]


# ── Topic verifiers ────────────────────────────────────────────

def _verify_fraction(params: dict, actual_answer: str) -> VerifyResult:
    """Independently verify fraction word problem answer."""
    n1 = params['a_num']
    d1 = params['a_den']
    n2 = params['b_num']
    d2 = params['b_den']
    tpl_idx = params.get('template_index', 0)
    operation = params.get('operation', _FRACTION_TEMPLATES[tpl_idx % 5]['pattern'])

    errors = []
    inv_checked = 0
    inv_passed = 0

    # Ensure a >= b for subtract (replicating generator logic)
    if operation == 'subtract':
        lcd_check = _lcm(d1, d2)
        a_lcd = n1 * (lcd_check // d1)
        b_lcd = n2 * (lcd_check // d2)
        if a_lcd < b_lcd:
            n1, d1, n2, d2 = n2, d2, n1, d1

    lcd = _lcm(d1, d2)
    a_lcd = n1 * (lcd // d1)
    b_lcd = n2 * (lcd // d2)

    if operation == 'add':
        result_num = a_lcd + b_lcd
    else:
        result_num = a_lcd - b_lcd

    expected = _frac_str(result_num, lcd)
    match = actual_answer == expected

    if not match:
        errors.append(f'answer_mismatch:expected={expected},got={actual_answer}')

    # Invariant: result must be >= 0
    inv_checked += 1
    rn, rd = _simplify(result_num, lcd)
    if rn < 0:
        errors.append('invariant:negative_fraction_result')
    else:
        inv_passed += 1

    # Invariant: result must be simplified
    inv_checked += 1
    if actual_answer == expected:
        # Verify the answer string is actually simplified
        if '/' in actual_answer:
            parts = actual_answer.split('/')
            an, ad = int(parts[0]), int(parts[1])
            if _gcd(abs(an), abs(ad)) != 1:
                errors.append('invariant:fraction_not_simplified')
            else:
                inv_passed += 1
        else:
            inv_passed += 1  # Integer result is always simplified

    # Invariant: for addition, result >= each operand
    if operation == 'add':
        inv_checked += 1
        a_val = n1 / d1
        b_val = n2 / d2
        r_val = rn / rd if rd != 0 else 0
        if r_val >= a_val - 1e-9 and r_val >= b_val - 1e-9:
            inv_passed += 1
        else:
            errors.append('invariant:addition_result_less_than_operand')

    return VerifyResult(
        topic='fraction_word_problem',
        match=match,
        expected=expected,
        actual=actual_answer,
        errors=errors,
        invariants_checked=inv_checked,
        invariants_passed=inv_passed,
    )


def _verify_decimal(params: dict, actual_answer: str) -> VerifyResult:
    """Independently verify decimal word problem answer."""
    a_str = params['a']
    b_str = params['b']
    operation = params.get('operation', 'add')

    errors = []
    inv_checked = 0
    inv_passed = 0

    if operation == 'add':
        expected = _decimal_add(a_str, b_str)
    elif operation == 'subtract':
        expected = _decimal_sub(a_str, b_str)
    elif operation == 'multiply':
        expected = _decimal_mul(a_str, b_str)
    else:
        return VerifyResult(
            topic='decimal_word_problem',
            match=False,
            expected='unknown',
            actual=actual_answer,
            errors=[f'unknown_operation:{operation}'],
        )

    match = actual_answer == expected
    if not match:
        errors.append(f'answer_mismatch:expected={expected},got={actual_answer}')

    # Invariant: for add with positive operands, result > max(a, b)
    if operation == 'add':
        inv_checked += 1
        try:
            a_val = float(a_str)
            b_val = float(b_str)
            r_val = float(actual_answer) if actual_answer else 0
            if a_val >= 0 and b_val >= 0 and r_val >= max(a_val, b_val) - 1e-9:
                inv_passed += 1
            elif a_val < 0 or b_val < 0:
                inv_passed += 1  # Skip for negative operands
            else:
                errors.append('invariant:add_result_less_than_operand')
        except ValueError:
            errors.append('invariant:unparseable_decimal')

    # Invariant: multiply result sign is correct
    if operation == 'multiply':
        inv_checked += 1
        try:
            a_val = float(a_str)
            b_val = float(b_str)
            r_val = float(actual_answer) if actual_answer else 0
            expected_sign = (a_val >= 0) == (b_val >= 0)
            actual_sign = r_val >= 0
            if expected_sign == actual_sign or r_val == 0:
                inv_passed += 1
            else:
                errors.append('invariant:multiply_wrong_sign')
        except ValueError:
            errors.append('invariant:unparseable_decimal')

    # Invariant: no trailing zeros in decimal part
    inv_checked += 1
    if '.' in actual_answer:
        dec_part = actual_answer.split('.')[1]
        if dec_part.endswith('0'):
            errors.append('invariant:trailing_zeros')
        else:
            inv_passed += 1
    else:
        inv_passed += 1  # Integer, no trailing zeros

    return VerifyResult(
        topic='decimal_word_problem',
        match=match,
        expected=expected,
        actual=actual_answer,
        errors=errors,
        invariants_checked=inv_checked,
        invariants_passed=inv_passed,
    )


def _verify_average(params: dict, actual_answer: str) -> VerifyResult:
    """Independently verify average word problem answer.

    Uses integer arithmetic to avoid IEEE 754 issues:
      - If sum % n == 0 → integer answer
      - Else → one decimal place via integer division with rounding
    """
    values = params['values']
    errors = []
    inv_checked = 0
    inv_passed = 0

    total = sum(values)
    n = len(values)

    if n == 0:
        return VerifyResult(
            topic='average_word_problem',
            match=False,
            expected='undefined',
            actual=actual_answer,
            errors=['division_by_zero:empty_values'],
        )

    # Compute expected answer using integer arithmetic only
    if total % n == 0:
        expected = str(total // n)
    else:
        # One decimal place: (total * 10) // n, then format
        # This matches Python's f"{total/n:.1f}" for positive integers
        scaled = total * 10
        quotient = scaled // n
        remainder = scaled % n
        # Round half-up
        if remainder * 2 >= n:
            quotient += 1
        integer_part = quotient // 10
        decimal_part = quotient % 10
        if decimal_part == 0:
            expected = str(integer_part)
        else:
            expected = f'{integer_part}.{decimal_part}'

    match = actual_answer == expected
    if not match:
        errors.append(f'answer_mismatch:expected={expected},got={actual_answer}')

    # Invariant: result is between min and max of values
    if values:
        inv_checked += 1
        try:
            r_val = float(actual_answer) if actual_answer else 0
            if min(values) - 0.1 <= r_val <= max(values) + 0.1:
                inv_passed += 1
            else:
                errors.append('invariant:average_out_of_range')
        except ValueError:
            errors.append('invariant:unparseable_average')

    # Invariant: if all values equal, result equals that value
    if values and len(set(values)) == 1:
        inv_checked += 1
        expected_all_same = str(values[0])
        if actual_answer == expected_all_same:
            inv_passed += 1
        else:
            errors.append('invariant:all_same_values_wrong_average')

    return VerifyResult(
        topic='average_word_problem',
        match=match,
        expected=expected,
        actual=actual_answer,
        errors=errors,
        invariants_checked=inv_checked,
        invariants_passed=inv_passed,
    )


def _verify_unit_conversion(params: dict, actual_answer: str) -> VerifyResult:
    """Independently verify unit conversion answer."""
    value_str = params['value']
    conv_idx = params.get('conversion_index', 0)
    direction = params.get('direction', 'forward')

    errors = []
    inv_checked = 0
    inv_passed = 0

    conv = _CONVERSIONS[conv_idx % len(_CONVERSIONS)]
    multiplier = conv[2]

    if direction == 'forward':
        expected = _decimal_mul(value_str, str(multiplier))
    else:
        expected = _reverse_division(value_str, multiplier)

    match = actual_answer == expected
    if not match:
        errors.append(f'answer_mismatch:expected={expected},got={actual_answer}')

    # Invariant: forward result should be >= value for multiplier >= 1
    if direction == 'forward' and multiplier >= 1:
        inv_checked += 1
        try:
            v = float(value_str)
            r = float(actual_answer) if actual_answer else 0
            if v >= 0 and r >= v - 1e-9:
                inv_passed += 1
            elif v < 0:
                inv_passed += 1  # Skip for negative
            else:
                errors.append('invariant:forward_result_less_than_value')
        except ValueError:
            errors.append('invariant:unparseable_conversion')

    # Invariant: reverse result should be <= value for multiplier >= 1
    if direction == 'reverse' and multiplier >= 1:
        inv_checked += 1
        try:
            v = float(value_str)
            r = float(actual_answer) if actual_answer else 0
            if v >= 0 and r <= v + 1e-9:
                inv_passed += 1
            elif v < 0:
                inv_passed += 1
            else:
                errors.append('invariant:reverse_result_greater_than_value')
        except ValueError:
            errors.append('invariant:unparseable_conversion')

    # Invariant: round-trip check (forward then reverse, or vice versa)
    inv_checked += 1
    try:
        if direction == 'forward':
            roundtrip = _reverse_division(expected, multiplier)
        else:
            roundtrip = _decimal_mul(expected, str(multiplier))
        if roundtrip == value_str:
            inv_passed += 1
        else:
            errors.append(f'invariant:roundtrip_mismatch:got={roundtrip},expected={value_str}')
    except Exception:
        errors.append('invariant:roundtrip_error')

    return VerifyResult(
        topic='unit_conversion',
        match=match,
        expected=expected,
        actual=actual_answer,
        errors=errors,
        invariants_checked=inv_checked,
        invariants_passed=inv_passed,
    )


# ── Public API ──────────────────────────────────────────────────

_VERIFIERS = {
    'fraction_word_problem': _verify_fraction,
    'decimal_word_problem': _verify_decimal,
    'average_word_problem': _verify_average,
    'unit_conversion': _verify_unit_conversion,
}


def verify_answer(topic: str, params: dict, actual_answer: str) -> VerifyResult:
    """Verify a generated question's answer using independent computation.

    Args:
        topic: The question topic (e.g. 'fraction_word_problem')
        params: The input parameters used to generate the question
        actual_answer: The generator's correct_answer value

    Returns:
        VerifyResult with match status, expected answer, and any errors
    """
    verifier = _VERIFIERS.get(topic)
    if verifier is None:
        return VerifyResult(
            topic=topic,
            match=False,
            expected='unknown',
            actual=actual_answer,
            errors=[f'no_verifier_for_topic:{topic}'],
        )
    return verifier(params, actual_answer)


def verify_question(question: dict) -> VerifyResult:
    """Verify a complete question dict's answer."""
    return verify_answer(
        topic=question.get('topic', ''),
        params=question.get('parameters', {}),
        actual_answer=question.get('correct_answer', ''),
    )
