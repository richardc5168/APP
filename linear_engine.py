# -*- coding: utf-8 -*-

import random
import sympy as sp
from typing import Dict, Any
try:
    from gamification import MathGamifier
except ImportError:
    # Fallback if regular import fails (e.g. during certain test setups), though in this env it works
    MathGamifier = None

class LinearEngine:
    """
    Core engine for Linear Equations in One Variable (一元一次方程式).
    Levels focused on key concepts: Transposition, Removing Brackets, Combining Terms.
    Integrated with Gamification for student engagement.
    """

    def __init__(self):
        self.x = sp.Symbol('x')
        self.gm = MathGamifier() if MathGamifier else None

    def _step(self, text):
        if self.gm:
            return self.gm.wrap_step(text)
        return f"👉 {text}"

    def _hint(self, text):
        if self.gm:
            return f"{self.gm.get_hint_prefix()} {text}"
        return f"💡 {text}"

    def generate_problem(self, level: int = 1) -> Dict[str, Any]:
        """
        Generate a linear equation problem based on difficulty Level 1-5.
        """
        x = self.x
        explanation_steps = []
        
        # Strategy: Pick a solution x first, then construct the equation backwards to ensure integer solutions (mostly).
        sol = random.randint(-10, 10)
        # Avoid 0 sometimes to make it strictly signed, but 0 is valid.
        if sol == 0: sol = random.randint(1, 9)

        question_latex = ""
        question_text = ""
        
        if level == 1:
            # Level 1: One-step equations (ax = b or x + a = b)
            # Concept: Inverse operation
            mode = random.choice(['add', 'mul'])
            if mode == 'add':
                a = random.randint(1, 20) * random.choice([1, -1])
                # x + a = target -> target = sol + a
                target = sol + a
                expr = x + a - target
                question_text = f"解方程式：x {self._sign(a)} = {target}"
                
                explanation_steps.append(f"🏁 題目: {question_text}")
                explanation_steps.append(self._hint(f"我們的目標是讓 x 單獨留在左邊！觀察看看，左邊除了 x 還有什麼？ 是 {a}！"))
                explanation_steps.append(self._step(f"啟動移項法則：把 {a} 移到右邊去。記得口訣：『加變減，減變加』喔！"))
                explanation_steps.append(self._step(f"算式變身：x = {target} - ({a})"))
                explanation_steps.append(self._step(f"小心計算... 答案出來了！ x = {sol}"))
                if self.gm: explanation_steps.append(self.gm.get_encouragement())

            else:
                a = random.choice([2, 3, 4, 5, -2, -3, -4, -5])
                target = a * sol
                expr = a * x - target
                question_text = f"解方程式：{a}x = {target}"
                
                explanation_steps.append(f"🏁 題目: {question_text}")
                explanation_steps.append(self._hint(f"觀察發現 x 黏著一個係數 {a}。它們之間是乘法關係喔！"))
                explanation_steps.append(self._step(f"使用等量公理：為了抵銷乘法，我們將等號兩邊同時『除以 {a}』。"))
                explanation_steps.append(self._step(f"計算：x = {target} / {a}"))
                explanation_steps.append(self._step(f"搞定！ x = {sol}"))
                if self.gm: explanation_steps.append(self.gm.get_encouragement())

        elif level == 2:
            # Level 2: Two-step equations (ax + b = c)
            # Concept: Move constant first, then coefficient
            a = random.choice([2, 3, 4, 5, -2, -3])
            b = random.randint(1, 20) * random.choice([1, -1])
            c = a * sol + b
            expr = a * x + b - c
            question_text = f"解方程式：{a}x {self._sign(b)} = {c}"
            
            explanation_steps.append(f"🏁 題目: {question_text}")
            explanation_steps.append(self._hint("這題需要兩個步驟！想像這是剝洋蔥，要先剝外面（常數項），再剝裡面（係數）。"))
            explanation_steps.append(self._step(f"第一步：先處理常數項 {b}。把它踢到等號右邊變號！"))
            rhs = c - b
            explanation_steps.append(self._step(f"現在算式變乾淨了： {a}x = {c} - ({b})  =>  {a}x = {rhs}"))
            explanation_steps.append(self._step(f"第二步：處理 X 前面的係數 {a}。兩邊同除以 {a}。"))
            explanation_steps.append(self._step(f"計算結果： x = {rhs} / {a}"))
            explanation_steps.append(f"🎉 答案： x = {sol}")

        elif level == 3:
            # Level 3: Variables on both sides (ax + b = cx + d)
            # Concept: Grouping like terms (unknowns to left, constants to right)
            c = random.randint(2, 5) * random.choice([1, -1])
            a = c + random.choice([2, 3, 4]) * random.choice([1, -1]) # Ensure a != c
            if a == c: a += 1
            
            # ax + b = cx + d
            b = random.randint(1, 10) * random.choice([1, -1])
            lhs_val = a * sol + b
            d = lhs_val - c * sol
            
            expr = (a*x + b) - (c*x + d)
            question_text = f"解方程式：{a}x {self._sign(b)} = {c}x {self._sign(d)}"
            
            explanation_steps.append(f"🏁 題目: {question_text}")
            explanation_steps.append(self._hint("哇！兩邊都有 x，好像在拔河！除此之外還有常數項。"))
            explanation_steps.append(self._step("策略：『讓 x 回家，讓數字分家』。通常把有 x 的都趕到左邊，沒有 x 的都趕到右邊。"))
            explanation_steps.append(self._step(f"行動：把右邊的 {c}x 移到左邊變成 -({c}x)；把左邊的 {b} 移到右邊變成 -({b})。"))
            explanation_steps.append(self._step(f"列式：{a}x - ({c}x) = {d} - ({b})"))
            explanation_steps.append(self._step(f"合併同類項：({a-c})x = {d-b}"))
            explanation_steps.append(f"x = {d-b} / {a-c}")
            explanation_steps.append(f"x = {sol}")

        elif level == 4:
            # Level 4: Equations with Parentheses a(x+b) = c
            # Concept: Distributive property (去括號)
            a = random.choice([2, 3, 4, -2])
            b = random.randint(1, 5) * random.choice([1, -1])
            # a(x+b) = result
            rhs_val = a * (sol + b)
            
            question_text = f"解方程式：{a}(x {self._sign(b)}) = {rhs_val}"
            expr = a*(x+b) - rhs_val
            
            explanation_steps.append(f"題目: {question_text}")
            explanation_steps.append(f"第一步：等號兩邊同除以 {a}，先把係數消掉。")
            explanation_steps.append(f"x {self._sign(b)} = {rhs_val} / ({a})")
            simplified_rhs = rhs_val / a
            explanation_steps.append(f"x {self._sign(b)} = {simplified_rhs}")
            explanation_steps.append(f"第二步：移項，將 {b} 移到右邊變號。")
            explanation_steps.append(f"x = {simplified_rhs} - ({b})")
            explanation_steps.append(f"x = {sol}")

        else:
            # Level 5: Rational Equations reducible to Linear (Competition style)
            # Example: A / (x - B) = C / (x - D)
            # A(x - D) = C(x - B) -> Ax - AD = Cx - CB -> (A-C)x = AD - CB
            
            # Ensure solution is integer and valid (not B or D)
            while True:
                A = random.choice([2, 3, 4, 5])
                C = random.choice([1, 2, 3])
                if A == C: C += 1
                
                # Pick solution first
                sol = random.randint(-10, 10)
                if abs(sol) < 2: sol = 5
                
                # Pick B and D such that they don't equal sol
                B = sol - random.choice([1, 2, 3])
                # We need equation to hold: A(sol - D) = C(sol - B)
                # sol - D = (C/A)(sol - B) -> D = sol - (C/A)(sol - B)
                # To make D integer, (sol - B) must be divisible by A
                # Let's reconstruct: let's pick B such that sol-B is multiple of A
                k = random.choice([1, 2]) * random.choice([1, -1])
                # sol - B = k * A  => B = sol - k*A
                B = sol - k * A
                
                # Then D = sol - C*k
                D = sol - C * k
                
                # Check validity
                if D != sol and B != sol and B != D:
                   break
            
            question_text = f"解方程式：{A} / (x {self._sign(-B)}) = {C} / (x {self._sign(-D)})"
            # Cross multiplication form for easy checking logic if needed, but we output text
            
            explanation_steps.append(f"【題目】 {question_text} (Level 5 分式方程式)")
            explanation_steps.append(f"【觀察】 咦？未知數 x 躲在分母裡面？")
            explanation_steps.append(f"【小撇步】 當兩個分數相等時，它們的「交叉相乘」也會相等喔！")
            explanation_steps.append(f"【步驟 1】 交叉相乘把分母變不見：\n   {A} * (x {self._sign(-D)}) = {C} * (x {self._sign(-B)})")
            
            # Expand
            lhs_const = -A*D
            rhs_const = -C*B
            explanation_steps.append(f"【步驟 2】 用分配律把括號炸開 (小心負號)：\n   {A}x {self._sign(lhs_const)} = {C}x {self._sign(rhs_const)}")
            
            # Solve
            explanation_steps.append(f"【步驟 3】 讓 x 站左邊，數字站右邊 (移項)：")
            explanation_steps.append(f"   {A}x - ({C}x) = {rhs_const} - ({lhs_const})")
            val = rhs_const - lhs_const
            explanation_steps.append(f"   {A-C}x = {val}")
            explanation_steps.append(f"【步驟 4】 算出答案 x = {sol}")
            explanation_steps.append(f"【驗算】 最後檢查分母是不是 0？ (x≠{B}, x≠{D}) -> 通過驗算，答案正確！")

        return {
            "topic": "一元一次方程式",
            "level": level,
            "question_text": question_text,
            "correct_answer": str(sol),
            "explanation": "\n".join(explanation_steps),
            "coefficients": {}, # Not strictly needed for linear unless specified
            "type": "linear"
        }

    def check_answer(self, user_input: str, question_data: Dict[str, Any]) -> bool:
        """
        Check if user input is correct using SymPy.
        """
        try:
            # Basic parsing provided user doesn't input malicious code
            correct = question_data['correct_answer']
            
            # Simple string check first
            if user_input.strip() == correct.strip():
                return True
                
            # SymPy check (handle x=5 vs 5)
            u_str = user_input.replace('x', '').replace('=', '').strip()
            if not u_str: return False
            
            u_val = sp.sympify(u_str)
            c_val = sp.sympify(correct)
            
            return abs(u_val - c_val) < 1e-9
            
        except Exception:
            return False

    def _sign(self, num):
        return f"+ {num}" if num >= 0 else f"- {abs(num)}"

linear_engine = LinearEngine()
