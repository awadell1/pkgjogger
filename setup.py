from setuptools import setup, find_packages

setup(
    name="pkgjogger",
    description="Benchmark Julia Pkgs on Arjuna",
    version="0.0.1",
    author="Alexius Wadell",
    author_email="awadell@gmail.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "gitpython",
        "toml",
        "pyyaml",
        "tabulate",
        "inquirer",
    ],
    entry_points={"console_scripts": ["pkg-jogger=pkgjogger.cli:cli"]},
)
