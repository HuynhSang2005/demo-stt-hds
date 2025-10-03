#!/usr/bin/env python3
"""
Script để download model từ Hugging Face về local
Updated: Switched from Wav2Vec2 to PhoWhisper for better accuracy
"""

import os
from huggingface_hub import snapshot_download

def download_models():
    """Download các model cần thiết về local folders"""
    
    # Tạo thư mục models nếu chưa có
    os.makedirs("models", exist_ok=True)
    
    # Model 1: PhoWhisper-base (Speech-to-Text)
    # Thay thế wav2vec2-base-vietnamese-250h
    # Ưu điểm: WER 5.28% vs 8.66%, auto punctuation, unlimited audio length
    phowhisper_path = "./PhoWhisper-base"
    print("🔄 Checking PhoWhisper-base (Speech-to-Text)...")
    if os.path.exists(phowhisper_path) and os.path.isdir(phowhisper_path):
        # Kiểm tra xem có đầy đủ files cần thiết không
        required_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
        has_all_files = all(
            os.path.exists(os.path.join(phowhisper_path, f)) 
            for f in required_files
        )
        if has_all_files:
            print(f"✅ PhoWhisper-base đã tồn tại tại {phowhisper_path}, skip download!")
        else:
            print(f"⚠️ PhoWhisper-base chưa đầy đủ files, downloading...")
            try:
                snapshot_download(
                    repo_id="vinai/PhoWhisper-base",
                    local_dir=phowhisper_path,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                print("✅ PhoWhisper-base downloaded successfully!")
            except Exception as e:
                print(f"❌ Error downloading PhoWhisper: {e}")
    else:
        print(f"📥 Downloading PhoWhisper-base from HuggingFace...")
        try:
            snapshot_download(
                repo_id="vinai/PhoWhisper-base",
                local_dir=phowhisper_path,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            print("✅ PhoWhisper-base downloaded successfully!")
        except Exception as e:
            print(f"❌ Error downloading PhoWhisper: {e}")
    
    # Model 2: PhoBERT (Sentiment Classification)
    phobert_path = "./phobert-vi-comment-4class"
    print("\n🔄 Checking phobert-vi-comment-4class (Sentiment Analysis)...")
    if os.path.exists(phobert_path) and os.path.isdir(phobert_path):
        # Kiểm tra xem có đầy đủ files cần thiết không
        required_files = ["config.json", "model.safetensors", "tokenizer_config.json"]
        has_all_files = all(
            os.path.exists(os.path.join(phobert_path, f)) 
            for f in required_files
        )
        if has_all_files:
            print(f"✅ phobert-vi-comment-4class đã tồn tại tại {phobert_path}, skip download!")
        else:
            print(f"⚠️ phobert-vi-comment-4class chưa đầy đủ files, downloading...")
            try:
                snapshot_download(
                    repo_id="vanhai123/phobert-vi-comment-4class", 
                    local_dir=phobert_path,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                print("✅ phobert-vi-comment-4class downloaded successfully!")
            except Exception as e:
                print(f"❌ Error downloading phobert: {e}")
    else:
        print(f"📥 Downloading phobert-vi-comment-4class from HuggingFace...")
        try:
            snapshot_download(
                repo_id="vanhai123/phobert-vi-comment-4class", 
                local_dir=phobert_path,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            print("✅ phobert-vi-comment-4class downloaded successfully!")
        except Exception as e:
            print(f"❌ Error downloading phobert: {e}")

if __name__ == "__main__":
    download_models()
    print("\n🎉 Hoàn thành download models!")