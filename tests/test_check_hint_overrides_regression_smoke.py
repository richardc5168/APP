from scripts.check_hint_overrides_regression import check_template


def test_check_template_flags_leakage():
    # Use a fake override entry (no need to touch global HINT_OVERRIDES).
    entry = {
        "approved": True,
        "level1": "答案是 123",  # intentionally leaky
        "level2": "列式...",
        "level3": "計算...",
    }

    # Use a template that exists; '1' should always exist.
    errs = check_template(template_id="1", entry=entry, per_template=1, seed=123)

    # Either it flags leakage or override-not-applied (depending on engine safety gate).
    # In current design, check_template expects override to apply (when approved=True),
    # so leakage should be detectable.
    assert any(("leaks answer" in e) or ("override not applied" in e) for e in errs)
