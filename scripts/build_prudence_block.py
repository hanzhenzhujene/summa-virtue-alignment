from summa_moral_graph.annotations.prudence import build_prudence_annotation_artifacts
from summa_moral_graph.annotations.review_queue import build_prudence_review_queue
from summa_moral_graph.graph.prudence import build_prudence_graph_artifacts
from summa_moral_graph.validation.prudence import build_prudence_reports

if __name__ == "__main__":
    print(build_prudence_annotation_artifacts())
    print(build_prudence_graph_artifacts())
    print(build_prudence_reports())
    print(build_prudence_review_queue())
