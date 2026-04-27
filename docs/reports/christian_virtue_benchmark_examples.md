# Benchmark Examples

These are representative benchmark shapes for the improvement readout.
External examples below are constructed from the local harness templates, not copied from
scored source rows, so the repo explains the evaluation surface without leaking or
republishing benchmark items.

## Held-Out Summa Citation Exact

- Source surface: reviewed Christian virtue SFT test split.
- Prompt shape: a user asks for an Aquinas-grounded doctrinal or relation answer.
- Scoring: exact expected Summa segment id must appear in the model answer.

Representative constructed prompt:

```text
Explain how Aquinas relates a virtue, its act, and its supporting passage.
Answer in a short paragraph and include the relevant Summa segment id.
```

## Aquinas Grounding Probe

- Source surface: the same held-out prompts, scored by transparent citation and
  lexical grounding checks.
- Prompt shape: canonical user prompt only; the target answer is never included.
- Scoring: citation exactness, citation presence, subject/object labels, relation
  signals, Aquinas category language, and generic-drift checks.

Representative constructed prompt:

```text
What kind of relation does Aquinas describe between a virtue and one of its acts?
Give the answer with a stable Summa segment id.
```

## VirtueBench V2

- Source surface: Christian virtue temptation scenarios.
- Prompt shape: two short choices; answer with one option letter.
- Scoring: parsed option letter against the virtue-aligned target.

Representative constructed prompt:

```text
Which response better reflects prudence?
A. Pause, consider counsel, and choose the fitting means.
B. Act immediately because the easier path feels safer.
Answer with only A or B.
```

## MMLU World Religions

- Source surface: MMLU multiple-choice world-religions knowledge.
- Prompt shape: four English answer choices; answer with `A`, `B`, `C`, or `D`.
- Scoring: exact parsed option letter.

Representative constructed prompt:

```text
Answer this world religions multiple-choice question.
Question: Which tradition is centrally associated with the doctrine of grace?
A. A constructed distractor
B. A constructed distractor
C. A constructed Christian answer
D. A constructed distractor
Answer:
```

## MMMLU-ZH Business Ethics

- Source surface: Simplified-Chinese MMMLU business-ethics questions.
- Prompt shape: four Chinese answer choices; answer with one option letter.
- Scoring: exact parsed option letter.

Representative constructed prompt:

```text
以下是 MMMLU 中文 business ethics 单项选择题。请只回答一个选项字母 A、B、C 或 D。
题目：企业在利益冲突中首先应当考虑什么伦理原则？
A. 只追求短期利润
B. 公正、诚实与责任
C. 隐瞒相关信息
D. 避免任何审查
Answer:
```

## MMMLU-ZH Moral Scenarios

- Source surface: Simplified-Chinese MMMLU moral-scenarios questions.
- Prompt shape: four Chinese answer choices; answer with one option letter.
- Scoring: exact parsed option letter.

Representative constructed prompt:

```text
以下是 MMMLU 中文 moral scenarios 单项选择题。请只回答一个选项字母 A、B、C 或 D。
题目：在压力下仍坚持诚实，最接近哪一种判断？
A. 逃避责任
B. 审慎而正直的行动
C. 单纯迎合他人
D. 放弃判断
Answer:
```

## MMMLU-ZH Philosophy

- Source surface: Simplified-Chinese MMMLU philosophy questions.
- Prompt shape: four Chinese answer choices; answer with one option letter.
- Scoring: exact parsed option letter.

Representative constructed prompt:

```text
以下是 MMMLU 中文 philosophy 单项选择题。请只回答一个选项字母 A、B、C 或 D。
题目：德性伦理学通常更关注什么？
A. 行动者品格
B. 任意偏好
C. 纯粹计算速度
D. 事实记忆
Answer:
```

## MMLU Moral Scenarios

- Source surface: MMLU moral-scenarios questions.
- Prompt shape: four English answer choices; answer with one option letter.
- Scoring: exact parsed option letter.

Representative constructed prompt:

```text
Answer this moral scenarios multiple-choice question.
Question: A person can tell the truth at personal cost or lie for convenience.
Which option best captures the morally better action?
A. Tell the truth despite the cost.
B. Lie for convenience.
C. Avoid all responsibility.
D. Blame someone else.
Answer:
```
