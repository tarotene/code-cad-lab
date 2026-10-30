"""スライス。機種(`lab.printers`)が決めるスライサーに、書き出した 3MF を渡す。

Bambu Studio は `lab.slice_bambu`、PrusaSlicer は `lab.slice_prusa`。
ここは機種からスライサーを選ぶ入口。
"""

from __future__ import annotations

from pathlib import Path

from . import slice_bambu, slice_prusa
from .printers import BambuCompensation, Printer, PrusaCompensation
from .slice_common import PresetError, SliceResult, SlicerNotFoundError

__all__ = [
    "PresetError",
    "SliceResult",
    "SlicerNotFoundError",
    "expected_version",
    "installed_version",
    "slice_3mf",
    "slicer_label",
]


def slicer_label(printer: Printer) -> str:
    return {"bambu": "Bambu Studio", "prusa": "PrusaSlicer"}[printer.slicer]


def expected_version(printer: Printer) -> str:
    """その機種のスライサーで、プリセットと CLI を確かめた版。"""
    return {"bambu": slice_bambu.EXPECTED_VERSION, "prusa": slice_prusa.EXPECTED_VERSION}[
        printer.slicer
    ]


def installed_version(printer: Printer) -> str | None:
    if printer.slicer == "bambu":
        return slice_bambu.installed_version()
    return slice_prusa.installed_version()


def slice_3mf(
    input_3mf: Path,
    out_dir: Path,
    name: str,
    printer: Printer,
    *,
    printer_preset: str | None = None,
    process: str | None = None,
    filament: str | None = None,
) -> SliceResult:
    """機種のスライサーでスライスする。プリセット名は、指定が無ければ機種の既定を使う。"""
    presets = {
        "printer_preset": printer_preset or printer.printer_preset,
        "process": process or printer.process,
        "filament": filament or printer.filament,
    }
    compensation = printer.compensation
    if isinstance(compensation, BambuCompensation):
        return slice_bambu.slice_3mf(input_3mf, out_dir, name, **presets, compensation=compensation)
    assert isinstance(compensation, PrusaCompensation)
    return slice_prusa.slice_3mf(
        input_3mf,
        out_dir,
        name,
        **presets,
        compensation=compensation,
        center=(printer.bed[0] / 2, printer.bed[1] / 2),
    )
