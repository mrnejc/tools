#!/usr/bin/env python
from __future__ import print_function

import os
import os.path
import re
import sys
import time
from optparse import OptionParser

"""
A simple program for renaming files based on their creation/modification timestamp.

Me and my GF take a lot of pictures with both our Android phones and DSLR camera.
When we get home I dump all files in same folder but I like to have them sorted by time the photo
was taken. Android camera app names the files in format YYYYMMDD_HHmmss but all DSLRs have this
stupid IMG_xxxx.JPG naming scheme - I use this app to rename DSLR photos to play nicely with other
files.

Since we usually move between timezones there is also a time difference on those timestamps so the
ability to shift time on timestamp is also available.
"""
def printerr(*message):
    """just an utility method so I don't do file=sys.stderr constantly

    :rtype : None
    """
    print(*message, file=sys.stderr)


def get_file_timestamp(file_name, mtime=False):
    """get file creation or modification time

    :param mtime: return modification time instead of creation time
    :rtype: int
    :returns: file creation or modification time in seconds since epoch, or None if error occurs
    """
    if not os.path.exists(file_name):
        printerr("ERROR", file_name, "does not exist")
        return None
    if not os.path.isfile(file_name):
        printerr("ERROR", file_name, "is not a file")
        return None
    if mtime:
        t = os.path.getmtime(file_name)
    else:
        t = os.path.getctime(file_name)
    return t


def rename_with_timestamp(file_to_rename, use_file_time, is_dry_run=False,
                          use_file_mask="%Y%m%d_%H%M%S"):
    """rename file with timestamp prefix

    :param file_to_rename: file to be renamed
    :param use_file_time: use provided time (seconds since epoch) to construct timestamp prefix
    :rtype: bool
    :returns: True if file was successfully renamed, False if any error occurred
    """
    file_split = os.path.split(file_to_rename)
    assert type(use_file_time) == int
    f_new = time.strftime(use_file_mask, time.localtime(use_file_time)) + "_" + file_split[1]
    print("RENAME", file_to_rename, f_new)
    if is_dry_run:
        return True
    else:
        # noinspection PyBroadException
        try:
            os.rename(file_to_rename, os.path.join(file_split[0], f_new))
            return True
        except:
            printerr("Error renaming", file_to_rename)
            return False


if __name__ == "__main__":
    # read command line optiongs
    usage = "usage: %prog [options] FILE_1 [FILE_2 ... FILE_N]"
    parser = OptionParser(usage=usage)
    # just a simple add or subtract time option
    parser.add_option("-t", "--time-diff", dest="time_diff",
                      help="Add or subtract arbitrary time from file timestamp. "
                           "Format can be a positive or negative number of seconds or "
                           "formatted as [+-][HH:]MM:SS")
    parser.add_option("-n", "--dryrun", dest="dryrun", default=False,
                      action="store_true",
                      help="don't do anything, just write what it would do")
    parser.add_option("-m", "--mtime", dest="use_mtime",
                      action="store_true", default=False,
                      help="use file modification time instead of file creation time")

    (options, args) = parser.parse_args()
    # if time_diff was provided convert it to number of seconds
    if options.time_diff:
        # noinspection PyBroadException
        try:
            tdp = options.time_diff
            f = 1
            # see if there is a sign at the beginning of string
            if re.compile("[+-].*").match(tdp):
                if tdp[0] == '-':
                    f = -1
                tdp = tdp[1:]
            if tdp.isdigit():
                # have simple format - just number
                time_delta = f * int(tdp)
            else:
                # must be in HH:MM:SS format
                tdp = tdp.split(":")
                if len(tdp) > 3 or len(tdp) == 1:
                    raise Exception("expecting time format of [HH:]MM:SS")
                time_delta = int(tdp[-1])
                if len(tdp) > 2:
                    time_delta += int(tdp[-2])*60
                if len(tdp) == 3:
                    time_delta += int(tdp[-3]) * 3600
                time_delta *= f
        except Exception, e:
            printerr("error parsing time format", options.time_diff)
            sys.exit(100)
    else:
        time_delta = 0

    # do the work
    for file_name in args:
        # get filename timestamp
        try:
            file_time = get_file_timestamp(file_name, mtime=options.use_mtime) + time_delta
            if file_time:
                rename_with_timestamp(file_name, file_time, is_dry_run=options.dryrun)
        except Exception, e:
            printerr(e)
