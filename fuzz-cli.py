#!/usr/bin/env python

"""
fuzz-cli.py -- CLI fuzzer
  by Daniel Roberson @dmfroberson

TODO:
- map signal numbers to names
- be verbose when potential errors are encountered
- logging
- more fuzz strings
"""

import os
import shlex
import argparse
import subprocess32

import constants as fuzz_constants


def fuzz_test(arguments, timeout=0):
    """fuzz_test() -- fuzz tests a program with specified types of strings

    Args:
        arguments (list) - list of argments to run against the program. Expects
                           at least one variable in @@ format. See scripts
                           directory for examples.
        timeout (int)    - Timeout in seconds to allow a program to run. A value
                           of 0 disables the timeout, so the programs must exit
                           on their own or be closed by the user.

    Returns:
        Nothing.
    """
    # Determine what type of fuzz to be performed, based on variable type
    fuzz = []
    for arg in arguments:
        if arg[:1] == "@":
            count = 0
            for variable in fuzz_constants.FUZZ_VARS:
                count += 1
                if arg == variable[0]:
                    fuzz_strings = fuzz_constants.FUZZ_VARS[count - 1][1]
                    fuzz.append("@@")
                    continue

        # Add non-variable CLI argument
        fuzz.append(arg)

    # Perform the actual fuzzing
    for fuzz_string in fuzz_strings:
        current_fuzz = []
        for arg in arguments:
            if arg == "@@": # Replace this with string
                current_fuzz.append(fuzz_string[1])
            current_fuzz.append(arg)

            process = subprocess32.Popen(args=current_fuzz,
                                         shell=False,
                                         stdout=subprocess32.PIPE,
                                         stderr=subprocess32.PIPE)
        out = ""
        err = ""
        try:
            out, err = process.communicate(timeout=timeout)
        except subprocess32.TimeoutExpired:
            process.terminate()

        # Display summary of fuzzing run
        print " [*] exit:%sstdout:%sstderr:%stest:%s" % \
            (str(process.returncode).ljust(8),
             str(len(out)).ljust(8),
             str(len(err)).ljust(8),
             fuzz_string[0])


if __name__ == "__main__":
    print "[+] fuzz-cli.py -- by Daniel Roberson @dmfroberson\n"

    # Parse CLI arguments
    description = "example: ./fuzz-cli.py -t <timeout> <binary> <script>"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("binary",
                        nargs="+",
                        help="Path to binary to fuzz")
    parser.add_argument("script",
                        nargs="+",
                        help="Path to script file containing test cases")
    parser.add_argument("-t",
                        "--timeout",
                        default=1,
                        type=float,
                        required=False,
                        help="Timeout before killing program being fuzzed")
    args = parser.parse_args()

    # Make sure target exists and is executable
    progname = args.binary[0]
    if not os.path.isfile(progname) and not os.access(progname, os.X_OK):
        print "[-] Specified program \"%s\" is not executable." % progname
        print "[-] Exiting."
        exit(os.EX_USAGE)

    # Make sure script is readable
    testfile = args.script[0]
    if not os.access(testfile, os.R_OK):
        print "[-] Specified script \"%s\" is not readable." % testfile
        print "[-] Exiting."
        exit(os.EX_USAGE)

    print "[+] Fuzzing %s with tests defined in %s\n" % (progname, testfile)

    linecount = 0
    for line in open(testfile, "r"):
        linecount += 1
        line = line.rstrip()

        # Skip blank lines
        if len(line) == 0:
            continue

        # Skip comments
        if line[:1] == "#":
            continue

        # Make sure only one @@ per line
        varcount = 0
        for variable in fuzz_constants.FUZZ_VARS:
            varcount += line.count(variable[0])
        if varcount > 1:
            print "[-] Too many variables on line %d of %s -- Skipping." % \
                (linecount, testfile)
            print "    %s\n" % line
            continue

        # Create argv[] for Popen()
        fuzz_args = shlex.split(line)
        fuzz_args.insert(0, progname)

        # Finally, fuzz the target
        print "[+] %s" % fuzz_args
        fuzz_test(fuzz_args, timeout=args.timeout)
        print

    # All done.
    print "[+] Pledge your allegiance to Shadaloo and I will let you live!"
    print "[+] Done"
