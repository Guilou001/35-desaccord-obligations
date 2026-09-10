"""Présentation des résultats, modèles de texte contrôlés et source PDF unique."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

BLUE = "#17659A"
ORANGE = "#C76D28"
TEAL = "#258575"
GREY = "#626C78"
RED = "#A64545"


def style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#B9C2CC",
            "axes.labelcolor": "#303B46",
            "xtick.color": "#46515D",
            "ytick.color": "#46515D",
            "grid.color": "#E5E9ED",
            "grid.linewidth": 0.7,
            "legend.frameon": False,
            "lines.linewidth": 2,
            "figure.dpi": 140,
            "savefig.dpi": 180,
        }
    )


def polish(ax, percent: bool = False) -> None:
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    if percent:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))


def save(fig, name: str) -> None:
    dest = Path("results/figures")
    dest.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg", "pdf"]:
        fig.savefig(dest / f"{name}.{suffix}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def number(value: float, decimals: int = 2, percent: bool = False, signed: bool = False) -> str:
    result = format(value * (100 if percent else 1), ("+" if signed else "") + f",.{decimals}f")
    return result.replace(",", " ").replace(".", ",")


def table(headers: list[str], rows: list[list]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def templates(values: dict) -> None:
    """Refuse une valeur manquante plutôt que de publier un champ de modèle."""
    for source, dest in [("readme.md", "README.md"), ("article.md", "ARTICLE.md")]:
        text = Path("docs/templates", source).read_text()

        def replace(match):
            key = match.group(1)
            if key not in values:
                raise KeyError(f"Valeur de publication absente {key}")
            return str(values[key])

        text = re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", replace, text)
        if "{{" in text:
            raise ValueError("Champ de modèle non résolu")
        Path(dest).write_text(text)
    Path("results/tables/publication_values.json").write_text(
        json.dumps(values, indent=2, ensure_ascii=False) + "\n"
    )


def compile_article(repo: str) -> None:
    """Compose l'article Markdown en Typst, avec correspondance explicite de ses équations."""
    import typst
    from gvf.markdown import chaine, convertir, ligne
    from gvf.rapport import GABARIT

    text = Path("ARTICLE.md").read_text().replace("\nGuillaume Vaudescal\n", "\n")
    equations = (
        json.loads(Path("docs/equations.json").read_text()) if Path("docs/equations.json").exists() else {}
    )
    substitutions = {}

    def equation(match):
        latex = match.group(1).strip()
        if latex not in equations:
            raise KeyError(f"Équation sans traduction contrôlée {latex}")
        tag = "FORMULE" + str(len(substitutions)) + "FIN"
        substitutions[tag] = "$ " + equations[latex] + " $"
        return tag

    text = re.sub(r"\$\$\s*(.*?)\s*\$\$", equation, text, flags=re.S)
    text = re.sub(r"(results/figures/[^)]+)\.png", r"\1.svg", text)
    document = convertir(text, racine="..")
    body = document.corps
    for tag, math in substitutions.items():
        body = body.replace(tag, math)
    source = GABARIT.format(
        titre=chaine(document.titre),
        titre_affiche=ligne(document.titre),
        pied="Document de recherche · Version 1.1",
        date="10 septembre 2026",
        depot=f"https://github.com/Guilou001/{repo}",
        depot_court=f"Guilou001/{repo}",
        corps=body,
    )
    source = source.replace(
        'font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt',
        'font: ("Libertinus Serif", "Times New Roman", "DejaVu Serif"), size: 10.5pt',
    )
    source = source.replace(
        "#show table: it => block(above:", "#show table: it => block(breakable: false, above:"
    )
    source = source.replace(
        'text(size: 18pt, weight: "bold")', 'text(size: 18pt, weight: "bold", hyphenate: false)'
    )
    source = "#set figure.caption(separator: [. ])\n" + source
    p = Path("rapport")
    p.mkdir(exist_ok=True)
    (p / "rapport.typ").write_text(source)
    (p / "rapport.pdf").write_bytes(typst.compile(p / "rapport.typ", root=Path.cwd()))
    (p / "source_manifest.json").write_text(
        json.dumps(
            {
                "source": "ARTICLE.md",
                "sha256": hashlib.sha256(Path("ARTICLE.md").read_bytes()).hexdigest(),
                "equations": "docs/equations.json",
            },
            indent=2,
        )
        + "\n"
    )
