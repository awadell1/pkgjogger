from ast import parse
import logging
import argparse
import subprocess
import toml
import yaml
from os import environ
from shutil import rmtree
from uuid import uuid4
from git import Repo
from pathlib import Path

logging.basicConfig()


def load_config(pkg_dir):
    pkg_name = toml.load(Path(pkg_dir, "Project.toml"))["name"]
    with open(Path.home().joinpath(".pkgjogger", "config.yaml"), "r") as fid:
        config = yaml.load(fid)

    return config[pkg_name]


def clone_pkg(url, rev):
    # Clone package to a local directory
    pkg_dir = Path.home().joinpath(".pkgjogger", str(uuid4()))
    repo = Repo.clone_from(url, pkg_dir)

    # Locate ref
    try:
        commit = repo.rev_parse(rev)
        rev_label = rev
    except:
        commit = repo.rev_parse("origin/" + rev)
        rev_label = f"{rev}@{str(commit)[0:8]}"

    repo.git.checkout(commit)

    pkg_name = toml.load(Path(pkg_dir, "Project.toml"))["name"]
    logging.info(
        "Cloned `%s` from %s to %s and checked out `%s`",
        pkg_name,
        url,
        pkg_dir,
        rev_label,
    )
    return repo, pkg_dir


def setup_pkg(pkg_dir):
    # Get Environment
    env = environ
    config = load_config(pkg_dir)
    if "env" in config:
        env.update(config["env"])

    # Setup pkg
    logging.info("Running `make` to setup package for benchmarking")
    out = subprocess.run(
        ["make", "-j", "install_benchmark", "test/incepts-test-data/"],
        cwd=pkg_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return out


def slurm_script(pkg_dir):
    script = [
        "#!/bin/bash",
        "#SBATCH -A venkvis",
        "#SBATCH -J incepts_benchmark",
        "#SBATCH -p cpu,gpu,highmem",
        "#SBATCH --nodes 1",
        "#SBATCH --ntasks 1",
        "#SBATCH --cpus-per-task 1",
        "#SBATCH --mem-per-cpu=2000",
        "#SBATCH -o slurm.log",
        "make benchmark",
    ]
    with open(Path(pkg_dir, "submit.sh"), "w") as fid:
        fid.writelines(l + "\n" for l in script)

    ignores = ["submit.sh", "slurm.log", "*.json"]
    with open(Path(pkg_dir, ".git", "info", "exclude"), "a+") as fid:
        fid.writelines(l + "\n" for l in ignores)

    return Path(pkg_dir, "submit.sh")


def run_benchmark(pkg_dir):
    script_path = slurm_script(pkg_dir)
    logging.info("Submitting %s to SLURM", script_path)
    subprocess.run(["sbatch", "--wait", str(script_path)], cwd=pkg_dir, check=True)
    logging.info("Finished benchmarking on SLURM cluster")


def upload_benchmark(repo, pkg_dir):
    logging.info("Uploading results to Google Drive")
    pkg_name = toml.load(Path(pkg_dir, "Project.toml"))["name"]
    subprocess.run(
        [
            "rclone",
            "copyto",
            str(Path(pkg_dir, "benchmark/benchmark.json")),
            "gdrive-cmu:%s".format(
                Path("benchmark", pkg_name, str(repo.head.commit) + ".json")
            ),
        ]
    )
    subprocess.run(
        [
            "rclone",
            "copyto",
            str(Path(pkg_dir, "slurm.log")),
            "gdrive-cmu:%s".format(
                Path("benchmark", pkg_name, str(repo.head.commit) + ".log")
            ),
        ]
    )


def benchmark_commit(url, rev):
    # Clone the package
    repo, pkg_dir = clone_pkg(url, rev)
    config = load_config(pkg_dir)

    out = setup_pkg(pkg_dir)
    logging.info(out.stdout)

    # Submit to cluster and wait
    run_benchmark(pkg_dir)

    # Upload results
    upload_benchmark(repo, pkg_dir)

    # Cleanup
    # rmtree(pkg_dir, ignore_errors=True)


def cli():
    parser = argparse.ArgumentParser(
        "pkg-jogger", description="Tool for benchamarking packages on Arjuna"
    )
    parser.add_argument("repo", type=str, help="Git Repo to Clone for benchmarking")
    parser.add_argument("rev", type=str, help="Revision to benchmark")
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose, stacks up to 3",
    )
    args = parser.parse_args()

    # Set Logging level
    logging.getLogger().setLevel(max(logging.DEBUG, logging.WARN - 10 * args.verbose))

    # Benchmark package
    benchmark_commit(args.repo, args.rev)
