
import pathlib

from attrs import define


@define(frozen=True)
class InitContext:
    wiki: pathlib.Path