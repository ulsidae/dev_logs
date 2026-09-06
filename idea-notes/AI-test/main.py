import subprocess
import os

MODEL_NAME = "phi:2.7b-chat-v2-fp16"
HISTORY_FILE = "history.txt"

# Hardcoded system prompt
SYSTEM_PROMPT = """ use English """

def read_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def append_history(user_input, model_response):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"\nUser: {user_input}\nAI: {model_response}\n")

def run_info_bat():
    """Run info.bat sequentially before chat."""
    subprocess.run(["info.bat"], shell=True)

def chat_loop():
    print("=== AI Chat (type 'exit' to quit) ===\n")
    history = read_history()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        # Build full prompt
        prompt = f"{SYSTEM_PROMPT}\n\nHistory:\n{history}\n\nUser: {user_input}\nAI:"

        # Run ollama model
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, "--prompt", prompt],
            capture_output=True, text=True
        )
        model_response = result.stdout.strip()
        print(f"AI: {model_response}\n")

        append_history(user_input, model_response)
        history += f"\nUser: {user_input}\nAI: {model_response}"

if __name__ == "__main__":
    run_info_bat()  
    chat_loop()    
