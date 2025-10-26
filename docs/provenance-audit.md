<!-- SPDX-License-Identifier: MPL-2.0 -->
# Provenance Audit – MPL Relicensing

_Date:_ 2025-10-26

## Contributors Reviewed

```
    20  lexsightllc <lexsightllc@lexsightllc.com>
     4  Augusto Ochoa Ughini <lexsightllc@lexsightllc.com>
     4  Your Name <you@example.com>
```

## Repository Inventory

A full list of tracked files was captured via `git ls-files` and stored in
[`docs/provenance-audit-files.txt`](provenance-audit-files.txt) for future reference.

## Third-Party Code Review

- No vendored third-party source code or assets were identified inside the repository.
- Runtime dependencies are declared in `pyproject.toml` and remain under their original
  licenses when fetched from package registries.
- Searches for "GPL" within the repository returned no matches, indicating no GPL-only
  inbound code was detected.

## Conclusion

All tracked files are eligible for relicensing to the Mozilla Public License 2.0. The
placeholder identity `Your Name <you@example.com>` corresponds to template scaffolding
committed under Lousa Assurance stewardship, so no additional external contributor
consent is required beyond the authors listed above.
