# Dashboard Interaction Audit

This audit covers the unified Streamlit shell in `streamlit_app.py` and the wrapper pages in `app/`.

The goal is to keep the dashboard readable, evidence-first, and state-stable across:

- Home
- Concept Explorer
- Passage Explorer
- Overall Map
- Stats / Audit

## Audit scope

The audit checks:

- `st.button`
- `st.download_button`
- navigation buttons and page wrappers
- concept / passage / map route transitions
- graph click behavior and fallback behavior
- tract preset, question range, relation filter, focus-tag, and scope state interactions
- cross-view session state consistency

## Global shell and cross-view state

| Area | Control / state path | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|---|
| Sidebar | top-level view radio | Switches active view without losing shared session state | No hard bug found | Working | Manual click across all views |
| Sidebar | tract preset selectbox | Applies shared tract scope to concept, passage, and map views | Scope was later silently lost in concept fallback path | Fixed | Unit tests + manual scope switch |
| Sidebar | Download Data | Always visible and exports dashboard snapshot | No hard bug found; visibility previously too weak | Working and more visible | Manual click + file download |
| Shared state | `smg_map_range` | Must always be a valid `(start, end)` tuple | Could accept stale / malformed state and be blindly cast | Fixed | Unit test for range normalization |
| Shared state | selected concept / passage / edge | Must stay valid when moving across views | Passage state could become stale against current result set | Fixed | Unit test + manual filter change |
| Shared state | graph mode | Route buttons that promise overall map must force overall map | Home and concept flows could inherit stale local-map mode | Fixed | Unit test + manual route click |

## Home

| Control | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|
| Open concept | Opens selected concept in Concept Explorer | No hard bug found | Working | Manual click |
| Read passage | Opens selected passage in Passage Explorer | No hard bug found | Working | Manual click |
| Open tract in concepts | Activates preset and opens Concept Explorer | Hidden blank preset left the route looking dead because the button started disabled | Fixed with a real default tract selection | Unit test + manual click |
| Open overall map | Opens map view in true overall-map mode | Could inherit old `MAP_MODE_KEY` and land in local map | Fixed | Unit test + manual click |
| Open Audit | Opens Stats / Audit on reader stats tab | No hard bug found | Working | Manual click |
| Home download buttons | Download payload without changing state | No hard bug found | Working | Manual click |

## Concept Explorer

| Control | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|
| Concept search | Narrows concept list by label / alias / type | No hard bug found | Working | Manual search |
| Concept selectbox | Keeps chosen concept aligned with visible results | No hard bug found | Working | Manual selection |
| Concept shortcut buttons | Opens clicked related concept | No hard bug found | Working | Manual click |
| Local map node clicks | Opens clicked concept when interactive component is available | Silent fallback hid lost click behavior | Fixed with explicit warning | Unit tests + manual fallback check |
| Open overall map around this concept | Opens overall map, centered on current concept | Button text said overall map but behavior opened local map | Fixed | Unit test via shared route helper + manual click |
| Read passage buttons in support cards | Opens supporting passage | No hard bug found | Working | Manual click |
| Editorial / candidate expanders | Keep reviewed / editorial / candidate layers visibly separate | No hard bug found, but tract scope could silently disappear | Fixed scope handling | Manual click + scope checks |
| Tract-scoped concept payload | Keeps tract empty state instead of silently widening to full corpus | Sparse tract payloads could silently fall back to corpus view | Fixed; broader fallback must be explicit | Unit test |

## Passage Explorer

| Control | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|
| Search box | Filters passages by text, id, label, and concept hints | No hard bug found | Working | Manual search |
| Advanced filters | Narrow result set by part, question, article, segment type | No hard bug found | Working | Manual filter sweep |
| Result cards | Open selected passage into reader panel | No hard bug found | Working | Manual click |
| Previous / Next passage | Move within current visible result set | No hard bug found, but could feel stale because selected passage stuck | Working with reset logic | Manual click |
| Linked concept buttons | Open concept from current passage | No hard bug found | Working | Manual click |
| Inspect in map | Opens overall map from reviewed relation | No hard bug found | Working | Manual click |
| Selected passage sync | If current selected passage is not in visible results, switch to first visible result; if none, clear | Old passage could remain visible even when current results no longer contained it | Fixed | Unit tests + manual filter change |

## Overall Map

| Control | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|
| Map mode radio | Switches clearly between local and overall map | Route buttons could leave mode stale | Fixed by explicit route forcing | Unit test + manual toggle |
| Structural / editorial / candidate toggles | Keep non-doctrinal layers explicit and optional | No hard bug found | Working | Manual toggle |
| Center concept | Drives local map and concept-centered overall exploration | No hard bug found | Working | Manual selection |
| Question spotlight | Narrows map slice by question | No hard bug found | Working | Manual selection |
| Quick span buttons | Jump the question-range slider and immediately redraw the map for the chosen reviewed span | Cross-tract spans only worked for the first two buttons because range rendering assumed a single tract family | Fixed with cross-family range aggregation + widget-safe range updates | Unit tests + manual click |
| Question span slider | Supports arbitrary reviewed spans without blanking the map just because the span crosses tract-family boundaries | Cross-family spans could collapse to an empty map / scope prompt | Fixed with cross-family range aggregation | Unit tests + manual drag |
| Relation-group / relation-type / node-type filters | Narrow map without breaking state | No hard bug found | Working | Manual filter sweep |
| Focus tags | Always remain visible and clearable | Focus-tag control could disappear when its own filter emptied the graph | Fixed | Unit test + manual empty-map recovery |
| Evidence segment-type filter | Filters by supporting segment types | No hard bug found | Working | Manual filter sweep |
| Node clicks | Navigate from graph node to concept page | Silent fallback made clicks fail with no explanation | Fixed with explicit static-fallback warning | Unit tests + manual fallback check |
| Evidence spotlight selectbox | Keeps selected edge stable within visible slice | No hard bug found | Working | Manual selection |
| Open source / target concept | Jumps to corresponding concept page | No hard bug found | Working | Manual click |
| Read supporting passage | Opens supporting passage from selected edge | No hard bug found | Working | Manual click |
| Download edges / nodes / snapshot | Export current visible slice | No hard bug found; button affordance previously weak | Working and still explicit | Manual click |
| Structural range behavior | Structural map rows should not silently ignore I-II | Structural range helper only accepted `st.ii-ii.q...` | Fixed | Unit test |

## Stats / Audit

| Control | Expected behavior | Prior issue | Status after fix | Verification |
|---|---|---|---|---|
| Stats tab radio | Switches tabs while staying inside audit page | No hard bug found | Working | Manual click |
| Coverage filters | Narrow question coverage table | No hard bug found | Working | Manual filter sweep |
| Review / validation tables | Stay available but secondary to reader-facing pages | No hard bug found, but this area previously dominated the app | Working in secondary position | Manual review |

## Known UX traps addressed in this refactor

1. Overall-map route buttons now force overall-map mode instead of inheriting stale local-map state.
2. Passage reader selection now resets predictably when filters change.
3. Tract-scoped concept pages no longer silently widen to a full-corpus rendering when tract evidence is sparse.
4. Static graph fallback is now explicit, with a warning and alternate navigation guidance.
5. Focus tags remain visible and clearable even when they filter the graph to zero rows.
6. Structural range filtering now accounts for both `I-II` and `II-II` structural questions.
7. Map range state is normalized before use instead of being blindly cast.
8. Button labeling and behavior for concept → overall map now match.

## Verification plan

Run:

```bash
PYTHONPATH=src pytest tests/test_viewer.py tests/test_viewer_interactions.py -q
```

Then manually smoke-test:

1. Home → Open concept
2. Home → Read passage
3. Home → Open overall map
4. Concept Explorer → Open overall map around this concept
5. Passage Explorer → change filters until the old selected passage falls out of results
6. Overall Map → apply focus tags until the map empties, then clear them
7. Overall Map → click `57–122`, `141–170`, and `All` in quick spans and confirm the map still renders
8. Overall Map → drag `Question span` across multiple tract blocks and confirm the map still renders
9. Overall Map → confirm static fallback warning appears if interactive graph bridge is unavailable
