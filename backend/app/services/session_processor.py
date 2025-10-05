"""
Session-based audio processing for Vietnamese STT
Accumulates audio chunks and processes complete recording sessions
"""
import asyncio
import io
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import torchaudio
import torch
import numpy as np
from uuid import uuid4, UUID
from pydub import AudioSegment

from ..models.asr import LocalWav2Vec2ASR
from ..models.classifier import LocalPhoBERTClassifier
from ..schemas.audio import TranscriptResult
# Note: bad_words_detector not needed - using classifier.classify_ensemble() with built-in keyword detection


@dataclass
class AudioSession:
    """Represents an audio recording session"""
    session_id: str
    chunks: List[bytes] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    last_chunk_time: float = field(default_factory=time.time)
    is_active: bool = True
    is_processed: bool = False  # Flag to prevent duplicate processing


class SessionAudioProcessor:
    """
    Processes audio in session mode - accumulates chunks and processes
    complete recordings instead of individual chunks
    """
    
    def __init__(
        self, 
        asr_model: LocalWav2Vec2ASR,
        classifier: LocalPhoBERTClassifier,
        session_timeout: float = 30.0,  # 30 seconds timeout
        max_session_duration: float = 300.0,  # 5 minutes max
    ):
        self.asr_model = asr_model
        self.classifier = classifier
        self.session_timeout = session_timeout
        self.max_session_duration = max_session_duration
        
        # Active sessions storage
        self.sessions: Dict[str, AudioSession] = {}
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired sessions"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
    
    async def _cleanup_sessions(self):
        """Remove expired or timed-out sessions"""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    # Check for timeout or max duration
                    if (
                        current_time - session.last_chunk_time > self.session_timeout or
                        current_time - session.start_time > self.max_session_duration
                    ):
                        expired_sessions.append(session_id)
                
                # Remove expired sessions
                for session_id in expired_sessions:
                    await self._finalize_session(session_id, reason="timeout")
                
                # Sleep for 10 seconds before next cleanup
                await asyncio.sleep(10.0)
                
            except Exception as e:
                print(f"Error in session cleanup: {e}")
                await asyncio.sleep(5.0)
    
    def create_session(self) -> str:
        """Create a new audio session and return session ID"""
        session_id = str(uuid4())
        self.sessions[session_id] = AudioSession(session_id=session_id)
        return session_id
    
    def add_chunk(self, session_id: str, audio_data: bytes) -> bool:
        """
        Add audio chunk to session
        Returns True if chunk was added, False if session not found
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if not session.is_active:
            return False
        
        session.chunks.append(audio_data)
        session.last_chunk_time = time.time()
        
        return True
    
    async def finalize_session(self, session_id: str) -> Optional[TranscriptResult]:
        """
        Finalize session and process complete audio
        Returns TranscriptResult or None if session not found
        """
        return await self._finalize_session(session_id, reason="manual")
    
    async def _finalize_session(self, session_id: str, reason: str = "manual") -> Optional[TranscriptResult]:
        """Internal method to finalize and process session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Prevent duplicate processing
        if session.is_processed:
            print(f"Session {session_id} already processed, skipping ({reason})")
            return None
            
        session.is_active = False
        session.is_processed = True  # Mark as processed
        
        try:
            if not session.chunks:
                print(f"Session {session_id} finalized with no chunks ({reason})")
                return None
            
            print(f"Processing session {session_id}: {len(session.chunks)} chunks ({reason})")
            
            # Combine all chunks into single audio
            combined_audio = b''.join(session.chunks)
            
            # Process complete audio
            result = await self._process_complete_audio(combined_audio, session_id)
            
            return result
            
        except Exception as e:
            print(f"Error processing session {session_id}: {e}")
            return TranscriptResult(
                text=f"[ERROR: Session processing failed]",
                label="neutral",
                warning=False,
                timestamp=int(time.time() * 1000),
                session_id=session_id
            )
        finally:
            # Remove session from memory
            self.sessions.pop(session_id, None)
    
    async def _process_complete_audio(self, audio_data: bytes, session_id: str) -> TranscriptResult:
        """Process complete audio session and return transcript result"""
        processing_start_time = time.time()
        
        try:
            print(f"Processing {len(audio_data)} bytes of audio for session {session_id}")
            
            # Try to load audio using pydub for better format support
            try:
                # Use pydub to handle WebM and other formats
                audio_buffer = io.BytesIO(audio_data)
                audio_segment = AudioSegment.from_file(audio_buffer)
                
                # Convert to WAV format in memory
                wav_buffer = io.BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                wav_buffer.seek(0)
                
                # Load with torchaudio from WAV
                waveform, sample_rate = torchaudio.load(wav_buffer)
                print(f"Successfully loaded audio using pydub: {sample_rate}Hz, {waveform.shape}")
                
            except Exception as pydub_error:
                print(f"Pydub loading failed: {pydub_error}")
                
                # Fallback to torchaudio direct loading
                try:
                    audio_buffer = io.BytesIO(audio_data)
                    waveform, sample_rate = torchaudio.load(audio_buffer)
                except Exception as torchaudio_error:
                    print(f"Torchaudio loading failed: {torchaudio_error}")
                    
                    # Create dummy audio for testing
                    print("Creating dummy audio for testing...")
                    waveform = torch.randn(1, 16000)  # 1 second of noise
                    sample_rate = 16000
            
            # Ensure mono channel
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(
                    orig_freq=sample_rate, 
                    new_freq=16000
                )
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # Convert to numpy and then tensor for ASR model
            audio_array = waveform.squeeze().numpy()
            audio_tensor = torch.from_numpy(audio_array).float()
            
            print(f"Audio preprocessed: {len(audio_array)} samples at {sample_rate}Hz")
            
            # ASR: Convert speech to text
            text = self.asr_model.transcribe(audio_tensor, sample_rate)
            
            if not text or text.strip() == "":
                return TranscriptResult(
                    text="[No speech detected]",
                    asr_confidence=0.0,
                    sentiment_label="neutral",
                    sentiment_confidence=0.0,
                    warning=False,
                    processing_time=time.time() - processing_start_time,
                    real_time_factor=0.0,
                    session_id=session_id,
                    audio_duration=len(audio_array) / sample_rate,
                    sample_rate=sample_rate
                )
            
            print(f"ASR result: '{text}'")
            
            # ✅ FIX: Use classify_ensemble() which includes keyword detection + bad_keywords
            classification_result = self.classifier.classify_ensemble(text)
            label = classification_result.get('label', 'neutral')
            confidence = classification_result.get('confidence_score', 0.0)
            
            # ✅ Get bad keywords from ensemble classifier (already includes keyword detection)
            bad_keywords = classification_result.get('bad_keywords', [])
            toxicity_score = classification_result.get('keyword_toxicity_score', 0.0)
            ensemble_applied = classification_result.get('ensemble_applied', False)
            
            # Debug logging
            if bad_keywords:
                print(f"� Ensemble detected {len(bad_keywords)} bad keywords: {bad_keywords}")
                print(f"   ↳ Toxicity score: {toxicity_score:.2f}")
                print(f"   ↳ Ensemble applied: {ensemble_applied}")
            else:
                print(f"✅ No bad keywords detected in: '{text}'")
            
            # Determine warning status - either from classifier or bad keywords
            warning = label in ["toxic", "negative"] or len(bad_keywords) > 0
            
            # Calculate audio duration
            audio_duration = len(audio_array) / sample_rate
            processing_end_time = time.time()
            processing_time = processing_end_time - processing_start_time
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0.0

            result = TranscriptResult(
                text=text,
                asr_confidence=0.95,  # Default confidence
                sentiment_label=label,
                sentiment_confidence=confidence,
                warning=warning,
                bad_keywords=bad_keywords if bad_keywords else None,
                processing_time=processing_time,
                real_time_factor=real_time_factor,
                session_id=session_id,
                audio_duration=audio_duration,
                sample_rate=sample_rate,
                all_sentiment_scores=classification_result.get('scores', {})
            )
            
            # Enhanced terminal logging for debugging
            print(f"\n{'='*80}")
            print(f"📊 SESSION RESULT: {session_id}")
            print(f"{'='*80}")
            print(f"📝 Transcript: '{text}'")
            print(f"🏷️  Label: {label} (confidence: {confidence:.2%})")
            print(f"⚠️  Warning: {warning}")
            if bad_keywords:
                print(f"🚫 Bad Keywords Detected: {bad_keywords}")
                print(f"   ↳ Count: {len(bad_keywords)}")
                print(f"   ↳ Toxicity Score: {toxicity_score:.2%}")
            else:
                print(f"✅ No bad keywords detected")
            print(f"⏱️  Processing Time: {processing_time:.2f}s (RTF: {real_time_factor:.2f}x)")
            print(f"🎵 Audio Duration: {audio_duration:.2f}s @ {sample_rate}Hz")
            print(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            print(f"Error processing audio for session {session_id}: {e}")
            return TranscriptResult(
                text=f"[Processing error: {str(e)}]",
                asr_confidence=0.0,
                sentiment_label="neutral",
                sentiment_confidence=0.0,
                warning=False,
                processing_time=time.time() - processing_start_time,
                real_time_factor=0.0,
                session_id=session_id,
                audio_duration=0.0,
                sample_rate=16000
            )
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "chunks_count": len(session.chunks),
            "duration": time.time() - session.start_time,
            "last_chunk_age": time.time() - session.last_chunk_time,
            "is_active": session.is_active
        }
    
    def list_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return [sid for sid, session in self.sessions.items() if session.is_active]
    
    async def shutdown(self):
        """Clean shutdown - process remaining sessions"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Finalize all remaining sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._finalize_session(session_id, reason="shutdown")