"""Analyze benchmark coverage gaps across all topics."""
import json
import os
from collections import Counter, defaultdict

BENCH_DIR = 'mathgen/benchmarks'

def analyze_topic(filepath, topic):
    cases = json.load(open(filepath))
    print(f"\n=== {topic} ({len(cases)} cases) ===")

    # Template distribution
    templates = Counter(c['input'].get('template_index', 0) for c in cases)
    print(f"  Template distribution: {dict(sorted(templates.items()))}")

    # Risk level distribution
    risks = Counter(c.get('risk_level', 'unset') for c in cases)
    print(f"  Risk levels: {dict(sorted(risks.items()))}")

    # Pattern type distribution
    patterns = Counter(c.get('pattern_type', 'unset') for c in cases)
    print(f"  Pattern types: {dict(sorted(patterns.items()))}")

    if topic == 'fraction_word_problem':
        # Denominator pairs
        den_pairs = Counter()
        for c in cases:
            inp = c['input']
            den_pairs[(inp.get('a_den', 0), inp.get('b_den', 0))] += 1
        print(f"  Unique den pairs: {len(den_pairs)}")
        # Operations (template pattern)
        ops = Counter()
        for c in cases:
            tpl_idx = c['input'].get('template_index', 0)
            # Templates 0, 2, 4 = subtract; 1, 3 = add
            op = 'subtract' if tpl_idx in (0, 2, 4) else 'add'
            ops[op] += 1
        print(f"  Operations: {dict(ops)}")
        # Check for improper fractions (num > den)
        improper = sum(1 for c in cases
                      if c['input'].get('a_num', 0) > c['input'].get('a_den', 1)
                      or c['input'].get('b_num', 0) > c['input'].get('b_den', 1))
        print(f"  Cases with improper fractions: {improper}")
        # Same denominator cases
        same_den = sum(1 for c in cases
                      if c['input'].get('a_den') == c['input'].get('b_den'))
        print(f"  Same denominator: {same_den}")

    elif topic == 'decimal_word_problem':
        ops = Counter(c['input'].get('operation', '?') for c in cases)
        print(f"  Operations: {dict(sorted(ops.items()))}")
        # Decimal places
        for c in cases:
            a = c['input'].get('a', '0')
            b = c['input'].get('b', '0')

    elif topic == 'unit_conversion':
        dirs = Counter(c['input'].get('direction', '?') for c in cases)
        print(f"  Directions: {dict(sorted(dirs.items()))}")
        conv_idx = Counter(c['input'].get('conversion_index', -1) for c in cases)
        print(f"  Conversion indices: {dict(sorted(conv_idx.items()))}")
        # Decimal values
        decimal_vals = sum(1 for c in cases if '.' in str(c['input'].get('value', '')))
        print(f"  Cases with decimal values: {decimal_vals}")

    elif topic == 'average_word_problem':
        val_counts = Counter(len(c['input'].get('values', [])) for c in cases)
        print(f"  Value count distribution: {dict(sorted(val_counts.items()))}")

for fn in sorted(os.listdir(BENCH_DIR)):
    if fn.endswith('_bench.json'):
        topic = fn.replace('_bench.json', '')
        analyze_topic(os.path.join(BENCH_DIR, fn), topic)
