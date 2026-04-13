from summa_moral_graph.annotations.theological_virtues import (
    build_theological_virtues_annotation_artifacts,
)
from summa_moral_graph.annotations.theological_virtues_review import (
    build_theological_virtues_review_queue,
)
from summa_moral_graph.graph.theological_virtues import (
    build_theological_virtues_graph_artifacts,
)
from summa_moral_graph.validation.theological_virtues import (
    build_theological_virtues_reports,
)

if __name__ == "__main__":
    print(build_theological_virtues_annotation_artifacts())
    print(build_theological_virtues_graph_artifacts())
    print(build_theological_virtues_reports())
    print(build_theological_virtues_review_queue())
