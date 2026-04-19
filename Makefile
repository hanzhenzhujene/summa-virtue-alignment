PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin
LOCAL_15B_ROOT := runs/christian_virtue/qwen2_5_1_5b_instruct
LOCAL_15B_REPORT := docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md
LOCAL_15B_PACKAGE_DIR := artifacts/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite_adapter
SMALL_MODEL_ROOT := runs/christian_virtue/qwen3_0_6b
SMALL_DATASET := data/processed/sft/exports/christian_virtue_v1/all.jsonl
SMALL_OOD_DATASET := data/processed/sft/exports/christian_virtue_v1_ood/all.jsonl
SMALL_SMOKE_METADATA := $(SMALL_MODEL_ROOT)/smoke/train_metadata.json
SMALL_PROTO_METADATA := $(SMALL_MODEL_ROOT)/proto/train_metadata.json
SMALL_BASE_TEST_PREDICTIONS := $(SMALL_MODEL_ROOT)/base_test/predictions.jsonl
SMALL_ADAPTER_TEST_PREDICTIONS := $(SMALL_MODEL_ROOT)/adapter_test/predictions.jsonl
SMALL_BASE_OOD_PREDICTIONS := $(SMALL_MODEL_ROOT)/base_ood/predictions.jsonl
SMALL_ADAPTER_OOD_PREDICTIONS := $(SMALL_MODEL_ROOT)/adapter_ood/predictions.jsonl
SMALL_BASE_TEST_METRICS := $(SMALL_MODEL_ROOT)/base_test/metrics.json
SMALL_ADAPTER_TEST_METRICS := $(SMALL_MODEL_ROOT)/adapter_test/metrics.json
SMALL_BASE_OOD_METRICS := $(SMALL_MODEL_ROOT)/base_ood/metrics.json
SMALL_ADAPTER_OOD_METRICS := $(SMALL_MODEL_ROOT)/adapter_ood/metrics.json
SMALL_COMPARE_TEST_REPORT := $(SMALL_MODEL_ROOT)/compare_test/report.md
SMALL_COMPARE_OOD_REPORT := $(SMALL_MODEL_ROOT)/compare_ood/report.md

.PHONY: \
	install setup-christian-virtue-local reproduce-christian-virtue-qwen2-5-1-5b-local \
	build-interim validate-interim build-corpus validate-candidates \
	build-pilot validate-pilot build-prudence validate-prudence \
	build-connected-virtues-109-120 validate-connected-virtues-109-120 \
	build-fortitude-parts-129-135 validate-fortitude-parts-129-135 \
	build-fortitude-closure-136-140 validate-fortitude-closure-136-140 \
	build-temperance-141-160 validate-temperance-141-160 \
	build-temperance-closure-161-170 validate-temperance-closure-161-170 \
	build-theological-virtues validate-theological-virtues \
	build-justice-core validate-justice-core build-religion-tract \
	validate-religion-tract build-owed-relation-tract validate-owed-relation-tract \
	review-queue review-pilot review-corpus review-theological-virtues \
	review-justice-core review-religion-tract review-owed-relation-tract \
	review-connected-virtues-109-120 review-fortitude-parts-129-135 \
	review-fortitude-closure-136-140 review-temperance-141-160 \
	review-temperance-closure-161-170 build-christian-virtue-sft \
	build-christian-virtue-sft-ood smoke-test-christian-virtue-sft \
	preflight-christian-virtue-gpu train-christian-virtue-proto \
	train-christian-virtue-qwen2-5-1-5b-local-smoke \
	train-christian-virtue-qwen2-5-1-5b-local-pilot-lite \
	train-christian-virtue-qwen2-5-1-5b-local-pilot \
	eval-christian-virtue-qwen2-5-1-5b-local-base-test \
	eval-christian-virtue-qwen2-5-1-5b-local-adapter-test \
	compare-christian-virtue-qwen2-5-1-5b-local-test \
	report-christian-virtue-qwen2-5-1-5b-local-pilot-lite \
	package-christian-virtue-qwen2-5-1-5b-local-adapter \
	publish-christian-virtue-qwen2-5-1-5b-local-adapter \
	verify-christian-virtue-qwen2-5-1-5b-local-publishable \
	run-christian-virtue-qwen2-5-1-5b-local-loop \
	train-christian-virtue-small-smoke train-christian-virtue-small \
	generate-christian-virtue-predictions generate-christian-virtue-small-predictions \
	generate-christian-virtue-small-base-test generate-christian-virtue-small-adapter-test \
	generate-christian-virtue-small-base-ood generate-christian-virtue-small-adapter-ood \
	eval-christian-virtue-sft eval-christian-virtue-ood \
	eval-christian-virtue-small-base-test eval-christian-virtue-small-adapter-test \
	eval-christian-virtue-small-base-ood eval-christian-virtue-small-adapter-ood \
	compare-christian-virtue-small-test compare-christian-virtue-small-ood \
	run-christian-virtue-small-loop app test lint typecheck check

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e ".[dev]"

setup-christian-virtue-local:
	bash scripts/setup_christian_virtue_local.sh

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

$(SMALL_DATASET): configs/sft/christian_virtue_v1.yaml scripts/build_christian_virtue_sft_dataset.py
	$(BIN)/python scripts/build_christian_virtue_sft_dataset.py --config configs/sft/christian_virtue_v1.yaml

$(SMALL_OOD_DATASET): configs/sft/christian_virtue_v1_ood.yaml scripts/build_christian_virtue_sft_dataset.py
	$(BIN)/python scripts/build_christian_virtue_sft_dataset.py --config configs/sft/christian_virtue_v1_ood.yaml

build-christian-virtue-sft: $(SMALL_DATASET)

build-christian-virtue-sft-ood: $(SMALL_OOD_DATASET)

smoke-test-christian-virtue-sft:
	$(BIN)/python scripts/smoke_test_christian_virtue_sft.py

preflight-christian-virtue-gpu:
	$(BIN)/python scripts/preflight_christian_virtue_gpu.py

train-christian-virtue-proto:
	$(BIN)/python scripts/train_christian_virtue_qlora.py --config configs/train/qwen3_4b_qlora.yaml

train-christian-virtue-qwen2-5-1-5b-local-smoke:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh smoke

train-christian-virtue-qwen2-5-1-5b-local-pilot-lite:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh pilot-lite

train-christian-virtue-qwen2-5-1-5b-local-pilot:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh pilot

eval-christian-virtue-qwen2-5-1-5b-local-base-test:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh

eval-christian-virtue-qwen2-5-1-5b-local-adapter-test:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh

compare-christian-virtue-qwen2-5-1-5b-local-test:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_compare.sh

report-christian-virtue-qwen2-5-1-5b-local-pilot-lite:
	$(BIN)/python scripts/build_christian_virtue_local_report.py

package-christian-virtue-qwen2-5-1-5b-local-adapter:
	$(BIN)/python scripts/publish_christian_virtue_adapter.py --skip-hf --skip-github-release

publish-christian-virtue-qwen2-5-1-5b-local-adapter:
	$(BIN)/python scripts/publish_christian_virtue_adapter.py

verify-christian-virtue-qwen2-5-1-5b-local-publishable:
	$(MAKE) build-christian-virtue-sft
	$(MAKE) report-christian-virtue-qwen2-5-1-5b-local-pilot-lite
	$(MAKE) package-christian-virtue-qwen2-5-1-5b-local-adapter
	$(BIN)/pytest tests/test_sft_public_artifacts.py tests/test_sft_publication.py tests/test_sft_reporting.py
	$(BIN)/python scripts/verify_christian_virtue_publication.py

run-christian-virtue-qwen2-5-1-5b-local-loop:
	bash scripts/run_christian_virtue_qwen2_5_1_5b_local_loop.sh

reproduce-christian-virtue-qwen2-5-1-5b-local:
	bash scripts/reproduce_christian_virtue_qwen2_5_1_5b_local.sh

$(SMALL_SMOKE_METADATA): $(SMALL_DATASET) configs/train/qwen3_0_6b_qlora_smoke.yaml scripts/run_christian_virtue_small_train.sh scripts/christian_virtue_small_common.sh scripts/preflight_christian_virtue_gpu.py scripts/train_christian_virtue_qlora.py
	bash scripts/run_christian_virtue_small_train.sh smoke

$(SMALL_PROTO_METADATA): $(SMALL_DATASET) configs/train/qwen3_0_6b_qlora.yaml scripts/run_christian_virtue_small_train.sh scripts/christian_virtue_small_common.sh scripts/preflight_christian_virtue_gpu.py scripts/train_christian_virtue_qlora.py
	bash scripts/run_christian_virtue_small_train.sh proto

train-christian-virtue-small-smoke: $(SMALL_SMOKE_METADATA)

train-christian-virtue-small: $(SMALL_PROTO_METADATA)

generate-christian-virtue-predictions:
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_4b_base_test.yaml

$(SMALL_BASE_TEST_PREDICTIONS): $(SMALL_DATASET) configs/inference/qwen3_0_6b_base_test.yaml scripts/generate_christian_virtue_predictions.py
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_base_test.yaml

$(SMALL_ADAPTER_TEST_PREDICTIONS): $(SMALL_DATASET) $(SMALL_PROTO_METADATA) configs/inference/qwen3_0_6b_adapter_test.yaml scripts/generate_christian_virtue_predictions.py
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_adapter_test.yaml

$(SMALL_BASE_OOD_PREDICTIONS): $(SMALL_OOD_DATASET) configs/inference/qwen3_0_6b_base_ood.yaml scripts/generate_christian_virtue_predictions.py
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_base_ood.yaml

$(SMALL_ADAPTER_OOD_PREDICTIONS): $(SMALL_OOD_DATASET) $(SMALL_PROTO_METADATA) configs/inference/qwen3_0_6b_adapter_ood.yaml scripts/generate_christian_virtue_predictions.py
	$(BIN)/python scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_adapter_ood.yaml

generate-christian-virtue-small-predictions: generate-christian-virtue-small-base-test

generate-christian-virtue-small-base-test: $(SMALL_BASE_TEST_PREDICTIONS)

generate-christian-virtue-small-adapter-test: $(SMALL_ADAPTER_TEST_PREDICTIONS)

generate-christian-virtue-small-base-ood: $(SMALL_BASE_OOD_PREDICTIONS)

generate-christian-virtue-small-adapter-ood: $(SMALL_ADAPTER_OOD_PREDICTIONS)

$(SMALL_BASE_TEST_METRICS): $(SMALL_BASE_TEST_PREDICTIONS) scripts/eval_christian_virtue_sft.py
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1 --predictions $(SMALL_BASE_TEST_PREDICTIONS) --splits test --report-path $(SMALL_MODEL_ROOT)/base_test/report.md --metrics-path $(SMALL_BASE_TEST_METRICS)

$(SMALL_ADAPTER_TEST_METRICS): $(SMALL_ADAPTER_TEST_PREDICTIONS) scripts/eval_christian_virtue_sft.py
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1 --predictions $(SMALL_ADAPTER_TEST_PREDICTIONS) --splits test --report-path $(SMALL_MODEL_ROOT)/adapter_test/report.md --metrics-path $(SMALL_ADAPTER_TEST_METRICS)

$(SMALL_BASE_OOD_METRICS): $(SMALL_BASE_OOD_PREDICTIONS) scripts/eval_christian_virtue_sft.py
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1_ood --predictions $(SMALL_BASE_OOD_PREDICTIONS) --splits ood_test --report-path $(SMALL_MODEL_ROOT)/base_ood/report.md --metrics-path $(SMALL_BASE_OOD_METRICS)

$(SMALL_ADAPTER_OOD_METRICS): $(SMALL_ADAPTER_OOD_PREDICTIONS) scripts/eval_christian_virtue_sft.py
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1_ood --predictions $(SMALL_ADAPTER_OOD_PREDICTIONS) --splits ood_test --report-path $(SMALL_MODEL_ROOT)/adapter_ood/report.md --metrics-path $(SMALL_ADAPTER_OOD_METRICS)

eval-christian-virtue-sft:
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1 --splits test

eval-christian-virtue-ood:
	$(BIN)/python scripts/eval_christian_virtue_sft.py --dataset-dir data/processed/sft/exports/christian_virtue_v1_ood --splits ood_test

eval-christian-virtue-small-base-test: $(SMALL_BASE_TEST_METRICS)

eval-christian-virtue-small-adapter-test: $(SMALL_ADAPTER_TEST_METRICS)

eval-christian-virtue-small-base-ood: $(SMALL_BASE_OOD_METRICS)

eval-christian-virtue-small-adapter-ood: $(SMALL_ADAPTER_OOD_METRICS)

$(SMALL_COMPARE_TEST_REPORT): $(SMALL_BASE_TEST_METRICS) $(SMALL_ADAPTER_TEST_METRICS) scripts/compare_christian_virtue_runs.py
	$(BIN)/python scripts/compare_christian_virtue_runs.py --baseline-metrics $(SMALL_BASE_TEST_METRICS) --candidate-metrics $(SMALL_ADAPTER_TEST_METRICS) --baseline-label qwen3-0.6b-base-test --candidate-label qwen3-0.6b-adapter-test --output $(SMALL_COMPARE_TEST_REPORT)

$(SMALL_COMPARE_OOD_REPORT): $(SMALL_BASE_OOD_METRICS) $(SMALL_ADAPTER_OOD_METRICS) scripts/compare_christian_virtue_runs.py
	$(BIN)/python scripts/compare_christian_virtue_runs.py --baseline-metrics $(SMALL_BASE_OOD_METRICS) --candidate-metrics $(SMALL_ADAPTER_OOD_METRICS) --baseline-label qwen3-0.6b-base-ood --candidate-label qwen3-0.6b-adapter-ood --output $(SMALL_COMPARE_OOD_REPORT)

compare-christian-virtue-small-test: $(SMALL_COMPARE_TEST_REPORT)

compare-christian-virtue-small-ood: $(SMALL_COMPARE_OOD_REPORT)

run-christian-virtue-small-loop:
	bash scripts/run_christian_virtue_small_loop.sh

app:
	$(BIN)/streamlit run streamlit_app.py

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check .

typecheck:
	$(BIN)/mypy src tests app

check: lint typecheck test validate-interim validate-pilot validate-prudence validate-connected-virtues-109-120 validate-fortitude-parts-129-135 validate-fortitude-closure-136-140 validate-temperance-141-160 validate-temperance-closure-161-170 validate-theological-virtues validate-justice-core validate-religion-tract validate-owed-relation-tract validate-candidates
