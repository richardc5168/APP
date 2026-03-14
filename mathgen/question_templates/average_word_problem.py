"""平均數應用題生成器 — 規則式。"""
import random
from .base import BaseGenerator


_TEMPLATES = [
    {
        'text': '{name}三次考試的分數分別是 {vals}，請問平均分數是多少分？',
        'unit': '分',
        'context': 'exam',
    },
    {
        'text': '{name}連續 {n} 天記錄氣溫，分別是 {vals} 度，平均氣溫是多少度？',
        'unit': '度',
        'context': 'temperature',
    },
    {
        'text': '籃球隊 {n} 場比賽的得分分別是 {vals}，平均每場得多少分？',
        'unit': '分',
        'context': 'sports',
    },
    {
        'text': '{name}每天喝水量分別是 {vals} 毫升，平均每天喝多少毫升？',
        'unit': '毫升',
        'context': 'health',
    },
]

_NAMES = ['小明', '小華', '小美', '小強', '小芳']


class AverageWordProblemGenerator(BaseGenerator):
    TOPIC = 'average_word_problem'
    GRADE = 5

    def generate(self, params=None):
        if params:
            values = params['values']
            tpl_idx = params.get('template_index', 0)
            name = params.get('name', '小明')
        else:
            tpl_idx = random.randint(0, len(_TEMPLATES) - 1)
            name = random.choice(_NAMES)
            n = random.randint(3, 5)
            tpl = _TEMPLATES[tpl_idx]
            if tpl['context'] == 'exam':
                values = [random.randint(60, 100) for _ in range(n)]
            elif tpl['context'] == 'temperature':
                values = [random.randint(20, 35) for _ in range(n)]
            elif tpl['context'] == 'sports':
                values = [random.randint(50, 120) for _ in range(n)]
            else:
                values = [random.randint(800, 2500) for _ in range(n)]

        tpl = _TEMPLATES[tpl_idx % len(_TEMPLATES)]
        n = len(values)
        total = sum(values)
        vals_str = '、'.join(str(v) for v in values)

        # Exact division check — if not exact, present as decimal
        # Use integer arithmetic only (IEEE 754 avoidance)
        if total % n == 0:
            answer = str(total // n)
        else:
            # One decimal place via integer arithmetic
            scaled = total * 10
            quotient = scaled // n
            remainder = scaled % n
            # Round half-up (matches Python's f"{x:.1f}" for positives)
            if remainder * 2 >= n:
                quotient += 1
            integer_part = quotient // 10
            decimal_part = quotient % 10
            if decimal_part == 0:
                answer = str(integer_part)
            else:
                answer = f'{integer_part}.{decimal_part}'

        steps = [
            f'所有數值加總：{" + ".join(str(v) for v in values)} = {total}',
            f'共有 {n} 個數值',
            f'平均 = 總和 ÷ 個數 = {total} ÷ {n}',
            f'答案：{answer} {tpl["unit"]}',
        ]

        # Build hints — must NOT leak the final answer
        # L2: listing individual values can accidentally match the answer,
        # so use a generic phrasing instead.
        hint_ladder = {
            'level_1': '平均數 = 總和 ÷ 個數，先把所有數字加起來。',
            'level_2': f'把題目裡的 {n} 個數字全部加起來，求出總和。',
            'level_3': f'總和 = {total}，接下來算 {total} ÷ {n}。',
            'level_4': f'算完後，用平均數乘以 {n} 驗算是否等於 {total}。',
        }
        # Extra leak guard: if answer appears in any hint, rewrite that hint
        for lvl_key in list(hint_ladder.keys()):
            if answer and len(answer) > 1 and answer in hint_ladder[lvl_key]:
                if lvl_key == 'level_3':
                    hint_ladder[lvl_key] = f'算出總和後，除以 {n} 就是平均數。'
                elif lvl_key == 'level_4':
                    hint_ladder[lvl_key] = f'驗算：平均數 × {n} 應該等於總和。'

        problem_text = tpl['text'].format(
            name=name, n=n, vals=vals_str
        )
        parameters = {
            'values': values,
            'name': name,
            'template_index': tpl_idx,
        }

        return self.build_question(
            topic=self.TOPIC,
            difficulty='easy',
            problem_text=problem_text,
            parameters=parameters,
            correct_answer=answer,
            unit=tpl['unit'],
            steps=steps,
            hint_ladder=hint_ladder,
            validation_rules={
                'answer_type': 'integer_or_decimal',
                'unit': tpl['unit'],
            },
        )
