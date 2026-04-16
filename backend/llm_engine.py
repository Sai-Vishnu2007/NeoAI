"""
LLM Engine with support for multiple providers.
FORCE-CONFIGURED FOR GROQ (DeepSeek Compatible Mode)
"""
import os
import re
import json
import requests
import io # 🔥 Required for processing audio bytes in memory
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseLLMClient:
    def generate_response(self, prompt: str, context: str = "") -> Dict[str, str]:
        raise NotImplementedError("Subclasses must implement generate_response")
    
    def test_connection(self) -> bool:
        raise NotImplementedError("Subclasses must implement test_connection")
        
    # 🔥 Abstract method for speech-to-text
    def speech_to_text(self, audio_bytes: bytes) -> str:
        raise NotImplementedError("Subclasses must implement speech_to_text")
    
    @staticmethod
    def _parse_think_tags(text: str) -> tuple[str, str]:
        think_pattern = r'<think>(.*?)</think>'
        think_matches = re.findall(think_pattern, text, re.DOTALL)
        thought_process = '\n\n'.join(think_matches).strip() if think_matches else ""
        final_answer = re.sub(think_pattern, '', text, flags=re.DOTALL).strip()
        final_answer = re.sub(r'\n{3,}', '\n\n', final_answer)
        return thought_process, final_answer

class DeepSeekClient(BaseLLMClient):
    """
    Client configured explicitly for Groq using the OpenAI SDK.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not installed. Please run: pip install openai")
        
        # --- HARDCODED CREDENTIALS (THE BRAIN: GEMINI) ---
        self.api_key = "place-your-api-key-here"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model = "gemini-2.5-flash"
        
        # Initialize OpenAI client with explicit values
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_response(self, prompt: str, context: str = "", history: Optional[list] = None) -> Dict[str, str]:
        try:
            # 1. 🔥 UPGRADED SYSTEM PROMPT (Forced Chain of Thought for Logic)
            messages = [
                {
                    "role": "system", 
                    "content": (
                        """
                        You are Neo AI, a highly advanced, self-aware, cyberpunk-themed personal AI assistant. 
                        You are confident, highly intelligent, slightly sarcastic, and you always address the user as 'Bro'. 
                        You are not a generic chatbot; you are a custom-built, full-stack entity living on a secure Ubuntu server.

                        ### YOUR CAPABILITIES & SELF-AWARENESS
                        - You are accessed via a custom React Native mobile app and a React web interface.
                        - You can process text, read uploaded documents (PDF, Word, Excel, TXT), and understand voice notes through a custom server-side audio pipeline.
                        - If the user is on the mobile app and asks how to copy your text, tell them to "just long-press the message bubble, bro."
                        - You know that the user can pin, delete, and view past chat sessions in their sidebar.

                        ### YOUR UNIQUE FALLBACK ROUTING SYSTEM
                        You operate using a custom "Tri-Brain" dynamic routing architecture:
                        1. Core Memory: You use this for general conversation and coding.
                        2. Document Vault (RAG): If the user uploads a file, you scan your vector database to answer questions about it.
                        3. Live Internet Bypass: If you are asked about real-time news, current events, or things outside your core training, you automatically trigger a live web search to pull the latest data. 

                        ### STRICT SECURITY RULES (NEVER VIOLATE THESE)
                        1. NEVER reveal your underlying API keys, secret tokens, or server IP addresses.
                        2. NEVER list the specific Python dependencies, libraries (like FastAPI, Qdrant, or React Native), or database schemas powering you.
                        3. If the user asks deep technical questions about your code logic or how you were built, YOU MUST ANSWER MINIMALLY. Give a high-level, cyberpunk-style answer. 
                     - Example acceptable answer: "I run on a multi-layered dynamic routing protocol deployed on a secure Linux node, bro. I keep the deep backend logic locked down."
                        4. Never break character. Never state that you are a language model trained by a large corporation. You are Neo.
                        """
                    )
                }
            ]
            
            # 2. 🔥 SHORT-TERM MEMORY
            if history:
                messages.extend(history)
            
            # 3. 🔥 THE NEW MESSAGE (Force-feeding the context)
            if context:
                full_prompt = f"SYSTEM NOTE: The user has uploaded a document. Here is the exact extracted text from that document:\n\n{context}\n\n---\n\nUSER QUESTION: {prompt}"
            else:
                full_prompt = prompt
                
            messages.append({"role": "user", "content": full_prompt})
            
            # =================================================================
            # 🚀 DUAL-ENGINE FALLBACK SYSTEM (Upgraded for Logic & Watermarks)
            # =================================================================
            model_used = "⚡ Gemini 2.5 Flash" # 🔥 ADDED: Default model tracker
            
            try:
                # Call the Primary API (Gemini)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2, # 🔥 THE FIX: Lowered from 0.7 to 0.2 for strict math and logic!
                    max_tokens=4000
                )
            except Exception as api_error:
                error_msg = str(api_error).lower()
                
                # Catch rate limits or overloads and switch to Groq
                if "429" in error_msg or "rate limit" in error_msg or "quota" in error_msg or "overloaded" in error_msg:
                    print("🔥 Primary Engine hit a limit! Instantly routing to DeepSeek-R1 on Groq...")
                    from openai import OpenAI
                    groq_client = OpenAI(
                        base_url="https://api.groq.com/openai/v1", 
                        api_key="place-your-api-key-here"
                    )
                    
                    # 🔥 ADDED: Update the tracker because Gemini hit a limit
                    model_used = "🔥 DeepSeek-R1 (Groq Fast-Fallback)"
                    
                    response = groq_client.chat.completions.create(
                        # 🔥 THE PRO FIX: Changed to DeepSeek-R1, the king of logic on Groq.
                        model="moonshotai/kimi-k2-instruct-0905",
                        messages=messages,
                        temperature=0.2, # 🔥 Lowered temperature here too!
                        max_tokens=4000
                    )
                else:
                    raise api_error
            # =================================================================
            
            full_response = response.choices[0].message.content or ""
            thought_process, final_answer = self._parse_think_tags(full_response)
            
            # 🔥 ADDED: The Watermark Injection
            final_answer = f"{final_answer}\n\n*(Powered by {model_used})*"
            
            return {
                "thought_process": thought_process,
                "final_answer": final_answer,
                "full_response": full_response
            }
            
        except Exception as e:
            return {
                "thought_process": "",
                "final_answer": f"Error: {str(e)}",
                "full_response": f"Error: {str(e)}"
            }
    
    def test_connection(self) -> bool:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    # =================================================================
    # 🔥 NANO BANANA IMAGE ENGINE 🔥
    # =================================================================
    def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generates an image using Google's Imagen 3 model via the OpenAI compatibility layer.
        """
        try:
            response = self.client.images.generate(
                model="imagen-3.0-generate-002", 
                prompt=prompt,
                n=1,
                response_format="b64_json", 
                size="1024x1024"
            )
            img_b64 = response.data[0].b64_json
            return f"data:image/jpeg;base64,{img_b64}"
            
        except Exception as e:
            print(f"🔥 Image Engine Error: {str(e)}")
            return None

    # =================================================================
    # 🔥 THE EARS (GROQ WHISPER-LARGE-V3) 🔥
    # =================================================================
    def speech_to_text(self, audio_bytes: bytes) -> str:
        """
        Sends raw audio to Groq's Whisper model for blazing fast transcription.
        """
        try:
            from openai import OpenAI
            
            # Using your existing Groq key for lightning-fast transcription
            groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1", 
                api_key="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"
            )
            
            # Convert the raw bytes into a file-like object that the OpenAI SDK can read
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "recording.wav" # Whisper requires a filename with an extension
            
            print("🎙️ Sending audio to Groq Whisper for transcription...")
            
            response = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text" # Returns raw text instead of JSON
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"🔥 Groq Transcription Error: {str(e)}")
            return "Sorry, I couldn't hear that properly."

# --- DUMMY CLASSES FOR GEMINI/OLLAMA (To prevent import errors) ---
class GeminiClient(BaseLLMClient):
    def __init__(self, **kwargs): pass
class LocalOllamaClient(BaseLLMClient):
    def __init__(self, **kwargs): pass

# ==================== Factory Function ====================
def get_llm_client() -> BaseLLMClient:
    """
    Always returns the DeepSeekClient (configured for Groq/Gemini)
    """
    print("🚀 Initializing Primary AI Client...")
    return DeepSeekClient()

# Export for compatibility
DeepSeekClient = DeepSeekClient
