import argparse
import os
from typing import Iterable

import yaml


class SafeDumperNoAliases(yaml.SafeDumper):
    """
    A dumper that will never emit aliases.
    """

    def ignore_aliases(self, data):
        return True


class BaseConfig:
    """Implements abstract config, that can read params from file and dump data to file"""

    def __init__(self):
        self._file_path = None

    def __repr__(self):
        return f"{self.__class__.__name__}:\n---\n{yaml.dump(self.get_public_vars())}---\n"

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, file_path):
        self._file_path = file_path

    def get_public_vars(self) -> dict:
        variables = {}
        for dict_ in [self.__class__.__dict__, self.__dict__]:
            for k, v in dict_.items():
                # callable -> function, instance of 'type' -> class
                if k.startswith("_") or callable(v) or isinstance(v, (type, staticmethod, classmethod, property)):
                    continue
                variables[k] = v
        return variables

    def set_public_vars(self, data_dict):
        for k, v in data_dict.items():
            setattr(self, k, v)

    def _read_from_file(self) -> dict:
        file_path = self._file_path
        if file_path is None:
            raise Exception("Failed to read: file_path not specified!")

        _, ext = os.path.splitext(file_path)
        assert ext == ".yaml"

        with open(file_path, "r") as inf:
            data_dict = yaml.safe_load(inf)
        return data_dict

    def load_from_file(self):
        data_dict = self._read_from_file()
        self.set_public_vars(data_dict)

    def save_to_file(self):
        file_path = self._file_path
        if file_path is None:
            raise Exception("Failed to save: file_path not specified!")

        _, ext = os.path.splitext(file_path)
        assert ext == ".yaml"

        dirname = os.path.dirname(os.path.abspath(file_path))
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        public_vars = self.get_public_vars()
        with open(file_path, "w") as outf:
            yaml.dump(public_vars, outf, Dumper=SafeDumperNoAliases)


def add_arguments_to_parser(parser: argparse.ArgumentParser, config: BaseConfig, exclude_params: Iterable = ()):
    for key, value in config.get_public_vars().items():
        if key not in exclude_params:
            if type(value) in [int, str, float]:
                parser.add_argument(
                    f"--{key.replace('_', '-')}",
                    type=type(value),
                )
            elif type(value) == bool:
                # argparse is really bad at handling bools.
                # So just use default value False, so that any non-empty string will evaluate to True
                assert value is False, f"Default value for {key} is True. This is not supported"
                parser.add_argument(
                    f"--{key.replace('_', '-')}",
                    type=bool,
                )
            elif type(value) == list:
                parser.add_argument(
                    f"--{key.replace('_', '-')}",
                    type=type(value[0]),
                    nargs="*",
                )
            else:
                raise NotImplementedError(f"Type {type(value)} is not supported for config variable {key}")
