# Copilot Instructions — ai-math-web (Stability First)

## Role
You are an engineering agent working in this repo (`ai-math-web`). The product is an elementary math content supply chain. Stability and 100% correctness are top priority.

## MUST READ (Strict Workflow)
Before proposing ANY changes, you **MUST** read and follow the "AI Agent Workflow Instructions" in `README.md`.
For `exam-sprint` changes, also read `README.md` section **"Agent 快速問題點（Exam Sprint）"** first.

## Non-negotiables (do not violate)
1) **Stability First**: Do not break existing pipeline.
2) **No Hint Leaks**: Ensure NO Level 3 hint contains the final answer verbatim. Hints must guide, not solve.
3) **Strict Validation**:
   - **Local Check**: MUST pass `python tools/validate_all_elementary_banks.py` before any commit.
   - **Remote Check**: MUST pass `node tools/cross_validate_remote.cjs` after deployment.
4) **No Silent Failures**: Any invalid item must fail with explicit question id + reason.

## Definition of Done (DoD)
A change is complete ONLY when:
- **Local Validation**: `tools/validate_all_elementary_banks.py` outputs "ALL CHECKS PASSED".
- **Documentation**: Verify `README.md` instructions are followed.
- **Remote Verification**: Verify `tools/cross_validate_remote.cjs` passes (clean baseline or post-deployment).

## Atomic Changes Policy
- Make small, atomic changes. One commit should do one thing.
- If modifying validators/solver, add regression tests to prevent hint leaks.

---
**CRITICAL**: Always check `README.md` for the latest validation commands.

## Hint/Diagram Optimization Memory (Auto-learned)
Before modifying `docs/shared/hint_engine.js` or any diagram rendering, **MUST** consult `tools/hint_diagram_known_issues.json` for past issues and anti-patterns. After every fix, update the registry.

### Known Anti-Patterns (DO NOT reintroduce):
1. **AP-001**: Never use `extractIntegers()[2]` as height for volume diagrams — use `parseVolumeDims(text, kind)`.
2. **AP-002**: Never render `buildFractionBarSVG` (remainder diagram) for fraction addition word problems — check `isFracAddition` first.
3. **AP-003**: Every SVG dimension label must have a colour-coded arrow marker (not bare text).
4. **AP-004**: Pure calculations (`isPureCalculation()`) must skip diagrams and show text-based steps.

### Validation Gate:
- Run `node tools/audit_hint_diagrams.cjs` before committing any hint_engine.js changes.
- This audit is also run automatically in the 12h autonomous runner (Phase 4).
- After editing `docs/shared/hint_engine.js`, always sync to `dist_ai_math_web_pages/docs/shared/hint_engine.js`.
