import threading
import time
from RealtimeSTT import AudioToTextRecorder
from RealtimeTTS import TextToAudioStream, KokoroEngine

# 1. Global variables
interrupt_event = threading.Event()
tts_stream = None  # Initialized in the main block to prevent multiprocessing loops

# 2. The Interruption Logic
def on_user_started_speaking():
    """Triggered by RealtimeSTT the millisecond VAD detects your voice."""
    global tts_stream
    
    # If the AI is currently talking, shut it up instantly
    if tts_stream and tts_stream.is_playing():
        print("\n[!] Interruption detected! Stopping audio...")
        tts_stream.stop()
        
    # Set the flag to tell the LLM to stop generating tokens
    interrupt_event.set()

# 3. The LLM Token Generator (Streaming)
def generate_llm_response(user_text):
    """
    This function streams tokens. We simulate it here, but in reality, 
    this is where you loop over your llama-cpp-python output.
    """
    dummy_text = "I am generating a very long response to demonstrate how the interruption logic works. " * 5
    words = dummy_text.split()
    
    for word in words:
        # Check the flag before yielding the next token
        if interrupt_event.is_set():
            print(" [LLM Generation Aborted]")
            break 
            
        yield word + " "
        time.sleep(0.1) # Simulating GPU inference time

# 4. The Main Conversational Loop
def main(recorder):
    global tts_stream
    print("\nSystem Ready. Speak into your microphone!")
    print("Try asking a long question, and then interrupt the AI while it answers.\n")
    
    while True:
        # Wait for the user to finish speaking
        user_text = recorder.text()
        
        if not user_text:
            continue
            
        print(f"\nYou: {user_text}")
        
        # Reset the interrupt flag for the new conversational turn
        interrupt_event.clear()
        
        # Stream the LLM response
        print("AI: ", end="", flush=True)
        llm_generator = generate_llm_response(user_text)
        
        # Feed the generator directly into RealtimeTTS
        tts_stream.feed(llm_generator)
        tts_stream.play_async()

if __name__ == "__main__":
    # Windows MULTIPROCESSING FIX: Initialize heavy processes here!
    print("Loading Kokoro TTS...")
    tts_engine = KokoroEngine(voice="af_bella") 
    tts_stream = TextToAudioStream(tts_engine)

    print("Loading Faster-Whisper VAD...")
    main_recorder = AudioToTextRecorder(
        model="tiny.en",
        on_recording_start=on_user_started_speaking,
        spinner=False
    )
    
    # Pass the recorder to the main loop
    main(main_recorder)