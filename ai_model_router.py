#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import argparse
import sys

class Model(Enum):
    GPT_5_4 = "GPT-5.4"
    GEMINI_3_1_PRO = "Gemini 3.1 Pro"
    CLAUDE_SONNET_4_6 = "Claude Sonnet 4.6"
    KIMI_K2_6 = "Kimi K2.6"
    NEMOTRON_3_ULTRA = "Nemotron 3 Ultra"

@dataclass
class ModelInfo:
    name: str
    input_cost_per_1m: float
    output_cost_per_1m: float
    context_window_k: int
    hallucination_rate: Optional[float]
    speed_tier: str
    multimodal: list[str]

MODELS = {
    Model.GPT_5_4: ModelInfo("GPT-5.4", 2.50, 15.00, 1000, 6.0, "Média", ["texto", "imagem", "computer_vision"]),
    Model.GEMINI_3_1_PRO: ModelInfo("Gemini 3.1 Pro", 2.00, 12.00, 2000, 9.0, "Média", ["texto", "imagem", "vídeo", "áudio"]),
    Model.CLAUDE_SONNET_4_6: ModelInfo("Claude Sonnet 4.6", 3.00, 15.00, 200, 4.0, "Média", ["texto", "imagem", "computer_vision"]),
    Model.KIMI_K2_6: ModelInfo("Kimi K2.6", 1.20, 4.00, 256, None, "Média", ["texto", "imagem", "vídeo"]),
    Model.NEMOTRON_3_ULTRA: ModelInfo("Nemotron 3 Ultra", 0.20, 0.50, 1000, None, "Muito rápida", ["texto"]),
}

TASKS = {
    "codigo": {
        "keywords": ["código", "code", "debug", "bug", "refator", "teste", "sql", "api", "automação"],
        "scores": {
            Model.GPT_5_4: 8,
            Model.GEMINI_3_1_PRO: 7,
            Model.CLAUDE_SONNET_4_6: 10,
            Model.KIMI_K2_6: 9,
            Model.NEMOTRON_3_ULTRA: 7,
        },
    },
    "escrita": {
        "keywords": ["proposta", "apresentação", "pitch", "texto", "copy", "plano", "estratégia"],
        "scores": {
            Model.GPT_5_4: 10,
            Model.GEMINI_3_1_PRO: 8,
            Model.CLAUDE_SONNET_4_6: 8,
            Model.KIMI_K2_6: 6,
            Model.NEMOTRON_3_ULTRA: 5,
        },
    },
    "pesquisa": {
        "keywords": ["pesquisa", "research", "mercado", "documento", "pdf", "benchmark", "concorrente"],
        "scores": {
            Model.GPT_5_4: 8,
            Model.GEMINI_3_1_PRO: 10,
            Model.CLAUDE_SONNET_4_6: 7,
            Model.KIMI_K2_6: 6,
            Model.NEMOTRON_3_ULTRA: 9,
        },
    },
    "multimodal": {
        "keywords": ["imagem", "vídeo", "audio", "áudio", "screenshot", "design", "figma"],
        "scores": {
            Model.GPT_5_4: 7,
            Model.GEMINI_3_1_PRO: 10,
            Model.CLAUDE_SONNET_4_6: 6,
            Model.KIMI_K2_6: 8,
            Model.NEMOTRON_3_ULTRA: 3,
        },
    },
    "agente": {
        "keywords": ["agente", "pipeline", "orquestração", "workflow longo", "autônomo"],
        "scores": {
            Model.GPT_5_4: 8,
            Model.GEMINI_3_1_PRO: 7,
            Model.CLAUDE_SONNET_4_6: 8,
            Model.KIMI_K2_6: 9,
            Model.NEMOTRON_3_ULTRA: 10,
        },
    },
}

def analyze_task(task_description: str):
    task_lower = task_description.lower()
    scores = {model: 0 for model in Model}
    matched = []

    for category, data in TASKS.items():
        if any(keyword in task_lower for keyword in data["keywords"]):
            matched.append(category)
            for model, score in data["scores"].items():
                scores[model] += score

    if not matched:
        scores[Model.GPT_5_4] += 10
        scores[Model.CLAUDE_SONNET_4_6] += 8
        scores[Model.GEMINI_3_1_PRO] += 7
        scores[Model.KIMI_K2_6] += 6
        scores[Model.NEMOTRON_3_ULTRA] += 6
        matched.append("geral")

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return matched, ranking

def estimate_cost(model: Model, input_tokens: int, output_tokens: int):
    info = MODELS[model]
    return (input_tokens / 1_000_000) * info.input_cost_per_1m + (output_tokens / 1_000_000) * info.output_cost_per_1m

def main():
    parser = argparse.ArgumentParser(description="Roteador de modelos de IA")
    parser.add_argument("task", nargs="+", help="Descrição da tarefa")
    parser.add_argument("--input", type=int, default=10000, help="Tokens de entrada estimados")
    parser.add_argument("--output", type=int, default=5000, help="Tokens de saída estimados")
    args = parser.parse_args()

    # Validação de tokens
    if args.input < 0 or args.output < 0:
        print("❌ Erro: Tokens não podem ser negativos", file=sys.stderr)
        sys.exit(1)

    # Validação de descrição da tarefa
    task_desc = " ".join(args.task).strip()
    if not task_desc:
        print("❌ Erro: Descrição da tarefa não pode estar vazia", file=sys.stderr)
        sys.exit(1)

    try:
        matched, ranking = analyze_task(task_desc)
        top_model, top_score = ranking[0]
        info = MODELS[top_model]

        print("\n=== RECOMENDAÇÃO ===")
        print("Tarefa:", task_desc)
        print("Categorias detectadas:", ", ".join(matched))
        print("Melhor modelo:", top_model.value)
        print("Pontuação:", top_score)
        print("Contexto:", f"{info.context_window_k}K")
        print("Velocidade:", info.speed_tier)
        print("Multimodalidade:", ", ".join(info.multimodal))
        if info.hallucination_rate is not None:
            print("Alucinação estimada:", f"{info.hallucination_rate}%")

        cost = estimate_cost(top_model, args.input, args.output)
        print("Custo estimado:", f"${cost:.4f}")

        print("\n=== RANKING ===")
        for model, score in ranking:
            print(f"{model.value}: {score}")

    except Exception as e:
        print(f"❌ Erro ao processar: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
