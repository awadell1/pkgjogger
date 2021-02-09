import logging
import yaml
import subprocess
from shutil import rmtree
from uuid import uuid4
from pathlib import Path

from git import Repo

from yaml.loader import Loader

class Pkg:
    track_pack = Path.home().joinpath(".pkgjogger")
    config_filename = "pkg-config.yaml"

    def __init__(self, url, revision, uuid=uuid4().hex) -> None:
        self.uuid: str = uuid
        self.url = url
        self.revision = revision
        self.commit = None
        self.state("init")

        # Write config file
        self.path.mkdir(parents=True, exist_ok=True)
        config_path = self.path.joinpath("pkg-config.yaml")
        with open(config_path, "a+") as fid:
            yaml.dump(self, fid, Dumper=yaml.Dumper)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pkg):
            return False
        return self.uuid == other.uuid

    def state(self, state):
        self.state = state
        self.path.mkdir(parents=True, exist_ok=True)
        config_path = self.path.joinpath("pkg-config.yaml")
        with open(config_path, "a+") as fid:
            yaml.dump(self, fid, Dumper=yaml.Dumper)

    @property
    def path(self):
        return Pkg.track_pack.joinpath(self.uuid)

    def _def_get_commit(self):
        try:
            # Parse Revison directly
            commit = repo.rev_parse(self.revision)
        except:
            # Fall back to treating revision as remote branch
            commit = repo.rev_parse("origin/" + self.revision)

        return commit

    def remove(self):
        logging.info("Removing %s", self)
        rmtree(self.path)

    def status(self):
        info = {
            "uuid": self.uuid,
            "repo": self.url,
            "revision": self.revision,
            "state": self.state,
        }
        return info

    @classmethod
    def discover(cls):
        pkgs = []
        for item in cls.track_pack.iterdir():
            if item.is_dir():
                pkgs.append(Pkg.from_path(item))

        return pkgs

    @classmethod
    def from_path(cls, path: Path):
        config_file = path.joinpath("pkg-config.yaml")
        with open(config_file, "r") as fid:
            pkg = yaml.load(fid, Loader=yaml.Loader)
        return pkg

    def clone(self):
        pkg_dir = self.path.joinpath("pkg-dir")
        repo = Repo.clone_from(self.url, pkg_dir)

        # Check out revision
        try:
            commit = repo.rev_parse(self.revision)
        except:
            commit = repo.rev_parse("origin/" + self.revision)

        repo.git.checkout(commit)
        self.commit = str(commit)
        self.state("cloned")

    def setup(self):
        assert self.state == "cloned"
        subprocess.run(
            ["make", "install_benchmark"], cwd=self.path.joinpath("pkg-dir"), check=True
        )
        self.state("ready")
