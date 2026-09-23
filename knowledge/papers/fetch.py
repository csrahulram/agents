"""Download the papers behind the knowledge base into this folder.

  python knowledge/papers/fetch.py

PDFs are not committed (see .gitignore) — this script rebuilds them from arXiv.
"""
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

PAPERS = {
    "2508.07407-self-evolving-agents-survey": "Survey of Self-Evolving AI Agents (Fang et al. 2025) — read in full",
    "2503.13657-mast-why-multi-agent-fails": "MAST: Why Do Multi-Agent LLM Systems Fail? (Cemri et al. 2025)",
    "2306.09896-self-repair-silver-bullet": "Is Self-Repair a Silver Bullet for Code Generation? (ICLR 2024)",
    "2509.09677-illusion-diminishing-returns": "Long-horizon execution and self-conditioning (ICLR 2026)",
    "2607.05197-three-magic-number-repair-loops": "Is Three the Magic Number? Repair loops (2026)",
    "2604.10508-how-many-tries-self-repair": "How Many Tries Does It Take? (2026)",
    "2409.12186-qwen2.5-coder": "Qwen2.5-Coder Technical Report — our coder's benchmark source",
    "2507.03160-assessing-slm-code-generation": "Assessing Small Language Models for Code Generation",
    "2608.18066-fragility-self-improving-agents": "On the Fragility of Self-Improving Agents (Salesforce 2026)",
    "2607.01641-infinite-agentic-loops": "When Agents Do Not Stop: Infinite Agentic Loops (2026)",
    "2502.12110-a-mem-agentic-memory": "A-MEM: Agentic Memory for LLM Agents (NeurIPS 2025)",
    "2401.08500-alphacodium": "Code Generation with AlphaCodium",
    "2301.04589-memory-augmented-llms-universal": "Memory Augmented LLMs are Computationally Universal",
    "2507.01701-blackboard-multi-agent": "LLM Multi-Agent Systems Based on Blackboard Architecture",
    "2506.02153-small-models-future-agentic-ai": "Small Language Models are the Future of Agentic AI (NVIDIA)",
    "2605.00334-agentfloor-tool-use": "AgentFloor: how far up the tool-use ladder can small models go",
}


def main():
    for name, description in PAPERS.items():
        out = HERE / f"{name}.pdf"
        if out.exists():
            print(f"have    {name}")
            continue
        arxiv_id = name.split("-")[0]
        url = f"https://arxiv.org/pdf/{arxiv_id}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                out.write_bytes(r.read())
            print(f"got     {name}  ({out.stat().st_size / 1e6:.1f} MB)  — {description}")
        except Exception as e:
            print(f"failed  {name}: {e}")


if __name__ == "__main__":
    main()
