import argparse
import logging
import inquirer
from tabulate import tabulate
from sys import argv

from .pkg import Pkg


def status(args):
    pkgs = Pkg.discover()
    table = [pkg.status() for pkg in pkgs]
    print(tabulate(table, headers="keys", tablefmt="github"))


def add(args):
    pkg = Pkg(args.url, args.rev)
    logging.info("Added %s (%s) at %s", pkg.url, pkg.revision, pkg.path)
    pkg.clone()

def rm(args):
    pkgs = Pkg.discover()
    if not pkgs:
        return

    if args.uuid is not None:
        rm_uuid = [args.uuid]
    else:
        get_uuids = inquirer.Checkbox(
            "uuids",
            message="Which Joggers should be removed?",
            choices=[pkg.uuid for pkg in pkgs],
        )
        rm_uuid = inquirer.prompt([get_uuids])["uuids"]

    # Remove uuids
    pkg_uuid = {pkg.uuid: pkg for pkg in pkgs}
    for uuid in rm_uuid:
        pkg_uuid[uuid].remove()


def cli(cli_args=argv[1:]):
    parser = argparse.ArgumentParser(
        prog="pkg-jogger",
        description="Take your packages out for a jog on SLURM",
    )
    parser.set_defaults(func=lambda x: parser.print_usage())
    subp = parser.add_subparsers(help="SubCommands")

    # Add Package
    addp = subp.add_parser(name="add")
    addp.add_argument("url", type=str, help="URL of the Git Repo to jog")
    addp.add_argument("rev", type=str, help="Revision of the Git repo to jog")
    addp.set_defaults(func=add)

    # Remove Packages
    rmp = subp.add_parser(name="rm", help="Remove one or more Joggers")
    rmp.add_argument(
        "--uuid", type=str, default=None, help="Remove the Jogger with UUID"
    )
    rmp.set_defaults(func=rm)

    # Getting Status
    st = subp.add_parser(name="status")
    st.add_argument(
        "--uuid", type=str, default=None, help="Get Status of Jogger with UUID"
    )
    st.set_defaults(func=status)

    # Parse arguments and run subcommand
    args = parser.parse_args(cli_args)
    args.func(args)
