# CompOund
A compile_commands.json parser script which can infer missing compilation commands.

**NOTE**: This project is a work in progress.

CompOund is a python script which can be used as a simple and clean
way to access compilation commands from `compile_commands.json` files
without having to reimplement the wheel in every tool.

It is possible that in-tool implementations of this logic may be faster
or better integrated, which is fine. The goal is to ease writing inference
logic for missing `compile_commands.json` entries, and to allow tools to
have a reference implementation.

In addition, it is possible to add rewrites of this logic in other languages
like C, elisp, even VimL perhaps. It might help editor plugin writers.

## CLI

Current CLI looks like the following, and should be self-explanatory.
```
$ python compound.py --help
usage: compound.py [-h] [--version] -f FILES [FILES ...] [--root ROOT]
                   [--compdb COMPDB] [--sanitize]

optional arguments:
  -h, --help            show this help message and exit
  --version             Print CLI version and exit.
  -f FILES [FILES ...], --files FILES [FILES ...]
                        File(s) for which the compile commands have to be
                        printed
  --root ROOT           Project root containing compile_commands.json. Can be
                        inferred.
  --compdb COMPDB       Path to compile_commands.json
  --sanitize            Whether to remove unwanted options from the
                        compilation command.
```

The output is a JSON-formatted dictionary of the form:
```
{
    "<filename>": {
        "command": "<command>",
        "directory": "<directory>"
    }
}
```
