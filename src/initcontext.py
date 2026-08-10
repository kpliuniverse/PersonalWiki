
import pathlib

from attrs import define


@define(frozen=True)
class InitContext:
    path_to_pwi_file: pathlib.Path