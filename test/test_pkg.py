from pathlib import Path
from pkgjogger.pkg import Pkg


def test_construct():
    # Create a package
    pkg = Pkg("git@github.com:awadell1/pkgjogger.git", "main")
    assert isinstance(pkg.path, Path)
    assert pkg.path.is_dir()

    # Try to discover the package
    pkgs = Pkg.discover()
    assert pkg in pkgs

    # Cleanup
    path = pkg.path
    pkg.remove()
    assert path.exists() == False
