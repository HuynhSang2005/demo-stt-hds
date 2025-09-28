#!/usr/bin/env python3
"""
Script để download model từ Hugging Face về local
"""

import os
from huggingface_hub import snapshot_download

def download_models():
    """Download các model cần thiết về local folders"""
    
    # Tạo thư mục models nếu chưa có
    os.makedirs("models", exist_ok=True)
    
    print("🔄 Đang download wav2vec2-base-vietnamese-250h...")
    try:
        snapshot_download(
            repo_id="nguyenvulebinh/wav2vec2-base-vietnamese-250h",
            local_dir="./wav2vec2-base-vietnamese-250h",
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print("✅ wav2vec2-base-vietnamese-250h downloaded successfully!")
    except Exception as e:
        print(f"❌ Error downloading wav2vec2: {e}")
    
    print("\n🔄 Đang download phobert-vi-comment-4class...")
    try:
        snapshot_download(
            repo_id="vanhai123/phobert-vi-comment-4class", 
            local_dir="./phobert-vi-comment-4class",
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print("✅ phobert-vi-comment-4class downloaded successfully!")
    except Exception as e:
        print(f"❌ Error downloading phobert: {e}")

if __name__ == "__main__":
    download_models()
    print("\n🎉 Hoàn thành download models!")