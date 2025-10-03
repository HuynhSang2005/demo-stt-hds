"""
Vietnamese bad words detection utilities
Detects toxic/inappropriate words in Vietnamese text
"""

import re
from typing import List, Set

# Vietnamese bad words list (sample - add more as needed)
# IMPORTANT: Removed standalone neutral words to avoid false positives
# - "thằng" alone is neutral (like "he/that guy"), only toxic when combined (e.g., "thằng ngu")
# - "khốn" removed due to tone confusion with "khôn" (smart)
VIETNAMESE_BAD_WORDS = {
    # Common toxic words
    "đồ chó", "con chó", "súc vật", "con điên", "khùng", 
    "đần", "ngu", "đâm", "giết", "chết", "tử", "địt", "đụ", 
    "cặc", "lồn", "buồi", "đĩ", "cave", "gái điếm", "con đĩ",
    "óc chó", "não chó", "đầu óc", "não cá vàng", "đầu tôm",
    "chửi", "bậy", "tệ", "dở", "dớ", "xấu xa", "đáng ghét",
    "khốn nạn", "đồ khốn", "con khốn", "tồi tệ",  # Removed standalone "khốn" 
    "độc ác", "xấu tính", "ác độc", "đê tiện", "hèn hạ",
    "phản bội", "lừa dối", "gian lận", "lúc lưỡi", "xảo quyệt",
    
    # Insulting terms
    "thằng ngu", "con ngu", "đồ ngu", "ngu ngốc", "ngu si",
    "đần độn", "đầu bò", "đầu gỗ", "não tôm", "não udang",
    "con heo", "đồ heo", "thằng heo", "con lợn", "đồ lợn",
    "thằng chó", "đồ chó", "con chó", "súc vật", "thú vật",
    
    # Threats and violence
    "đánh", "đập", "choảng", "tát", "đấm", "đá", "ném",
    "giết chết", "giết", "chết", "tử vong", "sát hại",
    "đâm chết", "đâm", "chém", "cắt", "xẻo", "thịt",
    
    # Political sensitive (if needed)
    "độc tài", "phản động", "phản quốc", "bán nước",
    "tham nhũng", "tham ô", "đê hèn", "bội bạc"
}

def preprocess_text_for_detection(text: str) -> str:
    """
    Preprocess text for bad word detection
    IMPORTANT: Preserves Vietnamese tones for accurate matching
    - Remove extra spaces
    - Remove special characters that might hide bad words
    - NO lowercase to preserve tone marks (khôn ≠ khốn)
    """
    # DO NOT lowercase - preserves Vietnamese tone distinctions
    # (khôn = smart, khốn = bad; thẳng = straight, thằng = guy)
    
    # Remove common obfuscation characters
    text = text.replace("*", "").replace("-", "").replace("_", "")
    text = text.replace("@", "a").replace("3", "e").replace("0", "o")
    text = text.replace("1", "i").replace("5", "s").replace("4", "a")
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_bad_words(text: str) -> List[str]:
    """
    Detect bad words in Vietnamese text with tone-aware matching
    
    Args:
        text: Input Vietnamese text
        
    Returns:
        List of detected bad words
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # Preprocess text (preserves tones)
    processed_text = preprocess_text_for_detection(text)
    print(f"[Bad Words] Processing text: '{text}' -> '{processed_text}'")
    
    detected_words = []
    
    # Check each bad word with case-insensitive + word boundary matching
    for bad_word in VIETNAMESE_BAD_WORDS:
        # Use regex with word boundaries for accurate matching
        # Case-insensitive but tone-sensitive (preserves Vietnamese diacritics)
        pattern = r'\b' + re.escape(bad_word) + r'\b'
        if re.search(pattern, processed_text, re.IGNORECASE):
            detected_words.append(bad_word)
            print(f"[Bad Words] Detected: '{bad_word}' in '{processed_text}'")
    
    # Remove duplicates and return
    result = list(set(detected_words))
    print(f"[Bad Words] Final detected words: {result}")
    return result

def is_text_toxic(text: str) -> bool:
    """
    Check if text contains toxic content
    
    Args:
        text: Input Vietnamese text
        
    Returns:
        True if text contains bad words, False otherwise
    """
    bad_words = detect_bad_words(text)
    return len(bad_words) > 0

def get_toxicity_score(text: str) -> float:
    """
    Get toxicity score based on bad words count
    
    Args:
        text: Input Vietnamese text
        
    Returns:
        Toxicity score between 0.0 (clean) and 1.0 (very toxic)
    """
    if not text or len(text.strip()) == 0:
        return 0.0
    
    bad_words = detect_bad_words(text)
    word_count = len(text.split())
    
    if word_count == 0:
        return 0.0
    
    # Simple scoring: ratio of bad words to total words
    ratio = len(bad_words) / word_count
    
    # Cap at 1.0 and apply some scaling
    return min(1.0, ratio * 2.0)