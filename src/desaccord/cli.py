"""Commandes du laboratoire obligataire."""

import typer

from . import dataset, experiment

app = typer.Typer(no_args_is_help=True)
app.command()(dataset.fetch)
app.command()(experiment.run)


@app.command()
def report() -> None:
    from .publication import publish

    publish()


@app.command()
def verify() -> None:
    from .verification import verify as execute

    execute()
