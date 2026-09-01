
---

## Addendum (same session, after handoff was written)

- Early RAG code removed from `baseline-v1`, parked at branch `wip/rag-early`
  and tag `rag-early-parked`. See `tests/golden/KNOWN_GAPS.md` for reasoning.
- `find_violations.ps1` and `violation_report.txt` removed (an earlier `git rm`
  had aborted atomically because one path didn't exist).
- `data/chroma/` and `*.egg-info/` added to `.gitignore`.
- Tag `baseline-v1-clean` marks the end of the cleanup phase.
