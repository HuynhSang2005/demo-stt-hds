#!/usr/bin/env python3
"""
Audio Processor Factory
Creates optimized audio processors based on configuration
"""

import asyncio
from typing import Optional, Union
from enum import Enum

from ..core.config import Settings
from ..core.logger import AudioProcessingLogger
from .audio_processor import AudioProcessor
from .async_audio_processor import OptimizedAsyncAudioProcessor

class ProcessorType(Enum):
    """Available processor types"""
    STANDARD = "standard"
    OPTIMIZED_ASYNC = "optimized_async"

class AudioProcessorFactory:
    """Factory for creating audio processors"""
    
    _instances: dict = {}
    _lock = asyncio.Lock()
    
    @classmethod
    async def create_processor(
        cls,
        processor_type: ProcessorType = ProcessorType.OPTIMIZED_ASYNC,
        settings: Optional[Settings] = None,
        cache_key: Optional[str] = None
    ) -> Union[AudioProcessor, OptimizedAsyncAudioProcessor]:
        """
        Create or get cached audio processor instance
        
        Args:
            processor_type: Type of processor to create
            settings: Configuration settings
            cache_key: Cache key for instance reuse
            
        Returns:
            Audio processor instance
        """
        if cache_key is None:
            cache_key = f"{processor_type.value}_{hash(str(settings))}"
        
        async with cls._lock:
            if cache_key in cls._instances:
                return cls._instances[cache_key]
            
            logger = AudioProcessingLogger("processor_factory")
            logger.logger.info(
                "creating_processor",
                event_type="processor_creation",
                processor_type=processor_type.value,
                cache_key=cache_key
            )
            
            if processor_type == ProcessorType.STANDARD:
                processor = AudioProcessor(settings)
            elif processor_type == ProcessorType.OPTIMIZED_ASYNC:
                processor = OptimizedAsyncAudioProcessor(settings)
                # Initialize models asynchronously
                await processor.initialize_models()
            else:
                raise ValueError(f"Unknown processor type: {processor_type}")
            
            # Cache the instance
            cls._instances[cache_key] = processor
            
            logger.logger.info(
                "processor_created",
                event_type="processor_creation_complete",
                processor_type=processor_type.value,
                cache_key=cache_key
            )
            
            return processor
    
    @classmethod
    async def get_optimized_processor(
        cls,
        settings: Optional[Settings] = None
    ) -> OptimizedAsyncAudioProcessor:
        """
        Get optimized async processor (convenience method)
        
        Args:
            settings: Configuration settings
            
        Returns:
            Optimized async audio processor
        """
        processor = await cls.create_processor(
            processor_type=ProcessorType.OPTIMIZED_ASYNC,
            settings=settings
        )
        return processor
    
    @classmethod
    async def cleanup_all(cls) -> None:
        """Cleanup all cached processor instances"""
        async with cls._lock:
            logger = AudioProcessingLogger("processor_factory")
            logger.logger.info(
                "cleaning_up_all_processors",
                event_type="factory_cleanup",
                instance_count=len(cls._instances)
            )
            
            for cache_key, processor in cls._instances.items():
                try:
                    if hasattr(processor, 'cleanup'):
                        if asyncio.iscoroutinefunction(processor.cleanup):
                            await processor.cleanup()
                        else:
                            processor.cleanup()
                except Exception as e:
                    logger.logger.error(
                        "processor_cleanup_failed",
                        event_type="cleanup_error",
                        cache_key=cache_key,
                        error=str(e)
                    )
            
            cls._instances.clear()
            logger.logger.info("all_processors_cleaned_up", event_type="factory_cleanup_complete")

# Global processor instance for dependency injection
_global_processor: Optional[OptimizedAsyncAudioProcessor] = None

async def get_audio_processor() -> OptimizedAsyncAudioProcessor:
    """
    Get global optimized audio processor instance
    Used for FastAPI dependency injection
    
    Returns:
        Global optimized audio processor
    """
    global _global_processor
    
    if _global_processor is None:
        _global_processor = await AudioProcessorFactory.get_optimized_processor()
    
    return _global_processor

async def initialize_global_processor(settings: Optional[Settings] = None) -> None:
    """
    Initialize global audio processor
    
    Args:
        settings: Configuration settings
    """
    global _global_processor
    
    if _global_processor is None:
        _global_processor = await AudioProcessorFactory.get_optimized_processor(settings)
        logger = AudioProcessingLogger("processor_factory")
        logger.logger.info("global_processor_initialized", event_type="global_init")

async def cleanup_global_processor() -> None:
    """Cleanup global audio processor"""
    global _global_processor
    
    if _global_processor is not None:
        try:
            await _global_processor.cleanup()
            _global_processor = None
            logger = AudioProcessingLogger("processor_factory")
            logger.logger.info("global_processor_cleaned_up", event_type="global_cleanup")
        except Exception as e:
            logger = AudioProcessingLogger("processor_factory")
            logger.logger.error(
                "global_processor_cleanup_failed",
                event_type="global_cleanup_error",
                error=str(e)
            )
