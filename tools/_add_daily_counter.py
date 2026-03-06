"""Inject daily limit counter UI into empire modules."""
import re, os

BASE = os.path.dirname(os.path.dirname(__file__))

EMPIRE_MODULES = [
    'interactive-decimal-g5',
    'interactive-g5-life-pack1-empire',
    'interactive-g5-life-pack1plus-empire',
    'interactive-g5-life-pack2-empire',
    'interactive-g5-life-pack2plus-empire',
]

COUNTER_DIV = '        <div id="gDailyCounter" style="margin-top:6px"></div>'

COUNTER_FUNC_LINES = [
    '',
    '    function gUpdateDailyCounter(){',
    '      if (els.gDailyCounter && window.AIMathDailyLimit){',
    '        els.gDailyCounter.innerHTML = window.AIMathDailyLimit.buildCounterHTML();',
    '      }',
    '    }',
]

for mod in EMPIRE_MODULES:
    path = os.path.join(BASE, 'docs', mod, 'index.html')
    if not os.path.exists(path):
        print(f"SKIP {mod} (not found)")
        continue

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changes = 0

    # 1. Add gDailyCounter div after meter bar
    has_counter_div = any('id="gDailyCounter"' in l for l in lines)
    if not has_counter_div:
        for i, l in enumerate(lines):
            if 'id="gBar"' in l and '<div class="meter"' in l:
                # Insert after this line (or after gProgressMeta if it follows)
                insert_at = i + 1
                # Check if next line is gProgressMeta
                if insert_at < len(lines) and 'gProgressMeta' in lines[insert_at]:
                    insert_at += 1
                lines.insert(insert_at, COUNTER_DIV + '\n')
                changes += 1
                break

    # 2. Add gDailyCounter to els object
    has_counter_el = any('gDailyCounter:' in l for l in lines)
    if not has_counter_el:
        for i, l in enumerate(lines):
            if "gBar: document.getElementById('gBar')" in l:
                lines.insert(i + 1, "      gDailyCounter: document.getElementById('gDailyCounter'),\n")
                changes += 1
                break

    # 3. Add gUpdateDailyCounter function after gBanner function
    has_counter_func = any('gUpdateDailyCounter' in l for l in lines)
    if not has_counter_func:
        for i, l in enumerate(lines):
            if 'function gBanner(kind, text){' in l:
                # Find the closing brace of gBanner
                brace_count = 0
                for j in range(i, min(i + 10, len(lines))):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count == 0 and j > i:
                        # Insert after closing brace
                        for k, func_line in enumerate(COUNTER_FUNC_LINES):
                            lines.insert(j + 1 + k, func_line + '\n')
                        changes += 1
                        break
                break

    # 4. Add gUpdateDailyCounter() after gUpdate() in gStart
    counter_calls = sum(1 for l in lines if 'gUpdateDailyCounter()' in l)
    if counter_calls < 1:
        for i, l in enumerate(lines):
            if 'gUpdate();' in l.strip() and l.strip() == 'gUpdate();':
                # Check if nearby lines suggest this is in gStart (look for gPick above)
                context = ''.join(lines[max(0,i-10):i])
                if 'gPick()' in context or 'buildGamePool' in context:
                    indent = l[:len(l) - len(l.lstrip())]
                    lines.insert(i + 1, indent + 'gUpdateDailyCounter();\n')
                    changes += 1
                    break

    # 5. Add gUpdateDailyCounter() after increment() in gSubmit
    counter_calls = sum(1 for l in lines if 'gUpdateDailyCounter()' in l)
    if counter_calls < 2:
        for i, l in enumerate(lines):
            if 'AIMathDailyLimit.increment()' in l:
                indent = l[:len(l) - len(l.lstrip())]
                lines.insert(i + 1, indent + 'gUpdateDailyCounter();\n')
                changes += 1
                break

    # 6. Add gUpdateDailyCounter() in init after saveEmpire()
    counter_calls = sum(1 for l in lines if 'gUpdateDailyCounter()' in l)
    if counter_calls < 3:
        # Find the init section: look for "// init" or "// ---------- init"
        for i, l in enumerate(lines):
            if '// init' in l.lower() or '// ---------- init' in l:
                # Find saveEmpire() after this
                for j in range(i, min(i + 10, len(lines))):
                    if 'saveEmpire()' in lines[j]:
                        indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                        lines.insert(j + 1, indent + 'gUpdateDailyCounter();\n')
                        changes += 1
                        break
                break

    if changes > 0:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(lines)
        total_refs = sum(1 for l in lines if 'gUpdateDailyCounter' in l)
        print(f"OK {mod} ({changes} changes, {total_refs} total refs)")
    else:
        print(f"NO-CHANGE {mod}")
