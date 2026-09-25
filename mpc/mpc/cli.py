import argparse as ap
import os
from mpc.core import *

def compress(inp, output, algorithm, key, force=False, split_size=0, split_count=0):
    if os.path.isdir(inp):
        mode = "dir" 
    elif os.path.exists(inp):
        mode = "file"
    else:
        raise FileNotFoundError(f"Input file or directory not found: {inp}")
    
    if os.path.exists(output) and not force:
        raise FileNotFoundError(f"Output file or directory already exists: {output}")
    
    p = Packer(name=inp,
               mode=mode,
               compress=True,
               compression_algorithm=algorithm,
               encrypt=bool(key),
               password=key or "",
               volume_size=split_size,
               volume_count=split_count)
    p.pack(output)
    return True

def decompress(inp, output, key, force=False):
    if not os.path.exists(inp):
        raise FileNotFoundError(f"Input file or directory not found: {inp}")
    if os.path.exists(output) and not force:
        raise FileNotFoundError(f"Output file or directory already exists: {output}")
    
    unp = Unpacker(filepath=inp,
                   password=key or "")
    unp.unpack(output)
    return True

def main():
    parser = ap.ArgumentParser(description="MPC CLI - Pack, Unpack, and List archives with split support")

    parser.add_argument("command", choices=["pack", "unpack", "list", "help"], help="Operation mode")
    parser.add_argument("input", nargs="?", type=str, help="Input file or directory path")
    parser.add_argument("output", nargs="?", type=str, help="Output path (optional)")
    
    parser.add_argument("--algorithm", "-al", choices=get_available_algorithms().keys(), 
                        type=str, default="zstd", help="Compression algorithm to use")
    
    parser.add_argument("--key", "-k", type=str, default="", help="Encryption key/password")
    parser.add_argument("--key-file", "-kf", type=str, default="", help="Read key from file")
    parser.add_argument("--key-env", "-ke", type=str, default="", help="Read key from environment variable")
    
    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument("--split-size", "-ss", type=int, default=0,
                             help="Split volume size in bytes (e.g., 1073741824 for 1GB)")
    split_group.add_argument("--split-count", "-sc", type=int, default=0,
                             help="Split into N volumes")
    
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files/directory")
    parser.add_argument("--auto", "-a", nargs="?", const="size", choices=["speed", "size"], help="Auto choose algorithm")

    args = parser.parse_args()
    if args.command == "help":
        help_text = """
╔════════════════════════════════════════════════════════════════════════════════╗
║                          MPC CLI - Pack/Unpack/List Tool                       ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Usage:                                                                         ║
║     mpc <command> [input] [output] [options]                                   ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Commands:                                                                      ║
║     pack     - Pack a file or directory into an archive                        ║
║     unpack   - Unpack an archive to a directory                                ║
║     list     - List contents of an archive                                     ║
║     help     - Show this help message                                          ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Pack Options:                                                                  ║
║     -a, --algorithm ALGO    Compression algorithm (zstd, gzip, lzma, bz2, none)║
║                               Default: zstd                                    ║
║     -k, --key PASSWORD      Encryption key/password                            ║
║     -f, --force             Overwrite existing files/directory                 ║
║     --split-size SIZE       Split volume size (e.g., 1G, 100MB, 1073741824)    ║
║     --split-count N         Split into N volumes                               ║
║     --auto [speed|size]     Auto choose algorithm (default: size)              ║
║                                                                                ║
║     Note: If both --split-size and --split-count are provided,                 ║
║           --split-size takes priority.                                         ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Unpack Options:                                                                ║
║     -k, --key PASSWORD      Decryption password                                ║
║     -f, --force             Overwrite existing files                           ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ List Options:                                                                  ║
║     -k, --key PASSWORD      Decryption password (for encrypted archives)       ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Examples:                                                                      ║
║                                                                                ║
║   # Pack a file                                                                ║
║   mpc pack ./example.txt archive.mpc -k mypassword                             ║
║                                                                                ║
║   # Pack a directory with zstd compression                                     ║
║   mpc pack ./myfolder backup.mpc -a zstd -k 123456                             ║
║                                                                                ║
║   # Pack with auto algorithm (prioritize speed)                                ║
║   mpc pack ./data archive.mpc --auto speed                                     ║
║                                                                                ║
║   # Pack into 100MB volumes                                                    ║
║   mpc pack ./largefolder split.mpc --split-size 100MB                          ║
║                                                                                ║
║   # Pack into 5 volumes                                                        ║
║   mpc pack ./folder volumes.mpc --split-count 5                                ║
║                                                                                ║
║   # Unpack with password                                                       ║
║   mpc unpack archive.mpc ./output -k mypassword                                ║
║                                                                                ║
║   # List archive contents                                                      ║
║   mpc list archive.mpc                                                         ║
║                                                                                ║
║   # List encrypted archive                                                     ║
║   mpc list encrypted.mpc -k mypassword                                         ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
        print(help_text)
        exit(0)
    
    if not args.input:
        print("Error: Input file or directory path is required.")
        exit(1)

    if args.key_file and args.key:
        print("Warning: --key-file and --key are both set, --key will be ignored.")
        with open(args.key_file, "r") as f:
            args.key = f.read().strip()
    elif args.key_env and args.key:
        print("Warning: --key-env and --key are both set, --key will be ignored.")
        args.key = os.getenv(args.key_env, "")
    elif args.key_env:
        args.key = os.getenv(args.key_env, "")
    
    if args.auto is not None:
        if args.command == "pack":
            if args.algorithm != "zstd":
                print("Warning: --auto and --algorithm are both set, --algorithm will be ignored.")
            args.algorithm = auto_choose_algo(path=args.input,
                                              speed_first=args.auto == "speed")
            print(f"Auto choose algorithm: {args.algorithm}")
        else:
            print("Warning: --auto is not supported for unpack/list commands.")
    
    if not args.output:
        if args.command == "pack":
            args.output = os.path.basename(args.input.rstrip("/\\")) + ".mpc"
        elif args.command == "unpack":
            args.output = "extracted"
        elif args.command == "list":
            args.output = "list"

    try:
        res = False
        if args.command == "pack":
            res = compress(args.input, args.output, args.algorithm, args.key, 
                          args.force, args.split_size, args.split_count)
        elif args.command == "unpack":
            res = decompress(args.input, args.output, args.key, args.force)
        elif args.command == "list":
            lister = Lister(args.input)
            lister.print()
            res = True
            
    except FileNotFoundError as e:
        print(e)
        res = False
    except EncryptionError as e:
        print(f"[EncError] {e}")
        res = False
    except Exception as e:
        print(f"[Error] {e}")
        res = False
    
    if res:
        if args.command == "pack":
            if args.split_size > 0 or args.split_count > 0:
                print(f"Split compression completed successfully, first volume: {os.path.basename(args.input.rstrip("/\\")) + ".1mp"}")
            else:
                print(f"Compression completed successfully, path: {args.output}")
        elif args.command == "unpack":
            print(f"Decompression completed successfully, path: {args.output}")
        exit(0)
    else:
        print("Operation failed")
        exit(1)

if __name__ == "__main__":
    main()