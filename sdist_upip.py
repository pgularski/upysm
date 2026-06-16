#
# This module overrides distutils (also compatible with setuptools) "sdist"
# command to perform pre- and post-processing as required for MicroPython's
# upip package manager.
#
# Postprocessing steps:
#  * Removing metadata files not used by upip (this includes setup.py)
#  * Recompressing gzip archive with 4K dictionary size so it can be
#    installed even on low-heap targets.
#
import sys
import os
import zlib
import tarfile
import re
import io

from setuptools.command.sdist import sdist as _sdist


def gzip_4k(inf, fname):
    comp = zlib.compressobj(level=9, wbits=16 + 12)
    with open(fname + ".out", "wb") as outf:
        while 1:
            data = inf.read(1024)
            if not data:
                break
            outf.write(comp.compress(data))
        outf.write(comp.flush())
    os.rename(fname, fname + ".orig")
    os.rename(fname + ".out", fname)


FILTERS = [
    r"LICENSE$",
    r"PKG-INFO$",
    r".+\.egg-info/(PKG-INFO|requires\.txt)$",
    r"pysm/.+\.py$",
]


def should_include(fname):
    return any(re.match(pattern, fname) for pattern in FILTERS)


def filter_tar(name):
    outbuf = io.BytesIO()
    fin = tarfile.open(name, "r:gz")
    fout = tarfile.open(fileobj=outbuf, mode="w")
    for info in fin:
#        print(info)
        if not "/" in info.name:
            continue
        fname = info.name.split("/", 1)[1]

        if should_include(fname):
            print("including:", fname)
        else:
            print("excluding:", fname)
            continue

        farch = fin.extractfile(info)
        fout.addfile(info, farch)
    fout.close()
    fin.close()
    outbuf.seek(0)
    return outbuf


class sdist(_sdist):

    def run(self):
        r = super().run()

        assert len(self.archive_files) == 1
        print("filtering files and recompressing with 4K dictionary")
        outbuf = filter_tar(self.archive_files[0])
        gzip_4k(outbuf, self.archive_files[0])

        return r


# For testing only
if __name__ == "__main__":
    outbuf = filter_tar(sys.argv[1])
    gzip_4k(outbuf, sys.argv[1])
