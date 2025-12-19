# 🏈 NFL Insight Assistant

An interactive Generative AI system for **tactical NFL scouting**, designed to help coaches, analysts, scouts, and players quickly extract opponent tendencies from structured play-by-play data using natural language queries.

Traditional football analytics rely on manual film study and custom scripts, which are time-intensive and require technical expertise.  
The **NFL Insight Assistant** accelerates this process by converting structured play-by-play data into **clear, tactical summaries** using Retrieval-Augmented Generation (RAG) and football-specific reasoning.

<p align="center">
  <img src="https://github.com/user-attachments/assets/d6e1cebc-28d5-4a55-9b71-ae5820995f80" width="500" alt="My image"/>
 <sub><i> Landing page of our NFL Chatbot</a> </i></sub>
</p>

---

## System Overview

| Component | Description |
|--------|------------|
| Data Source | NFL play-by-play data extracted from ESPN |
| RAG Chunks | Each play converted into structured natural-language summaries |
| Reasoning Model | Gemini 2.5 with Chain-of-Thought prompting |
| Interface | Local web-based interactive assistant |
| Output | Tactical scouting insights grounded in data |

---

## How It Works

1. Play-by-play data is converted into readable RAG chunks  
2. Users ask natural-language football questions  
3. The assistant extracts situational patterns (downs, red zone, player usage)  
4. A structured, data-backed scouting summary is generated  

All answers are derived **only from provided game data**.

---

## Evaluation Summary

| Criteria | Observation |
|-------|------------|
| Insight Quality | Produced tactically rich summaries with player and situational awareness |
| Speed & Ease of Use | Faster than manual reports; supports rapid follow-up queries |
| End-User Usefulness | Directly applicable in scouting and coaching meetings |
| Trustworthiness | Structured reasoning improves interpretability, but exact counts may vary |

---

## Advanced System Features

| Capability | Description |
|----------|------------|
| Dynamic RAG Chunking | Play-by-play data is chunked at multiple granularities (play, drive, quarter). This allows the system to adapt retrieval scope based on question intent, improving answer structure and relevance. |
| Chain-of-Thought Reasoning | Explicit football-specific reasoning steps (down, distance, player role, outcome) improve transparency and reduce shallow pattern matching. |
| Chat Log Extraction | All user queries and model responses are logged and exportable for offline review, auditability, and iterative prompt optimization. |
| Calendar Integration | Supports scheduling scouting reviews and follow-up analysis sessions directly from the assistant interface, enabling smoother analyst workflows. |
| Context-Aware Prompting | Prompts dynamically adjust emphasis (team-level vs player-level) based on detected query intent, reducing irrelevant output. |

---
## Future Work

| Direction | Description |
|--------|------------|
| Multi-Game RAG | Season-level and cross-team analysis |
| Player-Level Modeling | Track individual tendencies across games |
| Hybrid Analytics | LLM front-end calling deterministic functions |
| Real-Time Use | Integration with live or near-live game feeds |


## Conclusion

The **NFL Insight Assistant** shows that Generative AI, when grounded in structured football data, can meaningfully support game preparation.  
Rather than replacing traditional analytics, it serves as a **fast, accessible scouting companion**, helping teams explore tendencies and validate insights more efficiently.
