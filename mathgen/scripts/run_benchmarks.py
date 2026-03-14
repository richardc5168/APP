#!/usr/bin/env python3
"""Benchmark runner — validates generators against benchmark datasets.

Usage:
    python mathgen/scripts/run_benchmarks.py [--topic TOPIC]

Exit code 0 = all pass, 1 = failures found.
"""
import json
import os
import sys
from datetime import datetime, timezone

# Ensure package root is on path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

from mathgen.question_templates import ALL_GENERATORS
from mathgen.validators.schema_validator import validate_question_schema
from mathgen.validators.hint_validator import validate_hint_ladder
from mathgen.validators.answer_verifier import verify_answer
from mathgen.error_taxonomy import classify_error


BENCH_DIR = os.path.join(os.path.dirname(_HERE), 'benchmarks')
LOG_DIR = os.path.join(os.path.dirname(_HERE), 'logs')


def load_benchmark(topic):
    path = os.path.join(BENCH_DIR, f'{topic}_bench.json')
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_topic(topic, generator_cls, cases):
    """Run benchmark cases for a single topic.

    Returns:
        (pass_count, fail_count, failures_list)
    """
    gen = generator_cls()
    passed = 0
    failures = []

    for i, case in enumerate(cases):
        case_id = f'{topic}[{i}]'
        errs = []

        try:
            q = gen.generate(params=case['input'])
        except Exception as e:
            errs.append(f'generator_exception:{e}')
            failures.append({'case': case_id, 'errors': errs, 'note': case.get('note', '')})
            continue

        # Schema validation
        valid, schema_errs = validate_question_schema(q)
        errs.extend(schema_errs)

        # Hint validation
        hint_valid, hint_errs = validate_hint_ladder(q)
        errs.extend(hint_errs)

        # Independent answer verification
        vr = verify_answer(topic, q.get('parameters', {}), q.get('correct_answer', ''))
        if not vr.match:
            errs.append(f'verifier_mismatch:expected={vr.expected},got={vr.actual}')
        errs.extend(vr.errors)

        # Answer correctness
        if 'expected_answer' in case:
            actual = q.get('correct_answer', '')
            expected = str(case['expected_answer'])
            if actual != expected:
                errs.append(f'wrong_answer:expected={expected}, got={actual}')

        # Unit correctness
        if 'expected_unit' in case:
            actual_unit = q.get('unit', '')
            if actual_unit != case['expected_unit']:
                errs.append(f'wrong_unit:expected={case["expected_unit"]}, got={actual_unit}')

        # Step content check
        if 'expected_step_contains' in case:
            steps_text = ' '.join(q.get('steps', []))
            for keyword in case['expected_step_contains']:
                if str(keyword) not in steps_text:
                    errs.append(f'step_missing_keyword:{keyword}')

        # Hint answer leak check
        if case.get('hint_must_not_contain_answer', False):
            answer = q.get('correct_answer', '')
            if answer and len(answer) > 1:
                for lvl in ['level_1', 'level_2', 'level_3', 'level_4']:
                    hint_text = q.get('hint_ladder', {}).get(lvl, '')
                    if answer in hint_text:
                        errs.append(f'hint_leaks_answer:{lvl}')

        if errs:
            failures.append({
                'case': case_id,
                'errors': errs,
                'classified': [classify_error(e) for e in errs],
                'note': case.get('note', ''),
            })
        else:
            passed += 1

    return passed, len(failures), failures


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run mathgen benchmarks')
    parser.add_argument('--topic', type=str, default=None,
                        help='Run only this topic (default: all)')
    args = parser.parse_args()

    topics = [args.topic] if args.topic else list(ALL_GENERATORS.keys())
    all_pass = 0
    all_fail = 0
    all_failures = []
    results_by_topic = {}

    for topic in topics:
        if topic not in ALL_GENERATORS:
            print(f'[SKIP] Unknown topic: {topic}')
            continue

        cases = load_benchmark(topic)
        if cases is None:
            print(f'[SKIP] No benchmark file for: {topic}')
            continue

        p, f, failures = run_topic(topic, ALL_GENERATORS[topic], cases)
        all_pass += p
        all_fail += f
        all_failures.extend(failures)
        results_by_topic[topic] = {'pass': p, 'fail': f}

        status = 'PASS' if f == 0 else 'FAIL'
        print(f'[{status}] {topic}: {p}/{p+f} passed')
        for fail in failures:
            print(f'  ✗ {fail["case"]}: {fail["errors"]}')

    print(f'\n--- Summary ---')
    print(f'Total: {all_pass} passed, {all_fail} failed')

    # Pattern type & risk level coverage
    pattern_stats = {}
    risk_stats = {}
    for topic in topics:
        if topic not in ALL_GENERATORS:
            continue
        cases = load_benchmark(topic)
        if cases is None:
            continue
        for c in cases:
            pt = c.get('pattern_type', 'unknown')
            rl = c.get('risk_level', 'unknown')
            pattern_stats[pt] = pattern_stats.get(pt, 0) + 1
            risk_stats[rl] = risk_stats.get(rl, 0) + 1
    if pattern_stats:
        print(f'\n--- Coverage by pattern_type ---')
        for k in sorted(pattern_stats):
            print(f'  {k}: {pattern_stats[k]}')
        print(f'\n--- Coverage by risk_level ---')
        for k in sorted(risk_stats):
            print(f'  {k}: {risk_stats[k]}')

    # Write failures to log
    if all_failures:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, 'benchmark_failures.jsonl')
        with open(log_path, 'a', encoding='utf-8') as f:
            entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_pass': all_pass,
                'total_fail': all_fail,
                'failures': all_failures,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f'Failures logged to: {log_path}')

    sys.exit(0 if all_fail == 0 else 1)


if __name__ == '__main__':
    main()
