#!/usr/bin/env python3
"""
ONNX Model Export & Quantization Script
Export Wav2Vec2 và PhoBERT models sang ONNX format với INT8 quantization

Requirements:
- optimum[onnxruntime]
- onnxruntime
- transformers

Usage:
    python backend/scripts/export_onnx_quantized.py

Output:
    - wav2vec2-base-vietnamese-250h-onnx/ (ONNX quantized ASR model)
    - phobert-vi-comment-4class-onnx/ (ONNX quantized Classifier model)
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add backend to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from optimum.onnxruntime import (
        ORTModelForCTC,
        ORTModelForSequenceClassification,
        ORTQuantizer,
        AutoQuantizationConfig,
    )
    from transformers import AutoTokenizer, Wav2Vec2Processor
    import torch
    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False
    print("⚠️  Warning: optimum library not found. Install with: pip install optimum[onnxruntime]")


class ONNXModelExporter:
    """Export và quantize models sang ONNX format"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.asr_model_path = project_root / "wav2vec2-base-vietnamese-250h"
        self.classifier_model_path = project_root / "phobert-vi-comment-4class"
        self.asr_onnx_path = project_root / "wav2vec2-base-vietnamese-250h-onnx"
        self.classifier_onnx_path = project_root / "phobert-vi-comment-4class-onnx"
    
    def export_asr_to_onnx(self, quantize: bool = True) -> bool:
        """
        Export Wav2Vec2 ASR model sang ONNX với quantization
        
        Args:
            quantize: Enable INT8 dynamic quantization
            
        Returns:
            True if successful
        """
        if not OPTIMUM_AVAILABLE:
            print("❌ Cannot export: optimum library not installed")
            return False
        
        print("\n" + "="*60)
        print("📦 EXPORTING WAV2VEC2 ASR MODEL TO ONNX")
        print("="*60)
        
        try:
            # Check if source model exists
            if not self.asr_model_path.exists():
                print(f"❌ Source model not found: {self.asr_model_path}")
                return False
            
            print(f"📂 Source: {self.asr_model_path}")
            print(f"📂 Output: {self.asr_onnx_path}")
            
            # Export to ONNX format
            print("\n⏳ Exporting to ONNX format...")
            model = ORTModelForCTC.from_pretrained(
                str(self.asr_model_path),
                export=True,
                local_files_only=True
            )
            
            # Save ONNX model
            model.save_pretrained(str(self.asr_onnx_path))
            print("✅ ONNX export successful")
            
            # Quantization
            if quantize:
                print("\n⏳ Applying INT8 dynamic quantization...")
                quantizer = ORTQuantizer.from_pretrained(model)
                
                # Dynamic quantization config (no calibration data needed)
                qconfig = AutoQuantizationConfig.avx512_vnni(
                    is_static=False,  # Dynamic quantization
                    per_channel=True   # Better accuracy
                )
                
                # Apply quantization
                quantizer.quantize(
                    save_dir=str(self.asr_onnx_path),
                    quantization_config=qconfig
                )
                print("✅ Quantization successful")
            
            # Copy processor config
            print("\n⏳ Copying processor files...")
            processor = Wav2Vec2Processor.from_pretrained(
                str(self.asr_model_path),
                local_files_only=True
            )
            processor.save_pretrained(str(self.asr_onnx_path))
            print("✅ Processor files copied")
            
            print("\n" + "="*60)
            print("✅ ASR MODEL EXPORT COMPLETE")
            print("="*60)
            return True
            
        except Exception as e:
            print(f"\n❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_classifier_to_onnx(self, quantize: bool = True) -> bool:
        """
        Export PhoBERT classifier sang ONNX với quantization
        
        Args:
            quantize: Enable INT8 dynamic quantization
            
        Returns:
            True if successful
        """
        if not OPTIMUM_AVAILABLE:
            print("❌ Cannot export: optimum library not installed")
            return False
        
        print("\n" + "="*60)
        print("📦 EXPORTING PHOBERT CLASSIFIER TO ONNX")
        print("="*60)
        
        try:
            # Check if source model exists
            if not self.classifier_model_path.exists():
                print(f"❌ Source model not found: {self.classifier_model_path}")
                return False
            
            print(f"📂 Source: {self.classifier_model_path}")
            print(f"📂 Output: {self.classifier_onnx_path}")
            
            # Export to ONNX format
            print("\n⏳ Exporting to ONNX format...")
            model = ORTModelForSequenceClassification.from_pretrained(
                str(self.classifier_model_path),
                export=True,
                local_files_only=True
            )
            
            # Save ONNX model
            model.save_pretrained(str(self.classifier_onnx_path))
            print("✅ ONNX export successful")
            
            # Quantization
            if quantize:
                print("\n⏳ Applying INT8 dynamic quantization...")
                quantizer = ORTQuantizer.from_pretrained(model)
                
                # Dynamic quantization config
                qconfig = AutoQuantizationConfig.avx512_vnni(
                    is_static=False,
                    per_channel=True
                )
                
                # Apply quantization
                quantizer.quantize(
                    save_dir=str(self.classifier_onnx_path),
                    quantization_config=qconfig
                )
                print("✅ Quantization successful")
            
            # Copy tokenizer files
            print("\n⏳ Copying tokenizer files...")
            tokenizer = AutoTokenizer.from_pretrained(
                str(self.classifier_model_path),
                local_files_only=True
            )
            tokenizer.save_pretrained(str(self.classifier_onnx_path))
            print("✅ Tokenizer files copied")
            
            print("\n" + "="*60)
            print("✅ CLASSIFIER EXPORT COMPLETE")
            print("="*60)
            return True
            
        except Exception as e:
            print(f"\n❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_onnx_models(self) -> bool:
        """Verify exported ONNX models work correctly"""
        print("\n" + "="*60)
        print("🔍 VERIFYING ONNX MODELS")
        print("="*60)
        
        success = True
        
        # Verify ASR model
        if self.asr_onnx_path.exists():
            try:
                print("\n⏳ Loading ONNX ASR model...")
                model = ORTModelForCTC.from_pretrained(str(self.asr_onnx_path))
                processor = Wav2Vec2Processor.from_pretrained(str(self.asr_onnx_path))
                
                # Test inference with dummy data
                dummy_input = processor(
                    torch.randn(16000).numpy(),
                    sampling_rate=16000,
                    return_tensors="pt"
                )
                
                with torch.inference_mode():
                    outputs = model(**dummy_input)
                
                print("✅ ONNX ASR model verification successful")
                print(f"   Output shape: {outputs.logits.shape}")
            except Exception as e:
                print(f"❌ ASR verification failed: {e}")
                success = False
        else:
            print("⚠️  ONNX ASR model not found")
            success = False
        
        # Verify Classifier model
        if self.classifier_onnx_path.exists():
            try:
                print("\n⏳ Loading ONNX Classifier model...")
                model = ORTModelForSequenceClassification.from_pretrained(
                    str(self.classifier_onnx_path)
                )
                tokenizer = AutoTokenizer.from_pretrained(str(self.classifier_onnx_path))
                
                # Test inference with dummy text
                dummy_text = "Đây là một câu test"
                inputs = tokenizer(dummy_text, return_tensors="pt")
                
                with torch.inference_mode():
                    outputs = model(**inputs)
                
                print("✅ ONNX Classifier model verification successful")
                print(f"   Output shape: {outputs.logits.shape}")
            except Exception as e:
                print(f"❌ Classifier verification failed: {e}")
                success = False
        else:
            print("⚠️  ONNX Classifier model not found")
            success = False
        
        return success


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Export models to ONNX format with quantization"
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable INT8 quantization"
    )
    parser.add_argument(
        "--asr-only",
        action="store_true",
        help="Export only ASR model"
    )
    parser.add_argument(
        "--classifier-only",
        action="store_true",
        help="Export only classifier model"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing ONNX models"
    )
    
    args = parser.parse_args()
    
    # Determine project root (3 levels up from this script)
    project_root = Path(__file__).resolve().parent.parent.parent
    
    print("\n" + "="*60)
    print("🚀 ONNX MODEL EXPORT & QUANTIZATION")
    print("="*60)
    print(f"📂 Project root: {project_root}")
    
    if not OPTIMUM_AVAILABLE:
        print("\n❌ Required packages not installed!")
        print("Install with: pip install optimum[onnxruntime] onnxruntime")
        return 1
    
    exporter = ONNXModelExporter(project_root)
    
    # Verify only mode
    if args.verify_only:
        success = exporter.verify_onnx_models()
        return 0 if success else 1
    
    # Export models
    quantize = not args.no_quantize
    
    success = True
    if not args.classifier_only:
        success = exporter.export_asr_to_onnx(quantize=quantize) and success
    
    if not args.asr_only:
        success = exporter.export_classifier_to_onnx(quantize=quantize) and success
    
    # Verify exports
    if success:
        success = exporter.verify_onnx_models()
    
    if success:
        print("\n" + "="*60)
        print("✅ ALL OPERATIONS COMPLETE!")
        print("="*60)
        print("\n💡 Next steps:")
        print("   1. Update config to use ONNX models")
        print("   2. Test inference performance")
        print("   3. Compare accuracy with PyTorch models")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME OPERATIONS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
