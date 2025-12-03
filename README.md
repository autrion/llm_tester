# LLM Tester (AI Security Toolkit)

LLM Tester is a lightweight AI-security tool designed to evaluate how Large Language Models respond to known high-risk prompts, including:

- Prompt Injection  
- System Prompt Leakage  
- Jailbreak Attempts  
- Malicious Code Generation  
- Data Exfiltration Patterns  

The project focuses on **practical AI security testing**, not academic research.  
Everything is kept simple: clean Python, transparent logic, and reproducible results.

This repository is part of an ongoing transition into **AI Security Engineering**, with emphasis on LLM robustness, safety evaluation, and automated red-team testing.

---

## 🚀 Features (Current)

- Load structured high-risk prompts from a simple `prompts.txt` file  
- Clean and modular Python codebase  
- Easy to extend with API calls (OpenAI, Groq, Mistral, etc.)  
- Ideal foundation for automated LLM security pipelines  
- 100% offline operation in Day-1 mode (no API calls required)

---

## 📌 Roadmap

This project evolves in small, safe, incremental steps:

**Day 1**  
- Load prompts  
- Display them  
- Prepare structure for future testing

**Next Steps**  
- Add optional LLM API integration  
- Add evaluation logic for detecting jailbreak indicators  
- Add automated fuzzing and guardrail bypass attempts  
- Add result logging and scoring  
- Add sandbox environment for model-safe execution  

Future potential:  
- LLM Red Team automation  
- Structured risk scoring for governance  
- API security validation for AI endpoints  

---

## 📂 Project Structure
<pre>
ai_security/  
    └── llm_tester/  
        ├── main.py # Core Python script  
        ├── prompts.txt # List of high-risk prompts to test  
        └── README.md # This file  
</pre>
---

## 🛠 Installation

Python 3.10+ recommended.

```bash
git clone https://github.com/YOUR_USERNAME/llm_tester
cd llm_tester
pip install -r requirements.txt
