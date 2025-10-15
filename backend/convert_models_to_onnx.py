#!/usr/bin/env python3
"""
Auto-convert Models to ONNX - Vietnamese STT Demo
Tự động convert PyTorch models sang ONNX khi clone repo hoặc setup
"""

import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import Settings
from app.core.logger import AudioProcessingLogger
from app.utils.smart_model_loader import get_smart_model_loader

def convert_models_to_onnx():
    """Convert all models to ONNX format"""
    print("🚀 Auto-converting Models to ONNX...")
    print("=" * 50)
    
    settings = Settings()
    logger = AudioProcessingLogger("auto_convert")
    
    # Check model paths
    model_paths = settings.get_model_paths()
    print(f"ASR Model Path: {model_paths['asr']}")
    print(f"ASR Exists: {model_paths['asr'].exists()}")
    print(f"Classifier Model Path: {model_paths['classifier']}")
    print(f"Classifier Exists: {model_paths['classifier'].exists()}")
    
    if not model_paths['asr'].exists():
        print("❌ ASR model not found. Please ensure models are downloaded.")
        return False
    
    if not model_paths['classifier'].exists():
        print("❌ Classifier model not found. Please ensure models are downloaded.")
        return False
    
    try:
        # Get smart model loader
        loader = get_smart_model_loader(settings, logger)
        
        print("\n🔄 Converting PhoWhisper to ONNX...")
        start_time = time.time()
        
        # Load PhoWhisper (this will trigger auto-conversion if enabled)
        phowhisper_result = loader.load_phowhisper_model(str(model_paths['asr']))
        
        phowhisper_time = time.time() - start_time
        print(f"✅ PhoWhisper conversion: {phowhisper_result.model_type} ({phowhisper_time:.2f}s)")
        
        if phowhisper_result.performance_metrics:
            metrics = phowhisper_result.performance_metrics
            print(f"   Performance: {metrics.speedup:.2f}x speedup")
        
        print("\n🔄 Converting PhoBERT to ONNX...")
        start_time = time.time()
        
        # Load PhoBERT (this will trigger auto-conversion if enabled)
        phobert_result = loader.load_phobert_model(str(model_paths['classifier']))
        
        phobert_time = time.time() - start_time
        print(f"✅ PhoBERT conversion: {phobert_result.model_type} ({phobert_time:.2f}s)")
        
        if phobert_result.performance_metrics:
            metrics = phobert_result.performance_metrics
            print(f"   Performance: {metrics.speedup:.2f}x speedup")
        
        # Get final status
        status = loader.get_model_status()
        print("\n📊 Final Status:")
        print(f"   PhoWhisper: {status['loaded_models'].get('phowhisper', {}).get('type', 'unknown')}")
        print(f"   PhoBERT: {status['loaded_models'].get('phobert', {}).get('type', 'unknown')}")
        print(f"   ONNX Available: {status['onnx_available']}")
        
        print("\n🎉 Model conversion completed!")
        return True
        
    except Exception as e:
        print(f"❌ Model conversion failed: {e}")
        return False

def check_onnx_models():
    """Check if ONNX models already exist"""
    print("🔍 Checking existing ONNX models...")
    
    onnx_dir = Path("app/onnx_models")
    phowhisper_onnx = onnx_dir / "phowhisper" / "phowhisper.onnx"
    phobert_onnx = onnx_dir / "phobert" / "phobert.onnx"
    
    phowhisper_exists = phowhisper_onnx.exists()
    phobert_exists = phobert_onnx.exists()
    
    print(f"   PhoWhisper ONNX: {'✅' if phowhisper_exists else '❌'}")
    print(f"   PhoBERT ONNX: {'✅' if phobert_exists else '❌'}")
    
    return phowhisper_exists and phobert_exists

def main():
    """Main conversion function"""
    print("🤖 Vietnamese STT Demo - Model ONNX Conversion")
    print("=" * 60)
    
    # Check if ONNX models already exist
    if check_onnx_models():
        print("\n✅ ONNX models already exist!")
        print("   Skipping conversion.")
        return True
    
    print("\n🔄 ONNX models not found. Starting conversion...")
    
    # Convert models
    success = convert_models_to_onnx()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("   Models are now optimized with ONNX.")
        print("   You can run the demo with: python start.py")
    else:
        print("\n⚠️  Setup completed with warnings.")
        print("   Models will fallback to PyTorch mode.")
        print("   You can still run the demo with: python start.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
