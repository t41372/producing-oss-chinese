import os
import glob
import tiktoken

def count_tokens_in_file(file_path):
    """计算单个文件的 token 数量"""
    # 使用 cl100k_base 编码 (适用于 GPT-4, GPT-3.5)
    enc = tiktoken.get_encoding("cl100k_base")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        return len(enc.encode(text))

def process_directory(directory_path):
    """遍历目录下的 xml 文件并打印 token 数量"""
    print(f"--- Processing {directory_path} ---")
    # 获取所有 .xml 文件
    xml_files = glob.glob(os.path.join(directory_path, "*.xml"))
    xml_files.sort()
    
    total_tokens = 0
    for file_path in xml_files:
        try:
            count = count_tokens_in_file(file_path)
            print(f"{os.path.basename(file_path)}: {count}")
            total_tokens += count
        except Exception as e:
            print(f"Error reading {os.path.basename(file_path)}: {e}")
    
    print(f"Total: {total_tokens}\n")

def main():
    # 定义要检查的目录
    base_dir = os.getcwd()
    dirs = [
        os.path.join(base_dir, "book", "en"),
        os.path.join(base_dir, "book", "zh")
    ]
    
    for d in dirs:
        if os.path.exists(d):
            process_directory(d)
        else:
            print(f"Directory not found: {d}")

if __name__ == "__main__":
    main()
