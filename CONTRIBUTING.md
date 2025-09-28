# Contributing to econsim-vmt

Thank you for your interest in contributing! This project is licensed under the Apache License 2.0. By submitting a contribution (code, documentation, or other materials), you agree that your contribution is licensed under the Apache-2.0 license.

## Quick Start
1. Fork the repository and create a feature branch.
2. Create and activate the virtual environment:
   - make venv
   - source vmt-dev/bin/activate
3. Install dev dependencies: `pip install -e .[dev]`
4. Run the validation pipeline locally:
   - make test-unit lint type perf
5. Launch the VMT test launcher for interactive development:
   - make launcher

## Development Guidelines
- Determinism: Never introduce nondeterministic iteration, randomness without using the sanctioned RNG split, or alter tie-break ordering.
- Performance: Respect O(n) per-step complexity; avoid quadratic expansions. Watch FPS via perf harness (`scripts/perf_stub.py`).
- Single QTimer Loop: Do not add extra timers/threads for simulation steps.
- Snapshot Schema: Only append new fields; never reorder or remove existing ones.
- Preferences: Must remain pure/stateless. Register in `preferences/factory.py` + accompanying tests.
- Logging: Use the centralized debug logger and existing debug categories.

## Pull Request Checklist
- [ ] Tests added/updated (unit + any determinism/perf guards needed)
- [ ] `make test-unit` passes
- [ ] `make lint type` passes (Black, Ruff, MyPy)
- [ ] Performance gate (`make perf`) shows no regression (> ~2% slowdown) for relevant modes
- [ ] Updated docs / README sections if behavior or interface changed
- [ ] No stray debug prints or excessive logging in hot paths
- [ ] License headers present if creating new top-level files with substantial code

## Commit Standards
Use clear, imperative commit messages. Reference related docs or plan cards when applicable (e.g., `launcher: extract gallery panel (Part2-G12)`). Keep diffs minimal and focused.

## Code Style
- Python 3.11+, Black (line length 100)
- Ruff for lint; prefer fixing rather than blanket ignores
- Type hints encouraged; avoid `Any` unless justified

## License Header Template
For new source files (optional for small trivial modules, mandatory for >30 lines or core logic):
```
# Copyright (c) 2024-2025 Chris Funderburk
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

## Contributor License / DCO
By contributing you affirm you have the right to submit the code. If you prefer a Developer Certificate of Origin (DCO) sign-off, append this line to each commit message:
```
Signed-off-by: Your Name <email@example.com>
```

## Reporting Issues
Use GitHub Issues. Include reproduction steps, expected vs actual behavior, and environment details.

## Security
Do not open public issues for security-sensitive findings. Instead, contact the maintainer privately.

## Questions
Open a discussion or issue; educational clarity improvements are welcome.

Welcome aboard — excited to have your help advancing the educational simulation platform!
