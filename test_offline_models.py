#!/usr/bin/env python3
"""
Script kiểm tra load model offline - Prompt 1.2
Mục tiêu: Đảm bảo cả Wav2Vec2 và PhoBERT đều load được với local_files_only=True
"""

import os
import sys
from pathlib import Path

def test_offline_model_loading():
    """
    Test load model offline theo yêu cầu Prompt 1.2
    """
    
    print("🔧 KIỂM TRA LOAD MODEL OFFLINE - Prompt 1.2")
    print("=" * 60)
    
    # Kiểm tra thư mục model tồn tại
    wav2vec2_path = "./wav2vec2-base-vietnamese-250h"
    phobert_path = "./phobert-vi-comment-4class"
    
    if not os.path.exists(wav2vec2_path):
        print(f"❌ Không tìm thấy folder: {wav2vec2_path}")
        return False
        
    if not os.path.exists(phobert_path):
        print(f"❌ Không tìm thấy folder: {phobert_path}")
        return False
    
    print(f"✅ Tìm thấy cả 2 folder model")
    
    # Test 1: Load Wav2Vec2 Processor và Model
    print("\n🎤 TEST 1: Wav2Vec2 ASR Model")
    print("-" * 40)
    
    try:
        from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
        
        print(f"🔄 Đang load Wav2Vec2Processor từ {wav2vec2_path}...")
        processor = Wav2Vec2Processor.from_pretrained(
            wav2vec2_path, 
            local_files_only=True
        )
        print("✅ Wav2Vec2Processor load thành công!")
        
        print(f"🔄 Đang load Wav2Vec2ForCTC từ {wav2vec2_path}...")
        model = Wav2Vec2ForCTC.from_pretrained(
            wav2vec2_path,
            local_files_only=True
        )
        print("✅ Wav2Vec2ForCTC model load thành công!")
        
        # Thông tin model
        print(f"📊 Model info:")
        print(f"   - Vocab size: {processor.tokenizer.vocab_size}")
        print(f"   - Model parameters: {sum(p.numel() for p in model.parameters()):,}")
        
    except Exception as e:
        print(f"❌ Lỗi load Wav2Vec2: {e}")
        return False
    
    # Test 2: Load PhoBERT Classification Pipeline  
    print("\n🔍 TEST 2: PhoBERT Classification Model")
    print("-" * 40)
    
    try:
        from transformers import pipeline
        import json
        
        print(f"🔄 Đang load PhoBERT pipeline từ {phobert_path}...")
        classifier = pipeline(
            'text-classification', 
            model=phobert_path,
            tokenizer=phobert_path,
            local_files_only=True
        )
        print("✅ PhoBERT classifier load thành công!")
        
        # Label mapping đã được xác định qua phân tích
        label_mapping = {
            "LABEL_0": "positive",
            "LABEL_1": "negative", 
            "LABEL_2": "neutral",
            "LABEL_3": "toxic"
        }
        
        # Test inference với text mẫu
        print("🧪 Test inference với label mapping chính xác...")
        test_texts = [
            ("Xin chào", "positive/neutral"),
            ("Đồ ngốc", "toxic"), 
            ("Bình thường", "neutral"),
            ("Tuyệt vời!", "positive"),
            ("Tệ quá", "negative")
        ]
        
        for text, expected in test_texts:
            result = classifier(text)
            raw_label = result[0]['label']
            mapped_label = label_mapping.get(raw_label, raw_label)
            score = result[0]['score']
            print(f"   Text: '{text}' → {mapped_label} (raw: {raw_label}, score: {score:.3f})")
            
    except Exception as e:
        print(f"❌ Lỗi load PhoBERT: {e}")
        return False
    
    # Kết quả cuối cùng
    print("\n" + "=" * 60)
    print("✅ TẤT CẢ MODEL LOAD THÀNH CÔNG OFFLINE!")
    print("✅ Sẵn sàng cho GIAI ĐOẠN 2: BACKEND – OFFLINE INFERENCE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_offline_model_loading()
    if not success:
        sys.exit(1)