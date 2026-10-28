"""MPQ extraction I/O regressions; builds local StormLib CLI in work scratch.

Run: TMPDIR="$PWD/work/tmp" python3 -m unittest tools.test_mpq_io -v
"""
import errno
import hashlib
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MpqIOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="mpq-io-", dir=ROOT / "work")
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.work = Path(cls.scratch.name)
        cls.env = dict(os.environ, TMPDIR=str(ROOT / "work/tmp"))
        cls.cli = cls.work / "mpq"
        compile_args = ["g++", "-O2", "-std=c++17", "-Wall", "-Wextra",
                        "-I", str(ROOT / "tools/stormlib/include"),
                        str(ROOT / "tools/mpq.cpp")]
        libs = [str(ROOT / "tools/stormlib/lib/libstorm.a"),
                "-lz", "-lbz2", "-lpthread", "-ldl"]
        subprocess.run(compile_args + libs + ["-o", str(cls.cli)],
                       env=cls.env, check=True)
        # Exercise otherwise impractical corrupt/oversized member API responses
        # through the real CLI and archive, without changing production code.
        wrapper = cls.work / "faults.cpp"
        wrapper.write_text(r'''
#include <StormLib.h>
#include <cstdlib>
#include <cstring>
#include <cerrno>
extern "C" DWORD __real_SFileGetFileSize(HANDLE, LPDWORD);
extern "C" bool __real_SFileReadFile(HANDLE, void*, DWORD, LPDWORD, LPOVERLAPPED);
extern "C" bool __real_SFileOpenFileEx(HANDLE, const char*, DWORD, HANDLE*);
extern "C" bool __wrap_SFileOpenFileEx(HANDLE a, const char* name, DWORD scope, HANDLE* f) {
    const char* mode = std::getenv("MPQ_IO_FAULT");
    if (mode && std::strcmp(mode, "open") == 0 && std::strcmp(name, "large.bin") == 0) {
        SErrSetLastError(EIO);
        return false;
    }
    return __real_SFileOpenFileEx(a, name, scope, f);
}
extern "C" DWORD __wrap_SFileGetFileSize(HANDLE f, LPDWORD high) {
    DWORD low = __real_SFileGetFileSize(f, high);
    const char* mode = std::getenv("MPQ_IO_FAULT");
    if (mode && std::strcmp(mode, "high") == 0 && high) *high = 1;
    if (mode && std::strcmp(mode, "size") == 0) {
        SErrSetLastError(EIO);
        return SFILE_INVALID_SIZE;
    }
    return low;
}
extern "C" bool __wrap_SFileReadFile(HANDLE f, void* b, DWORD n, LPDWORD got, LPOVERLAPPED o) {
    const char* mode = std::getenv("MPQ_IO_FAULT");
    if (mode && (std::strcmp(mode, "short") == 0 || std::strcmp(mode, "read") == 0)) {
        *got = 0;
        SErrSetLastError(EIO);
        return std::strcmp(mode, "short") == 0;
    }
    return __real_SFileReadFile(f, b, n, got, o);
}
''')
        cls.fault_cli = cls.work / "mpq-faults"
        subprocess.run(compile_args + [str(wrapper), "-Wl,--wrap=SFileGetFileSize",
                                      "-Wl,--wrap=SFileReadFile", "-Wl,--wrap=SFileOpenFileEx"] + libs
                       + ["-o", str(cls.fault_cli)], env=cls.env, check=True)

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.case.cleanup)
        self.path = Path(self.case.name)
        self.archive = self.path / "test.mpq"
        self.payloads = {"small.bin": b"buffered close failure\x00\xff",
                         "large.bin": bytes(range(256)) * 1024,
                         "empty.bin": b""}
        manifest = self.path / "create.txt"
        lines = []
        for name, data in self.payloads.items():
            source = self.path / ("source-" + name)
            source.write_bytes(data)
            lines.append(f"{source}|{name}\n")
        manifest.write_text("".join(lines))
        result = self.run_cli("create", self.archive, manifest)
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_cli(self, *args, fault=None, preexec_fn=None):
        env = self.env.copy()
        if fault:
            env["MPQ_IO_FAULT"] = fault
        return subprocess.run([str(self.fault_cli if fault else self.cli),
                               *map(str, args)], cwd=self.path, env=env,
                              capture_output=True, text=True, preexec_fn=preexec_fn)

    def extract(self, command, name, output, **kwargs):
        if command == "extract-one":
            return self.run_cli(command, self.archive, name, output, **kwargs)
        if command == "extract-list":
            names = self.path / "names.txt"
            names.write_text(name + "\n")
            return self.run_cli(command, self.archive, names, output, **kwargs)
        return self.run_cli(command, self.archive, output, **kwargs)

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0, result.stderr)
        for field in ("ERROR:", "expected=", "actual=", "errno="):
            self.assertIn(field, result.stderr)
        self.assertNotIn("# extracted", result.stderr)
        self.assertNotIn("# wrote", result.stderr)

    def test_normal_hashes_all_commands(self):
        for command in ("extract-one", "extract", "extract-list"):
            for name, data in self.payloads.items():
                with self.subTest(command=command, name=name):
                    out = self.path / (command + "-" + name)
                    target = out if command == "extract-one" else out / name
                    result = self.extract(command, name, out)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(hashlib.sha256(target.read_bytes()).digest(),
                                     hashlib.sha256(data).digest())

    @unittest.skipUnless(Path("/dev/full").exists(), "/dev/full required")
    def test_dev_full_write_and_buffered_close(self):
        before = os.stat("/dev/full")
        for command in ("extract-one", "extract", "extract-list"):
            for name in ("small.bin", "large.bin"):
                with self.subTest(command=command, name=name):
                    out = self.path / (command + "-full-" + name)
                    if command == "extract-one":
                        output = Path("/dev/full")
                    else:
                        out.mkdir()
                        # All entries may be enumerated, but the selected one
                        # must eventually fail regardless of archive ordering.
                        (out / name).symlink_to("/dev/full")
                        output = out
                    result = self.extract(command, name, output)
                    self.assert_failed(result)
                    self.assertIn(f"errno={errno.ENOSPC}", result.stderr)
                    self.assertIn("close output" if name == "small.bin" else "write",
                                  result.stderr)
                    if command != "extract-one":
                        self.assertTrue((out / name).is_symlink())
                    after = os.stat("/dev/full")
                    self.assertTrue(stat.S_ISCHR(after.st_mode))
                    self.assertEqual((before.st_dev, before.st_ino),
                                     (after.st_dev, after.st_ino))

    def test_read_size_failures_all_commands(self):
        for command in ("extract-one", "extract", "extract-list"):
            for fault in ("open", "high", "size", "short", "read"):
                with self.subTest(command=command, fault=fault):
                    out = self.path / (command + fault)
                    result = self.extract(command, "large.bin", out, fault=fault)
                    self.assert_failed(result)
                    target = out if command == "extract-one" else out / "large.bin"
                    self.assertFalse(target.exists())

    def test_partial_cleanup_only_new_regular_files(self):
        def limit_output():
            signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))

        for command in ("extract-one", "extract", "extract-list"):
            for existing in (False, True):
                with self.subTest(command=command, existing=existing):
                    out = self.path / (command + str(existing))
                    target = out if command == "extract-one" else out / "large.bin"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if existing:
                        target.write_bytes(b"preexisting")
                        inode = target.stat().st_ino
                    result = self.extract(command, "large.bin", out, preexec_fn=limit_output)
                    self.assert_failed(result)
                    self.assertEqual(target.exists(), existing)
                    if existing:
                        self.assertEqual(target.stat().st_ino, inode)

    def test_missing_member_preserves_absence_probe_contract(self):
        result = self.extract("extract-one", "missing.bin", self.path / "one")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.encode(), b"ERROR: file not found in archive\n")
        self.assertFalse((self.path / "one").exists())
        names = self.path / "absent.txt"
        names.write_text("missing.bin\nother.bin\n")
        out = self.path / "absent-output"
        result = self.run_cli("extract-list", self.archive, names, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.splitlines(), ["WARN: not found missing.bin",
                         "WARN: not found other.bin", "# extracted 0 files"])
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
