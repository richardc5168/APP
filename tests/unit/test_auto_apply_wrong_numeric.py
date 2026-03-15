"""Tests for the wrong_numeric_answer auto-apply executor."""
import json
from pathlib import Path
from unittest.mock import patch

from tools.auto_apply_wrong_numeric import apply_fix, diagnose_benchmark, verify_after_fix


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _read_jsonl(path: Path):
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


# ----------- helpers to build a minimal mock generator+verifier -----------

class _MockVerifyResult:
    def __init__(self, *, match, expected, actual, errors=None):
        self.topic = 'decimal_word_problem'
        self.match = match
        self.expected = expected
        self.actual = actual
        self.errors = errors or []
        self.invariants_checked = 0
        self.invariants_passed = 0


class _MockGenerator:
    """Generator that returns correct_answer based on the input 'a' and 'b'."""
    def __init__(self):
        pass

    def generate(self, params=None):
        a = params.get('a', '0')
        b = params.get('b', '0')
        # Simple subtraction simulation: just return 'a-b' as the answer
        answer = params.get('_mock_answer', f'{a}-{b}')
        return {
            'correct_answer': answer,
            'parameters': params,
            'topic': 'decimal_word_problem',
        }


def _mock_verify_agree(topic, params, actual_answer):
    """Verifier that always agrees with the generator."""
    return _MockVerifyResult(match=True, expected=actual_answer, actual=actual_answer)


def _mock_verify_disagree(topic, params, actual_answer):
    """Verifier that always disagrees with the generator."""
    return _MockVerifyResult(match=False, expected='VERIFIER_SAYS_OTHER', actual=actual_answer)


# ----------- diagnose tests -----------

def test_diagnose_all_passing_when_benchmark_matches_generator(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.3'},
        {'input': {'a': '5.0', 'b': '2.0', '_mock_answer': '3'}, 'expected_answer': '3'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = diagnose_benchmark('decimal_word_problem')

    assert result['total_cases'] == 2
    assert result['passing'] == 2
    assert result['auto_fixable'] == 0
    assert result['escalations'] == 0


def test_diagnose_detects_auto_fixable_when_benchmark_stale(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.30'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = diagnose_benchmark('decimal_word_problem')

    assert result['auto_fixable'] == 1
    assert result['auto_fixable_cases'][0]['generator_answer'] == '2.3'
    assert result['auto_fixable_cases'][0]['expected'] == '2.30'


def test_diagnose_escalates_when_generator_and_verifier_disagree(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '999'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_disagree):
        result = diagnose_benchmark('decimal_word_problem')

    assert result['escalations'] == 1
    assert result['auto_fixable'] == 0


# ----------- apply tests -----------

def test_apply_dry_run_does_not_write_file(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.30'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = apply_fix('decimal_word_problem', dry_run=True, artifact_root=tmp_path / 'artifacts')

    assert result['applied'] == 1
    assert result['dry_run'] is True
    updated = _read_json(bench_path)
    assert updated[0]['expected_answer'] == '2.30'  # unchanged in dry-run


def test_apply_writes_updated_benchmark_and_outcome(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.30'},
        {'input': {'a': '5.0', 'b': '2.0', '_mock_answer': '3'}, 'expected_answer': '3'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = apply_fix('decimal_word_problem', dry_run=False, artifact_root=artifact_root)

    assert result['applied'] == 1
    assert result['dry_run'] is False

    updated = _read_json(bench_path)
    assert updated[0]['expected_answer'] == '2.3'  # fixed
    assert updated[1]['expected_answer'] == '3'    # untouched

    outcomes = _read_jsonl(artifact_root / 'strategy_outcomes.jsonl')
    assert outcomes[-1]['strategy_key'] == 'verifier_policy_first'
    assert outcomes[-1]['event'] == 'auto_applied'


def test_apply_no_fixable_returns_cleanly(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.3'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = apply_fix('decimal_word_problem', dry_run=False, artifact_root=tmp_path / 'artifacts')

    assert result['applied'] == 0


# ----------- verify_after_fix tests -----------

def test_verify_after_fix_reports_clean(tmp_path):
    bench_path = tmp_path / 'mathgen' / 'benchmarks' / 'decimal_word_problem_bench.json'
    _write_json(bench_path, [
        {'input': {'a': '3.5', 'b': '1.2', '_mock_answer': '2.3'}, 'expected_answer': '2.3'},
    ])

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', tmp_path / 'mathgen' / 'benchmarks'), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', _mock_verify_agree):
        result = verify_after_fix('decimal_word_problem')

    assert result['clean'] is True
    assert result['auto_fixable'] == 0
    assert result['escalations'] == 0
