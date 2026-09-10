"""Commandes du laboratoire obligataire."""

import typer

from . import dataset, experiment

app = typer.Typer(no_args_is_help=True)
app.command()(dataset.fetch)
app.command()(experiment.run)


@app.command()
def selection() -> None:
    """Recalcule l'extension sur les intervalles et les filtres."""
    from .selection_extension import run

    run()


@app.command()
def report() -> None:
    from .publication import publish

    publish()


@app.command()
def verify() -> None:
    from .verification import verify as execute

    execute()
    from .selection_verification import verify as extension_verify

    extension_verify()
