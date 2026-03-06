"""Fix daily counter injection in empire life-pack modules — add function def, remove dupes."""
import os

BASE = os.path.dirname(os.path.dirname(__file__))

MODULES = [
    'interactive-g5-life-pack1-empire',
    'interactive-g5-life-pack1plus-empire',
    'interactive-g5-life-pack2-empire',
    'interactive-g5-life-pack2plus-empire',
]

FUNC_DEF = """
    function gUpdateDailyCounter(){
      if (els.gDailyCounter && window.AIMathDailyLimit){
        els.gDailyCounter.innerHTML = window.AIMathDailyLimit.buildCounterHTML();
      }
    }
"""

for mod in MODULES:
    path = os.path.join(BASE, 'docs', mod, 'index.html')
    if not os.path.exists(path):
        print(f"SKIP {mod}")
        continue

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    # 1. Add function def after gBanner if missing
    if 'function gUpdateDailyCounter' not in content:
        # Find the end of gBanner function
        target = "    function gBanner(kind, text){\n      if (!els.gBanner) return;\n      els.gBanner.className = `banner ${kind}`;\n      els.gBanner.textContent = text;\n    }"
        if target in content:
            content = content.replace(target, target + FUNC_DEF, 1)
            changes.append('added function def')
        else:
            print(f"WARN {mod}: gBanner pattern not found")

    # 2. Remove duplicate gUpdateDailyCounter() calls
    content = content.replace(
        '        gUpdateDailyCounter();\n        gUpdateDailyCounter();\n',
        '        gUpdateDailyCounter();\n'
    )

    # 3. Add gStart call if missing
    counter_calls = content.count('gUpdateDailyCounter();')
    if counter_calls < 3:
        # Check if gStart has the call
        # Find gUpdate(); in gStart context
        lines = content.split('\n')
        found_gstart_call = False
        for i, l in enumerate(lines):
            if 'gUpdate();' in l.strip() and l.strip() == 'gUpdate();':
                context = '\n'.join(lines[max(0,i-10):i])
                if 'gPick()' in context or 'buildGamePool' in context:
                    # Check if next line already has the call
                    if i+1 < len(lines) and 'gUpdateDailyCounter' in lines[i+1]:
                        found_gstart_call = True
                    else:
                        indent = l[:len(l) - len(l.lstrip())]
                        lines.insert(i + 1, indent + 'gUpdateDailyCounter();')
                        content = '\n'.join(lines)
                        changes.append('added gStart call')
                        found_gstart_call = True
                    break

    if changes:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        total = content.count('gUpdateDailyCounter')
        print(f"OK {mod}: {changes}, {total} total refs")
    else:
        total = content.count('gUpdateDailyCounter')
        print(f"CLEAN {mod}: {total} total refs")
