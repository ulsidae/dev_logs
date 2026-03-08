## 🍯 Create a Simple Custom Model Using Ollama

---

This project explores how to get the most out of Ollama by creating lightweight custom models.

Instead of relying on complex fine-tuning pipelines, the goal is to build simple and practical custom models using **Modelfiles**.
The focus is on clarity, experimentation, and minimal setup.

---

### 1. Install Ollama

Download and install Ollama from the official website:

🔗[Ollama](https://ollama.com/download)

---

### 2. Choose a Base Model

Search for a model that fits your use case:

🔗[Search](https://ollama.com/search)

Recommended starter models:

| Name | Description |
| :--- | :--- |
| [Gemma 3](https://ollama.com/library/gemma3) | Try 12B model! If you're using an RTX 3060 or higher |
| [Hermes 3](https://ollama.com/library/hermes3) | The most "unfilterd" one(=great for experimenting). |
| [Mistral](https://ollama.com/library/mistral) | Great for a conversation partner |
| [Exaone 3.5:2.4b](https://ollama.com/library/exaone3.5:2.4b) | If you have a potato & want speak French, Spanish, etc. |

 ^ Click the model name you want to use as the base for your custom model.

---

### 3. Create a Modelfile

Create a **Modelfile** based on the model you selected.

A Modelfile allows you to define behavior, prompts, and configuration for your custom model.
Below is an example:

```modelfile
FROM {base_model}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048

SYSTEM """
You are name is...
(blabla)
"""
```

You can extend this file with additional parameters, system prompts, or other configuration options depending on your needs.

---

### Project Goal

This repository serves as a small experiment demonstrating how custom models can be created quickly using Ollama’s Modelfile system.
The intention is to keep the workflow simple, transparent, and easy to reproduce.

No fine-tuning.
No heavy infrastructure.

Just practical experimentation with local models.

