"""Adaptive manual sampling — selects questions for human review.

Sampling policy (configurable):
  - high risk   → 100% sampled for manual review
  - medium risk →  20% sampled
  - low risk    →   5% sampled

When a topic has recent failures (from baseline), ALL cases of that
topic are sampled regardless of risk level.

Output: a review queue written to logs/manual_review_queue.jsonl
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional

from mathgen.risk_scorer import score_benchmark_case


_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGS = os.path.join(_HERE, 'logs')
_REVIEW_QUEUE_PATH = os.path.join(_LOGS, 'manual_review_queue.jsonl')

# Sampling rates by risk level (0.0 – 1.0)
DEFAULT_SAMPLING_RATES = {
    'high': 1.0,
    'medium': 0.20,
    'low': 0.05,
}


def _deterministic_sample(case_id: str, rate: float) -> bool:
    """Deterministic sampling using hash — reproducible across runs.

    Uses MD5 of case_id to decide sample membership, so the same case
    will always be sampled (or not) for a given rate.
    """
    if rate >= 1.0:
        return True
    if rate <= 0.0:
        return False
    h = int(hashlib.md5(case_id.encode()).hexdigest(), 16)
    return (h % 10000) < int(rate * 10000)


def select_for_review(
    topic: str,
    cases: List[dict],
    baseline: Optional[dict] = None,
    sampling_rates: Optional[Dict[str, float]] = None,
) -> Dict:
    """Select benchmark cases for manual review based on risk scoring.

    Args:
        topic: Generator topic name.
        cases: List of benchmark case dicts (with 'input' key).
        baseline: Previous baseline dict (with 'by_topic').
        sampling_rates: Override default sampling rates.

    Returns:
        {
            'topic': str,
            'total_cases': int,
            'scored': [
                {
                    'case_index': int,
                    'case_id': str,
                    'risk_score': int,
                    'risk_level': str,
                    'risk_factors': [...],
                    'sampled_for_review': bool,
                    'sample_reason': str,
                },
                ...
            ],
            'review_count': int,
            'skip_count': int,
            'risk_distribution': {'low': int, 'medium': int, 'high': int},
        }
    """
    rates = sampling_rates or DEFAULT_SAMPLING_RATES

    # Check if topic has recent failures → force full review
    topic_has_failures = False
    if baseline:
        by_topic = baseline.get('by_topic', {})
        topic_baseline = by_topic.get(topic, {})
        if topic_baseline.get('failed', 0) > 0:
            topic_has_failures = True

    scored = []
    risk_dist = {'low': 0, 'medium': 0, 'high': 0}
    review_count = 0

    for i, case in enumerate(cases):
        case_id = f'{topic}[{i}]'
        risk = score_benchmark_case(topic, case)
        level = risk['risk_level']
        risk_dist[level] = risk_dist.get(level, 0) + 1

        # Determine if sampled
        if topic_has_failures:
            sampled = True
            reason = 'topic_has_baseline_failures'
        elif _deterministic_sample(case_id, rates.get(level, 0.05)):
            sampled = True
            reason = f'sampled_at_{rates.get(level, 0.05):.0%}_rate'
        else:
            sampled = False
            reason = 'below_sampling_threshold'

        if sampled:
            review_count += 1

        scored.append({
            'case_index': i,
            'case_id': case_id,
            'risk_score': risk['risk_score'],
            'risk_level': level,
            'risk_factors': risk['risk_factors'],
            'sampled_for_review': sampled,
            'sample_reason': reason,
        })

    return {
        'topic': topic,
        'total_cases': len(cases),
        'scored': scored,
        'review_count': review_count,
        'skip_count': len(cases) - review_count,
        'risk_distribution': risk_dist,
    }


def build_review_queue(
    all_topics_results: List[Dict],
) -> List[Dict]:
    """Collect all sampled cases into a flat review queue.

    Returns list of dicts suitable for writing to JSONL.
    """
    queue = []
    for topic_result in all_topics_results:
        topic = topic_result['topic']
        for entry in topic_result['scored']:
            if entry['sampled_for_review']:
                queue.append({
                    'case_id': entry['case_id'],
                    'topic': topic,
                    'risk_score': entry['risk_score'],
                    'risk_level': entry['risk_level'],
                    'risk_factors': entry['risk_factors'],
                    'sample_reason': entry['sample_reason'],
                })
    return queue


def write_review_queue(queue: List[Dict], path: Optional[str] = None) -> str:
    """Write the review queue to a JSONL file.

    Returns the file path written to.
    """
    target = path or _REVIEW_QUEUE_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w', encoding='utf-8') as f:
        for item in queue:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return target


def generate_sampling_report(all_topics_results: List[Dict]) -> str:
    """Generate a markdown report summarizing the sampling decisions.

    Returns markdown string.
    """
    lines = [
        '# Manual Sampling Report',
        '',
        f'> Auto-generated by `manual_sampler.py`',
        '',
        '## Summary',
        '',
    ]

    total_cases = 0
    total_review = 0
    total_skip = 0
    global_risk = {'low': 0, 'medium': 0, 'high': 0}

    for r in all_topics_results:
        total_cases += r['total_cases']
        total_review += r['review_count']
        total_skip += r['skip_count']
        for level in ('low', 'medium', 'high'):
            global_risk[level] += r['risk_distribution'].get(level, 0)

    review_pct = total_review / total_cases * 100 if total_cases else 0
    skip_pct = total_skip / total_cases * 100 if total_cases else 0

    lines.append(f'| Metric | Value |')
    lines.append(f'|--------|-------|')
    lines.append(f'| Total cases | {total_cases} |')
    lines.append(f'| Sampled for review | {total_review} ({review_pct:.1f}%) |')
    lines.append(f'| Skipped (trusted) | {total_skip} ({skip_pct:.1f}%) |')
    lines.append(f'| Theoretical human-time saved | {skip_pct:.0f}% |')
    lines.append('')

    # Risk distribution
    lines.append('## Risk Distribution')
    lines.append('')
    lines.append('| Risk Level | Count | % |')
    lines.append('|-----------|-------|---|')
    for level in ('low', 'medium', 'high'):
        cnt = global_risk[level]
        pct = cnt / total_cases * 100 if total_cases else 0
        lines.append(f'| {level} | {cnt} | {pct:.1f}% |')
    lines.append('')

    # Per-topic breakdown
    lines.append('## Per-Topic Breakdown')
    lines.append('')
    lines.append('| Topic | Total | Low | Med | High | Sampled | Skip |')
    lines.append('|-------|-------|-----|-----|------|---------|------|')
    for r in all_topics_results:
        rd = r['risk_distribution']
        lines.append(
            f"| {r['topic']} | {r['total_cases']} | "
            f"{rd.get('low', 0)} | {rd.get('medium', 0)} | {rd.get('high', 0)} | "
            f"{r['review_count']} | {r['skip_count']} |"
        )
    lines.append('')

    # High-risk cases detail
    high_cases = []
    for r in all_topics_results:
        for entry in r['scored']:
            if entry['risk_level'] == 'high':
                high_cases.append(entry)

    if high_cases:
        lines.append('## High-Risk Cases (Always Reviewed)')
        lines.append('')
        lines.append('| Case ID | Score | Factors |')
        lines.append('|---------|-------|---------|')
        for c in sorted(high_cases, key=lambda x: x['risk_score'], reverse=True):
            factors_str = ', '.join(c['risk_factors'])
            lines.append(f"| {c['case_id']} | {c['risk_score']} | {factors_str} |")
        lines.append('')

    return '\n'.join(lines)
