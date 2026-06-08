"""Local smoke test of the pipeline WITHOUT the LLM or Celonis.

Runs the full assembly (load -> classify -> push) over a small SELF-CONTAINED synthetic
sample using a deterministic keyword-based stub classifier, writing
output/review_insights.parquet. Exercises every code path except the real CelonisOpenAI
call and the real S3 push — and works straight after a fresh clone (no data files needed).

    python -m scripts.dry_run
"""
from __future__ import annotations

import os

from src.config import get_config
from src.ingestion import push_to_celonis
from src.pipeline import run
from src.schema import ReviewInsight

# Synthetic, inline sample so this works for everyone post-clone (test-data/ is gitignored).
_SAMPLE_CSV = (
    "review_id,order_id,review_score,review_comment_title,review_comment_message\n"
    'syn1,o1,5,,"Produto excelente, chegou antes do prazo."\n'
    "syn2,o2,1,,O produto chegou quebrado e a entrega atrasou muito.\n"
    "syn3,o3,3,,\n"
    "syn4,o4,5,,O preco estava otimo mas a embalagem veio amassada.\n"
    "syn5,o5,5,,Atendimento ao cliente muito atencioso.\n"
)

_NEG = ("quebrado", "atrasou", "nao chegou", "amassada")
_THEME_KEYWORDS = {
    "delivery": ("entrega", "chegou", "prazo", "atrasou"),
    "product_quality": ("quebrado", "funciona", "qualidade"),
    "price": ("preco", "caro", "barato"),
    "packaging": ("embalagem", "amassada"),
    "customer_service": ("atendimento", "cliente"),
}


def _stub_classifier(comment: str) -> ReviewInsight:
    low = comment.lower()
    sentiment = "negative" if any(w in low for w in _NEG) else "positive"
    themes = [t for t, kws in _THEME_KEYWORDS.items() if any(k in low for k in kws)] or ["other"]
    return ReviewInsight(sentiment=sentiment, themes=themes, summary_en=comment[:60])


def main() -> None:
    cfg = get_config()
    os.makedirs("input-data", exist_ok=True)
    sample_path = os.path.join("input-data", "_dry_run_sample.csv")
    with open(sample_path, "w") as f:
        f.write(_SAMPLE_CSV)
    try:
        df = run(input_filename="_dry_run_sample.csv", classifier=_stub_classifier, config=cfg)
        print(f"Assembled {len(df)} rows (empty-comment row dropped)")
        print(df.to_string(index=False))
        dest = push_to_celonis(df, config=cfg)
        print(f"Wrote: {dest}")
    finally:
        if os.path.exists(sample_path):
            os.remove(sample_path)


if __name__ == "__main__":
    main()
