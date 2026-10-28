// mpq.cpp - Minimal MPQ CLI built on StormLib for the turtle-wow-maps port.
// Subcommands:
//   list   <archive> [listfile]            - list all files (name<TAB>size)
//   extract <archive> <outdir> [listfile]  - extract all files
//   extract-one <archive> <name> <outfile> [listfile] - extract one file
//   add    <archive> <diskfile> <mpqname>  - add a single file to an archive
//   remove <archive> <mpqname> [...]     - remove named entries (no compaction)
//   create <archive> [listfile]            - create new archive and add files
//                                              listed one-per-line in <listfile>
//                                              (each line: <diskpath>|<mpqname>)
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cerrno>
#include <cstdint>
#include <fcntl.h>
#include <string>
#include <vector>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include "StormLib.h"

static void die(const char* msg)
{
    fprintf(stderr, "ERROR: %s\n", msg);
    exit(1);
}

static bool mkdirs(const std::string& path)
{
    std::string cur;
    for (size_t i = 0; i < path.size(); ++i)
    {
        if (path[i] == '/' && !cur.empty())
        {
            if (mkdir(cur.c_str(), 0755) != 0 && errno != EEXIST)
                return false;
        }
        cur += path[i];
    }
    return true;
}

static int cmd_list(const char* arc, const char* listfile)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (listfile && *listfile)
        SFileAddListFile(h, listfile);

    DWORD archiveCount = 0;
    if (!SFileGetFileInfo(h, SFileMpqNumberOfFiles, &archiveCount, sizeof(archiveCount), nullptr))
        die("cannot query archive file count");
    SFILE_FIND_DATA fd;
    HANDLE f = SFileFindFirstFile(h, "*", &fd, nullptr);
    size_t count = 0;
    while (f != nullptr)
    {
        if (fd.lcLocale != 0)
            die("non-neutral locale entry is unsupported");
        printf("%s\t%u\n", fd.cFileName, fd.dwFileSize);
        ++count;
        if (!SFileFindNextFile(f, &fd))
            break;
    }
    if (f)
        SFileFindClose(f);
    fprintf(stderr, "# total files: %zu\n", count);
    fprintf(stderr, "# archive files: %u\n", archiveCount);
    SFileCloseArchive(h);
    return 0;
}

static bool extract_error(const char* operation, const char* path, uint64_t expected,
                          uint64_t actual, int error, DWORD storm = 0)
{
    fprintf(stderr, "ERROR: %s %s: expected=%llu actual=%llu errno=%d (%s) storm=%u\n",
            operation, path, (unsigned long long)expected, (unsigned long long)actual,
            error, strerror(error), storm);
    return false;
}

static bool extract_file(HANDLE archive, const char* name, const char* path, uint64_t& size,
                         bool* missing = nullptr, bool legacy_missing_error = false)
{
    HANDLE file = nullptr;
    errno = 0;
    if (!SFileOpenFileEx(archive, name, SFILE_OPEN_FROM_MPQ, &file))
    {
        DWORD error = SErrGetLastError();
        if (legacy_missing_error && error == ERROR_FILE_NOT_FOUND)
        {
            fprintf(stderr, "ERROR: file not found in archive\n");
            return false;
        }
        // extract-list is also used for exact absence probes by asset builders.
        // Only genuine absence retains the historical warning/skip contract.
        if (missing && error == ERROR_FILE_NOT_FOUND)
        {
            *missing = true;
            fprintf(stderr, "WARN: not found %s\n", name);
            return true;
        }
        return extract_error("open member", name, 0, 0, errno, error);
    }
    DWORD high = 0;
    SErrSetLastError(0);
    errno = 0;
    DWORD low = SFileGetFileSize(file, &high);
    DWORD storm = SErrGetLastError();
    size = (uint64_t(high) << 32) | low;
    if ((low == SFILE_INVALID_SIZE && storm != 0) || high != 0)
    {
        extract_error("size (unsupported high word or query failed)", name,
                      UINT32_MAX, size, errno, storm);
        SFileCloseFile(file);
        return false;
    }
    if (!mkdirs(path))
    {
        extract_error("mkdir", path, size, 0, errno);
        SFileCloseFile(file);
        return false;
    }

    // Only a newly created regular inode belongs to this extraction. Existing
    // files/devices (including symlinks to /dev/full) must never be unlinked.
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0666);
    bool created = fd >= 0;
    if (fd < 0 && errno == EEXIST)
        fd = open(path, O_WRONLY | O_TRUNC);
    struct stat owned = {};
    bool own_regular = created && fstat(fd, &owned) == 0 && S_ISREG(owned.st_mode);
    auto cleanup = [&]() {
        struct stat current;
        if (own_regular && lstat(path, &current) == 0 && S_ISREG(current.st_mode)
            && current.st_dev == owned.st_dev && current.st_ino == owned.st_ino)
            unlink(path);
    };
    FILE* output = fd >= 0 ? fdopen(fd, "wb") : nullptr;
    if (!output)
    {
        int error = errno;
        if (fd >= 0) close(fd);
        cleanup();
        SFileCloseFile(file);
        return extract_error("open output", path, size, 0, error);
    }

    unsigned char buffer[64 * 1024];
    uint64_t read_total = 0, written = 0;
    bool ok = true;
    while (read_total < size)
    {
        DWORD wanted = size - read_total < sizeof(buffer) ? DWORD(size - read_total) : sizeof(buffer);
        DWORD got = 0;
        errno = 0;
        bool read_ok = SFileReadFile(file, buffer, wanted, &got, nullptr);
        int error = errno;
        storm = read_ok ? 0 : SErrGetLastError();
        read_total += got;
        if (!read_ok || got != wanted)
        {
            ok = extract_error("read", name, size, read_total, error, storm);
            break;
        }
        errno = 0;
        size_t count = fwrite(buffer, 1, got, output);
        written += count;
        if (count != got || ferror(output))
        {
            ok = extract_error("write", path, size, written, errno);
            break;
        }
    }
    errno = 0;
    if (fclose(output) != 0)
        ok = extract_error("close output", path, size, written, errno);
    errno = 0;
    if (!SFileCloseFile(file))
        ok = extract_error("close member", name, size, read_total, errno, SErrGetLastError());
    if (!ok) cleanup();
    return ok;
}

static int cmd_extract(const char* arc, const char* outdir, const char* listfile, const char* onlyName)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (listfile && *listfile)
        SFileAddListFile(h, listfile);

    SFILE_FIND_DATA fd;
    HANDLE f = SFileFindFirstFile(h, "*", &fd, nullptr);
    size_t count = 0;
    uint64_t bytes = 0;
    bool ok = true;
    while (f != nullptr)
    {
        std::string name = fd.cFileName;
        if (onlyName && name != onlyName)
        {
            if (!SFileFindNextFile(f, &fd))
                break;
            continue;
        }
        std::string outpath = std::string(outdir) + "/" + name;
        uint64_t size = 0;
        if (!(ok = extract_file(h, name.c_str(), outpath.c_str(), size)))
            break;
        bytes += size;
        ++count;
        if (onlyName)
            break;
        if (!SFileFindNextFile(f, &fd))
            break;
    }
    if (f)
        SFileFindClose(f);
    if (ok) fprintf(stderr, "# extracted %zu files (%llu bytes)\n", count, (unsigned long long)bytes);
    SFileCloseArchive(h);
    return ok ? 0 : 1;
}

static int cmd_extract_list(const char* arc, const char* listFile, const char* outdir, const char* lf)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (lf && *lf)
        SFileAddListFile(h, lf);
    FILE* f = fopen(listFile, "r");
    if (!f)
        die("cannot open list file");
    char line[1024];
    size_t count = 0;
    bool ok = true;
    while (fgets(line, sizeof(line), f))
    {
        size_t n = strlen(line);
        while (n && (line[n-1] == '\n' || line[n-1] == '\r'))
            line[--n] = 0;
        if (!n)
            continue;
        std::string name = line;
        std::string outpath = std::string(outdir) + "/" + name;
        uint64_t size = 0;
        bool missing = false;
        if (!(ok = extract_file(h, name.c_str(), outpath.c_str(), size, &missing)))
            break;
        if (!missing) ++count;
    }
    if (ferror(f)) ok = extract_error("read list", listFile, 0, 0, errno);
    if (fclose(f) != 0) ok = extract_error("close list", listFile, 0, 0, errno);
    SFileCloseArchive(h);
    if (ok) fprintf(stderr, "# extracted %zu files\n", count);
    return ok ? 0 : 1;
}

static int cmd_extract_one(const char* arc, const char* name, const char* outfile, const char* listfile)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (listfile && *listfile)
        SFileAddListFile(h, listfile);
    uint64_t size = 0;
    bool ok = extract_file(h, name, outfile, size, nullptr, true);
    SFileCloseArchive(h);
    if (ok) fprintf(stderr, "# wrote %s (%llu bytes)\n", outfile, (unsigned long long)size);
    return ok ? 0 : 1;
}

static int cmd_add(const char* arc, const char* diskfile, const char* mpqname)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, 0, &h))
        die("open archive failed (must exist; use 'create' first)");
    bool ok = SFileAddFileEx(h, diskfile, mpqname, MPQ_FILE_REPLACEEXISTING, MPQ_COMPRESSION_ZLIB, MPQ_COMPRESSION_NEXT_SAME);
    if (!ok)
    {
        fprintf(stderr, "add failed: %u\n", SErrGetLastError());
        SFileCloseArchive(h);
        die("SFileAddFileEx");
    }
    SFileFlushArchive(h);
    SFileCloseArchive(h);
    return 0;
}

static int cmd_remove(const char* arc, int count, char** names)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, 0, &h))
        die("open archive failed");
    // Preflight all names before changing the archive. Callers must use copies.
    for (int i = 0; i < count; ++i)
        if (names[i][0] == '(' || !SFileHasFile(h, names[i]))
            die("missing or internal entry in remove request");
    for (int i = 0; i < count; ++i)
        if (!SFileRemoveFile(h, names[i], SFILE_OPEN_FROM_MPQ))
            die("remove failed");
    if (!SFileFlushArchive(h) || !SFileCloseArchive(h))
        die("flush/close failed after remove");
    return 0;
}

static int cmd_create(const char* arc, const char* listfile)
{
    HANDLE h = nullptr;
    // Version 3 archive; add (listfile) so the archive is self-describing.
    // V2 (0x2C header, hi-block table) matches the format of the client's own
    // patch-Z.mpq and is guaranteed readable by the 3.3.5a client.
    DWORD flags = MPQ_CREATE_ARCHIVE_V2 | MPQ_CREATE_LISTFILE;
    if (!SFileCreateArchive(arc, flags, 4096, &h))
        die("create archive failed");

    if (listfile && *listfile)
    {
        FILE* f = fopen(listfile, "r");
        if (!f)
            die("cannot open listfile");
        char line[8192];
        size_t added = 0;
        while (fgets(line, sizeof(line), f))
        {
            size_t n = strlen(line);
            while (n && (line[n-1] == '\n' || line[n-1] == '\r'))
                line[--n] = 0;
            if (!n || line[0] == '#')
                continue;
            char* sep = strchr(line, '|');
            if (!sep)
                continue;
            *sep = 0;
            const char* disk = line;
            const char* mpq = sep + 1;
            bool ok = SFileAddFileEx(h, disk, mpq, MPQ_FILE_REPLACEEXISTING, MPQ_COMPRESSION_ZLIB, MPQ_COMPRESSION_NEXT_SAME);
            if (!ok)
            {
                fprintf(stderr, "WARN: add failed for %s -> %s (err %u)\n", disk, mpq, SErrGetLastError());
                continue;
            }
            ++added;
        }
        fclose(f);
        fprintf(stderr, "# added %zu files\n", added);
    }
    SFileFlushArchive(h);
    SFileCloseArchive(h);
    return 0;
}

int main(int argc, char** argv)
{
    if (argc < 2)
    {
        fprintf(stderr, "usage: mpq <list|extract|extract-one|add|remove|create> ...\n");
        return 2;
    }
    std::string cmd = argv[1];
    if (cmd == "list")
    {
        if (argc < 3) die("usage: mpq list <archive> [listfile]");
        return cmd_list(argv[2], argc > 3 ? argv[3] : "");
    }
    if (cmd == "extract")
    {
        if (argc < 4) die("usage: mpq extract <archive> <outdir> [listfile]");
        return cmd_extract(argv[2], argv[3], argc > 4 ? argv[4] : "", nullptr);
    }
    if (cmd == "extract-one")
    {
        if (argc < 5) die("usage: mpq extract-one <archive> <name> <outfile> [listfile]");
        return cmd_extract_one(argv[2], argv[3], argv[4], argc > 5 ? argv[5] : "");
    }
    if (cmd == "extract-list")
    {
        if (argc < 5) die("usage: mpq extract-list <archive> <listfile-of-names> <outdir> [listfile]");
        return cmd_extract_list(argv[2], argv[3], argv[4], argc > 5 ? argv[5] : "");
    }
    if (cmd == "add")
    {
        if (argc < 5) die("usage: mpq add <archive> <diskfile> <mpqname>");
        return cmd_add(argv[2], argv[3], argv[4]);
    }
    if (cmd == "create")
    {
        if (argc < 3) die("usage: mpq create <archive> [listfile]");
        return cmd_create(argv[2], argc > 3 ? argv[3] : "");
    }
    if (cmd == "remove")
    {
        if (argc < 4) die("usage: mpq remove <archive> <mpqname> [...]");
        return cmd_remove(argv[2], argc - 3, argv + 3);
    }
    fprintf(stderr, "unknown command %s\n", cmd.c_str());
    return 2;
}
