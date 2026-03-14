"""Fail clustering — groups benchmark failures by root cause pattern.

Analyzes failures from benchmark_failures.jsonl and current runs
to identify clusters of related failures that share a common root cause.
Ranks clusters by fix leverage (fixing one root cause resolves N cases).
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from mathgen.error_taxonomy import classify_error, KNOWN_ERROR_CODES


_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGS = os.path.join(_HERE, 'logs')
_FAILURES_PATH = os.path.join(_LOGS, 'benchmark_failures.jsonl')


# ── Cluster definitions ─────────────────────────────────────────

# A cluster key is a tuple: (error_category, root_cause_pattern)
# These regex patterns extract root-cause substrings from raw error messages.

_ROOT_CAUSE_PATTERNS = [
    # hint_leaks_answer:level_X → group by level
    (r'hint_leaks_answer:(level_\d)', 'hint_leak_{0}'),
    # wrong_answer with expected/got → group by topic prefix
    (r'wrong_answer:expected=([^,]+)', 'wrong_answer_expected_{0}'),
    # wrong_unit with unit name → group by expected unit
    (r'wrong_unit:expected=([^,]+)', 'wrong_unit_{0}'),
    # step_missing_keyword → group by keyword
    (r'step_missing_keyword:(.+)', 'missing_step_{0}'),
    # generator_exception → group by exception type
    (r'generator_exception:(\w+)', 'gen_exception_{0}'),
]


def _extract_root_cause(error_str: str) -> str:
    """Extract a normalized root-cause key from a raw error string."""
    for pattern, template in _ROOT_CAUSE_PATTERNS:
        m = re.search(pattern, error_str)
        if m:
            return template.format(m.group(1))
    # Fall back to the classified error code
    return classify_error(error_str)


# ── Cluster building ────────────────────────────────────────────

def cluster_failures(fail_cases: List[Dict]) -> Dict[str, Dict]:
    """Group failures into clusters by root cause.

    Args:
        fail_cases: List of failure dicts from run_benchmarks:
            [{'case': 'topic[i]', 'errors': [...], 'classified': [...], 'note': ''}]

    Returns:
        Dict[cluster_key] → {
            'root_cause': str,
            'error_category': str,
            'cases': [case_id, ...],
            'count': int,
            'sample_errors': [first 3 raw error strings],
            'notes': [case notes],
        }
    """
    clusters = defaultdict(lambda: {
        'root_cause': '',
        'error_category': '',
        'cases': [],
        'count': 0,
        'sample_errors': [],
        'notes': [],
    })

    for fc in fail_cases:
        case_id = fc.get('case', '?')
        errors = fc.get('errors', [])
        note = fc.get('note', '')

        # Each failure may have multiple errors — use the first one for clustering
        if not errors:
            continue

        primary_error = errors[0]
        root_cause = _extract_root_cause(primary_error)
        category = classify_error(primary_error)

        cluster = clusters[root_cause]
        cluster['root_cause'] = root_cause
        cluster['error_category'] = category
        cluster['cases'].append(case_id)
        cluster['count'] += 1
        if len(cluster['sample_errors']) < 3:
            cluster['sample_errors'].append(primary_error)
        if note and note not in cluster['notes']:
            cluster['notes'].append(note)

    return dict(clusters)


# ── Fix ranking ─────────────────────────────────────────────────

# Leverage multiplier by error category (how impactful fixing each type is)
_CATEGORY_IMPACT = {
    'hint_leaks_answer': 3.0,     # Security-critical: hints must not leak
    'wrong_numeric_answer': 2.5,  # Correctness-critical
    'wrong_unit': 2.0,
    'schema_violation': 1.5,
    'decimal_precision_error': 2.5,  # IEEE 754 — systematic
    'fraction_not_simplified': 1.5,
    'missing_intermediate_step': 1.0,
    'hint_too_big_jump': 1.0,
    'empty_answer': 2.0,
    'step_order_wrong': 0.5,
    'wording_ambiguity': 0.5,
    'grade_level_too_hard': 0.5,
    'report_missing_fields': 0.5,
    'unknown': 0.5,
}


def rank_fixes(clusters: Dict[str, Dict]) -> List[Dict]:
    """Rank clusters by fix leverage — highest-impact fixes first.

    Leverage = case_count × category_impact_multiplier

    Returns list of ranked fix recommendations:
        [{
            'rank': 1,
            'root_cause': str,
            'leverage_score': float,
            'cases_affected': int,
            'error_category': str,
            'impact_multiplier': float,
            'sample_errors': [...],
            'recommendation': str,
        }]
    """
    ranked = []

    for key, cluster in clusters.items():
        category = cluster['error_category']
        impact = _CATEGORY_IMPACT.get(category, 0.5)
        leverage = cluster['count'] * impact

        # Generate fix recommendation
        recommendation = _generate_recommendation(key, cluster)

        ranked.append({
            'root_cause': key,
            'leverage_score': leverage,
            'cases_affected': cluster['count'],
            'error_category': category,
            'impact_multiplier': impact,
            'sample_errors': cluster['sample_errors'],
            'case_ids': cluster['cases'],
            'notes': cluster['notes'],
            'recommendation': recommendation,
        })

    # Sort by leverage score descending
    ranked.sort(key=lambda x: x['leverage_score'], reverse=True)

    # Assign ranks
    for i, item in enumerate(ranked):
        item['rank'] = i + 1

    return ranked


def _generate_recommendation(root_cause: str, cluster: Dict) -> str:
    """Generate a human-readable fix recommendation for a cluster."""
    category = cluster['error_category']
    count = cluster['count']

    recommendations = {
        'hint_leaks_answer': (
            f'檢查 {root_cause} 的 hint 生成邏輯。'
            f'確保 correct_answer 不會出現在該 level 的 hint 文字中。'
            f'可能需要重寫 hint template 或加入 answer-masking。'
        ),
        'wrong_numeric_answer': (
            f'驗證生成器的運算邏輯。{count} 個 case 的預期答案不符。'
            f'檢查是否使用了 float 運算（應使用 integer arithmetic）。'
        ),
        'wrong_unit': (
            f'{count} 個 case 的單位不符。檢查 template 的 unit 欄位'
            f'是否與 conversion table 一致。'
        ),
        'decimal_precision_error': (
            f'發現 IEEE 754 精度問題。務必使用 integer-based 運算。'
            f'檢查是否意外使用了 float() 或 parseFloat()。'
        ),
        'schema_violation': (
            f'生成的 JSON 結構不符 schema。'
            f'檢查 build_question() 是否缺少必要欄位。'
        ),
    }

    return recommendations.get(
        category,
        f'{count} 個 case 失敗於 {root_cause}。'
        f'檢查對應生成器的 {category} 邏輯。'
    )


# ── Historical analysis ─────────────────────────────────────────

def load_failure_history() -> List[Dict]:
    """Load all historical failure records from benchmark_failures.jsonl."""
    if not os.path.isfile(_FAILURES_PATH):
        return []
    entries = []
    with open(_FAILURES_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def analyze_failure_trends(history: List[Dict]) -> Dict:
    """Analyze failure trends across historical runs.

    Returns:
        {
            'total_runs': int,
            'recurring_causes': {root_cause: occurrence_count},
            'resolved_causes': [root_causes that appeared before but not in latest],
            'persistent_causes': [root_causes present in ≥2 consecutive runs],
        }
    """
    if not history:
        return {
            'total_runs': 0,
            'recurring_causes': {},
            'resolved_causes': [],
            'persistent_causes': [],
        }

    # Collect root causes per run
    runs_causes = []
    for entry in history:
        causes = set()
        for fc in entry.get('failures', []):
            for err in fc.get('errors', []):
                causes.add(_extract_root_cause(err))
        runs_causes.append(causes)

    # Count occurrences
    recurring = defaultdict(int)
    for causes in runs_causes:
        for c in causes:
            recurring[c] += 1

    # Latest vs previous
    latest = runs_causes[-1] if runs_causes else set()
    all_previous = set()
    for causes in runs_causes[:-1]:
        all_previous |= causes

    resolved = sorted(all_previous - latest)

    # Persistent: in latest AND in at least one previous run
    persistent = sorted(latest & all_previous)

    return {
        'total_runs': len(history),
        'recurring_causes': dict(recurring),
        'resolved_causes': resolved,
        'persistent_causes': persistent,
    }


# ── Report generation ───────────────────────────────────────────

def generate_cluster_report(
    clusters: Dict[str, Dict],
    ranked_fixes: List[Dict],
    trends: Optional[Dict] = None,
    total_cases: Optional[int] = None,
) -> str:
    """Generate a markdown report of failure clusters and fix priorities."""
    lines = [
        '# Fail Clustering & Fix Ranking Report',
        '',
    ]

    if not clusters:
        lines.append('## Status: ✅ No failures to cluster')
        lines.append('')
        case_count = total_cases if total_cases is not None else 0
        lines.append(f'All {case_count} benchmark cases pass. No action needed.')
        return '\n'.join(lines)

    total_failures = sum(c['count'] for c in clusters.values())
    lines.append(f'## Summary: {total_failures} failures across {len(clusters)} clusters')
    lines.append('')

    # Fix priority table
    lines.append('## Fix Priority (by leverage)')
    lines.append('')
    lines.append('| Rank | Root Cause | Cases | Impact | Leverage | Category |')
    lines.append('|------|-----------|-------|--------|----------|----------|')
    for fix in ranked_fixes[:10]:
        lines.append(
            f"| {fix['rank']} | {fix['root_cause']} | {fix['cases_affected']} | "
            f"{fix['impact_multiplier']:.1f}× | {fix['leverage_score']:.1f} | "
            f"{fix['error_category']} |"
        )
    lines.append('')

    # Detailed recommendations
    lines.append('## Recommendations')
    lines.append('')
    for fix in ranked_fixes[:5]:
        lines.append(f"### #{fix['rank']}: {fix['root_cause']}")
        lines.append(f"- **Cases affected**: {', '.join(fix['case_ids'][:5])}"
                     + (f' (+{len(fix["case_ids"]) - 5} more)' if len(fix['case_ids']) > 5 else ''))
        lines.append(f"- **Leverage score**: {fix['leverage_score']:.1f}")
        lines.append(f"- **Recommendation**: {fix['recommendation']}")
        if fix['notes']:
            lines.append(f"- **Notes**: {'; '.join(fix['notes'][:3])}")
        lines.append('')

    # Trends
    if trends and trends.get('total_runs', 0) > 1:
        lines.append('## Trend Analysis')
        lines.append('')
        lines.append(f"- Total historical runs: {trends['total_runs']}")
        if trends['persistent_causes']:
            lines.append(f"- **Persistent causes** (recurring): {', '.join(trends['persistent_causes'])}")
        if trends['resolved_causes']:
            lines.append(f"- **Resolved causes**: {', '.join(trends['resolved_causes'])}")
        lines.append('')

    return '\n'.join(lines)
