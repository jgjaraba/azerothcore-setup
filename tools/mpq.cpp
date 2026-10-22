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

static int cmd_extract(const char* arc, const char* outdir, const char* listfile, const char* onlyName)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (listfile && *listfile)
        SFileAddListFile(h, listfile);

    SFILE_FIND_DATA fd;
    HANDLE f = SFileFindFirstFile(h, "*", &fd, nullptr);
    size_t count = 0, bytes = 0;
    std::vector<unsigned char> buf;
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
        mkdirs(outpath);
        HANDLE fh = nullptr;
        if (SFileOpenFileEx(h, name.c_str(), SFILE_OPEN_FROM_MPQ, &fh))
        {
            if (buf.size() < fd.dwFileSize + 1)
                buf.resize(fd.dwFileSize + 1);
            DWORD read = 0;
            SFileReadFile(fh, buf.data(), fd.dwFileSize, &read, nullptr);
            FILE* o = fopen(outpath.c_str(), "wb");
            if (o)
            {
                fwrite(buf.data(), 1, read, o);
                fclose(o);
                bytes += read;
                ++count;
            }
            SFileCloseFile(fh);
        }
        else
        {
            fprintf(stderr, "WARN: cannot open %s\n", name.c_str());
        }
        if (onlyName)
            break;
        if (!SFileFindNextFile(f, &fd))
            break;
    }
    if (f)
        SFileFindClose(f);
    fprintf(stderr, "# extracted %zu files (%zu bytes)\n", count, bytes);
    SFileCloseArchive(h);
    return 0;
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
    std::vector<unsigned char> buf;
    size_t count = 0;
    while (fgets(line, sizeof(line), f))
    {
        size_t n = strlen(line);
        while (n && (line[n-1] == '\n' || line[n-1] == '\r'))
            line[--n] = 0;
        if (!n)
            continue;
        std::string name = line;
        HANDLE fh = nullptr;
        if (!SFileOpenFileEx(h, name.c_str(), SFILE_OPEN_FROM_MPQ, &fh))
        {
            fprintf(stderr, "WARN: not found %s\n", name.c_str());
            continue;
        }
        DWORD sz = SFileGetFileSize(fh, nullptr);
        if (buf.size() < sz + 1)
            buf.resize(sz + 1);
        DWORD read = 0;
        SFileReadFile(fh, buf.data(), sz, &read, nullptr);
        std::string outpath = std::string(outdir) + "/" + name;
        mkdirs(outpath);
        FILE* o = fopen(outpath.c_str(), "wb");
        if (o)
        {
            fwrite(buf.data(), 1, read, o);
            fclose(o);
            ++count;
        }
        SFileCloseFile(fh);
    }
    fclose(f);
    SFileCloseArchive(h);
    fprintf(stderr, "# extracted %zu files\n", count);
    return 0;
}

static int cmd_extract_one(const char* arc, const char* name, const char* outfile, const char* listfile)
{
    HANDLE h = nullptr;
    if (!SFileOpenArchive(arc, 0, MPQ_OPEN_READ_ONLY, &h))
        die("open archive failed");
    if (listfile && *listfile)
        SFileAddListFile(h, listfile);
    HANDLE fh = nullptr;
    if (!SFileOpenFileEx(h, name, SFILE_OPEN_FROM_MPQ, &fh))
        die("file not found in archive");
    DWORD sz = SFileGetFileSize(fh, nullptr);
    std::vector<unsigned char> buf(sz + 1);
    DWORD read = 0;
    SFileReadFile(fh, buf.data(), sz, &read, nullptr);
    FILE* o = fopen(outfile, "wb");
    if (!o)
        die("cannot open outfile");
    fwrite(buf.data(), 1, read, o);
    fclose(o);
    SFileCloseFile(fh);
    SFileCloseArchive(h);
    fprintf(stderr, "# wrote %s (%u bytes)\n", outfile, read);
    return 0;
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
