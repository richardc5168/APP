"""Auto-apply executor for wrong_numeric_answer — verifier_policy_first strategy.

This executor reads benchmark cases for a given topic, runs the generator and
verifier, and updates expected_answer values where the generator and verifier
agree but the benchmark expectation was stale or formatted differently.

When the generator and verifier disagree, the case is logged as an escalation
rather than auto-fixed.

Usage:
    python tools/auto_apply_wrong_numeric.py diagnose --topic <topic>
    python tools/auto_apply_wrong_numeric.py apply --topic <topic> [--dry-run]
    python tools/auto_apply_wrong_numeric.py apply --topic <topic> --artifact-root artifacts/run_10h
"""
import argparse
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from mathgen.question_templates import ALL_GENERATORS
from mathgen.validators.answer_verifier import verify_answer

BENCH_DIR = _ROOT / 'mathgen' / 'benchmarks'
DEFAULT_ARTIFACT_ROOT = _ROOT / 'artifacts' / 'run_10h'


def _load_benchmark(topic: str):
    path = BENCH_DIR / f'{topic}_bench.json'
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def _write_benchmark(topic: str, cases):
    path = BENCH_DIR / f'{topic}_bench.json'
    path.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')


def diagnose_benchmark(topic: str):
    """Classify each benchmark case into: passing, auto_fixable, escalate."""
    cases = _load_benchmark(topic)
    if cases is None:
        return {'error': f'No benchmark file for topic: {topic}'}

    generator_cls = ALL_GENERATORS.get(topic)
    if generator_cls is None:
        return {'error': f'No generator for topic: {topic}'}

    gen = generator_cls()
    results = []

    for i, case in enumerate(cases):
        case_id = f'{topic}[{i}]'
        expected = str(case.get('expected_answer', ''))

        try:
            q = gen.generate(params=case['input'])
        except Exception as exc:
            results.append({
                'case_id': case_id,
                'index': i,
                'status': 'escalate',
                'reason': f'generator_exception: {exc}',
                'expected': expected,
                'generator_answer': '',
                'verifier_answer': '',
            })
            continue

        gen_answer = q.get('correct_answer', '')
        vr = verify_answer(topic, q.get('parameters', {}), gen_answer)
        verifier_answer = vr.expected

        if gen_answer == expected:
            # Benchmark already matches generator
            if vr.match:
                results.append({
                    'case_id': case_id,
                    'index': i,
                    'status': 'passing',
                    'reason': 'All agree.',
                    'expected': expected,
                    'generator_answer': gen_answer,
                    'verifier_answer': verifier_answer,
                })
            else:
                # Generator matches benchmark but not verifier — suspicious
                results.append({
                    'case_id': case_id,
                    'index': i,
                    'status': 'escalate',
                    'reason': f'Generator matches benchmark but verifier disagrees (verifier={verifier_answer}).',
                    'expected': expected,
                    'generator_answer': gen_answer,
                    'verifier_answer': verifier_answer,
                })
        else:
            # Generator answer differs from benchmark expectation
            if vr.match:
                # Generator and verifier agree — benchmark was stale
                results.append({
                    'case_id': case_id,
                    'index': i,
                    'status': 'auto_fixable',
                    'reason': f'Generator and verifier agree on "{gen_answer}" but benchmark expected "{expected}".',
                    'expected': expected,
                    'generator_answer': gen_answer,
                    'verifier_answer': verifier_answer,
                })
            else:
                # Generator and verifier disagree — logic bug
                results.append({
                    'case_id': case_id,
                    'index': i,
                    'status': 'escalate',
                    'reason': f'Generator ({gen_answer}) and verifier ({verifier_answer}) disagree. Benchmark expected ({expected}). Manual review needed.',
                    'expected': expected,
                    'generator_answer': gen_answer,
                    'verifier_answer': verifier_answer,
                })

    passing = [r for r in results if r['status'] == 'passing']
    auto_fixable = [r for r in results if r['status'] == 'auto_fixable']
    escalations = [r for r in results if r['status'] == 'escalate']

    return {
        'topic': topic,
        'total_cases': len(cases),
        'passing': len(passing),
        'auto_fixable': len(auto_fixable),
        'escalations': len(escalations),
        'auto_fixable_cases': auto_fixable,
        'escalation_cases': escalations,
        'all_results': results,
    }


def apply_fix(topic: str, *, dry_run: bool = True, artifact_root: Path = DEFAULT_ARTIFACT_ROOT):
    """Apply verifier_policy_first auto-fix: update benchmark expected_answer.

    Only updates cases where generator and verifier agree but benchmark was stale.
    Returns a report dict.
    """
    diagnosis = diagnose_benchmark(topic)
    if 'error' in diagnosis:
        return diagnosis

    auto_fixable = diagnosis['auto_fixable_cases']
    if not auto_fixable:
        return {
            'topic': topic,
            'applied': 0,
            'dry_run': dry_run,
            'message': 'No auto-fixable cases found.',
            'escalations': diagnosis['escalations'],
        }

    cases = _load_benchmark(topic)
    original_cases = deepcopy(cases)
    changes = []

    for item in auto_fixable:
        idx = item['index']
        old_val = str(cases[idx].get('expected_answer', ''))
        new_val = item['generator_answer']
        cases[idx]['expected_answer'] = new_val
        changes.append({
            'case_id': item['case_id'],
            'index': idx,
            'old_expected': old_val,
            'new_expected': new_val,
            'reason': item['reason'],
        })

    if not dry_run:
        _write_benchmark(topic, cases)

        # Record in strategy outcomes
        outcome_path = artifact_root / 'strategy_outcomes.jsonl'
        _append_jsonl(outcome_path, {
            'timestamp': _now_iso(),
            'issue_id': f'benchmark:wrong_numeric_answer:{topic}',
            'error_category': 'wrong_numeric_answer',
            'topic': topic,
            'strategy_key': 'verifier_policy_first',
            'strategy': 'Generate expected answers from verifier policy before changing generator logic.',
            'event': 'auto_applied',
            'outcome': 'applied',
            'has_side_effect': False,
            'counts_toward_blacklist': False,
            'source': 'auto_apply_wrong_numeric',
            'reason': f'Updated {len(changes)} benchmark expected_answer values to match verifier policy.',
            'changed_files': [f'mathgen/benchmarks/{topic}_bench.json'],
            'changes_count': len(changes),
        })

    return {
        'topic': topic,
        'applied': len(changes),
        'dry_run': dry_run,
        'changes': changes,
        'escalations': diagnosis['escalations'],
        'escalation_count': diagnosis['escalations'],
        'message': f'{"Would update" if dry_run else "Updated"} {len(changes)} expected_answer values.',
    }


def verify_after_fix(topic: str):
    """Run generator + verifier on all cases post-fix to confirm zero failures."""
    diagnosis = diagnose_benchmark(topic)
    if 'error' in diagnosis:
        return diagnosis
    return {
        'topic': topic,
        'total_cases': diagnosis['total_cases'],
        'passing': diagnosis['passing'],
        'auto_fixable': diagnosis['auto_fixable'],
        'escalations': diagnosis['escalations'],
        'clean': diagnosis['auto_fixable'] == 0 and diagnosis['escalations'] == 0,
    }


def main():
    parser = argparse.ArgumentParser(description='Auto-apply executor for wrong_numeric_answer (verifier_policy_first)')
    sub = parser.add_subparsers(dest='command', required=True)

    diag = sub.add_parser('diagnose', help='Classify all benchmark cases for a topic')
    diag.add_argument('--topic', required=True)

    apply_cmd = sub.add_parser('apply', help='Apply auto-fix for auto_fixable cases')
    apply_cmd.add_argument('--topic', required=True)
    apply_cmd.add_argument('--dry-run', action='store_true', default=False)
    apply_cmd.add_argument('--artifact-root', default=str(DEFAULT_ARTIFACT_ROOT))

    verify_cmd = sub.add_parser('verify', help='Verify all cases pass after fix')
    verify_cmd.add_argument('--topic', required=True)

    args = parser.parse_args()

    if args.command == 'diagnose':
        result = diagnose_benchmark(args.topic)
    elif args.command == 'apply':
        result = apply_fix(args.topic, dry_run=args.dry_run, artifact_root=Path(args.artifact_root))
    else:
        result = verify_after_fix(args.topic)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
