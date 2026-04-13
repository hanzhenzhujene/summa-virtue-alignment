# Fortitude Tract Synthesis

This synthesis export combines the existing reviewed fortitude-parts block (`II-II qq.129-135`) with the fortitude-closure block (`II-II qq.136-140`).

Default synthesis behavior:
- includes only reviewed doctrinal edges
- preserves provenance to annotation ids and passage ids
- excludes candidate mentions and candidate relation proposals

Optional editorial layer:
- `data/processed/fortitude_tract_synthesis_with_editorial.graphml` adds reviewed structural-editorial correspondences for inspection
- editorial correspondences remain outside default doctrinal graph views

Current scope note:
- this repository state does not yet include a dedicated reviewed doctrinal fortitude-core block for `II-II qq.123-128`
- accordingly, the synthesis export is structurally situated inside the fortitude tract `qq.123-140`, but its doctrinal population currently comes from the reviewed `qq.129-140` layers only

Current counts:
- synthesis nodes: `89`
- synthesis edges: `64`
- gift-linkage relations in closure block: `6`
- precept-linkage relations in closure block: `9`
