# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ulrik Dan Christensen

r"""
Navisworks Appearance Profiler migration
Note: Navisworks is a trademark of Autodesk, Inc. This project is not affiliated with Autodesk.
Fixes issues in Appearance Profiler XML exported by newer Navisworks when importing
older (.dat) profiles containing AVEVA/PDMS categories and resets unintended “Hidden”
visibility.

Changes applied:
- <ForceVisibility>Hidden</ForceVisibility> -> <ForceVisibility>Unchanged</ForceVisibility>
- <Category Internal="">PDMS</Category> -> <Category Internal="lcldrvm_props">AVEVA</Category>
- Next-sibling <Property Internal="">X</Property> -> <Property Internal="lcldrvm_prop_x">X</Property>

Output: creates a patched copy named "<Name> (Imported)_fixed.xml" next to the input.
Typical Navisworks folder (Windows): %APPDATA%\Autodesk\Navisworks [Simulate|Manage] 20XX\AppearanceProfiler\

Requirements: Python 3.13 with Tkinter (tested). Other Python versions may work but are unverified.

"""
__version__ = "0.1.0"

import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional, Tuple, Union
import shutil
import xml.etree.ElementTree as ET

def patch_xml_in_place(
    xml_path: Union[str, Path]
) -> Tuple[bool, Optional[str], int, int, int]:
    """
    Returns (ok, error, force_visibility_changes, category_changes, property_changes).

    Rules:
      - <ForceVisibility>Hidden</ForceVisibility> -> <ForceVisibility>Unchanged</ForceVisibility>
      - <Category Internal="">PDMS</Category> -> <Category Internal="lcldrvm_props">AVEVA</Category>
      - For each such Category changed, if the next sibling is <Property Internal="">X</Property>,
        set it to <Property Internal="lcldrvm_prop_x">X</Property> where x is X lowercased.
    """
    try:
        p = Path(xml_path)
        if not p.is_file():
            return False, f"File not found: {p}", 0, 0, 0

        tree = ET.parse(p)
        root = tree.getroot()

        def local(tag: str) -> str:
            return tag.rsplit('}', 1)[-1]

        fv_changes = 0
        cat_changes = 0
        prop_changes = 0

        # Walk each parent and its direct children so we can see "next sibling"
        for parent in root.iter():
            children = list(parent)
            for i, elem in enumerate(children):
                name = local(elem.tag)

                if name == "ForceVisibility":
                    if (elem.text or "").strip() == "Hidden":
                        elem.text = "Unchanged"
                        fv_changes += 1
                    continue

                if name == "Category":
                    if (elem.text or "").strip() == "PDMS" and elem.get("Internal", "") == "":
                        # Change the Category
                        elem.text = "AVEVA"
                        elem.set("Internal", "lcldrvm_props")
                        cat_changes += 1

                        # Change the next sibling Property if it matches
                        if i + 1 < len(children):
                            prop = children[i + 1]
                            if local(prop.tag) == "Property" and prop.get("Internal", "") == "":
                                prop_text = (prop.text or "").strip()
                                if prop_text:
                                    prop.set("Internal", f"lcldrvm_prop_{prop_text.lower()}")
                                    prop_changes += 1

        tree.write(p, encoding="utf-8", xml_declaration=True)
        return True, None, fv_changes, cat_changes, prop_changes

    except ET.ParseError as e:
        return False, f"XML parse error: {e}", 0, 0, 0
    except OSError as e:
        return False, str(e), 0, 0, 0

def copy_as_output_status(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    overwrite: bool = False,
    make_dirs: bool = True
) -> Tuple[bool, Optional[str]]:
    src = Path(input_path)
    dst = Path(output_path)

    if not src.exists():
        return False, f"Input file not found: {src}"
    if not src.is_file():
        return False, f"Input path is not a file: {src}"

    try:
        if make_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not overwrite:
            return False, f"Output already exists: {dst}"
        shutil.copy2(src, dst)
        return True, None
    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except OSError as e:
        return False, str(e)

def build_output_xml_file_name(xml_path, suffix="_fixed"):
    r"""
    Insert `suffix` before the file extension and return the new path as str.
    Example: C:\temp\pythontest\abc.xml -> C:\temp\pythontest\abc_fixed.xml
    """
    p = Path(xml_path)
    if p.suffix:  # has an extension
        new_name = f"{p.stem}{suffix}{p.suffix}"
    else:         # no extension, just append suffix
        new_name = f"{p.name}{suffix}"
    return str(p.with_name(new_name))

def pick_xml_file(title="Select an XML file", initialdir=None):
    """Open a file dialog and return the selected XML file path or None."""
    root = tk.Tk()
    root.withdraw()  # hide the empty root window
    try:
        path = filedialog.askopenfilename(
            title=title,
            initialdir=initialdir or os.getcwd(),
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        return path or None
    finally:
        root.destroy()

if __name__ == '__main__':
    xml_path = pick_xml_file("Select an Appearance Profiler XML file", None)
    if xml_path is not None:
        output_xml_path = build_output_xml_file_name(xml_path)
        print(f"Input file: {xml_path}")
        ok, err = copy_as_output_status(xml_path, output_xml_path, overwrite=True)
        if not ok:
            print(f"Copy failed: {err}")
            raise SystemExit(1)
        print(f"Output file: {output_xml_path}")
        print("Patching...")
        ok, err, n_fv, n_cat, n_prop = patch_xml_in_place(output_xml_path)
        print("OK" if ok else f"Failed: {err}")
        print(f"ForceVisibility: {n_fv}, Category: {n_cat}, Property: {n_prop}")
        raise SystemExit(0 if ok else 2)
    else:
        print("No file selected.")

