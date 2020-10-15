import runpy
import sys

import click
from prefect.environments.execution.base import Environment
from prefect.environments.storage.base import Storage


@click.group()
@click.version_option()
def main():
    pass


@click.command()
@click.argument("pipeline", type=click.Path(exists=True))
def check(pipeline):
    """
    Check that the pipeline definition is valid. This does not run the pipeline.
    """
    # result returns the namespace of the module as a dict of {name: value}.
    return_code = 0
    result = runpy.run_path(pipeline)
    # The toplevel of the recipe must have two instances
    # 1. pipeline: required by pangeo-forge for metadata.
    # 2. flow: required by Prefect for flow execution.
    missing = [key for key in ["pipeline", "flow"] if key not in result]

    if missing:
        click.echo(f"missing {missing}", err=True)
        return_code = 1
    pipe = result["pipeline"]

    if not isinstance(pipe.flow.environment, Environment):
        click.echo(f"Incorrect flow.environment {type(pipe.flow.environment)}", err=True)
        return_code = 1
    if not isinstance(pipe.flow.storage, Storage):
        click.echo(f"Incorrect flow.storage {type(pipe.flow.storage)}", err=True)
        return_code = 1
    pipe.flow.validate()
    sys.exit(return_code)


@click.command()
@click.argument("pipeline", type=click.Path(exists=True))
def register(pipeline):
    env = runpy.run_path(pipeline)
    flow = env["flow"]
    # XXX: Setting after the fact doesn't seem to work.
    # We need users to specify it when creating the `Flow`
    # pipe = env["pipeline"]
    # flow.environment = pipe.environment
    # flow.storage = pipe.storage
    flow.register(project_name="pangeo-forge", labels=["gcp"])


main.add_command(check)
main.add_command(register)


if __name__ == "__main__":
    main()
