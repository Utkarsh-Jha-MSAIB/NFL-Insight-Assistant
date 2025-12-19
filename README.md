# 🏈 NFL Insight Assistant

An interactive Generative AI system for **tactical NFL scouting**, designed to help coaches, analysts, scouts, and players quickly extract opponent tendencies from structured play-by-play data using natural language queries.

![image](https://github.com/user-attachments/assets/d6e1cebc-28d5-4a55-9b71-ae5820995f80)
 <p align="right"><sub><i> Landing page of our NFL Chatbot</a> </i></sub></p>

---

## 🎯 Purpose

Traditional football analytics rely on manual film study and custom scripts, which are time-intensive and require technical expertise.  
The **NFL Insight Assistant** accelerates this process by converting structured play-by-play data into **clear, tactical summaries** using Retrieval-Augmented Generation (RAG) and football-specific reasoning.

---

## 🧠 System Overview

| Component | Description |
|--------|------------|
| Data Source | NFL play-by-play data extracted from ESPN |
| RAG Chunks | Each play converted into structured natural-language summaries |
| Reasoning Model | Gemini 2.5 with Chain-of-Thought prompting |
| Interface | Local web-based interactive assistant |
| Output | Tactical scouting insights grounded in data |

---

## ⚙️ How It Works

1. Play-by-play data is converted into readable RAG chunks  
2. Users ask natural-language football questions  
3. The assistant extracts situational patterns (downs, red zone, player usage)  
4. A structured, data-backed scouting summary is generated  

All answers are derived **only from provided game data**.

---

## 📊 Evaluation Summary

| Criteria | Observation |
|-------|------------|
| Insight Quality | Produced tactically rich summaries with player and situational awareness |
| Speed & Ease of Use | Faster than manual reports; supports rapid follow-up queries |
| End-User Usefulness | Directly applicable in scouting and coaching meetings |
| Trustworthiness | Structured reasoning improves interpretability, but exact counts may vary |

---

## 🏟️ Use Cases

| Role | Example Usage |
|----|--------------|
| Coaches | Review opponent tendencies before film sessions |
| Scouts | Generate quick team and player summaries |
| Analysts | Rapid exploratory analysis before deep dives |
| Players | Recall red-zone or down-specific tendencies |

---

## ⚠️ Limitations

- May miss rare events or exact counts  
- Relies only on play-by-play data (no tracking or alignment info)  
- Team-level insights can change due to injuries and roster movement  

---

## 🚀 Future Work

| Direction | Description |
|--------|------------|
| Multi-Game RAG | Season-level and cross-team analysis |
| Player-Level Modeling | Track individual tendencies across games |
| Hybrid Analytics | LLM front-end calling deterministic functions |
| Real-Time Use | Integration with live or near-live game feeds |

---

## 🧾 Conclusion

The **NFL Insight Assistant** shows that Generative AI, when grounded in structured football data, can meaningfully support game preparation.  
Rather than replacing traditional analytics, it serves as a **fast, accessible scouting companion**, helping teams explore tendencies and validate insights more efficiently.
