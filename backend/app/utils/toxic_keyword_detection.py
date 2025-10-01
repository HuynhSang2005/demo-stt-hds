#!/usr/bin/env python3
"""
Toxic Keyword Detection Module
Task 11: Ensemble keyword matching for improved classification precision

Features:
- Vietnamese toxic keyword dictionary
- Fuzzy matching for common misspellings
- Context-aware scoring
- Confidence boosting for keyword matches
- Bad word pattern detection
"""

import re
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass

@dataclass
class KeywordMatch:
    """Result of keyword matching"""
    keyword: str
    position: int
    context: str  # Surrounding text
    severity: str  # 'high', 'medium', 'low'
    confidence: float


class VietnameseToxicKeywordDetector:
    """
    Vietnamese toxic keyword detection with fuzzy matching
    Task 11: Improve classification precision with keyword ensemble
    """
    
    # Vietnamese toxic keywords categorized by severity
    TOXIC_KEYWORDS_HIGH = {
        # Explicit profanity (high severity)
        'địt', 'đụ', 'lồn', 'cặc', 'buồi', 'đéo', 'đệch',
        'dm', 'đm', 'vl', 'vcl', 'clgt', 'dmm', 'đkm',
        'thằng chó', 'con chó', 'đồ chó', 'súc vật',
        'đồ ngu', 'ngu si', 'đần độn', 'thằng ngu',
    }
    
    TOXIC_KEYWORDS_MEDIUM = {
        # Offensive but less explicit
        'ngứa', 'rẻ rách', 'thấp hèn', 'đê tiện',
        'khốn nạn', 'đồ khốn', 'đồ bẩn', 'đồ rác',
        'khốn', 'thằng khốn', 'con khốn',
        'kém cỏi', 'vô dụng', 'vô giátrị', 'bất tài',
        'xấu xa', 'độc ác', 'ác độc', 'tệ hại',
    }
    
    TOXIC_KEYWORDS_LOW = {
        # Mildly offensive
        'ngu ngốc', 'ngu xuẩn', 'dở hơi', 'điên khùng',
        'khùng điên', 'mất dạy', 'vô học', 'dốt nát',
        'tồi tệ', 'tệ hại', 'thảm hại', 'phá hoại',
    }
    
    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = {
        'ghét', 'căm ghét', 'thù hận', 'oán hận',
        'chán nản', 'thất vọng', 'buồn bã', 'đau khổ',
        'khổ sở', 'tức giận', 'phẫn nộ', 'tức tối',
        'chán', 'buồn', 'tệ', 'xấu', 'kém',
    }
    
    # Common Vietnamese profanity patterns (for regex matching)
    TOXIC_PATTERNS = [
        r'\b(đ[íi]t|đ[ụu])\b',
        r'\b(l[ồo]n|c[ặa]c)\b',
        r'\b(đ[éè]o|đ[ệe]ch)\b',
        r'\b(c[họo]|chó)\s+(m[ẹe]|đ[ẻe])\b',
        r'\b(th[ằa]ng|con)\s+(ch[óo]|n[gu]u)\b',
        r'\b(vl|vcl|clgt|dmm|đkm)\b',
        r'\b(m[ẹe]|m[ày]y|t[ôo]i)\s+(đ[íi]t|đ[ụu])\b',
    ]
    
    # Common misspellings and variations
    MISSPELLING_MAP = {
        'djt': 'địt',
        'dit': 'địt',
        'deo': 'đéo',
        'dech': 'đệch',
        'lon': 'lồn',
        'cac': 'cặc',
        'cho': 'chó',
        'ngu': 'ngu',
        'dm': 'đm',
        'vl': 'vl',
    }
    
    def __init__(self, enable_fuzzy_matching: bool = True):
        """
        Initialize keyword detector
        
        Args:
            enable_fuzzy_matching: Enable detection of common misspellings
        """
        self.enable_fuzzy_matching = enable_fuzzy_matching
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.TOXIC_PATTERNS]
        
        # Combine all keywords
        self.all_keywords = (
            self.TOXIC_KEYWORDS_HIGH | 
            self.TOXIC_KEYWORDS_MEDIUM | 
            self.TOXIC_KEYWORDS_LOW |
            self.NEGATIVE_KEYWORDS
        )
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better keyword matching
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Lowercase
        text = text.lower()
        
        # Remove excessive punctuation
        text = re.sub(r'[.,!?]{2,}', ' ', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Apply misspelling corrections if enabled
        if self.enable_fuzzy_matching:
            for misspell, correct in self.MISSPELLING_MAP.items():
                text = re.sub(r'\b' + re.escape(misspell) + r'\b', correct, text)
        
        return text.strip()
    
    def detect_keywords(self, text: str) -> List[KeywordMatch]:
        """
        Detect toxic keywords in text
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of KeywordMatch objects
        """
        if not text or len(text.strip()) == 0:
            return []
        
        matches = []
        normalized_text = self.normalize_text(text)
        
        # Check high severity keywords
        for keyword in self.TOXIC_KEYWORDS_HIGH:
            if keyword in normalized_text:
                position = normalized_text.find(keyword)
                context = self._extract_context(text, position, keyword)
                matches.append(KeywordMatch(
                    keyword=keyword,
                    position=position,
                    context=context,
                    severity='high',
                    confidence=0.95
                ))
        
        # Check medium severity keywords
        for keyword in self.TOXIC_KEYWORDS_MEDIUM:
            if keyword in normalized_text:
                position = normalized_text.find(keyword)
                context = self._extract_context(text, position, keyword)
                matches.append(KeywordMatch(
                    keyword=keyword,
                    position=position,
                    context=context,
                    severity='medium',
                    confidence=0.85
                ))
        
        # Check low severity keywords
        for keyword in self.TOXIC_KEYWORDS_LOW:
            if keyword in normalized_text:
                position = normalized_text.find(keyword)
                context = self._extract_context(text, position, keyword)
                matches.append(KeywordMatch(
                    keyword=keyword,
                    position=position,
                    context=context,
                    severity='low',
                    confidence=0.75
                ))
        
        # Check patterns
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(normalized_text):
                keyword = match.group(0)
                position = match.start()
                context = self._extract_context(text, position, keyword)
                matches.append(KeywordMatch(
                    keyword=keyword,
                    position=position,
                    context=context,
                    severity='high',  # Patterns are typically explicit
                    confidence=0.90
                ))
        
        return matches
    
    def _extract_context(self, text: str, position: int, keyword: str, window: int = 30) -> str:
        """
        Extract context around keyword
        
        Args:
            text: Original text
            position: Keyword position
            keyword: Matched keyword
            window: Context window size (characters)
            
        Returns:
            Context string
        """
        start = max(0, position - window)
        end = min(len(text), position + len(keyword) + window)
        return text[start:end]
    
    def calculate_toxicity_score(self, matches: List[KeywordMatch]) -> float:
        """
        Calculate overall toxicity score from matches
        
        Args:
            matches: List of keyword matches
            
        Returns:
            Toxicity score (0.0-1.0)
        """
        if not matches:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            'high': 1.0,
            'medium': 0.6,
            'low': 0.3
        }
        
        total_score = 0.0
        for match in matches:
            weight = severity_weights.get(match.severity, 0.5)
            total_score += match.confidence * weight
        
        # Normalize to [0, 1]
        # Multiple keywords increase toxicity
        score = min(1.0, total_score / (1 + len(matches) * 0.1))
        
        return score
    
    def is_toxic(self, text: str, threshold: float = 0.5) -> Tuple[bool, float, List[str]]:
        """
        Check if text is toxic
        
        Args:
            text: Text to analyze
            threshold: Toxicity threshold (0.0-1.0)
            
        Returns:
            Tuple of (is_toxic, toxicity_score, bad_keywords)
        """
        matches = self.detect_keywords(text)
        toxicity_score = self.calculate_toxicity_score(matches)
        bad_keywords = [match.keyword for match in matches]
        
        return (toxicity_score >= threshold, toxicity_score, bad_keywords)


# Singleton instance
default_keyword_detector = VietnameseToxicKeywordDetector()


if __name__ == '__main__':
    # Test examples
    detector = VietnameseToxicKeywordDetector()
    
    test_texts = [
        "Xin chào các bạn",  # Clean
        "Thằng ngu này làm gì vậy",  # Toxic
        "Tôi ghét cái này quá",  # Negative
        "dm bạn ngu quá",  # Toxic with abbreviation
        "Đồ chó đéo",  # High toxicity
    ]
    
    print("Vietnamese Toxic Keyword Detection Examples:\n")
    for text in test_texts:
        is_toxic, score, keywords = detector.is_toxic(text)
        print(f"Text: {text}")
        print(f"Toxic: {is_toxic}, Score: {score:.2f}, Keywords: {keywords}\n")
