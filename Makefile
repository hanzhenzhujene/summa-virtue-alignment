PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install build-interim validate-interim build-corpus validate-candidates build-pilot validate-pilot build-prudence validate-prudence build-connected-virtues-109-120 validate-connected-virtues-109-120 build-fortitude-parts-129-135 validate-fortitude-parts-129-135 build-fortitude-closure-136-140 validate-fortitude-closure-136-140 build-temperance-141-160 validate-temperance-141-160 build-temperance-closure-161-170 validate-temperance-closure-161-170 build-theological-virtues validate-theological-virtues build-justice-core validate-justice-core build-religion-tract validate-religion-tract build-owed-relation-tract validate-owed-relation-tract review-queue review-pilot review-corpus review-theological-virtues review-justice-core review-religion-tract review-owed-relation-tract review-connected-virtues-109-120 review-fortitude-parts-129-135 review-fortitude-closure-136-140 review-temperance-141-160 review-temperance-closure-161-170 build-christian-virtue-sft smoke-test-christian-virtue-sft train-christian-virtue-proto train-christian-virtue-small generate-christian-virtue-predictions generate-christian-virtue-small-predictions eval-christian-virtue-sft eval-christian-virtue-ood app test lint typecheck check

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e ".[dev]"

build-interim:
	$(BIN)/summa-moral-graph build-interim

validate-interim:
	$(BIN)/summa-moral-graph validate-interim

build-corpus:
	$(BIN)/summa-moral-graph build-corpus

validate-candidates:
	$(BIN)/summa-moral-graph validate-candidates

build-pilot:
	$(BIN)/summa-moral-graph build-pilot

validate-pilot:
	$(BIN)/summa-moral-graph validate-pilot

build-prudence:
	$(BIN)/summa-moral-graph build-prudence

validate-prudence:
	$(BIN)/summa-moral-graph validate-prudence

build-connected-virtues-109-120:
	$(BIN)/summa-moral-graph build-connected-virtues-109-120

validate-connected-virtues-109-120:
	$(BIN)/summa-moral-graph validate-connected-virtues-109-120

build-fortitude-parts-129-135:
	$(BIN)/summa-moral-graph build-fortitude-parts-129-135

validate-fortitude-parts-129-135:
	$(BIN)/summa-moral-graph validate-fortitude-parts-129-135

build-fortitude-closure-136-140:
	$(BIN)/summa-moral-graph build-fortitude-closure-136-140

validate-fortitude-closure-136-140:
	$(BIN)/summa-moral-graph validate-fortitude-closure-136-140

build-temperance-141-160:
	$(BIN)/summa-moral-graph build-temperance-141-160

validate-temperance-141-160:
	$(BIN)/summa-moral-graph validate-temperance-141-160

build-temperance-closure-161-170:
	$(BIN)/summa-moral-graph build-temperance-closure-161-170

validate-temperance-closure-161-170:
	$(BIN)/summa-moral-graph validate-temperance-closure-161-170

build-theological-virtues:
	$(BIN)/summa-moral-graph build-theological-virtues

validate-theological-virtues:
	$(BIN)/summa-moral-graph validate-theological-virtues

build-justice-core:
	$(BIN)/summa-moral-graph build-justice-core

validate-justice-core:
	$(BIN)/summa-moral-graph validate-justice-core

build-religion-tract:
	$(BIN)/summa-moral-graph build-religion-tract

validate-religion-tract:
	$(BIN)/summa-moral-graph validate-religion-tract

build-owed-relation-tract:
	$(BIN)/summa-moral-graph build-owed-relation-tract

validate-owed-relation-tract:
	$(BIN)/summa-moral-graph validate-owed-relation-tract

review-queue:
	$(BIN)/python scripts/build_prudence_review_queue.py

review-pilot:
	$(BIN)/python scripts/pilot_review_tools.py

review-corpus:
	$(BIN)/python scripts/build_corpus_review_queue.py

review-theological-virtues:
	$(BIN)/python scripts/build_theological_virtues_review_queue.py

review-justice-core:
	$(BIN)/python scripts/build_justice_core_review_queue.py

review-religion-tract:
	$(BIN)/python scripts/build_religion_tract_review_queue.py

review-owed-relation-tract:
	$(BIN)/python scripts/build_owed_relation_tract_review_queue.py

review-connected-virtues-109-120:
	$(BIN)/python scripts/build_connected_virtues_109_120_review_queue.py

review-fortitude-parts-129-135:
	$(BIN)/python scripts/build_fortitude_parts_129_135_review_queue.py

review-fortitude-closure-136-140:
	$(BIN)/python scripts/build_fortitude_closure_136_140_review_queue.py

review-temperance-141-160:
	$(BIN)/python scripts/build_temperance_141_160_review_queue.py

review-temperance-closure-161-170:
	$(BIN)/python scripts/build_temperance_closure_161_170_review_queue.py

build-christian-virtue-sft:
	$(BIN)/python scripts/build_christian_virtue_sft_dataset.py --config configs/sft/christian_virtue_v1.yaml

smoke-test-christian-virtue-sft:
	$(BIN)/python scripts/smoke_test_christian_virtue_sft.py

train-christian-virtue-proto:
	$(BIN)/python scripts/train_christian_virtue_qlora.py --config configs/train/qwen3_4b_qlora.yaml

train-christian-virtue-small:
	$(BIN)/python scripts/train_christian_virtue_qlora.py --config configs/train/qwen3_0_6b_qlora.yaml

generate-christian-virtue-predictions:
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_4b_base_test.yaml

generate-christian-virtue-small-predictions:
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_base_test.yaml

eval-christian-virtue-sft:
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1 --splits test

eval-christian-virtue-ood:
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1_ood --splits ood_test

app:
	$(BIN)/streamlit run streamlit_app.py

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check .

typecheck:
	$(BIN)/mypy src tests app

check: lint typecheck test validate-interim validate-pilot validate-prudence validate-connected-virtues-109-120 validate-fortitude-parts-129-135 validate-fortitude-closure-136-140 validate-temperance-141-160 validate-temperance-closure-161-170 validate-theological-virtues validate-justice-core validate-religion-tract validate-owed-relation-tract validate-candidates
