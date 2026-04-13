from summa_moral_graph.annotations.justice_core import build_justice_core_annotation_artifacts
from summa_moral_graph.annotations.justice_core_review import build_justice_core_review_queue
from summa_moral_graph.graph.justice_core import build_justice_core_graph_artifacts
from summa_moral_graph.validation.justice_core import build_justice_core_reports

if __name__ == "__main__":
    print(
        {
            "annotations": build_justice_core_annotation_artifacts(),
            "graph": build_justice_core_graph_artifacts(),
            "reports": build_justice_core_reports(),
            "review_queue": build_justice_core_review_queue(),
        }
    )
