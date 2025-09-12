import os
import hashlib

# 해시 계산 함수
def get_file_hashes(file_path):
    hashes = {"MD5": None, "SHA1": None, "SHA256": None}
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            hashes["MD5"] = hashlib.md5(data).hexdigest()
            hashes["SHA1"] = hashlib.sha1(data).hexdigest()
            hashes["SHA256"] = hashlib.sha256(data).hexdigest()
    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
    return hashes

# 메인 실행
def main(folder_path, output_file="hash_results.txt"):
    results = []
    with open(output_file, "w", encoding="utf-8") as out:
        header = "File Path\tMD5\tSHA1\tSHA256\n"
        out.write(header)

        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                hashes = get_file_hashes(full_path)
                line = f"{full_path}\t{hashes['MD5']}\t{hashes['SHA1']}\t{hashes['SHA256']}\n"
                out.write(line)
                results.append((full_path, hashes))

    print(f"✅ 해시 계산 완료! 결과 저장: {os.path.abspath(output_file)}")
    return results

if __name__ == "__main__":
    # 여기 경로를 네가 확인하려는 폴더 경로로 바꿔줘
    target_folder = r"C:\Users\User\Desktop\miniproject"
    main(target_folder)
