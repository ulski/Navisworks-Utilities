# Navisworks Appearance Profiler migration
Note: Autodesk® and Navisworks® are trademarks or registered trademarks of Autodesk, Inc. This project is not affiliated with, sponsored, or endorsed by Autodesk.

Fixes malformed Appearance Profiler XML produced when importing older (.dat) Appearance Profiler files into newer Navisworks versions, and resets unintended “Hidden” visibility.

## Why this exists
When a Navisworks 2024 (or older) Appearance Profiler `.dat` file is imported into a newer Navisworks version, Navisworks writes an XML profile to:
- `%APPDATA%\Autodesk\Navisworks [Simulate|Manage] 20XX\AppearanceProfiler\`

If your `.dat` was named `myfile.dat`, Navisworks creates:
- `myfile (Imported).xml`

However:
- If the original `.dat` used AVEVA/PDMS properties, the generated XML can be malformed.
- Some Navisworks versions also mark rules as “Hidden,” although `.dat` files don’t support hidden visibility.

This script corrects those issues and writes a fixed XML:
- `myfile (Imported)_fixed.xml`
You can (and usually should) rename the file and the profile name inside the XML afterwards.

## What this script changes
For the selected XML file, it:
- Replaces `<ForceVisibility>Hidden</ForceVisibility>` with `<ForceVisibility>Unchanged</ForceVisibility>`.
- Converts AVEVA/PDMS categories:
  - `<Category Internal="">PDMS</Category>` ➜ `<Category Internal="lcldrvm_props">AVEVA</Category>`
- Updates the immediately following property (if present and missing an Internal value):
  - `<Property Internal="">X</Property>` ➜ `<Property Internal="lcldrvm_prop_x">X</Property>` (where `x` is lowercase).

It reports how many ForceVisibility, Category, and Property elements were changed.

## Requirements
- Python 3.13 with Tkinter (tested). Other Python versions may work but are unverified.
- No external dependencies

## Usage
1) In the newer Navisworks version, import your older `.dat` Appearance Profiler. This creates `<Name> (Imported).xml` in the folder mentioned above.  
2) Run this script:
   - From a terminal in this folder:
     ```bash
     python main.py
     ```
   - A file picker opens. Select the XML created by Navisworks (e.g., `myfile (Imported).xml`).
3) The script creates a copy alongside the original and patches it:
   - Output: `myfile (Imported)_fixed.xml`
4) Optional but recommended:
   - Rename the file to your desired final name (e.g., `myfile.xml`).
   - Also update the profile name inside the XML (open in a text editor and adjust the visible name element/attribute) or rename it after loading the XML file back into Navisworks.
  
## Limitations and notes
- If the XML is not well‑formed, you’ll see “XML parse error.”
- If the file is locked or you lack permissions, you’ll see a permission error.
- Always keep the original `(Imported).xml` as a backup.

## License
SPDX: MIT — see the [LICENSE](../LICENSE) file for details.

---

See the code: [script.py](./script.py)
