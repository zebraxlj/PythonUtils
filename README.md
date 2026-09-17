# PythonUtils

A collection of small, **dependency-free** (stdlib-only) Python utilities for
terminal and everyday scripting work:

| Module | What it does |
|---|---|
| `ColorHelper` | xterm-256 color palette as an `IntEnum`, with RGB/hex conversions |
| `StringComparator` | Rule-based string matching driven by TOML rule files |
| `SystemTools` | Clipboard write (tkinter + xclip/wl-copy/pbcopy/win32 fallbacks), terminal redraw, filesystem helpers |
| `TablePrinter` | Unicode box-drawing tables with alignment, conditional formatting, hyperlinks and row banding |

Requires Python 3.11+ (uses `tomllib`).

## Install

```bash
pip install -e .[dev]    # for development (pytest, ruff)
# or just use the folders directly — everything is stdlib
```

## ColorHelper

```python
from ColorHelper.color_xterm_256 import ColorXTerm256

ColorXTerm256.BRIGHT_RED                    # <ColorXTerm256.BRIGHT_RED: 9>
ColorXTerm256.from_rgb(255, 0, 0)           # nearest of the 256 colors → BRIGHT_RED
ColorXTerm256.from_hex('#3f51b5')           # nearest palette entry for an RGB hex
ColorXTerm256(196).to_rgb()                 # (255, 0, 0) — cube index back to RGB
```

`to_rgb()` covers all three palette regions: the 16 basic ANSI colors, the
6×6×6 color cube (16–231), and the 24-step grayscale ramp (232–255).

## StringComparator

Match a line against rules loaded from a TOML file. Each rule group is an
array of tables; a rule has `method` (`contain`/`start_with`/`end_with`/`regex`),
`keywords` (one or more), and an optional `logic` (`and`/`or`) used when more
than one keyword is given.

```toml
# rules.toml
[[RuleGroup1]]
method = "contain"
keywords = ["Samson"]

[[RuleGroup2]]
method = "regex"
keywords = [".*?\\[Samson.*?"]
```

```python
from StringComparator.string_comparitor import get_rule_dict

rules = get_rule_dict("rules.toml")      # cached per file path
for group_name, rules in rules.items():
    for rule in rules:
        print(group_name, rule.matches("padding [samson is good"))
```

Bundled sample rules live in `StringComparator/data/sample_rules.toml`.

## SystemTools

```python
from SystemTools.clipboard_writer import copy_to_clipboard
copy_to_clipboard("text to copy")

from SystemTools.file_system_helper import create_dir_if_not_exists
create_dir_if_not_exists(dir_path="/tmp/out")          # mkdir -p
create_dir_if_not_exists(file_path="/tmp/out/a.txt")   # ...or parent of a file

from SystemTools.terminal_updater import TerminalUpdater
updater = TerminalUpdater()
updater.update(["progress 42%", "eta 3s"])   # redraws only changed lines
updater.update(["progress 87%", "eta 1s"])
```

Clipboard strategy: tkinter first (interactive X/Wayland sessions), then
`wl-copy`/`xclip`/`xsel` on Linux, `pbcopy` on macOS, and the Win32 API on
Windows. An explicit `RuntimeError` is raised when no backend is available —
no silent "clipboard write failed" prints that leave you guessing.

## TablePrinter

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from TablePrinter.table_printer import BaseRow, BaseTable, ColumnConfig, ColumnAlignment

@dataclass
class Employee(BaseRow):
    Name: str = ''
    __Name_config: ClassVar[ColumnConfig] = ColumnConfig(alias='Name')
    Salary: int = 0
    __Salary_config: ClassVar[ColumnConfig] = ColumnConfig(alias='Salary')
    HiredAt: datetime = field(default_factory=datetime.now)
    __HiredAt_config: ClassVar[ColumnConfig] = ColumnConfig(format='%Y-%m-%d')

class EmployeeTable(BaseTable):
    row_type = Employee

table = EmployeeTable()
table.insert_row(Employee(Name='Ada', Salary=5000))
table.print_table(order_by=['Salary'], ascending=[False])
```

Features: column aliases, alignment (left/center/right), hidden columns,
datetime formatting, sorting (multi-key, mixed ascending/descending),
conditional formatting (`CondFmtContain` / `CondFmtExactMatch`), OSC-8
hyperlinks via `col_href`/`col_url` fields, alternating row banding
(`ENABLE_ROW_BACKGROUND`), and header color bands.

**Piped output is safe:** ANSI color and hyperlink escapes are only emitted
when stdout is an interactive terminal, so `script.py > out.txt` produces
clean plain-text output.

## Tests

```bash
pytest                # ~150 offline tests, no network, no hardware
ruff check .          # bug-catching lints (F, E9)
```

## License

MIT — see [LICENSE](LICENSE).