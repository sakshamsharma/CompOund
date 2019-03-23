import argparse
import json
import os
import shlex
import sys

from collections import OrderedDict
from os.path import dirname, abspath

VERSION=0.1
HEADER_EXTENSIONS=set([".hh", ".hpp", ".h"])
COMP_UNIT_EXTENSIONS=set([".cpp", ".c", ".cc", ".cxx", ".x.cpp"])

# Source: https://stackoverflow.com/questions/21498939/
def commonpath(l):
    cp = []
    ls = [p.split('/') for p in l]
    ml = min( len(p) for p in ls )
    for i in range(ml):
        s = set( p[i] for p in ls )
        if len(s) != 1:
            break
        cp.append(s.pop())
    return '/'.join(cp)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Print CLI version and exit.",
                        default=False, action="store_true")
    parser.add_argument("-f", "--files", help="File(s) for which the compile "
                        + " commands have to be printed", nargs="+",
                        required=True)
    parser.add_argument("--root", help="Project root containing "
                        + "compile_commands.json. Can be inferred.")
    parser.add_argument("--compdb", help="Path to compile_commands.json")
    parser.add_argument("--sanitize", help="Whether to remove unwanted "
                        "options from the compilation command.",
                        default=False, action="store_true")
    return parser.parse_args()

def prepare_lookup_cdb(cdb):
    # Consumes a raw representation of the JSON from the file, and
    # returns a lookup table from file name to directory / command.
    new_cdb = {}
    for entry in cdb:
        new_cdb[entry["file"]] = (entry["directory"], entry["command"])
    return new_cdb

# Borrowed partially from:
# https://github.com/Sarcasm/compdb/blob/master/compdb/complementer/headerdb.py
def sanitize_compile_options(compile_command):
    # TODO(saksham): Make the sanitized flags configurable.
    adjusted = []
    i = 0
    arguments = shlex.split(compile_command)
    while i < len(arguments):
        # end of options, skip all positional arguments (source files)
        arg = arguments[i]
        if arg == "--":
            break
        # strip -c
        if arg == "-c" or arg == "-S":
            i += 1
            continue
        # strip -o <output-file> and -o<output-file>
        if arg.startswith("-o"):
            if arg == "-o":
                i += 2
            else:
                i += 1
            continue
        adjusted.append(arg)
        i += 1
    return " ".join(adjusted)

def infer_command(f, cdb):
    # Contains the primary logic of inferring / deducing the compilation
    # command for a file whose compilation command is not contained in the
    # compile_commands.json.
    froot = dirname(f)
    fbase = os.path.basename(f)
    fname, fext = os.path.splitext(fbase)

    if fext in HEADER_EXTENSIONS:
        for new_ext in COMP_UNIT_EXTENSIONS:
            new_base = fname + new_ext
            accompanying_cpp = os.path.join(froot, new_base)
            if os.path.isfile(accompanying_cpp):
                if accompanying_cpp in cdb:
                    (directory, command) = cdb[accompanying_cpp]
                    new_comm = command.replace(new_base, fbase)
                    return (directory, new_comm)
    # TODO(saksham): Implement inference logic where files in this
    # folder, and folders in parent directories are ranked on
    # similarity with this file, and their common flags are inferred.
    return ("", "")

def run():
    args = parse_args()

    if args.version is True:
        print(VERSION)
        sys.exit(0)

    for f in args.files:
        if not os.path.exists(f):
            raise ValueError("File does not exist: " + f)
    files = [abspath(f) for f in args.files]

    if args.compdb is not None:
        root = dirname(args.compdb)
    elif args.root is not None:
        root = args.root
        if not os.path.exists(root):
            raise ValueError("Root directory does not exist: " + root)
    else:
        croot = dirname(abspath(commonpath([f for f in files])))
        root = None
        while croot is not "/":
            if os.path.isfile(os.path.join(croot, "compile_commands.json")):
                root = croot
                break
            croot = dirname(croot)
        if root is None:
            raise ValueError("Files provided with no common root containing "
                             + "compile_commands.json")

    ccj = os.path.join(root, "compile_commands.json")
    assert(os.path.exists(ccj))

    with open(ccj) as f:
        cdb = json.load(f)

    file_command_lookup = {f: ("", "") for f in files}
    done = 0
    for entry in cdb:
        if entry["file"] in file_command_lookup:
            file_command_lookup[entry["file"]] = (
                entry["directory"], entry["command"])
            done += 1
        if done == len(files):
            break

    if done != len(files):
        lookup_cdb = prepare_lookup_cdb(cdb)
        for f, (directory, command) in file_command_lookup.items():
            if len(directory) != 0 and len(command) != 0:
                continue
            file_command_lookup[f] = infer_command(f, lookup_cdb)

    result = OrderedDict()
    for f in files:
        entry = file_command_lookup[f]
        if args.sanitize:
            command = sanitize_compile_options(entry[1])
        else:
            command = entry[1]
        result[f] = {"command": command, "directory": entry[0]}

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run()
