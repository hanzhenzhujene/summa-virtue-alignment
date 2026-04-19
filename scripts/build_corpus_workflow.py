"""Build full-corpus candidate, coverage, and validation artifacts for the moral corpus."""

from summa_moral_graph.annotations.corpus import build_corpus_candidate_artifacts
from summa_moral_graph.annotations.corpus_review import build_corpus_review_artifacts
from summa_moral_graph.ingest.corpus import build_corpus_structural_artifacts
from summa_moral_graph.validation.corpus import build_corpus_reports

if __name__ == "__main__":
    print(build_corpus_structural_artifacts())
    print(build_corpus_candidate_artifacts())
    print(build_corpus_reports())
    print(build_corpus_review_artifacts())
