import os
import io
import struct
import hashlib
import tempfile
import warnings
from typing import Optional, Union, List, Dict, BinaryIO, Tuple

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(x, **kwargs):  # type: ignore
        return x

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, hmac
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class EncryptionError(Exception):
    """加密/解密过程中的错误"""
    pass

class CompressionError(Exception):
    """压缩/解压缩过程中的错误"""
    pass

def _derive_key(password: str, salt: bytes = b'mpc_salt') -> bytes:
    """由密码派生 32 字节密钥"""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=32)

def _encrypt_data(data: bytes, password: str) -> bytes:
    """
    加密字节数据（一次性，用于少量数据）
    Args:
        data: 待加密数据
        password: 密码
    Returns:
        加密后的数据 (nonce + ciphertext + hmac)
    """
    if not CRYPTO_AVAILABLE:
        raise EncryptionError("Need to install cryptography module: pip install cryptography")
    key = _derive_key(password)
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(ct)
    tag = h.finalize()
    return nonce + ct + tag

def _decrypt_data(encrypted_data: bytes, password: str) -> bytes:
    """
    解密字节数据（一次性）
    Args:
        encrypted_data: nonce + ciphertext + hmac
        password: 密码
    Returns:
        解密后的数据
    """
    if not CRYPTO_AVAILABLE:
        raise EncryptionError("Need to install cryptography module: pip install cryptography")
    if len(encrypted_data) < 48:  # 16 nonce + 32 hmac
        raise EncryptionError("Invalid encrypted data")
    key = _derive_key(password)
    nonce = encrypted_data[:16]
    tag = encrypted_data[-32:]
    ct = encrypted_data[16:-32]
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(ct)
    h.verify(tag)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ct) + decryptor.finalize()

def _encrypt_stream(in_stream: BinaryIO, out_stream: BinaryIO, password: str) -> None:
    """流式加密，将 in_stream 内容加密后写入 out_stream，格式 nonce+ciphertext+hmac"""
    if not CRYPTO_AVAILABLE:
        raise EncryptionError("Need to install cryptography module: pip install cryptography")
    key = _derive_key(password)
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    hm = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    out_stream.write(nonce)
    while True:
        chunk = in_stream.read(1024 * 1024)
        if not chunk:
            break
        ct_chunk = encryptor.update(chunk)
        hm.update(ct_chunk)
        out_stream.write(ct_chunk)
    ct_final = encryptor.finalize()
    if ct_final:
        hm.update(ct_final)
        out_stream.write(ct_final)
    out_stream.write(hm.finalize())

def _decrypt_stream_to_temp(in_stream: BinaryIO, data_length: int, password: str) -> io.BytesIO:
    """
    流式解密，从 in_stream 读取 data_length 字节进行解密，返回含明文数据的 BytesIO
    HMAC 验证失败会抛出异常。
    """
    if not CRYPTO_AVAILABLE:
        raise EncryptionError("Need to install cryptography module: pip install cryptography")
    if data_length < 48:
        raise EncryptionError("Invalid encrypted data length")
    key = _derive_key(password)
    nonce = in_stream.read(16)
    if len(nonce) != 16:
        raise EncryptionError("Incomplete encrypted data")
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    hm = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    tmp = tempfile.SpooledTemporaryFile(max_size=1024*1024*100)
    remaining = data_length - 48
    while remaining > 0:
        chunk_size = min(1024 * 1024, remaining)
        chunk = in_stream.read(chunk_size)
        if not chunk:
            raise EncryptionError("Unexpected end of encrypted data")
        remaining -= len(chunk)
        hm.update(chunk)
        pt = decryptor.update(chunk)
        if pt:
            tmp.write(pt)
    tag = in_stream.read(32)
    if len(tag) != 32:
        raise EncryptionError("Incomplete HMAC tag")
    hm.verify(tag)
    final_pt = decryptor.finalize()
    if final_pt:
        tmp.write(final_pt)
    tmp.seek(0)
    return tmp

class BaseCompressor:
    """压缩器基类"""
    name: str = "base"
    id: int = 0
    speed: int = 5
    ratio: int = 5
    memory: int = 5

    def compress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def decompress(self, data: bytes, original_size: int = 0) -> bytes:
        raise NotImplementedError

    def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
        data = in_stream.read()
        out_stream.write(self.compress(data))

    def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
        data = in_stream.read()
        out_stream.write(self.decompress(data, original_size))

class Compressor:
    """压缩算法注册表"""
    _compressors: Dict[int, BaseCompressor] = {}
    _name_to_id: Dict[str, int] = {}
    _default_id: int = 1

    @classmethod
    def register(cls, compressor: BaseCompressor):
        cls._compressors[compressor.id] = compressor
        cls._name_to_id[compressor.name] = compressor.id

    @classmethod
    def get(cls, compressor_id: int) -> BaseCompressor:
        if compressor_id not in cls._compressors:
            raise CompressionError(f"Unsupported algorithm ID: {compressor_id}")
        return cls._compressors[compressor_id]

    @classmethod
    def get_by_name(cls, name: str) -> Optional[BaseCompressor]:
        return cls._compressors.get(cls._name_to_id.get(name, -1))

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._name_to_id

    @classmethod
    def get_default(cls) -> BaseCompressor:
        return cls.get(cls._default_id)

    @classmethod
    def set_default(cls, compressor_id: int):
        if compressor_id not in cls._compressors:
            raise CompressionError(f"Algorithm {compressor_id} not registered")
        cls._default_id = compressor_id

    @classmethod
    def list_algorithms(cls) -> Dict[str, int]:
        return dict(cls._name_to_id)

    @classmethod
    def compress(cls, data: bytes, algorithm: Union[str, int, None] = None) -> Tuple[bytes, int]:
        if algorithm is None:
            compressor = cls.get_default()
        elif isinstance(algorithm, str):
            c = cls.get_by_name(algorithm)
            if c is None:
                raise CompressionError(f"Unsupported algorithm: {algorithm}")
            compressor = c
        elif isinstance(algorithm, int):
            compressor = cls.get(algorithm)
        else:
            raise CompressionError(f"Invalid algorithm type: {type(algorithm)}")
        return compressor.compress(data), compressor.id

    @classmethod
    def decompress(cls, data: bytes, compressor_id: int, original_size: int = 0) -> bytes:
        return cls.get(compressor_id).decompress(data, original_size)

    @classmethod
    def compress_stream(cls, compressor_id: int, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
        cls.get(compressor_id).compress_stream(in_stream, out_stream)

    @classmethod
    def decompress_stream(cls, compressor_id: int, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
        cls.get(compressor_id).decompress_stream(in_stream, out_stream, original_size)

class NoneCompressor(BaseCompressor):
    name = "none"
    id = 0
    speed = 10
    ratio = 1
    memory = 1
    def compress(self, data: bytes) -> bytes:
        return data
    def decompress(self, data: bytes, original_size: int = 0) -> bytes:
        return data
    def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
        while True:
            chunk = in_stream.read(1024 * 1024)
            if not chunk:
                break
            out_stream.write(chunk)
    def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
        while True:
            chunk = in_stream.read(1024 * 1024)
            if not chunk:
                break
            out_stream.write(chunk)

Compressor.register(NoneCompressor())

try:
    import zstandard as _zstd
    class ZstdCompressor(BaseCompressor):
        name = "zstd"
        id = 1
        speed = 8
        ratio = 8
        memory = 4
        def compress(self, data: bytes) -> bytes:
            return _zstd.ZstdCompressor(level=3).compress(data)
        def decompress(self, data: bytes, original_size: int = 0) -> bytes:
            dctx = _zstd.ZstdDecompressor()
            return dctx.decompress(data, max_output_size=original_size) if original_size > 0 else dctx.decompress(data)
        def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
            cctx = _zstd.ZstdCompressor(level=3)
            compressor = cctx.compressobj()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(compressor.compress(chunk))
            out_stream.write(compressor.flush())
        def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
            dctx = _zstd.ZstdDecompressor()
            decompressor = dctx.decompressobj()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(decompressor.decompress(chunk))
    Compressor.register(ZstdCompressor())
except ImportError:
    Compressor.set_default(0)

try:
    import lzma
    class LZMACompressor(BaseCompressor):
        name = "lzma"
        id = 2
        speed = 3
        ratio = 9
        memory = 7
        def compress(self, data: bytes) -> bytes:
            return lzma.compress(data)
        def decompress(self, data: bytes, original_size: int = 0) -> bytes:
            return lzma.decompress(data)
        def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
            lzc = lzma.LZMACompressor()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(lzc.compress(chunk))
            out_stream.write(lzc.flush())
        def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
            lzd = lzma.LZMADecompressor()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(lzd.decompress(chunk))
    Compressor.register(LZMACompressor())
except ImportError:
    pass

try:
    import gzip as _gzip
    class GzipCompressor(BaseCompressor):
        name = "gzip"
        id = 3
        speed = 7
        ratio = 5
        memory = 3
        def compress(self, data: bytes) -> bytes:
            return _gzip.compress(data, compresslevel=6)
        def decompress(self, data: bytes, original_size: int = 0) -> bytes:
            return _gzip.decompress(data)
        def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
            with _gzip.GzipFile(fileobj=out_stream, mode='wb', compresslevel=6) as gz:
                while True:
                    chunk = in_stream.read(1024 * 1024)
                    if not chunk:
                        break
                    gz.write(chunk)
        def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
            with _gzip.GzipFile(fileobj=in_stream, mode='rb') as gz:
                while True:
                    chunk = gz.read(1024 * 1024)
                    if not chunk:
                        break
                    out_stream.write(chunk)
    Compressor.register(GzipCompressor())
except ImportError:
    pass

try:
    import bz2
    class Bz2Compressor(BaseCompressor):
        name = "bz2"
        id = 4
        speed = 4
        ratio = 7
        memory = 5
        def compress(self, data: bytes) -> bytes:
            return bz2.compress(data)
        def decompress(self, data: bytes, original_size: int = 0) -> bytes:
            return bz2.decompress(data)
        def compress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
            bzc = bz2.BZ2Compressor()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(bzc.compress(chunk))
            out_stream.write(bzc.flush())
        def decompress_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, original_size: int = 0) -> None:
            bzd = bz2.BZ2Decompressor()
            while True:
                chunk = in_stream.read(1024 * 1024)
                if not chunk:
                    break
                out_stream.write(bzd.decompress(chunk))
    Compressor.register(Bz2Compressor())
except ImportError:
    pass

SPLIT_MAGIC = b'MMP'
EXTRA_MAGIC = b'EMP'
SPLIT_VERSION = 1

INCOMPRESSIBLE_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.heic', '.bmp', '.ico',
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.hevc',
    '.mp3', '.aac', '.ogg', '.flac', '.wav', '.m4a', '.opus', '.wma',
    '.zip', '.7z', '.rar', '.tar.gz', '.tgz', '.bz2', '.xz', '.zst', '.gz', '.lz4', '.mpc',
    '.pdf', '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
    '.exe', '.dll', '.so', '.dylib',
    '.iso', '.img', '.dmg',
})

TEXT_EXTENSIONS = frozenset({
    '.txt', '.md', '.rst', '.csv', '.tsv', '.log',
    '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    '.c', '.cpp', '.h', '.hpp', '.rs', '.go', '.java', '.kt', '.swift',
    '.sh', '.bat', '.ps1', '.cfg', '.ini', '.toml',
    '.sql', '.r', '.m', '.tex', '.bib',
})

def _get_ext(name: str) -> str:
    """获取文件扩展名（支持 .tar.gz）"""
    name_lower = name.lower()
    if name_lower.endswith('.tar.gz'):
        return '.tar.gz'
    return os.path.splitext(name)[1].lower()

def _is_text_content(sample: bytes) -> bool:
    """根据样本判断是否为文本内容"""
    if not sample:
        return False
    text_chars = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13) or b >= 192)
    return (text_chars / len(sample)) > 0.95

def _choose_for_single(filepath: str, file_size: int, data_sample: Optional[bytes], speed_first: bool) -> str:
    """为单个文件选择压缩算法名"""
    ext = _get_ext(filepath)
    if ext in INCOMPRESSIBLE_EXTENSIONS:
        return "none"
    is_text = ext in TEXT_EXTENSIONS
    if not is_text and data_sample:
        is_text = _is_text_content(data_sample)
    if file_size < 1024:
        return "none" if not speed_first else "gzip"
    elif file_size < 1024 * 1024:
        return "gzip" if speed_first else "zstd"
    elif file_size < 100 * 1024 * 1024:
        if is_text:
            if speed_first:
                return "zstd"
            return "lzma" if Compressor.has("lzma") else "zstd"
        return "zstd"
    elif file_size < 1024 * 1024 * 1024:
        if is_text:
            return "zstd"
        return "gzip" if speed_first else "zstd"
    else:
        return "gzip" if Compressor.has("gzip") else "zstd"

def _scan_dir_stats(dirpath: str) -> dict:
    """扫描目录统计信息"""
    stats = {
        "total_size": 0, "file_count": 0,
        "incompressible_size": 0, "incompressible_count": 0,
        "text_size": 0, "text_count": 0,
        "has_large_files": False, "max_file_size": 0,
        "ext_counts": {},
    }
    for root, _, files in os.walk(dirpath):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                fsize = os.path.getsize(full_path)
            except OSError:
                continue
            stats["total_size"] += fsize
            stats["file_count"] += 1
            if fsize > stats["max_file_size"]:
                stats["max_file_size"] = fsize
            if fsize > 100 * 1024 * 1024:
                stats["has_large_files"] = True
            ext = _get_ext(file)
            stats["ext_counts"][ext] = stats["ext_counts"].get(ext, 0) + 1
            if ext in INCOMPRESSIBLE_EXTENSIONS:
                stats["incompressible_size"] += fsize
                stats["incompressible_count"] += 1
            elif ext in TEXT_EXTENSIONS:
                stats["text_size"] += fsize
                stats["text_count"] += 1
    if stats["file_count"] > 0:
        stats["avg_file_size"] = stats["total_size"] // stats["file_count"]
    else:
        stats["avg_file_size"] = 0
    return stats

def auto_choose_algo(
    path: str = "",
    data: Optional[bytes] = None,
    file_size: Optional[int] = None,
    speed_first: bool = False,
) -> str:
    """
    自动选择合适的压缩算法
    Args:
        path: 文件或目录路径
        data: 文件数据（可选）
        file_size: 文件大小（可选）
        speed_first: 是否速度优先
    Returns:
        算法名称
    """
    if data is not None:
        fsize = len(data)
        sample = data[:4096]
        return _choose_for_single(path or "data", fsize, sample, speed_first)
    if file_size is not None:
        sample = None
        if path and os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    sample = f.read(4096)
            except OSError:
                pass
        return _choose_for_single(path, file_size, sample, speed_first)
    if not path or not os.path.exists(path):
        return "zstd"
    if os.path.isfile(path):
        try:
            fsize = os.path.getsize(path)
        except OSError:
            fsize = 0
        sample = None
        try:
            with open(path, "rb") as f:
                sample = f.read(4096)
        except OSError:
            pass
        return _choose_for_single(path, fsize, sample, speed_first)
    if os.path.isdir(path):
        stats = _scan_dir_stats(path)
        total = stats["total_size"]
        if total == 0:
            return "none"
        incomp_ratio = stats["incompressible_size"] / total if total > 0 else 0
        text_ratio = stats["text_size"] / total if total > 0 else 0
        if incomp_ratio > 0.8:
            return "none"
        if incomp_ratio > 0.5:
            return "gzip" if speed_first else "zstd"
        if text_ratio > 0.6:
            if total > 100 * 1024 * 1024:
                return "zstd"
            if speed_first:
                return "zstd"
            return "lzma" if Compressor.has("lzma") else "zstd"
        if total < 1024 * 1024:
            return "gzip" if speed_first else "zstd"
        elif total < 100 * 1024 * 1024:
            return "zstd"
        elif total < 1024 * 1024 * 1024:
            if stats["has_large_files"] or stats["avg_file_size"] > 10 * 1024 * 1024:
                return "gzip" if speed_first else "zstd"
            return "zstd"
        else:
            return "gzip" if Compressor.has("gzip") else "zstd"
    return "zstd"

def get_algo_info(name: str) -> Optional[dict]:
    """获取算法信息"""
    comp = Compressor.get_by_name(name)
    if comp is None:
        return None
    return {
        "name": comp.name, "id": comp.id,
        "speed": comp.speed, "ratio": comp.ratio, "memory": comp.memory,
    }

class LimitedReader:
    """包装文件对象，限制最大读取字节数"""
    def __init__(self, stream: BinaryIO, limit: int):
        self._stream = stream
        self._remaining = limit

    def read(self, size: int = -1) -> bytes:
        if self._remaining <= 0:
            return b''
        if size < 0 or size > self._remaining:
            size = self._remaining
        data = self._stream.read(size)
        self._remaining -= len(data)
        return data

class MultiVolumeReader:
    """顺序读取多个分卷文件的数据部分（跳过各卷头）"""
    def __init__(self, first_volume_path: str, total_volumes: int, volume_size: int,
                 base: str, dirname: str):
        self._total = total_volumes
        self._vol_size = volume_size
        self._base = base
        self._dirname = dirname
        self._current_vol = 1
        self._current_file: Optional[BinaryIO] = None
        self._open_next()

    def _get_volume_path(self, vol: int) -> str:
        if vol <= 999:
            return os.path.join(self._dirname, f"{self._base}.{vol:03d}.mpc")
        return os.path.join(self._dirname, f"{self._base}.emp")

    def _open_next(self) -> None:
        if self._current_file:
            self._current_file.close()
        if self._current_vol > self._total:
            self._current_file = None
            return
        path = self._get_volume_path(self._current_vol)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing volume: {path}")
        f = open(path, 'rb')
        magic = f.read(3)
        if magic not in (SPLIT_MAGIC, EXTRA_MAGIC):
            f.close()
            raise ValueError(f"Invalid split magic in {path}")
        f.read(1)  # version
        if self._current_vol == 1:
            f.read(8 + 4)
        self._current_file = f
        self._current_vol += 1

    def read(self, size: int = -1) -> bytes:
        if self._current_file is None:
            return b''
        data = self._current_file.read(size)
        while size < 0 or len(data) < size:
            if self._current_vol > self._total:
                break
            self._open_next()
            if self._current_file is None:
                break
            if size < 0:
                data += self._current_file.read()
            else:
                data += self._current_file.read(size - len(data))
        return data

    def close(self) -> None:
        if self._current_file:
            self._current_file.close()
            self._current_file = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

class Packer:
    MODE_FILE = b'F'
    MODE_DIR = b'D'
    MODE_FILE_COMPRESSED = b'C'
    MODE_DIR_COMPRESSED = b'E'

    def __init__(self, name: str, mode: str = "dir",
                 compress: bool = True,
                 compression_algorithm: str = "zstd",
                 encrypt: bool = True,
                 password: str = "",
                 volume_size: int = 0,
                 volume_count: int = 0,
                 show_progress: bool = True):
        """
        初始化打包器
        Args:
            name: 文件/目录路径
            mode: 'file' 或 'dir'
            compress: 是否压缩
            compression_algorithm: 压缩算法名
            encrypt: 是否加密
            password: 加密密码
            volume_size: 分卷大小（字节），与 volume_count 二选一
            volume_count: 分卷数量
            show_progress: 是否显示进度条
        """
        if mode not in ("dir", "file"):
            raise ValueError("mode must be 'dir' or 'file'")
        self.name = name
        self.mode = mode
        self.compress_flag = compress
        self.compression_algorithm = compression_algorithm
        self.encrypt = encrypt
        self.password = password
        self.show_progress = show_progress and TQDM_AVAILABLE
        self._file_list: List[Tuple[str, str]] = []
        self._is_single_file = (mode == "file")
        self.is_split = False
        self.volume_size = 0
        self.volume_count = 0
        self.has_extra = False

        if volume_size > 0 and volume_count > 0:
            warnings.warn("Both volume_size and volume_count provided, using volume_size")
            self.volume_size = volume_size
            self.volume_count = 0
        elif volume_size > 0:
            self.is_split = True
            self.volume_size = volume_size
        elif volume_count > 0:
            self.is_split = True
            self.volume_count = volume_count

        if self._is_single_file:
            if not os.path.isfile(name):
                raise FileNotFoundError(f"{name} is not an existing file")
            self.path = name
        else:
            if not os.path.isdir(name):
                raise FileNotFoundError(f"{name} is not an existing directory")
            self.path = os.path.abspath(name)
            self._scan_dir()

    def _scan_dir(self):
        """扫描目录获取文件列表"""
        for root, _, files in os.walk(self.path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.path).replace(os.sep, "/")
                self._file_list.append((rel_path, full_path))

    def _process_file_to_temp(self, src_path: str) -> Tuple[int, io.IOBase]:
        """
        对单个文件进行压缩和加密，返回 (处理后数据大小, 临时文件对象 seeked to 0)
        """
        tmp = tempfile.SpooledTemporaryFile(max_size=1024*1024*100)
        try:
            if self.compress_flag or self.encrypt:
                if self.compress_flag:
                    comp_tmp = tempfile.SpooledTemporaryFile(max_size=1024*1024*100)
                    with open(src_path, 'rb') as src:
                        algo_id = Compressor.get_by_name(self.compression_algorithm).id
                        Compressor.compress_stream(algo_id, src, comp_tmp)
                    comp_tmp.seek(0)
                else:
                    comp_tmp = open(src_path, 'rb')
                if self.encrypt:
                    _encrypt_stream(comp_tmp, tmp, self.password)
                else:
                    while True:
                        chunk = comp_tmp.read(1024 * 1024)
                        if not chunk:
                            break
                        tmp.write(chunk)
                comp_tmp.close()
            else:
                with open(src_path, 'rb') as src:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        tmp.write(chunk)
            tmp.seek(0, os.SEEK_END)
            size = tmp.tell()
            tmp.seek(0)
            return size, tmp
        except Exception:
            tmp.close()
            raise

    def _write_entry(self, out_stream: BinaryIO, name: str, data_temp: io.IOBase, data_size: int,
                     encrypted: bool, compressed: bool, algo_id: int, raw_len: int):
        """写入单个文件条目到 out_stream"""
        name_bytes = name.encode('utf-8')
        header = struct.pack(f"!II{len(name_bytes)}s", len(name_bytes), data_size, name_bytes)
        out_stream.write(header)
        # metadata
        flags = 0
        if encrypted: flags |= 1
        if compressed: flags |= 2
        out_stream.write(struct.pack("!B", flags))
        if compressed:
            out_stream.write(struct.pack("!B", algo_id))
        if compressed or encrypted:
            out_stream.write(struct.pack("!Q", raw_len))
        while True:
            chunk = data_temp.read(1024 * 1024)
            if not chunk:
                break
            out_stream.write(chunk)

    def _pack_single_file_to_stream(self, out_stream: BinaryIO):
        """将单个文件写入流（不关流）"""
        filename = os.path.basename(self.name)
        with open(self.path, 'rb') as src:
            raw_len = os.path.getsize(self.path)
        data_size, data_temp = self._process_file_to_temp(self.path)
        encrypted = self.encrypt
        compressed = self.compress_flag
        algo_id = Compressor.get_by_name(self.compression_algorithm).id if compressed else 0
        mode_byte = self.MODE_FILE_COMPRESSED if (encrypted or compressed) else self.MODE_FILE
        out_stream.write(struct.pack("!3s1s", b"MPC", mode_byte))
        self._write_entry(out_stream, filename, data_temp, data_size, encrypted, compressed, algo_id, raw_len)
        data_temp.close()

    def _pack_directory_to_stream(self, out_stream: BinaryIO):
        """将目录写入流"""
        file_count = len(self._file_list)
        encrypted = self.encrypt
        compressed = self.compress_flag
        mode_byte = self.MODE_DIR_COMPRESSED if (encrypted or compressed) else self.MODE_DIR
        out_stream.write(struct.pack("!3s1sI", b"MPC", mode_byte, file_count))
        algo_id = Compressor.get_by_name(self.compression_algorithm).id if compressed else 0
        iter_files = tqdm(self._file_list, desc="Packing files", unit="file",
                          disable=not self.show_progress) if self.show_progress else self._file_list
        for rel_path, full_path in iter_files:
            raw_len = os.path.getsize(full_path)
            data_size, data_temp = self._process_file_to_temp(full_path)
            self._write_entry(out_stream, rel_path, data_temp, data_size, encrypted, compressed, algo_id, raw_len)
            data_temp.close()

    def pack(self, output: Optional[str] = None) -> str:
        """
        执行打包
        Args:
            output: 输出基础名（不含扩展名），None 则使用源名
        Returns:
            首个分卷的路径（非分卷时为 .mpc 路径）
        """
        if output is None:
            output = self.name
        elif output.endswith('.mpc'):
            output = output[:-4]
        if self.is_split:
            return self._pack_split(output)
        else:
            return self._pack_single(output)

    def _pack_single(self, output_base: str) -> str:
        """普通单文件打包"""
        output = f"{output_base}.mpc"
        with open(output, "wb") as f:
            if self._is_single_file:
                self._pack_single_file_to_stream(f)
            else:
                self._pack_directory_to_stream(f)
        return output

    def _pack_split(self, output_base: str) -> str:
        """分卷打包：先构建整个存档到临时文件，再分卷写入"""
        archive_tmp = tempfile.SpooledTemporaryFile(max_size=1024*1024*100)
        if self._is_single_file:
            self._pack_single_file_to_stream(archive_tmp)
        else:
            self._pack_directory_to_stream(archive_tmp)
        archive_tmp.seek(0, os.SEEK_END)
        total_size = archive_tmp.tell()
        archive_tmp.seek(0)
        if self.volume_size > 0:
            self.volume_count = (total_size + self.volume_size - 1) // self.volume_size
        else:
            self.volume_size = (total_size + self.volume_count - 1) // self.volume_count
        self.has_extra = self.volume_count > 999
        if self.has_extra:
            warnings.warn(f"Volume count ({self.volume_count}) exceeds 999, remaining data will be written to .emp file")
        written = 0
        pbar = tqdm(total=total_size, desc="Writing volumes", unit="B", unit_scale=True,
                    disable=not self.show_progress)
        for vol_idx in range(self.volume_count):
            start = vol_idx * self.volume_size
            end = min(start + self.volume_size, total_size)
            chunk = archive_tmp.read(end - start)
            if vol_idx + 1 <= 999:
                vol_path = self._get_volume_path(output_base, vol_idx + 1)
            else:
                vol_path = f"{output_base}.emp"
            with open(vol_path, "wb") as fvol:
                if vol_idx == 0:
                    fvol.write(SPLIT_MAGIC)
                    fvol.write(struct.pack("!B", SPLIT_VERSION))
                    fvol.write(struct.pack("!Q", self.volume_size))
                    fvol.write(struct.pack("!I", self.volume_count))
                else:
                    magic = SPLIT_MAGIC if vol_idx + 1 <= 999 else EXTRA_MAGIC
                    fvol.write(magic)
                    fvol.write(struct.pack("!B", SPLIT_VERSION))
                fvol.write(chunk)
            written += len(chunk)
            pbar.update(len(chunk))
        pbar.close()
        archive_tmp.close()
        return self._get_volume_path(output_base, 1)

    def _get_volume_path(self, base: str, vol_num: int) -> str:
        if vol_num <= 9:
            return f"{base}.00{vol_num}.mpc"
        elif vol_num <= 999:
            return f"{base}.{vol_num:03d}.mpc"
        return f"{base}.emp"
    

class Unpacker:
    def __init__(self, filepath: str, password: str = "", show_progress: bool = True):
        """
        初始化解包器
        Args:
            filepath: 存档文件路径（可以是任意一个分卷）
            password: 解密密码
            show_progress: 是否显示进度条
        """
        self.original_path = filepath
        self.password = password
        self.show_progress = show_progress and TQDM_AVAILABLE
        self.is_split = False
        self.first_volume_path: Optional[str] = None
        self.total_volumes = 0
        self.volume_size = 0
        with open(filepath, "rb") as f:
            magic = f.read(3)
            if magic in (SPLIT_MAGIC, EXTRA_MAGIC):
                self.is_split = True
                self.first_volume_path = self._find_first_volume(filepath)
                if self.first_volume_path:
                    self._read_split_header(self.first_volume_path)
            else:
                f.seek(0)
                self.magic = f.read(3)
                if self.magic != b"MPC":
                    raise ValueError(f"Invalid magic: {self.magic}")
                self.mode = f.read(1)
                if self.mode not in (b'F', b'D', b'C', b'E'):
                    raise ValueError(f"Unknown mode: {self.mode}")

    def _find_first_volume(self, path: str) -> Optional[str]:
        if path.endswith('.001.mpc') and os.path.isfile(path):
            return path
        
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        
        parts = basename.rsplit('.', 1)
        if len(parts) == 2:
            ext = parts[1]
            if ext.endswith('mp') or ext in ('mpc', 'emp'):
                base = parts[0]
                first_candidate = os.path.join(dirname, f"{base}.001.mpc")
                if os.path.isfile(first_candidate):
                    return first_candidate
        
        if not dirname:
            dirname = '.'

        try:
            for f in os.listdir(dirname):
                if f.endswith('.001.mpc'):
                    return os.path.join(dirname, f)
        except OSError:
            return None
        
        return None

    def _read_split_header(self, first_path: str):
        with open(first_path, "rb") as f:
            magic = f.read(3)
            if magic != SPLIT_MAGIC:
                raise ValueError(f"Invalid split magic in {first_path}")
            version = struct.unpack("!B", f.read(1))[0]
            if version != SPLIT_VERSION:
                raise ValueError(f"Unsupported split version: {version}")
            self.volume_size = struct.unpack("!Q", f.read(8))[0]
            self.total_volumes = struct.unpack("!I", f.read(4))[0]

    def _verify_split_volumes(self) -> List[int]:
        missing = []
        dirname = os.path.dirname(self.first_volume_path)
        base = os.path.basename(self.first_volume_path)[:-4]
        for vol in range(1, self.total_volumes + 1):
            if vol == 1:
                continue
            elif vol <= 9:
                vol_path = os.path.join(dirname, f"{base}.00{vol}.mpc")
            elif vol <= 999:
                vol_path = os.path.join(dirname, f"{base}.{vol:03d}.mpc")
            else:
                vol_path = os.path.join(dirname, f"{base}.emp")
            if not os.path.exists(vol_path):
                missing.append(vol)
        return missing

    def _build_multi_reader(self) -> MultiVolumeReader:
        if not self.first_volume_path:
            raise FileNotFoundError("Missing starting volume")
        missing = self._verify_split_volumes()
        if missing:
            raise FileNotFoundError(f"Missing volumes: {self._format_missing_ranges(missing)}")
        dirname = os.path.dirname(self.first_volume_path)
        base = os.path.basename(self.first_volume_path)[:-4]
        return MultiVolumeReader(self.first_volume_path, self.total_volumes, self.volume_size, base, dirname)

    @staticmethod
    def _format_missing_ranges(missing: List[int]) -> str:
        if not missing:
            return ""
        missing.sort()
        ranges = []
        start = missing[0]
        end = missing[0]
        for i in range(1, len(missing)):
            if missing[i] == end + 1:
                end = missing[i]
            else:
                ranges.append(str(start) if start == end else f"{start}-{end}")
                start = missing[i]
                end = missing[i]
        ranges.append(str(start) if start == end else f"{start}-{end}")
        return ", ".join(ranges)

    def unpack(self, output: Optional[str] = None):
        """
        解包
        Args:
            output: 输出路径，单文件时默认使用原文件名，目录时默认 'extracted'
        Returns:
            单文件返回输出路径，目录返回提取文件列表
        """
        if self.is_split:
            reader = self._build_multi_reader()
            try:
                return self._unpack_from_stream(reader, output)
            finally:
                reader.close()
        else:
            with open(self.original_path, "rb") as f:
                f.seek(3)
                self.mode = f.read(1)
                f.seek(4)
                if self.mode in (b'F', b'C'):
                    return self._unpack_single(f, output)
                else:
                    return self._unpack_dir(f, output)

    def _unpack_from_stream(self, stream: BinaryIO, output: Optional[str] = None):
        """从流中解包（分卷合并流）"""
        magic = stream.read(3)
        if magic != b"MPC":
            raise ValueError(f"Invalid inner magic: {magic}")
        mode = stream.read(1)
        if mode in (b'F', b'C'):
            return self._unpack_single_entry(stream, output)
        else:
            return self._unpack_multi_entries(stream, output)

    def _unpack_single(self, f: BinaryIO, output: Optional[str] = None):
        return self._unpack_single_entry(f, output)

    def _unpack_dir(self, f: BinaryIO, output: Optional[str] = None):
        return self._unpack_multi_entries(f, output)

    def _unpack_single_entry(self, stream: BinaryIO, output: Optional[str] = None):
        """读取并解包一个文件条目（已跳过魔数和模式）"""
        name_len = struct.unpack("!I", stream.read(4))[0]
        data_len = struct.unpack("!I", stream.read(4))[0]
        name = stream.read(name_len).decode("utf-8")
        encrypted, compressed, algo_id, raw_len = self._read_metadata(stream)
        if output is None:
            output = name
        self._extract_entry(stream, data_len, encrypted, compressed, algo_id, raw_len, output)
        return output

    def _unpack_multi_entries(self, stream: BinaryIO, output: Optional[str] = None):
        """读取并解包多个文件条目（已跳过魔数和模式，接下来是 file_count）"""
        file_count = struct.unpack("!I", stream.read(4))[0]
        if output is None:
            output = "extracted"
        extracted = []
        iter_range = tqdm(range(file_count), desc="Extracting files", unit="file",
                          disable=not self.show_progress) if self.show_progress else range(file_count)
        for _ in iter_range:
            name_len = struct.unpack("!I", stream.read(4))[0]
            data_len = struct.unpack("!I", stream.read(4))[0]
            name = stream.read(name_len).decode("utf-8")
            if os.path.isabs(name) or ".." in name.split("/"):
                raise ValueError(f"Path traversal detected: {name}")
            encrypted, compressed, algo_id, raw_len = self._read_metadata(stream)
            target = os.path.join(output, name)
            self._extract_entry(stream, data_len, encrypted, compressed, algo_id, raw_len, target)
            extracted.append(target)
        return extracted

    def _read_metadata(self, stream: BinaryIO) -> Tuple[bool, bool, int, int]:
        flags = struct.unpack("!B", stream.read(1))[0]
        encrypted = bool(flags & 1)
        compressed = bool(flags & 2)
        algo_id = 0
        if compressed:
            algo_id = struct.unpack("!B", stream.read(1))[0]
        raw_len = 0
        if compressed or encrypted:
            raw_len = struct.unpack("!Q", stream.read(8))[0]
        return encrypted, compressed, algo_id, raw_len

    def _extract_entry(self, stream: BinaryIO, data_len: int, encrypted: bool,
                       compressed: bool, algo_id: int, raw_len: int, output_path: str):
        """
        流式提取一个条目到 output_path
        利用 LimitedReader 避免一次性读取数据块，临时文件用于解密中间结果
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        if not encrypted and not compressed:
            with open(output_path, 'wb') as out:
                remain = data_len
                while remain > 0:
                    chunk = stream.read(min(1024 * 1024, remain))
                    if not chunk:
                        break
                    out.write(chunk)
                    remain -= len(chunk)
            return
        if encrypted:
            tmp_dec = _decrypt_stream_to_temp(stream, data_len, self.password)
            try:
                if compressed:
                    with open(output_path, 'wb') as out:
                        Compressor.decompress_stream(algo_id, tmp_dec, out, raw_len)
                else:
                    with open(output_path, 'wb') as out:
                        while True:
                            chunk = tmp_dec.read(1024 * 1024)
                            if not chunk:
                                break
                            out.write(chunk)
            finally:
                tmp_dec.close()
        else:
            with open(output_path, 'wb') as out:
                limited = LimitedReader(stream, data_len)
                Compressor.decompress_stream(algo_id, limited, out, raw_len)

    def unpack_file(self, output: Optional[str] = None):
        """解包单文件（兼容旧接口）"""
        return self.unpack(output)

    def unpack_dir(self, output: Optional[str] = None):
        """解包目录（兼容旧接口）"""
        return self.unpack(output)

class Lister:
    def __init__(self, filepath: str, show_progress: bool = True):
        """
        列出存档内容
        Args:
            filepath: 存档文件路径
            show_progress: 是否显示进度条
        """
        self.filepath = filepath
        self.show_progress = show_progress and TQDM_AVAILABLE
        self.files: List[Dict] = []
        self.is_split = False
        self.missing_volumes: List[int] = []
        self.volume_size = 0
        self.total_volumes = 0
        
        with open(filepath, "rb") as f:
            magic = f.read(3)
            if magic in (SPLIT_MAGIC, EXTRA_MAGIC):
                self.is_split = True
                first_vol = self._find_first_volume(filepath)
                if not first_vol:
                    raise FileNotFoundError(f"Missing starting volume: .001.mpc")
                self._load_split_archive(first_vol)
            else:
                f.seek(0)
                self._load_normal_archive(f)

    def _find_first_volume(self, path: str) -> Optional[str]:
        if path.endswith('.001.mpc') and os.path.isfile(path):
            return path
        
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        
        parts = basename.rsplit('.', 1)
        if len(parts) == 2:
            ext = parts[1]
            if ext in ('mpc', 'emp'):
                base = parts[0]
                first_candidate = os.path.join(dirname, f"{base}.001.mpc")
                if os.path.isfile(first_candidate):
                    return first_candidate
        
        if not dirname:
            dirname = '.'

        try:
            for f in os.listdir(dirname):
                if f.endswith('.001.mpc'):
                    return os.path.join(dirname, f)
        except OSError:
            return None
        
        return None

    def _load_split_archive(self, first_vol: str):
        """加载分卷存档，直接读取元数据，不依赖 Unpacker"""
        # 读取分卷头信息
        with open(first_vol, "rb") as f:
            magic = f.read(3)
            if magic != SPLIT_MAGIC:
                raise ValueError(f"Invalid split magic in {first_vol}")
            version = struct.unpack("!B", f.read(1))[0]
            if version != SPLIT_VERSION:
                raise ValueError(f"Unsupported split version: {version}")
            self.volume_size = struct.unpack("!Q", f.read(8))[0]
            self.total_volumes = struct.unpack("!I", f.read(4))[0]
        
        # 检查分卷完整性
        self.missing_volumes = self._check_volumes(first_vol, self.total_volumes)
        if self.missing_volumes:
            return
        
        # 直接构建 MultiVolumeReader，不经过 Unpacker
        dirname = os.path.dirname(first_vol)
        base = os.path.basename(first_vol)[:-4]
        reader = MultiVolumeReader(first_vol, self.total_volumes, self.volume_size, base, dirname)
        try:
            self._parse_entries(reader)
        finally:
            reader.close()

    def _check_volumes(self, first_vol: str, total: int) -> List[int]:
        missing = []
        dirname = os.path.dirname(first_vol)
        base = os.path.basename(first_vol)[:-4]
        for vol in range(1, total + 1):
            if vol == 1:
                continue
            if vol <= 9:
                path = os.path.join(dirname, f"{base}.00{vol}.mpc")
            elif vol <= 999:
                path = os.path.join(dirname, f"{base}.{vol:03d}.mpc")
            else:
                path = os.path.join(dirname, f"{base}.emp")
            if not os.path.exists(path):
                missing.append(vol)
        return missing

    def _load_normal_archive(self, f: BinaryIO):
        magic = f.read(3)
        if magic != b"MPC":
            raise ValueError(f"Invalid magic: {magic}")
        mode = f.read(1)
        if mode in (b'F', b'C'):
            self._add_entry(f)
        else:
            self._parse_entries(f)

    def _parse_entries(self, stream: BinaryIO):
        """从流中读取所有条目信息（跳过魔数和模式）"""
        try:
            file_count = struct.unpack("!I", stream.read(4))[0]
        except Exception:
            # 可能是单文件模式，只有一个条目没有 file_count
            self._add_entry(stream)
            return
        
        iter_range = tqdm(range(file_count), desc="Reading file list", unit="file",
                          disable=not self.show_progress) if self.show_progress else range(file_count)
        for _ in iter_range:
            self._add_entry(stream)

    def _add_entry(self, stream: BinaryIO):
        name_len = struct.unpack("!I", stream.read(4))[0]
        data_len = struct.unpack("!I", stream.read(4))[0]
        name = stream.read(name_len).decode("utf-8")
        flags = struct.unpack("!B", stream.read(1))[0]
        encrypted = bool(flags & 1)
        compressed = bool(flags & 2)
        algo_id = 0
        if compressed:
            algo_id = struct.unpack("!B", stream.read(1))[0]
        raw_size = 0
        if compressed or encrypted:
            raw_size = struct.unpack("!Q", stream.read(8))[0]
        stream.read(data_len)  # 跳过数据块
        
        algo_name = Compressor.get(algo_id).name if compressed else "none"
        self.files.append({
            "name": name,
            "size": raw_size if (compressed or encrypted) else data_len,
            "compressed_size": data_len,
            "compression": algo_name,
            "encrypted": encrypted,
        })

    def list(self) -> List[Dict]:
        """返回文件列表"""
        return self.files

    def print(self):
        """打印可读列表"""
        if self.missing_volumes:
            missing_str = Unpacker._format_missing_ranges(self.missing_volumes)
            print(f"[WARNING] Missing volumes: {missing_str}")
            print()
        if not self.files:
            print("(empty)")
            return
        
        max_name = max(len(f["name"]) for f in self.files)
        max_size = max(len(self._format_size(f["size"])) for f in self.files)
        print(f"{'Name':<{max_name}}  {'Size':>{max_size}}  {'Compressed':>{max_size}}  {'Ratio':>6}  {'Algo':>6}  {'Encrypted':>9}")
        print("-" * (max_name + max_size * 2 + 6 + 6 + 9 + 10))
        
        total_size = 0
        total_compressed = 0
        for f in self.files:
            name = f["name"]
            size_str = self._format_size(f["size"])
            comp_str = self._format_size(f["compressed_size"])
            ratio = f["compressed_size"] / f["size"] * 100 if f["size"] > 0 else 100
            algo = f["compression"]
            enc = "✓" if f["encrypted"] else "✗"
            print(f"{name:<{max_name}}  {size_str:>{max_size}}  {comp_str:>{max_size}}  {ratio:5.1f}%  {algo:>6}  {enc:>9}")
            total_size += f["size"]
            total_compressed += f["compressed_size"]
        
        print("-" * (max_name + max_size * 2 + 6 + 6 + 9 + 10))
        total_ratio = total_compressed / total_size * 100 if total_size > 0 else 100
        print(f"{'TOTAL':<{max_name}}  {self._format_size(total_size):>{max_size}}  {self._format_size(total_compressed):>{max_size}}  {total_ratio:5.1f}%")

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / 1024 / 1024:.1f} MB"
        else:
            return f"{size / 1024 / 1024 / 1024:.1f} GB"

def get_available_algorithms() -> Dict[str, int]:
    """返回可用压缩算法"""
    return Compressor.list_algorithms()