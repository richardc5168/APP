"""Model sandbox — constrained LLM interface for question wording polish only.

The sandbox provides a strict, safe interface for using language models
to improve question wording WITHOUT changing:
  - Mathematical content (numbers, operations, answers)
  - Hint ladder structure
  - Correct answer or unit
  - Steps or parameters

Safety guardrails:
  1. Pre/post invariant checking (answer, unit, parameters preserved)
  2. Numeric extraction comparison (no new numbers introduced)
  3. Semantic constraint (wording-only delta)
  4. Dry-run mode by default (shows diff without applying)
  5. All changes recorded in logs/model_sandbox_log.jsonl

Usage:
    from mathgen.model_sandbox import ModelSandbox

    sandbox = ModelSandbox()
    result = sandbox.polish_wording(question_dict)
    # result contains proposed new wording + safety check results
"""
from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple


_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGS = os.path.join(_HERE, 'logs')
_SANDBOX_LOG = os.path.join(_LOGS, 'model_sandbox_log.jsonl')

# ── Numeric extraction ──────────────────────────────────────────

_NUMBER_RE = re.compile(r'-?\d+(?:\.\d+)?(?:/\d+)?')


def _extract_numbers(text: str) -> List[str]:
    """Extract all numeric values from text."""
    return _NUMBER_RE.findall(text)


# ── Invariant checkers ──────────────────────────────────────────

def check_answer_preserved(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify correct_answer is unchanged."""
    orig_ans = original.get('correct_answer', '')
    new_ans = polished.get('correct_answer', '')
    if orig_ans != new_ans:
        return False, f'Answer changed: "{orig_ans}" → "{new_ans}"'
    return True, 'OK'


def check_unit_preserved(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify unit is unchanged."""
    orig_unit = original.get('unit', '')
    new_unit = polished.get('unit', '')
    if orig_unit != new_unit:
        return False, f'Unit changed: "{orig_unit}" → "{new_unit}"'
    return True, 'OK'


def check_parameters_preserved(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify parameters dict is unchanged."""
    orig_params = original.get('parameters', {})
    new_params = polished.get('parameters', {})
    if orig_params != new_params:
        return False, f'Parameters changed'
    return True, 'OK'


def check_steps_preserved(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify steps list is unchanged."""
    orig_steps = original.get('steps', [])
    new_steps = polished.get('steps', [])
    if orig_steps != new_steps:
        return False, f'Steps changed: {len(orig_steps)} → {len(new_steps)}'
    return True, 'OK'


def check_hints_preserved(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify hint_ladder is unchanged."""
    orig_hints = original.get('hint_ladder', {})
    new_hints = polished.get('hint_ladder', {})
    if orig_hints != new_hints:
        return False, 'Hint ladder changed'
    return True, 'OK'


def check_no_new_numbers(original: dict, polished: dict) -> Tuple[bool, str]:
    """Verify no new numbers were introduced in problem_text."""
    orig_text = original.get('problem_text', '')
    new_text = polished.get('problem_text', '')
    orig_nums = set(_extract_numbers(orig_text))
    new_nums = set(_extract_numbers(new_text))
    added = new_nums - orig_nums
    if added:
        return False, f'New numbers introduced: {added}'
    return True, 'OK'


_INVARIANT_CHECKS = [
    ('answer_preserved', check_answer_preserved),
    ('unit_preserved', check_unit_preserved),
    ('parameters_preserved', check_parameters_preserved),
    ('steps_preserved', check_steps_preserved),
    ('hints_preserved', check_hints_preserved),
    ('no_new_numbers', check_no_new_numbers),
]


# ── Sandbox ─────────────────────────────────────────────────────

class ModelSandbox:
    """Constrained sandbox for LLM-based question wording polish.

    The sandbox enforces strict invariants:
    - Only problem_text may be modified
    - Answer, unit, parameters, steps, hints must be preserved
    - No new numbers may be introduced
    """

    def __init__(
        self,
        rewriter: Optional[Callable[[str], str]] = None,
        dry_run: bool = True,
    ):
        """
        Args:
            rewriter: A function that takes original problem_text and returns
                polished text. If None, uses a no-op pass-through.
            dry_run: If True (default), shows proposed changes without applying.
        """
        self.rewriter = rewriter or (lambda text: text)
        self.dry_run = dry_run
        self._log_entries = []

    def polish_wording(self, question: dict) -> Dict:
        """Attempt to polish question wording through the sandbox.

        Returns:
            {
                'original_text': str,
                'proposed_text': str,
                'text_changed': bool,
                'safety_checks': {check_name: (passed, message)},
                'all_safe': bool,
                'applied': bool,
                'question': dict (original or polished),
            }
        """
        original = copy.deepcopy(question)
        proposed = copy.deepcopy(question)

        # Only allow rewriting problem_text
        orig_text = original.get('problem_text', '')
        try:
            new_text = self.rewriter(orig_text)
        except Exception as e:
            return self._make_result(
                original, original, orig_text, orig_text,
                {'rewriter_error': (False, str(e))},
                applied=False,
            )

        proposed['problem_text'] = new_text

        # Run invariant checks
        safety_results = {}
        for name, checker in _INVARIANT_CHECKS:
            passed, msg = checker(original, proposed)
            safety_results[name] = (passed, msg)

        all_safe = all(passed for passed, _ in safety_results.values())

        # Apply only if safe and not dry_run
        applied = False
        if all_safe and not self.dry_run:
            applied = True
            result_q = proposed
        else:
            result_q = original

        result = self._make_result(
            original, result_q, orig_text, new_text,
            safety_results, applied,
        )

        # Log the attempt
        self._log_attempt(result)

        return result

    def _make_result(
        self, original, result_q, orig_text, new_text,
        safety_results, applied,
    ):
        all_safe = all(passed for passed, _ in safety_results.values())
        return {
            'original_text': orig_text,
            'proposed_text': new_text,
            'text_changed': orig_text != new_text,
            'safety_checks': safety_results,
            'all_safe': all_safe,
            'applied': applied,
            'question': result_q,
        }

    def _log_attempt(self, result):
        """Log sandbox attempt to JSONL file."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'original_text': result['original_text'],
            'proposed_text': result['proposed_text'],
            'text_changed': result['text_changed'],
            'all_safe': result['all_safe'],
            'applied': result['applied'],
            'safety_results': {
                k: {'passed': v[0], 'message': v[1]}
                for k, v in result['safety_checks'].items()
            },
        }
        self._log_entries.append(entry)
        os.makedirs(os.path.dirname(_SANDBOX_LOG), exist_ok=True)
        with open(_SANDBOX_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_log(self) -> List[Dict]:
        """Get all logged attempts from this session."""
        return self._log_entries


# ── Batch polishing ─────────────────────────────────────────────

def batch_polish(
    questions: List[dict],
    rewriter: Callable[[str], str],
    dry_run: bool = True,
) -> Dict:
    """Run the sandbox on a batch of questions.

    Returns:
        {
            'total': int,
            'changed': int,
            'safe': int,
            'unsafe': int,
            'applied': int,
            'results': [per-question results],
        }
    """
    sandbox = ModelSandbox(rewriter=rewriter, dry_run=dry_run)
    results = []
    changed = 0
    safe = 0
    unsafe = 0
    applied = 0

    for q in questions:
        r = sandbox.polish_wording(q)
        results.append(r)
        if r['text_changed']:
            changed += 1
        if r['all_safe']:
            safe += 1
        else:
            unsafe += 1
        if r['applied']:
            applied += 1

    return {
        'total': len(questions),
        'changed': changed,
        'safe': safe,
        'unsafe': unsafe,
        'applied': applied,
        'results': results,
    }


# ── Report ──────────────────────────────────────────────────────

def generate_sandbox_report(batch_results: Dict) -> str:
    """Generate markdown report of sandbox batch results."""
    lines = [
        '# Model Sandbox Report',
        '',
        '## Summary',
        '',
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total questions | {batch_results['total']} |",
        f"| Text changed | {batch_results['changed']} |",
        f"| All safety checks passed | {batch_results['safe']} |",
        f"| Safety violations | {batch_results['unsafe']} |",
        f"| Applied (non-dry-run) | {batch_results['applied']} |",
        '',
    ]

    # Show changes
    changed_results = [r for r in batch_results['results'] if r['text_changed']]
    if changed_results:
        lines.append('## Proposed Changes')
        lines.append('')
        for r in changed_results[:10]:
            status = '✅' if r['all_safe'] else '❌'
            lines.append(f"### {status} Question")
            lines.append(f"- **Original**: {r['original_text'][:100]}")
            lines.append(f"- **Proposed**: {r['proposed_text'][:100]}")
            if not r['all_safe']:
                failed = [f"{k}: {v[1]}" for k, v in r['safety_checks'].items() if not v[0]]
                lines.append(f"- **Violations**: {', '.join(failed)}")
            lines.append('')

    # Safety violations
    unsafe_results = [r for r in batch_results['results'] if not r['all_safe']]
    if unsafe_results:
        lines.append('## Safety Violations')
        lines.append('')
        lines.append('| Question | Violation |')
        lines.append('|----------|-----------|')
        for r in unsafe_results[:10]:
            failed = [f"{k}: {v[1]}" for k, v in r['safety_checks'].items() if not v[0]]
            lines.append(f"| {r['original_text'][:50]}... | {'; '.join(failed)} |")
        lines.append('')

    return '\n'.join(lines)
