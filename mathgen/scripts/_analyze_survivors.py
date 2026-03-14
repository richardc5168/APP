"""Temporary script to analyze mutation survivors."""
from mathgen.mutator import run_all_mutations
from collections import Counter

data = run_all_mutations(max_cases_per_topic=5)
survivors = data['survivors']
killed_details = data['killed_details']

topic_survivors = Counter()
for s in survivors:
    tpc = s['case_id'].split('[')[0]
    topic_survivors[(tpc, s['mutation'])] += 1

print("=== Survivor breakdown ===")
for (tpc, mut), cnt in sorted(topic_survivors.items()):
    print(f"  {tpc:30s} {mut:25s} {cnt}")

total = data['total_mutations']
killed = data['killed']
print(f"\nTotal killed: {killed}/{total} ({100*killed/total:.1f}%)")
print(f"Total survivors: {data['survived']}/{total}")

print("\n=== Per-topic kill rates ===")
for tpc, info in sorted(data['by_topic'].items()):
    k = info['killed']
    t = info['total']
    print(f"  {tpc:30s} {k}/{t} ({100*k/t:.1f}%)")

# Show fraction survivors detail
print("\n=== Fraction survivors detail ===")
for s in survivors:
    tpc = s['case_id'].split('[')[0]
    if tpc == 'fraction_word_problem':
        print(f"  {s['case_id']} mutation={s['mutation']}")

# Show unit_conversion survivors detail
print("\n=== Unit conversion survivors detail ===")
for s in survivors:
    tpc = s['case_id'].split('[')[0]
    if tpc == 'unit_conversion':
        print(f"  {s['case_id']} mutation={s['mutation']}")

# Show decimal survivors detail
print("\n=== Decimal survivors detail ===")
for s in survivors:
    tpc = s['case_id'].split('[')[0]
    if tpc == 'decimal_word_problem':
        print(f"  {s['case_id']} mutation={s['mutation']}")
