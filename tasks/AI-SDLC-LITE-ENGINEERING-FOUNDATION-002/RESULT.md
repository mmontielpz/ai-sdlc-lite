# Result: ENGINEERING-FOUNDATION-002, framework corrections

- **Authority:** owner mission ENGINEERING-FOUNDATION-002, 2026-11-28 (OD-40). Gate 2: PENDING. Hosted CI results are recorded in the pull request.
- **Base:** `1338d5d36e357ba15d7ac456e2d554b9863716f8`. Local environment: Linux, Python 3.14; Ubuntu 24.04 container for the build.

| Item | Change | Local evidence |
|---|---|---|
| M-03 | Untracked and ignored content is read only with `--hash-untracked`; unprovable paths are judged changed; untracked in-repository evidence is refused | `tests/test_verify_foundation.py` (reads observed through `Path.read_bytes`) |
| EXP-2, EXP-3 | Name limit 200,000; baseline record limit 32 MiB; writers refuse output their reader rejects | 32,000-file round trip; limit boundary tests |
| EXP-4 | `baseline --out` prints a summary | summary tests; stdout without `--out` stays the JSON record |
| EXP-1 | Prerequisites and reproducible build documented; CI step builds twice in Ubuntu 24.04 | CI step run locally: identical wheels |

**Representation assessed first:** compact or grouped JSON would reduce size by a constant factor and still exceed 1 MiB for ordinary Node projects; per-directory digests would lose per-path classification. Raising the limits keeps schema `/1` and comparison semantics.

**Measured** (ignored files: old record / outcome → new record, verify time, peak memory): 1,000: 61 kB, works → 61 kB, 0.08 s, 23 MB. 25,000: 1.27 MB, verify exit 2 → 1.59 MB, 0.11 s, 34 MB. 100,000: exit 2 → 6.47 MB, 0.22 s, 65 MB. 200,000: exit 2 → 13.07 MB, 0.38 s, 108 MB. Synthetic empty files on local disk; real trees may differ.

**Test changes:** existing preservation tests and one golden scenario now pass `--hash-untracked`, the authorized mode they exercise; golden reports are unchanged. The pinned verifier digest in `tests/test_experience_cli.py` is updated.

**Correction to the W01 observation:** the Ubuntu wheel failure occurs with `setuptools` 68.1.2 when `wheel` is absent (virtual-environment route). The `python3-pip` package already depends on `python3-wheel`.

**Limits:** changes inside already-ignored files are not detected; names of untracked and ignored files are still recorded; Git itself reads tracked files and `.gitignore` files; delivery commands that hash files named in an approved plan are unchanged. macOS and Windows: not run.
