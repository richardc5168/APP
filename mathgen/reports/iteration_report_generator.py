"""Iteration report generator — auto-summary after each benchmark run."""
import json
import os
from datetime import date


def generate_iteration_report(benchmark_results, changes_description='',
                              new_tests=0, new_errors=None,
                              resolved_errors=None):
    """Generate a structured iteration report.

    Args:
        benchmark_results: dict with keys: total, passed, failed, by_topic, fail_cases
        changes_description: str describing what changed
        new_tests: int count of new tests added
        new_errors: list of newly discovered error types
        resolved_errors: list of resolved error types

    Returns:
        str: markdown report content
    """
    today = date.today().isoformat()
    total = benchmark_results.get('total', 0)
    passed = benchmark_results.get('passed', 0)
    failed = benchmark_results.get('failed', 0)
    pass_rate = passed / total if total > 0 else 0
    by_topic = benchmark_results.get('by_topic', {})

    lines = [
        f'# Iteration Report — {today}',
        '',
        '## 本輪修改內容',
        changes_description or '（無修改）',
        '',
        f'## 新增測試數量: {new_tests}',
        '',
        f'## 總 Pass Rate: {passed}/{total} ({pass_rate:.1%})',
        '',
        '## 各題型 Pass Rate',
        '| 題型 | Pass | Total | Rate |',
        '|------|------|-------|------|',
    ]

    for topic, stats in sorted(by_topic.items()):
        t_total = stats.get('total', 0)
        t_pass = stats.get('passed', 0)
        t_rate = t_pass / t_total if t_total > 0 else 0
        lines.append(f'| {topic} | {t_pass} | {t_total} | {t_rate:.1%} |')

    # Coverage stats
    pattern_stats = benchmark_results.get('pattern_stats', {})
    risk_stats = benchmark_results.get('risk_stats', {})
    if pattern_stats:
        lines.append('')
        lines.append('## Benchmark 覆蓋分布')
        lines.append('### pattern_type')
        lines.append('| 類型 | 數量 |')
        lines.append('|------|------|')
        for k in sorted(pattern_stats):
            lines.append(f'| {k} | {pattern_stats[k]} |')
        lines.append('')
        lines.append('### risk_level')
        lines.append('| 等級 | 數量 |')
        lines.append('|------|------|')
        for k in sorted(risk_stats):
            lines.append(f'| {k} | {risk_stats[k]} |')

    lines.append('')
    lines.append('## 新發現錯誤類型')
    if new_errors:
        for e in new_errors:
            lines.append(f'- {e}')
    else:
        lines.append('（無）')

    lines.append('')
    lines.append('## 已解決錯誤類型')
    if resolved_errors:
        for e in resolved_errors:
            lines.append(f'- {e}')
    else:
        lines.append('（無）')

    # Sampling summary (Phase 2)
    sampling = benchmark_results.get('sampling')
    if sampling:
        total_sampled = sampling.get('total_sampled', 0)
        total_skipped = sampling.get('total_skipped', 0)
        s_total = total_sampled + total_skipped
        review_pct = total_sampled / s_total * 100 if s_total else 0
        lines.append('')
        lines.append('## Risk-Based Sampling')
        lines.append(f'- 需人工審查: {total_sampled}/{s_total} ({review_pct:.1f}%)')
        lines.append(f'- 自動信任: {total_skipped}/{s_total} ({100 - review_pct:.1f}%)')
        lines.append(f'- 理論節省人力: {100 - review_pct:.0f}%')
        by_topic = sampling.get('by_topic', {})
        if by_topic:
            lines.append('')
            lines.append('| 題型 | Low | Medium | High |')
            lines.append('|------|-----|--------|------|')
            for t in sorted(by_topic):
                rd = by_topic[t]
                lines.append(f"| {t} | {rd.get('low', 0)} | {rd.get('medium', 0)} | {rd.get('high', 0)} |")

    # Clustering summary (Phase 3)
    clusters_data = benchmark_results.get('clusters')
    if clusters_data:
        lines.append('')
        lines.append('## Fail Clustering')
        if clusters_data.get('count', 0) == 0:
            lines.append('- ✅ 無失敗群集')
        else:
            lines.append(f"- {clusters_data['count']} 個群集")
            top_fix = clusters_data.get('top_fix')
            if top_fix:
                lines.append(f"- 最高槓桿修正: {top_fix['root_cause']} "
                             f"(影響 {top_fix['cases_affected']} 個 case, "
                             f"leverage={top_fix['leverage_score']:.1f})")

    lines.append('')
    lines.append('## 建議下一輪優先修正項目')
    if benchmark_results.get('fail_cases'):
        # Group by error category
        categories = {}
        for fc in benchmark_results['fail_cases']:
            cat = fc.get('error_category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        sorted_cats = sorted(categories.items(), key=lambda x: -x[1])
        for cat, count in sorted_cats[:3]:
            lines.append(f'- {cat} ({count} 次)')
    else:
        lines.append('- 全部通過，可考慮增加更多 benchmark cases')

    lines.append('')
    lines.append('## 是否值得升級為 Gold Sample')
    if pass_rate >= 1.0:
        lines.append('✅ 全部通過，建議將新增 cases 納入 gold_bank。')
    elif pass_rate >= 0.9:
        lines.append('⚠️ 接近全過，修正剩餘問題後可納入 gold_bank。')
    else:
        lines.append('❌ 尚未穩定，不建議納入 gold_bank。')

    return '\n'.join(lines)


def save_iteration_report(report_md, reports_dir):
    """Save report to latest and history."""
    os.makedirs(reports_dir, exist_ok=True)
    history_dir = os.path.join(reports_dir, 'history')
    os.makedirs(history_dir, exist_ok=True)

    latest_path = os.path.join(reports_dir, 'latest_iteration_report.md')
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    today = date.today().isoformat()
    history_path = os.path.join(history_dir, f'{today}_iteration_report.md')
    with open(history_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    return latest_path, history_path
