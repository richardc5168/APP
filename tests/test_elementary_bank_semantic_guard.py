import importlib.util
from pathlib import Path


def _load_validator_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "tools" / "validate_all_elementary_banks.py"
    spec = importlib.util.spec_from_file_location("validate_all_elementary_banks", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


validator = _load_validator_module()


def test_detects_non_integer_discrete_quantity():
    found = validator.find_non_integer_discrete_quantity("每份是 7/6 個水壺，共有 4 份。")
    assert found == ("7/6", "水壺")


def test_allows_integer_discrete_quantity():
    found = validator.find_non_integer_discrete_quantity("每份是 8/4 個水壺，共有 2 份。")
    assert found is None


def test_allows_non_integer_continuous_quantity():
    found = validator.find_non_integer_discrete_quantity("每份是 7/6 公升果汁，共有 4 份。")
    assert found is None


def test_semantic_guard_scoped_module_only_by_default():
    q = {
        "id": "demo_q_1",
        "kind": "u3_frac_times_int",
        "topic": "分數應用",
        "question": "每份是 7/6 個水壺，共有 4 份。",
        "answer": "14/3",
        "answer_mode": "fraction",
        "hints": ["a", "b", "c"],
    }
    issues_other = validator.validate_one("interactive-g5-life-pack1-empire", q, 1, False)
    codes_other = {code for code, _ in issues_other}
    assert "Q_SEMANTIC_UNIT" not in codes_other

    issues_pack2plus = validator.validate_one("interactive-g5-life-pack2plus-empire", q, 1, False)
    codes_pack2plus = {code for code, _ in issues_pack2plus}
    assert "Q_SEMANTIC_UNIT" in codes_pack2plus
