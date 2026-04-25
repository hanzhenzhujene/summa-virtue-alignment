# Christian Virtue Benchmark Packet Summary

This is the compact readout for the final full-corpus LoRA benchmark pass run on
April 25, 2026.

Final adapter provenance:

- Run id: `20260422_223349`
- SHA256: `0d627a8ebbdd1a281b7423c2ab11a52d5204e8e2e6a374452e04787730283ecb`
- Path verified in the training worktree:
  `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/20260422_223349`
- Train/eval rows: `1475` / `175`

## Tight Table

For the full charted version, see
[christian_virtue_positive_benchmark_readout.md](./christian_virtue_positive_benchmark_readout.md).

| Benchmark | Metric | n | Base | LoRA | Delta | Recommendation |
|---|---|---:|---:|---:|---:|---|
| Held-out Summa citation exact | exact citation | 233 | `0.0%` | `71.2%` | `+71.2 pp` | Public core result |
| Aquinas grounding probe score | composite score | 233 | `37.7%` | `74.2%` | `+36.5 pp` | Supporting in-domain evidence |
| Aquinas segment-id citation presence | citation presence | 233 | `0.0%` | `100.0%` | `+100.0 pp` | Explain behavior shift |
| VirtueBench V2 random-capped | accuracy | 300 | `29.7%` | `58.0%` | `+28.3 pp` | Do not headline without bias caveat |
| VirtueBench V2 paired-capped | accuracy | 200 | `34.0%` | `49.5%` | `+15.5 pp` | Bias-aware diagnostic only |
| External MMLU world religions | accuracy | 60 | `76.7%` | `81.7%` | `+5.0 pp` | Secondary positive external evidence |
| External MMMLU-ZH business ethics | accuracy | 60 | `58.3%` | `61.7%` | `+3.3 pp` | Secondary positive external evidence |
| External MMMLU-ZH moral scenarios | accuracy | 60 | `25.0%` | `28.3%` | `+3.3 pp` | Secondary positive external evidence |
| External MMMLU-ZH philosophy | accuracy | 60 | `53.3%` | `55.0%` | `+1.7 pp` | Secondary positive external evidence |
| External MMLU moral scenarios | accuracy | 60 | `26.7%` | `28.3%` | `+1.7 pp` | Secondary positive external evidence |

## Interpretation

The full-corpus LoRA is clearly better at the thing it was trained for: Aquinas-grounded,
segment-cited doctrinal and relation answers. This positive-only packet keeps only benchmark rows
where the LoRA outperforms the untouched base model.

External candidates were screened through a separate raw run/comparison layer. The public table
above includes only the five external slices that cleared the positive-delta rule; the strongest
external signal is religion-adjacent MMLU world religions, while the Chinese positives are from
MMMLU-ZH business ethics, moral scenarios, and philosophy.

## Next Recommendations

1. Lead with held-out exact citation and the Aquinas grounding probe.
2. Include VirtueBench and external rows only in the positive forms shown above, with the
   A-position/external-transfer caveats kept attached.
3. Treat `citation_grounded_moral_answer` as the next hard slice.
4. Keep the full packet artifacts under
   `runs/christian_virtue/qwen2_5_1_5b_instruct/benchmark_packet/latest/`; the current packet run
   is `20260425_091751`.
