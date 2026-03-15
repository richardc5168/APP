import json
from pathlib import Path
from unittest.mock import patch

from tools.manage_recipe_execution import execute_active_recipe, finalize_active_recipe, select_active_recipe


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


def test_select_active_recipe_writes_active_recipe_and_selection_outcome(tmp_path):
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    queue = {
        'next_best_actionable_targets': [
            {
                'issue_id': 'benchmark:wrong_numeric_answer:decimal_word_problem',
                'error_category': 'wrong_numeric_answer',
                'source_type': 'benchmark_history',
                'risk_score': 101,
                'affected_scope': {'topics': ['decimal_word_problem']},
                'fix_recipe': {
                    'allowed_edit_scope': ['mathgen/question_templates/*.py'],
                    'forbidden_shortcuts': ['no hand-edited expected answers'],
                    'rollback_condition': ['rollback on verifier drift'],
                    'recommended_diff_pattern': ['add failing case first'],
                    'mandatory_pre_test': ['python mathgen/scripts/run_benchmarks.py --topic <topic>'],
                    'mandatory_post_test': ['python mathgen/scripts/run_full_cycle.py'],
                },
                'anti_repeat': {
                    'decision': 'allow',
                    'reason': 'Safe controlled recipe available.',
                    'proposed_strategy_key': 'verifier_policy_first',
                    'proposed_strategy': 'Generate expected answers from verifier policy before changing generator logic.',
                },
                'reproducible_commands': ['python mathgen/scripts/run_benchmarks.py --topic decimal_word_problem'],
            }
        ]
    }
    _write_json(artifact_root / 'issue_queue.json', queue)

    result = select_active_recipe(artifact_root=artifact_root, run_id='20260315-select')

    active_recipe = _read_json(artifact_root / 'active_recipe.json')
    outcomes = _read_jsonl(artifact_root / 'strategy_outcomes.jsonl')

    assert result['selection_changed'] is True
    assert active_recipe['issue_id'] == 'benchmark:wrong_numeric_answer:decimal_word_problem'
    assert active_recipe['strategy_key'] == 'verifier_policy_first'
    assert active_recipe['status'] == 'selected'
    assert active_recipe['preflight_commands'][0]['display'] == 'python mathgen/scripts/run_benchmarks.py --topic decimal_word_problem'
    assert outcomes[-1]['event'] == 'selected'
    assert outcomes[-1]['strategy_key'] == 'verifier_policy_first'


def test_finalize_active_recipe_success_persists_durable_strategy_learning(tmp_path):
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    mathgen_logs = tmp_path / 'mathgen' / 'logs'
    _write_json(
        artifact_root / 'active_recipe.json',
        {
            'run_id': '20260315-finalize',
            'status': 'selected',
            'issue_id': 'benchmark:wrong_numeric_answer:decimal_word_problem',
            'error_category': 'wrong_numeric_answer',
            'topic': 'decimal_word_problem',
            'strategy_key': 'verifier_policy_first',
            'strategy': 'Generate expected answers from verifier policy before changing generator logic.',
            'allowed_edit_scope': ['mathgen/question_templates/*.py', 'mathgen/benchmarks/*_bench.json'],
        },
    )

    result = finalize_active_recipe(
        artifact_root=artifact_root,
        mathgen_logs=mathgen_logs,
        run_id='20260315-finalize',
        verify_mode='full',
        gate_pass=True,
        changed_files=['mathgen/question_templates/decimal_word_problem.py'],
    )

    assert result['finalized'] is True
    active_recipe = _read_json(artifact_root / 'active_recipe.json')
    strategy_outcomes = _read_jsonl(artifact_root / 'strategy_outcomes.jsonl')
    change_history = _read_jsonl(mathgen_logs / 'change_history.jsonl')
    lessons = _read_jsonl(mathgen_logs / 'lessons_learned.jsonl')

    assert active_recipe['status'] == 'validated_success'
    assert strategy_outcomes[-1]['outcome'] == 'successful'
    assert strategy_outcomes[-1]['scope_ok'] is True
    assert change_history[-1]['strategy_key'] == 'verifier_policy_first'
    assert change_history[-1]['error_codes_addressed'] == ['wrong_numeric_answer']
    assert lessons[-1]['type'] == 'fix_applied'
    assert lessons[-1]['strategy_key'] == 'verifier_policy_first'


def test_finalize_active_recipe_failure_writes_anti_pattern_lesson(tmp_path):
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    mathgen_logs = tmp_path / 'mathgen' / 'logs'
    _write_json(
        artifact_root / 'active_recipe.json',
        {
            'run_id': '20260315-failure',
            'status': 'selected',
            'issue_id': 'benchmark:hint_leaks_answer:fraction_word_problem',
            'error_category': 'hint_leaks_answer',
            'topic': 'fraction_word_problem',
            'strategy_key': 'validator_first',
            'strategy': 'Add or tighten hint validator coverage before touching template text.',
            'allowed_edit_scope': ['mathgen/question_templates/*.py'],
        },
    )

    result = finalize_active_recipe(
        artifact_root=artifact_root,
        mathgen_logs=mathgen_logs,
        run_id='20260315-failure',
        verify_mode='baseline',
        gate_pass=False,
        changed_files=['docs/exam-sprint/index.html'],
    )

    assert result['finalized'] is True
    active_recipe = _read_json(artifact_root / 'active_recipe.json')
    strategy_outcomes = _read_jsonl(artifact_root / 'strategy_outcomes.jsonl')
    lessons = _read_jsonl(mathgen_logs / 'lessons_learned.jsonl')

    assert active_recipe['status'] == 'validated_failure'
    assert strategy_outcomes[-1]['outcome'] == 'failed'
    assert strategy_outcomes[-1]['counts_toward_blacklist'] is True
    assert lessons[-1]['type'] == 'anti_pattern'
    assert lessons[-1]['strategy_key'] == 'validator_first'
    assert lessons[-1]['error_codes'] == ['hint_leaks_answer']


def test_execute_active_recipe_dispatches_to_wrong_numeric_executor(tmp_path):
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    _write_json(
        artifact_root / 'active_recipe.json',
        {
            'run_id': '20260315-exec',
            'status': 'selected',
            'issue_id': 'benchmark:wrong_numeric_answer:decimal_word_problem',
            'error_category': 'wrong_numeric_answer',
            'topic': 'decimal_word_problem',
            'strategy_key': 'verifier_policy_first',
            'strategy': 'Generate expected answers from verifier policy before changing generator logic.',
            'allowed_edit_scope': ['mathgen/benchmarks/*_bench.json'],
        },
    )

    class _MockVerifyResult:
        def __init__(self, *, match, expected, actual):
            self.topic = 'decimal_word_problem'
            self.match = match
            self.expected = expected
            self.actual = actual
            self.errors = []
            self.invariants_checked = 0
            self.invariants_passed = 0

    class _MockGenerator:
        def generate(self, params=None):
            return {'correct_answer': '2.3', 'parameters': params, 'topic': 'decimal_word_problem'}

    bench_dir = tmp_path / 'mathgen' / 'benchmarks'
    bench_dir.mkdir(parents=True, exist_ok=True)
    (bench_dir / 'decimal_word_problem_bench.json').write_text(
        json.dumps([{'input': {'a': '3.5', 'b': '1.2'}, 'expected_answer': '2.30'}], ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    def mock_verify(topic, params, actual):
        return _MockVerifyResult(match=True, expected=actual, actual=actual)

    with patch('tools.auto_apply_wrong_numeric.BENCH_DIR', bench_dir), \
         patch('tools.auto_apply_wrong_numeric.ALL_GENERATORS', {'decimal_word_problem': _MockGenerator}), \
         patch('tools.auto_apply_wrong_numeric.verify_answer', mock_verify):
        result = execute_active_recipe(artifact_root=artifact_root, run_id='20260315-exec', dry_run=True)

    assert result['executed'] is True
    assert result['executor'] == 'tools.auto_apply_wrong_numeric'
    assert result['apply_result']['applied'] == 1


def test_execute_active_recipe_returns_not_executed_for_unknown_category(tmp_path):
    artifact_root = tmp_path / 'artifacts' / 'run_10h'
    _write_json(
        artifact_root / 'active_recipe.json',
        {
            'run_id': '20260315-noexec',
            'status': 'selected',
            'issue_id': 'benchmark:sorting_semantics:some_module',
            'error_category': 'sorting_semantics',
            'topic': 'some_module',
            'strategy_key': 'sort_before_slice',
            'strategy': 'Sort raw events before slice.',
            'allowed_edit_scope': ['scripts/*.py'],
        },
    )

    result = execute_active_recipe(artifact_root=artifact_root, run_id='20260315-noexec')
    assert result['executed'] is False
    assert 'No auto-apply executor' in result['reason']
