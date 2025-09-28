#!/usr/bin/env python3
"""
Script kiểm tra label mapping cho PhoBERT - Cập nhật Prompt 1.2
"""

from transformers import pipeline
import json

def test_phobert_label_mapping():
    """
    Test PhoBERT để tìm ra mapping chính xác giữa LABEL_0/1/2/3 và positive/negative/neutral/toxic
    """
    
    print("🔍 KIỂM TRA LABEL MAPPING CHO PHOBERT")
    print("=" * 60)
    
    # Load model
    classifier = pipeline(
        'text-classification', 
        model="./phobert-vi-comment-4class",
        tokenizer="./phobert-vi-comment-4class",
        local_files_only=True
    )
    
    # Theo README: positive, negative, neutral, toxic
    # Cần tìm xem LABEL_0/1/2/3 tương ứng với label nào
    
    print("📋 Test với các câu rõ ràng để tìm mapping:")
    
    test_cases = [
        # Positive examples
        ("Tuyệt vời quá!", "positive"),
        ("Video này hay lắm!", "positive"), 
        ("Cảm ơn bạn nhiều!", "positive"),
        
        # Negative examples  
        ("Tệ quá", "negative"),
        ("Không hay", "negative"),
        ("Chán lắm", "negative"),
        
        # Neutral examples
        ("Được", "neutral"),
        ("Bình thường", "neutral"),
        ("Ok", "neutral"),
        
        # Toxic examples
        ("Đồ ngốc", "toxic"),
        ("Ngu quá", "toxic"), 
        ("Thằng khùa", "toxic"),
    ]
    
    # Collect results
    label_results = {"LABEL_0": [], "LABEL_1": [], "LABEL_2": [], "LABEL_3": []}
    
    for text, expected_type in test_cases:
        result = classifier(text)
        predicted_label = result[0]['label']
        score = result[0]['score']
        
        print(f"Text: '{text}' (expected: {expected_type})")
        print(f"   → {predicted_label} (score: {score:.3f})")
        
        label_results[predicted_label].append((text, expected_type, score))
    
    print("\n" + "=" * 60)
    print("📊 PHÂN TÍCH MAPPING LABELS:")
    print("=" * 60)
    
    # Analyze patterns
    for label_num in ["LABEL_0", "LABEL_1", "LABEL_2", "LABEL_3"]:
        if label_results[label_num]:
            print(f"\n🏷️  {label_num}:")
            expected_types = [item[1] for item in label_results[label_num]]
            most_common = max(set(expected_types), key=expected_types.count)
            confidence = expected_types.count(most_common) / len(expected_types)
            
            print(f"   Có thể là: {most_common} (confidence: {confidence:.1%})")
            print(f"   Examples:")
            for text, exp_type, score in label_results[label_num][:3]:
                print(f"      - '{text}' (expected: {exp_type}, score: {score:.3f})")
    
    # Suggested mapping
    print(f"\n🎯 ĐỀ XUẤT LABEL MAPPING:")
    print(f"Based on analysis above:")
    
    # We need to determine the actual mapping from the results
    suggested_mapping = {}
    for label_num in ["LABEL_0", "LABEL_1", "LABEL_2", "LABEL_3"]:
        if label_results[label_num]:
            expected_types = [item[1] for item in label_results[label_num]]
            most_common = max(set(expected_types), key=expected_types.count)
            suggested_mapping[label_num] = most_common
    
    for label_num, meaning in suggested_mapping.items():
        print(f"   {label_num} → {meaning}")
    
    return suggested_mapping

if __name__ == "__main__":
    mapping = test_phobert_label_mapping()
    
    # Save mapping to JSON file for later use
    with open("phobert_label_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Label mapping đã lưu vào phobert_label_mapping.json")
    print(f"🎯 Sử dụng mapping này cho implementation thực tế!")