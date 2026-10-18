"""Portable Python launcher. Run with a .bbmodel path, or without arguments to choose one."""
from pathlib import Path
import runpy
import sys


def main():
    root = Path(__file__).resolve().parent
    arguments = sys.argv[1:]
    if not arguments:
        try:
            import tkinter as tk
            from tkinter import filedialog
            window = tk.Tk()
            window.withdraw()
            try:
                selected = filedialog.askopenfilename(
                    title="Select Blockbench project / 选择 Blockbench 工程",
                    filetypes=[("Blockbench", "*.bbmodel")])
            finally:
                window.destroy()
        except Exception as error:
            raise SystemExit('File picker unavailable. Run: python Export-DollAnimation.py "my_scene.bbmodel"') from error
        if not selected:
            return
        arguments = [selected]
    tools = root / "tools"
    sys.path.insert(0, str(tools))
    sys.argv = [str(tools / "export_doll_pack.py"), *arguments]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
