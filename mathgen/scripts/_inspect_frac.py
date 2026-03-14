"""Inspect fraction benchmark cases."""
import json
cases = json.load(open('mathgen/benchmarks/fraction_word_problem.json'))
for i, c in enumerate(cases[:5]):
    inp = c.get('input', {})
    print(f"Case {i}: a={inp.get('a_num')}/{inp.get('a_den')}, "
          f"b={inp.get('b_num')}/{inp.get('b_den')}, "
          f"tpl={inp.get('template_index')}, "
          f"expected={c.get('expected_answer','?')}, "
          f"pattern={c.get('pattern_type','?')}, "
          f"risk={c.get('risk_level','?')}")
