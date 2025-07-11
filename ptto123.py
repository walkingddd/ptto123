import os
import time
import hashlib
from p123client import P123Client  # 导入123网盘客户端
from filewrap import SupportsRead  # 从原依赖导入必要类
from hashtools import file_digest  # 用于高效计算MD5

# ======================== 环境变量配置（优先读取，无则用默认值） ========================
try:
    # 123网盘账号密码（从环境变量获取）
    PASSPORT = os.getenv("ENV_123_PASSPORT", "0")
    PASSWORD = os.getenv("ENV_123_PASSWORD", "0")
    # 上传目标目录ID（整数）
    UPLOAD_TARGET_PID = int(os.getenv("ENV_123_UPLOAD_PID", "0"))

except ValueError as e:
    print(f"环境变量格式错误：{e}，将使用默认配置")
    PASSPORT = ""
    PASSWORD = ""
    UPLOAD_TARGET_PID = 0

# ======================== 其他固定配置 ========================
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "upload")  # 待上传目录
SLEEP_AFTER_FILE = 10  # 单个文件处理后休眠（秒）
SLEEP_AFTER_ROUND = 60  # 一轮遍历后休眠（秒）

# ======================== 工具函数 ========================
def check_file_size_stability(file_path, check_interval=30, max_attempts=1000):
    """检查文件大小稳定性，防止文件不完整"""
    for attempt in range(max_attempts):
        size1 = os.path.getsize(file_path)
        time.sleep(check_interval)
        size2 = os.path.getsize(file_path)
        if size1 == size2:
            print(f"[信息] 文件大小稳定：{file_path}")
            return True
        print(f"[警告] 文件大小不稳定，第 {attempt + 1} 次检查：{file_path}")
    print(f"[错误] 文件大小不稳定，放弃上传：{file_path}")
    return False

def fast_md5(file_path: str) -> str:
    """快速计算文件MD5（分块读取，适用于大文件）"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # 64KB分块读取，平衡速度和内存占用
        for chunk in iter(lambda: f.read(65536), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def init_123_client():
    """初始化123网盘客户端（账号密码认证）"""
    try:
        client = P123Client(passport=PASSPORT, password=PASSWORD)
        print("[信息] 123客户端初始化成功（账号密码有效）")
        return client
    except Exception as e:
        print(f"[错误] 123客户端初始化失败（检查账号密码是否有效）：{e}")
        raise

# ======================== 核心逻辑 ========================
def main():
    cache = {}  # 内存缓存：{文件绝对路径: MD5}
    client = init_123_client()
    last_delete_time = time.time()

    while True:
        print("[信息] 开始遍历待上传目录...")
        # 遍历upload目录文件
        for root, _, files in os.walk(UPLOAD_DIR):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_key = file_path

                print(f"[信息] 正在检查文件 {file_path} 的大小稳定性...")
                # 检查文件大小稳定性
                if not check_file_size_stability(file_path):
                    continue

                # 获取文件大小
                try:
                    filesize = os.path.getsize(file_path)
                    print(f"[信息] 获取到文件 {file_path} 的大小为 {filesize} 字节")
                except FileNotFoundError:
                    print(f"[信息] 文件已删除：{file_path}")
                    if file_key in cache:
                        del cache[file_key]
                    continue

                # 计算并缓存MD5（优先使用缓存）
                cached_md5 = cache.get(file_key)
                if cached_md5:
                    print(f"[信息] 使用缓存的MD5值：{file_path} → {cached_md5}")
                else:
                    print(f"[信息] 计算文件MD5：{file_path}")
                    cached_md5 = fast_md5(file_path)
                    cache[file_key] = cached_md5
                    print(f"[信息] 已缓存文件MD5：{file_path} → {cached_md5}")

                # 调用123网盘秒传接口
                try:
                    print(f"[信息] 开始上传文件：{file_path}")
                    upload_result = client.upload_file_fast(
                        file=file_path,
                        file_md5=cached_md5,
                        file_name=filename,
                        file_size=filesize,
                        parent_id=UPLOAD_TARGET_PID,
                        duplicate=2,  # 覆盖同名文件
                        async_=False
                    )

                    # 检查秒传结果（123网盘接口成功标识：code=0且reuse=True）
                    if upload_result.get("code") == 0 and upload_result["data"].get("Reuse"):
                        print(f"[成功] 秒传成功：{file_path}（文件ID：{upload_result['data']['Info']['FileId']}）")
                        os.remove(file_path)
                        print(f"[信息] 已删除本地文件：{file_path}")
                        if file_key in cache:
                            del cache[file_key]
                    else:
                        print(f"[失败] 秒传未成功：{file_path}，响应：{upload_result}")
                except Exception as e:
                    print(f"[错误] 上传失败：{file_path} → {e}")

                time.sleep(SLEEP_AFTER_FILE)

        # 一轮遍历结束后休眠
        print(f"[信息] 一轮遍历完成，休眠 {SLEEP_AFTER_ROUND} 秒...")
        time.sleep(SLEEP_AFTER_ROUND)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[信息] 用户终止程序")
    except Exception as e:
        print(f"[错误] 程序异常：{e}")