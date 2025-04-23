# UHI

The purpose of this project is to automatically detect Urban Heat Islands (UHI) in cities using satellite imagery and open data from citizen weather stations.

## Installation

This project uses poetry to manage its dependencies, run `poetry install --no-root` to install all dependencies mentioned in pyproject.toml. After that, execute `eval $(poetry env activate)` to activate the virtual environment.

## Documentation

The docs on how to use this tool are hosted on https://ayubero.github.io/uhi.

To run the documentation in localhost, use `mkdocs serve`. To update repository docs, use `mkdocs gh-deploy`.