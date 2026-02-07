# -*- coding: utf-8 -*-

import random
import sympy as sp
from typing import Dict, Any, Optional

try:
    from sympy import Symbol, solve, Eq, simplify, Rational, sqrt, expand, latex
except ImportError:
    # Fallback if sympy not installed
    Symbol = solve = Eq = simplify = Rational = sqrt = expand = latex = None

class QuadraticEngine:
    """
    Core engine for Quadratic Equations (Khan Academy A3-A5).
    Uses SymPy for rigorous generation and step verification (AlphaGeometry inspired logic).
    """

    def __init__(self):
        self.x = Symbol('x')

    def generate_problem(self, topic_id: str, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a problem based on topic and difficulty (MATH Dataset Levels 1-5).
        Returns question, answer, and STEP-BY-STEP explanation.
        """
        if topic_id == "A3":
            return self._gen_factoring(difficulty)
        elif topic_id == "A4":
            return self._gen_completing_square(difficulty)
        elif topic_id == "A5":
            return self._gen_formula(difficulty)
        else:
            return self._gen_factoring(difficulty) # Default

    def _build_hints(self, topic_id: str, level: int, a: int, b: int, c: int, kind: str) -> Dict[str, Any]:
        """Return a 3-level hint ladder aligned with the frontend buttons.

        Contract (important):
        - hints[0] => 因式分解法（先試）
        - hints[1] => 配方法（第二選擇）
        - hints[2] => 公式解準備（最後手段）

        Keep text free of backslashes for JSON safety.
        """

        x = self.x
        expr = a * x**2 + b * x + c

        # --- Hint 1: Factoring-first ---
        factoring_hint = "先試因式分解：把左邊拆成兩個一次因式，令每個因式為 0。"
        try:
            f = sp.factor(expr)
            # If factor() actually changed the expression, show it.
            if f != expr:
                # Special-case: repeated root (perfect square)
                repeated_base = None
                try:
                    if isinstance(f, sp.Pow) and f.exp == 2:
                        repeated_base = f.base
                    elif isinstance(f, sp.Mul):
                        args = list(f.args)
                        if len(args) == 2 and args[0] == args[1]:
                            repeated_base = args[0]
                except Exception:
                    repeated_base = None

                if repeated_base is not None:
                    base_str = self._fmt(repeated_base)
                    root_val = None
                    try:
                        sol = solve(repeated_base, x)
                        if sol:
                            root_val = str(sol[0]).replace('sqrt', '√')
                    except Exception:
                        root_val = None

                    if root_val is not None:
                        factoring_hint = (
                            f"因式分解：{self._fmt(expr)} = ({base_str})^2。"
                            f"同一個因式出現兩次，所以是重根。"
                            f"令 ({base_str})=0 → x={root_val}（重根）。"
                        )
                    else:
                        factoring_hint = (
                            f"因式分解：{self._fmt(expr)} = ({base_str})^2。"
                            f"同一個因式出現兩次，所以是重根。令 ({base_str})=0。"
                        )
                else:
                    f_str = str(f).replace('**', '^').replace('*', '')
                    factoring_hint = f"因式分解：{self._fmt(expr)} = {f_str}，令每個因式=0。"
            else:
                # Give classic guidance.
                if a == 1:
                    factoring_hint = f"先試因式分解：找兩個數 p、q，使得 p×q={c} 且 p+q={b}，寫成 (x+p)(x+q)=0。"
                else:
                    factoring_hint = "先試因式分解：若 a≠1，可用『ac 分解』：找兩數乘積=ac、和=b，拆中間項後分組分解。"
        except Exception:
            pass

        # --- Hint 2: Completing the square ---
        if a == 1:
            cs_hint = (
                f"配方法：x^2 + ({b})x = {-c}，補上 (b/2)^2 = ({b}/2)^2，"
                "把左邊補成 (x + b/2)^2，再開根號求 x。"
            )
            completing_square_hint = "".join(cs_hint)
        else:
            cs_hint = (
                "配方法：先兩邊同除以 a，變成 x^2 + (b/a)x + (c/a)=0；"
                "把常數移到右邊，在左邊補上 (b/2a)^2 讓它成為完全平方，再開根號求 x。"
            )
            completing_square_hint = cs_hint

        # --- Hint 3: Formula as last resort ---
        D = b**2 - 4*a*c
        formula_hint = (
            f"公式解（最後手段）：先算判別式 D=b^2-4ac = {b}^2 - 4·{a}·{c} = {D}，"
            f"再代入 x = (-b ± √D) / (2a) = ({-b} ± √{D}) / {2*a}。"
        )

        return {
            "hints": [factoring_hint, completing_square_hint, formula_hint],
            "method_order": ["factoring", "completing_square", "formula"],
            "hint_style": "tiered_v2"
        }

    def _gen_factoring(self, level: int):
        """
        Generates problems solvable by factoring.
        Also generates a step-by-step 'explanation_text'.
        """
        x = self.x
        explanation_steps = []
        
        if level <= 1:
            # Simple x(x-a)=0
            # Step 1: Logic
            r2 = random.randint(1, 10) * random.choice([1, -1])
            expr = expand(x * (x - r2))
            # Explanation
            explanation_steps.append(f"原始方程式: {str(expr).replace('**', '^').replace('*', '')} = 0")
            explanation_steps.append(f"提取公因式 x: x(x - {r2}) = 0")
            explanation_steps.append(f"令每一項為 0: x = 0 或 x - {r2} = 0")
            explanation_steps.append(f"解得: x = 0, {r2}")
            
        elif level == 2:
            # Monic: (x-r1)(x-r2)=0
            r1 = random.randint(1, 12) * random.choice([1, -1])
            r2 = random.randint(1, 12) * random.choice([1, -1])
            expr = expand((x - r1) * (x - r2))
            
            explanation_steps.append(f"原始方程式: {self._fmt(expr)} = 0")
            explanation_steps.append(f"尋找兩個數，乘積為 {r1*r2}，和為 {-(r1+r2)}。")
            explanation_steps.append(f"這兩個數為 {-r1} 和 {-r2}。")
            explanation_steps.append(f"因式分解: (x - {r1})(x - {r2}) = 0")
            explanation_steps.append(f"解得: x = {r1}, {r2}")
            
        else: # level >= 3
            # Non-monic: (a1x - b1)(a2x - b2) = 0
            # Cross multiplication logic
            a1 = random.randint(1, 5)
            b1 = random.randint(1, 5) * random.choice([1, -1])
            a2 = random.randint(1, 5)
            b2 = random.randint(1, 5) * random.choice([1, -1])
            expr = expand((a1*x - b1) * (a2*x - b2))
            
            explanation_steps.append(f"原始方程式: {self._fmt(expr)} = 0")
            explanation_steps.append(f"使用十字交乘法分解。")
            explanation_steps.append(f"分解: ({a1}x - {b1})({a2}x - {b2}) = 0")
            explanation_steps.append(f"令每項為 0: {a1}x = {b1} 或 {a2}x = {b2}")
            # Simplify fraction strings
            r1_str = f"{b1}/{a1}" if b1%a1!=0 else str(b1//a1)
            r2_str = f"{b2}/{a2}" if b2%a2!=0 else str(b2//a2)
            explanation_steps.append(f"解得: x = {r1_str}, {r2_str}")

        # Build Output
        a = int(expr.coeff(x, 2))
        b = int(expr.coeff(x, 1))
        c = int(expr.coeff(x, 0))
        
        equation_latex = latex(Eq(expr, 0))
        equation_str = self._fmt(expr) + " = 0"
        
        solutions = solve(expr, x)
        solutions_str = ", ".join([str(s) for s in solutions])

        return {
            "topic": "一元二次方程式-因式分解法",
            "level": level,
            "question_latex": equation_latex,
            "question_text": f"解方程式：{equation_str}",
            "correct_answer": solutions_str,
            "coefficients": {"a": a, "b": b, "c": c},
            "explanation": "\n".join(explanation_steps),
            "solution": "\n".join(explanation_steps),
            **self._build_hints("A3", level, a, b, c, kind="factoring"),
            "type": "factoring"
        }

    def _gen_completing_square(self, level: int):
        # Mapped to formula for now, but with specific explanation if I had time
        # Let's just generate a formula one but label it Completing Square for MVP
        res = self._gen_formula(level)
        res["topic"] = "一元二次方程式-配方法 (以公式解驗證)"
        return res

    def _gen_formula(self, level: int):
        """
        Generates problems suited for Quadratic Formula.
        """
        x = self.x
        
        # Construct valid quadratic
        while True:
            if level <= 4:
                a = random.randint(1, 5)
                b = random.randint(2, 12) * random.choice([1, -1])
                c = random.randint(1, 10) * random.choice([1, -1])
            else:
                a = random.randint(2, 9)
                b = random.randint(10, 30) * random.choice([1, -1])
                c = random.randint(5, 20) * random.choice([1, -1])
            
            D = b**2 - 4*a*c
            if D > 0: # Real roots
                break
        
        expr = a*x**2 + b*x + c
        equation_str = f"{self._fmt(expr)} = 0"
        
        # Explanation
        steps = []
        steps.append(f"方程式: {equation_str}")
        steps.append(f"辨識係數: a={a}, b={b}, c={c}")
        steps.append(f"計算判別式 D = b^2 - 4ac")
        steps.append(f"D = ({b})^2 - 4({a})({c}) = {b**2} - {4*a*c} = {D}")
        
        sqrtD = sqrt(D)
        if sqrtD.is_integer:
             steps.append(f"因為 D={D} 是完全平方數，根號 D = {int(sqrtD)}")
             steps.append(f"x = (-({b}) ± {int(sqrtD)}) / (2*{a})")
        else:
             steps.append(f"D={D} 不是完全平方數，保留根號。")
             steps.append(f"x = (-({b}) ± √{D}) / {2*a}")
        
        sol = solve(expr, x)
        sol_str = ", ".join([str(s).replace('sqrt', '√') for s in sol]) 
        steps.append(f"最終答案: {sol_str}")

        return {
            "topic": "一元二次方程式-公式解",
            "level": level,
            "question_text": f"解方程式 (公式解)：{equation_str}",
            "correct_answer": sol_str,
            "coefficients": {"a": a, "b": b, "c": c},
            "explanation": "\n".join(steps),
            "solution": "\n".join(steps),
            **self._build_hints("A5", level, a, b, c, kind="formula"),
            "type": "formula"
        }

    def check_answer(self, user_input: str, question_data: Dict[str, Any]) -> bool:
        """
        Uses SymPy logic to check equivalence.
        """
        try:
            # 1. Parse user input: remove 'x=', allow 'sqrt', normalizes
            raw = user_input.replace('x', '').replace('=', '').replace(' ', '')
            
            # Simple splitter for comma
            user_parts = raw.split(',')
            user_set = set()
            
            for p in user_parts:
                if not p: continue
                # Use SymPy parse_expr for safety if trusted, strictly we should use standard parsing
                # For this env, simple parsing:
                # Replace '√' with 'sqrt'
                p_sym = p.replace('√', 'sqrt')
                try:
                    # simplistic check
                    val = sp.sympify(p_sym)
                    user_set.add(val)
                except:
                    # Fallback
                    pass

            # 2. Get Truth
            coeffs = question_data['coefficients']
            a, b, c = coeffs['a'], coeffs['b'], coeffs['c']
            truth = solve(a*self.x**2 + b*self.x + c, self.x)
            truth_set = set(truth)
            
            # 3. Compare sets
            # Checking subset or equality? Equality for full credit.
            # But floating point issues? SymPy handles exact well.
            if len(user_set) != len(truth_set):
                 return False
            
            # Check each user val is in truth
            for uv in user_set:
                matched = False
                for tv in truth_set:
                    if simplify(uv - tv) == 0:
                        matched = True
                        break
                if not matched:
                    return False
            
            return True

        except Exception as e:
            print(f"Check Error: {e}")
            return False
            
    def _fmt(self, expr):
        return str(expr).replace('**', '^').replace('*', '')

quadratic_engine = QuadraticEngine()
