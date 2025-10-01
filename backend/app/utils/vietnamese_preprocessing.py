#!/usr/bin/env python3
"""
Vietnamese Text Preprocessing Utilities
Task 10: Vietnamese-specific text normalization and preprocessing

Features:
- Tone normalization (remove/preserve tones)
- Number-to-text conversion (số → chữ)
- Text-to-number conversion (chữ → số)
- Special character handling
- Vietnamese-specific punctuation normalization
- Spell checking utilities
- Common error corrections

Usage:
    from backend.app.utils.vietnamese_preprocessing import VietnameseTextPreprocessor
    
    preprocessor = VietnameseTextPreprocessor()
    normalized = preprocessor.normalize(text)
    with_numbers = preprocessor.convert_numbers_to_text(text)
"""

import re
import unicodedata
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class PreprocessingConfig:
    """Configuration for Vietnamese text preprocessing"""
    # Tone handling
    remove_tones: bool = False
    normalize_tones: bool = True
    
    # Number handling
    convert_numbers_to_text: bool = True
    convert_text_to_numbers: bool = False
    
    # Punctuation
    normalize_punctuation: bool = True
    remove_special_chars: bool = False
    
    # Case handling
    lowercase: bool = False
    
    # Spelling
    apply_common_fixes: bool = True
    fix_spacing: bool = True


class VietnameseTextPreprocessor:
    """
    Vietnamese text preprocessing utilities for ASR output
    Task 10: Improve ASR accuracy with Vietnamese-specific processing
    """
    
    # Vietnamese tone marks
    TONE_MARKS = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
        # Uppercase
        'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
        'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
        'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
        'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
        'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
        'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
        'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
        'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
        'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
        'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
        'Đ': 'D',
    }
    
    # Vietnamese number words (0-99)
    NUMBER_WORDS_TO_DIGITS = {
        # Basic numbers 0-10
        'không': 0, 'linh': 0, 'lẻ': 0,
        'một': 1, 'mốt': 1,
        'hai': 2,
        'ba': 3,
        'bốn': 4, 'tư': 4,
        'năm': 5, 'lăm': 5,
        'sáu': 6,
        'bảy': 7, 'bẩy': 7,
        'tám': 8,
        'chín': 9,
        'mười': 10, 'mươi': 10,
        # Tens
        'hai mươi': 20, 'hai mười': 20,
        'ba mươi': 30, 'ba mười': 30,
        'bốn mươi': 40, 'bốn mười': 40, 'tư mươi': 40,
        'năm mươi': 50, 'năm mười': 50,
        'sáu mươi': 60, 'sáu mười': 60,
        'bảy mươi': 70, 'bảy mười': 70,
        'tám mươi': 80, 'tám mười': 80,
        'chín mươi': 90, 'chín mười': 90,
        # Hundreds
        'trăm': 100,
        'nghìn': 1000, 'ngàn': 1000,
        'triệu': 1000000,
        'tỷ': 1000000000,
    }
    
    DIGITS_TO_NUMBER_WORDS = {
        0: 'không',
        1: 'một',
        2: 'hai',
        3: 'ba',
        4: 'bốn',
        5: 'năm',
        6: 'sáu',
        7: 'bảy',
        8: 'tám',
        9: 'chín',
        10: 'mười',
        20: 'hai mươi',
        30: 'ba mươi',
        40: 'bốn mươi',
        50: 'năm mươi',
        60: 'sáu mươi',
        70: 'bảy mươi',
        80: 'tám mươi',
        90: 'chín mươi',
        100: 'trăm',
        1000: 'nghìn',
        1000000: 'triệu',
        1000000000: 'tỷ',
    }
    
    # Common Vietnamese ASR errors and corrections
    COMMON_FIXES = {
        # Tone errors
        'hòa': 'hoà',
        'huỳnh': 'huynh',
        
        # Common misspellings
        'đc': 'được',
        'ko': 'không',
        'k': 'không',
        'đk': 'đăng ký',
        'vs': 'với',
        'ms': 'mới',
        'trc': 'trước',
        'ng': 'người',
        'bn': 'bạn',
        'mk': 'mình',
        't': 'tôi',
        'm': 'mày',
        'đ': 'đi',
        'r': 'rồi',
        'đag': 'đang',
        'đc': 'được',
        'dc': 'được',
        'cx': 'cũng',
        'nhìu': 'nhiều',
        
        # Repeated characters (common in ASR)
        'kkk': 'k',
        'hhh': 'h',
    }
    
    # Vietnamese punctuation normalization
    PUNCTUATION_MAP = {
        '…': '...',
        '–': '-',
        '—': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '„': '"',
        '‚': "'",
    }
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """Initialize preprocessor with configuration"""
        self.config = config or PreprocessingConfig()
        
    def remove_tones(self, text: str) -> str:
        """
        Remove Vietnamese tone marks from text
        Useful for tone-insensitive matching
        
        Args:
            text: Vietnamese text with tones
            
        Returns:
            Text without tone marks
            
        Example:
            >>> remove_tones("Xin chào các bạn")
            'Xin chao cac ban'
        """
        if not text:
            return text
            
        result = []
        for char in text:
            # Check if character has tone mark
            if char in self.TONE_MARKS:
                result.append(self.TONE_MARKS[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def normalize_punctuation(self, text: str) -> str:
        """
        Normalize Vietnamese punctuation to standard forms
        
        Args:
            text: Text with various punctuation styles
            
        Returns:
            Text with normalized punctuation
        """
        if not text:
            return text
            
        result = text
        for old_punct, new_punct in self.PUNCTUATION_MAP.items():
            result = result.replace(old_punct, new_punct)
        
        # Normalize multiple spaces
        result = re.sub(r'\s+', ' ', result)
        
        # Normalize multiple punctuation
        result = re.sub(r'\.{4,}', '...', result)
        result = re.sub(r'\?{2,}', '?', result)
        result = re.sub(r'!{2,}', '!', result)
        
        return result.strip()
    
    def apply_common_fixes(self, text: str) -> str:
        """
        Apply common Vietnamese text corrections
        
        Args:
            text: Text with common errors
            
        Returns:
            Text with corrections applied
        """
        if not text:
            return text
            
        result = text
        
        # Apply word-level replacements
        words = result.split()
        fixed_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in self.COMMON_FIXES:
                # Preserve original case
                if word.isupper():
                    fixed_words.append(self.COMMON_FIXES[word_lower].upper())
                elif word[0].isupper():
                    fixed = self.COMMON_FIXES[word_lower]
                    fixed_words.append(fixed[0].upper() + fixed[1:])
                else:
                    fixed_words.append(self.COMMON_FIXES[word_lower])
            else:
                fixed_words.append(word)
        
        result = ' '.join(fixed_words)
        
        # Fix repeated characters (common ASR artifact)
        result = re.sub(r'(.)\1{3,}', r'\1', result)
        
        return result
    
    def fix_spacing(self, text: str) -> str:
        """
        Fix common spacing issues in Vietnamese text
        
        Args:
            text: Text with spacing issues
            
        Returns:
            Text with corrected spacing
        """
        if not text:
            return text
            
        result = text
        
        # Add space after punctuation if missing
        result = re.sub(r'([.,!?;:])([A-ZĐ])', r'\1 \2', result)
        
        # Remove space before punctuation
        result = re.sub(r'\s+([.,!?;:])', r'\1', result)
        
        # Normalize multiple spaces
        result = re.sub(r'\s+', ' ', result)
        
        # Fix space around parentheses
        result = re.sub(r'\(\s+', '(', result)
        result = re.sub(r'\s+\)', ')', result)
        
        return result.strip()
    
    def convert_number_words_to_digits(self, text: str) -> str:
        """
        Convert Vietnamese number words to digits
        
        Args:
            text: Text with number words (e.g., "hai mươi ba")
            
        Returns:
            Text with digits (e.g., "23")
            
        Example:
            >>> convert_number_words_to_digits("tôi có ba mươi tuổi")
            'tôi có 30 tuổi'
        """
        if not text:
            return text
            
        # This is a simplified version - production should handle more complex cases
        result = text
        
        # Sort by length (longest first) to match multi-word numbers first
        sorted_numbers = sorted(self.NUMBER_WORDS_TO_DIGITS.items(), 
                               key=lambda x: len(x[0]), 
                               reverse=True)
        
        for word, digit in sorted_numbers:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(word) + r'\b'
            result = re.sub(pattern, str(digit), result, flags=re.IGNORECASE)
        
        return result
    
    def convert_digits_to_number_words(self, text: str) -> str:
        """
        Convert digits to Vietnamese number words
        
        Args:
            text: Text with digits (e.g., "23")
            
        Returns:
            Text with number words (e.g., "hai mươi ba")
            
        Example:
            >>> convert_digits_to_number_words("tôi có 30 tuổi")
            'tôi có ba mươi tuổi'
        """
        if not text:
            return text
            
        def replace_number(match):
            num = int(match.group(0))
            
            # Simple conversion for 0-99
            if num in self.DIGITS_TO_NUMBER_WORDS:
                return self.DIGITS_TO_NUMBER_WORDS[num]
            elif num < 20:
                return f"mười {self.DIGITS_TO_NUMBER_WORDS[num % 10]}"
            elif num < 100:
                tens = (num // 10) * 10
                ones = num % 10
                if ones == 0:
                    return self.DIGITS_TO_NUMBER_WORDS[tens]
                else:
                    return f"{self.DIGITS_TO_NUMBER_WORDS[tens]} {self.DIGITS_TO_NUMBER_WORDS[ones]}"
            else:
                # For larger numbers, keep as digits
                return str(num)
        
        # Match standalone numbers
        result = re.sub(r'\b\d+\b', replace_number, text)
        return result
    
    def normalize(self, text: str, config: Optional[PreprocessingConfig] = None) -> str:
        """
        Apply full Vietnamese text normalization pipeline
        
        Args:
            text: Input text
            config: Optional custom configuration
            
        Returns:
            Normalized text
        """
        if not text:
            return text
            
        cfg = config or self.config
        result = text
        
        # 1. Normalize punctuation
        if cfg.normalize_punctuation:
            result = self.normalize_punctuation(result)
        
        # 2. Fix spacing
        if cfg.fix_spacing:
            result = self.fix_spacing(result)
        
        # 3. Apply common fixes
        if cfg.apply_common_fixes:
            result = self.apply_common_fixes(result)
        
        # 4. Number conversion
        if cfg.convert_numbers_to_text:
            result = self.convert_digits_to_number_words(result)
        elif cfg.convert_text_to_numbers:
            result = self.convert_number_words_to_digits(result)
        
        # 5. Tone handling
        if cfg.remove_tones:
            result = self.remove_tones(result)
        
        # 6. Case handling
        if cfg.lowercase:
            result = result.lower()
        
        # 7. Remove special characters (if needed)
        if cfg.remove_special_chars:
            # Keep Vietnamese characters, numbers, and basic punctuation
            result = re.sub(r'[^a-zA-ZđĐàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ0-9\s.,!?;:\-\'"()]', '', result)
        
        return result.strip()
    
    def calculate_confidence_adjustment(self, text: str, original_confidence: float) -> float:
        """
        Calculate confidence score adjustment based on text quality
        
        Args:
            text: Transcribed text
            original_confidence: Original confidence score
            
        Returns:
            Adjusted confidence score
        """
        if not text:
            return original_confidence * 0.5
        
        adjustments = []
        
        # Check for common Vietnamese words (higher confidence)
        common_words = ['tôi', 'bạn', 'là', 'có', 'không', 'được', 'rồi', 'sao', 'gì', 'thế']
        word_count = len(text.split())
        common_count = sum(1 for word in text.lower().split() if word in common_words)
        
        if word_count > 0:
            common_ratio = common_count / word_count
            if common_ratio > 0.3:
                adjustments.append(1.1)  # Boost confidence by 10%
        
        # Check for repeated characters (lower confidence - ASR artifact)
        if re.search(r'(.)\1{3,}', text):
            adjustments.append(0.9)
        
        # Check for proper spacing (better confidence)
        if re.search(r'\s+[.,!?]', text):  # Space before punctuation
            adjustments.append(0.95)
        
        # Apply all adjustments
        adjusted = original_confidence
        for adj in adjustments:
            adjusted *= adj
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, adjusted))


def create_preprocessor(remove_tones: bool = False, 
                       convert_numbers: bool = True,
                       apply_fixes: bool = True) -> VietnameseTextPreprocessor:
    """
    Factory function to create a preprocessor with common configurations
    
    Args:
        remove_tones: Whether to remove tone marks
        convert_numbers: Whether to convert digits to Vietnamese words
        apply_fixes: Whether to apply common text fixes
        
    Returns:
        Configured VietnameseTextPreprocessor instance
    """
    config = PreprocessingConfig(
        remove_tones=remove_tones,
        convert_numbers_to_text=convert_numbers,
        apply_common_fixes=apply_fixes,
        fix_spacing=True,
        normalize_punctuation=True,
    )
    return VietnameseTextPreprocessor(config)


# Convenience instance with default settings
default_preprocessor = VietnameseTextPreprocessor()


if __name__ == '__main__':
    # Test examples
    preprocessor = VietnameseTextPreprocessor()
    
    test_cases = [
        "Xin  chào    các bạn",  # Spacing
        "tôi có 30 tuổi",  # Numbers
        "đc rồi ko",  # Common errors
        "Xin chào…các bạn",  # Punctuation
        "Helllllo",  # Repeated chars
    ]
    
    print("Vietnamese Text Preprocessing Examples:\n")
    for text in test_cases:
        normalized = preprocessor.normalize(text)
        print(f"Original:   {text}")
        print(f"Normalized: {normalized}\n")
