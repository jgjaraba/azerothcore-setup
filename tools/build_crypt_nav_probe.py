#!/usr/bin/env python3
"""Build only the offline probe against already-built native libraries."""
from pathlib import Path
import shlex
import subprocess

root = Path(__file__).resolve().parent.parent
core = Path('/home/dev/azerothcore')
build = core / 'build'
out = root / 'work/crypt-nav-probe/bin'
out.mkdir(parents=True, exist_ok=True)
flags = (build / 'src/common/CMakeFiles/common.dir/flags.make').read_text()
includes = next(line.split('=', 1)[1] for line in flags.splitlines() if line.startswith('CXX_INCLUDES ='))
link = shlex.split((build / 'src/tools/CMakeFiles/mmaps_generator.dir/link.txt').read_text())
libs = link[link.index('../common/libcommon.a'):]
libs = [str((build/'src/tools'/arg).resolve()) if arg.endswith('.a') and not Path(arg).is_absolute()
        else arg for arg in libs]
command = ['clang++', '-std=c++20', '-O2', '-Wall', '-Wextra', '-DENABLE_VMAP_CHECKS',
           *shlex.split(includes), str(root/'tools/crypt_nav_probe.cpp'), '-o',
           str(out/'crypt_nav_probe'), *libs]
subprocess.run(command, check=True)
print(out/'crypt_nav_probe')
