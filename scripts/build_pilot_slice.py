from summa_moral_graph.annotations.pilot import build_pilot_annotation_artifacts
from summa_moral_graph.annotations.pilot_review import build_pilot_review_artifacts
from summa_moral_graph.graph.pilot import build_pilot_graph_artifacts
from summa_moral_graph.validation.pilot import build_pilot_validation_artifacts


def main() -> None:
    print(build_pilot_annotation_artifacts())
    print(build_pilot_graph_artifacts())
    print(build_pilot_validation_artifacts())
    print(build_pilot_review_artifacts())


if __name__ == "__main__":
    main()
