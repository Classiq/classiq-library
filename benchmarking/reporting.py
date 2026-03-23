from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
import pandas as pd
from importlib.metadata import PackageNotFoundError, version

_LATEX_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def get_classiq_version() -> str:
    try:
        return version("classiq")
    except PackageNotFoundError:
        try:
            import classiq

            return getattr(classiq, "__version__", "unknown")
        except Exception:
            return "unknown"


def write_version_file(root: str | Path = "../report") -> None:
    root = ensure_report_dirs(root)
    version_path = root / "sections" / "_version.tex"
    classiq_version = latex_escape(get_classiq_version())
    version_path.write_text(
        rf"\newcommand{{\classiqversion}}{{{classiq_version}}}" + "\n",
        encoding="utf-8",
    )


def latex_escape(s: str) -> str:
    return "".join(_LATEX_ESCAPE_MAP.get(ch, ch) for ch in str(s))


def ensure_report_dirs(root: str | Path = "../report") -> Path:
    root = Path(root)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "sections").mkdir(parents=True, exist_ok=True)
    (root / "build").mkdir(parents=True, exist_ok=True)
    return root


def df_to_latex_table(df: pd.DataFrame) -> str:
    """
    booktabs + siunitx S columns.
    Fixed numeric format: table-format=-1.4
    Missing values become '--'.
    """
    if df.empty:
        return "% (empty section)\n"

    cols = list(df.columns)
    first = cols[0]
    rest = cols[1:]

    colspec = "l " + " ".join(
        ["S[table-format=-1.4,table-text-alignment=center]" for _ in rest]
    )

    header_cells = [r"\textbf{" + latex_escape(first) + "}"]
    for c in rest:
        header_cells.append(r"{\textbf{" + latex_escape(c) + "}}")
    header_row = " & ".join(header_cells) + r" \\"

    lines = []
    for _, row in df.iterrows():
        row_cells = [latex_escape(row[first])]
        for c in rest:
            v = row[c]
            if pd.isna(v):
                row_cells.append(r"\text{--}")
            else:
                row_cells.append(str(v))
        lines.append(" & ".join(row_cells) + r" \\")

    table = []
    table.append(r"\begin{tabular}{" + colspec + r"}")
    table.append(r"\toprule")
    table.append(header_row)
    table.append(r"\midrule")
    table.extend(lines)
    table.append(r"\bottomrule")
    table.append(r"\end{tabular}")

    return "\n".join(table) + "\n"


def df_to_latex_table_mixed(df: pd.DataFrame, numeric_cols: set[str]) -> str:
    """
    Like df_to_latex_table, but supports multiple text columns.
    numeric_cols: columns rendered as siunitx S; others are 'l'.
    """
    if df is None or df.empty:
        return "% (empty section)\n"

    cols = list(df.columns)

    spec_parts = []
    for c in cols:
        if c in numeric_cols:
            spec_parts.append("S[table-format=-1.4,table-text-alignment=center]")
        else:
            spec_parts.append("l")
    colspec = " ".join(spec_parts)

    header_cells = [r"\textbf{" + latex_escape(c) + "}" for c in cols]
    header_row = " & ".join(header_cells) + r" \\"

    lines = []
    for _, row in df.iterrows():
        row_cells = []
        for c in cols:
            v = row[c]
            if pd.isna(v):
                row_cells.append(r"\text{--}" if c in numeric_cols else r"--")
            else:
                if c in numeric_cols:
                    row_cells.append(str(v))
                else:
                    row_cells.append(latex_escape(v))
        lines.append(" & ".join(row_cells) + r" \\")

    table = []
    table.append(r"\begin{tabular}{" + colspec + r"}")
    table.append(r"\toprule")
    table.append(header_row)
    table.append(r"\midrule")
    table.extend(lines)
    table.append(r"\bottomrule")
    table.append(r"\end{tabular}")

    return "\n".join(table) + "\n"


def add_section(
    name: str,
    title: str,
    df: pd.DataFrame,
    root: str | Path = "../report",
    level: str = "section",
    numeric_cols: set[str] | None = None,
) -> None:
    root = ensure_report_dirs(root)
    data_path = root / "data" / f"{name}.csv"
    section_path = root / "sections" / f"{name}.tex"

    if df is None or df.empty:
        if section_path.exists():
            section_path.unlink()
        if data_path.exists():
            data_path.unlink()
        return

    df.to_csv(data_path, index=False)

    heading = r"\subsection*{" if level == "subsection" else r"\section*{"

    tex = []
    tex.append("% Auto-generated. Do not edit by hand.")
    tex.append(heading + latex_escape(title) + r"}")

    if numeric_cols is None:
        tex.append(df_to_latex_table(df))
    else:
        tex.append(df_to_latex_table_mixed(df, numeric_cols=numeric_cols))

    tex.append("")
    section_path.write_text("\n".join(tex), encoding="utf-8")


def write_includes(root: str | Path = "../report") -> None:
    root = ensure_report_dirs(root)
    sections_dir = root / "sections"
    include_path = sections_dir / "_includes.tex"

    tex_files = sorted(
        p.name for p in sections_dir.glob("*.tex") if not p.name.startswith("_")
    )

    lines = ["% Auto-generated. Do not edit by hand."]
    for name in tex_files:
        lines.append(rf"\input{{sections/{name}}}")

    include_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_heading(
    name: str, title: str, root: str | Path = "../report", level: str = "section"
) -> None:
    root = ensure_report_dirs(root)
    section_path = root / "sections" / f"{name}.tex"

    heading = r"\section*{" if level == "section" else r"\subsection*{"

    tex = []
    tex.append("% Auto-generated. Do not edit by hand.")
    tex.append(heading + latex_escape(title) + r"}")
    tex.append("")
    section_path.write_text("\n".join(tex), encoding="utf-8")


def build_report(root: str | Path = "../report", force: bool = True) -> None:
    root = Path(root)
    ensure_report_dirs(root)
    write_version_file(root)

    cmd = [
        "latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-outdir=build",
    ]
    if force:
        cmd.append("-g")
    cmd.append("report.tex")

    try:
        subprocess.run(cmd, cwd=str(root), check=True, capture_output=True, text=True)

        built_pdf = root / "build" / "report.pdf"
        final_pdf = root / "report.pdf"

        if built_pdf.exists():
            shutil.copy2(built_pdf, final_pdf)

    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        raise
