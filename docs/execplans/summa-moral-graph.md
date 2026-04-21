# Summa Moral Graph Execution Plan

## Progress

- The public release surface now has an explicit claim-to-artifact contract:
  - a new `docs/public_claim_map.md` now states the current public claims, the exact artifacts
    that support them, the reproduction commands, and the claim boundaries
  - README now links that claim map directly from both `Repository Structure` and `Start Here`
  - `docs/repository_map.md`, the dataset card, and the publication verifier now treat the claim
    map as a first-class public surface rather than an optional extra
- The README is now being tightened around repo anatomy and reproducibility, not just results:
  - a new `Repository Structure` section now tells a first-time reader where the dataset, SFT
    package, scripts, reports, and release artifacts live
  - the canonical command path is now framed explicitly as a `Reproducibility Contract`
  - this makes the repo read more like a serious paper companion and less like a collection of
    good artifacts without one explicit top-level map
- The public visual pass is now being pushed from “good enough” to release-grade consistency:
  - the README landing zone has been decluttered by removing low-value badge noise and replacing
    the first two table-heavy sections with denser prose bullets
  - the flagship `local-baseline` report now keeps the goal-demo panel in collapsible
    `<details>` blocks with a small panel-summary table, so the report scans like a paper artifact
    instead of a raw transcript dump
  - the completed citation-frontier follow-up report now uses human-readable slice labels and a
    proper figure caption, and its SVG subtitle now states that it is a completed same-budget
    follow-up rather than a generic audit
- The public-release gate is now being tightened around the new citation-frontier artifacts instead
  of only the canonical baseline bundle:
  - `verify_publication_bundle` now validates
    `docs/reports/christian_virtue_citation_frontier_audit.md`
  - it also now validates
    `docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md`
  - the release verifier therefore covers both the public baseline and the completed follow-up
    result instead of leaving the latter outside the contract
- The citation-frontier follow-up has now completed as a real local run rather than a planned
  recipe:
  - train run `20260421_005543` completed on Apple `mps` in about `6.8` minutes
  - adapter eval run `20260421_010240` completed and writes the new held-out metrics
  - overall held-out exact citation improved from `0.356` to `0.386`
  - the hardest user-style task `citation_grounded_moral_answer` moved from `0.000` to `0.030`
    exact stable-id recovery
  - the same run also surfaced real tradeoffs, especially `justice_core` (`0.452` to `0.190`) and
    `strong_textual_inference` (`0.486` to `0.200`)
- The repo is now being updated so this completed follow-up is represented as a first-class
  research artifact instead of staying buried under `runs/`:
  - the committed frontier audit has been refreshed to the finished `citation_frontier` adapter
  - a new curated follow-up report now summarizes the completed same-budget citation-heavy run
  - README, fine-tune guide, repository map, scripts guide, and experiment index now distinguish
    clearly between the public `local-baseline` demo and the finished citation-frontier follow-up
- The main public guide surfaces are now being synchronized to the new citation-frontier recipe so
  the code and the docs no longer diverge:
  - `docs/fine_tune_with_summa_moral_graph.md` now explains the citation-frontier experiment as
    the next concrete local step after the canonical baseline
  - the fine-tune guide now names the exact quota-based task mix and expected run directories
  - `docs/repository_map.md` now lists the citation-frontier configs and audit wrapper directly
  - repo-surface tests now assert that the fine-tune guide and repository map keep exposing that
    path
- The next research expansion is now implemented as a concrete same-budget local recipe instead of
  only a prose recommendation:
  - `TrainingConfig` now supports `task_tract_quota_round_robin` plus explicit
    `train_task_type_quotas` / `eval_task_type_quotas`
  - the new config
    `configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml` keeps the same `128`
    examples / `20` steps / `Qwen/Qwen2.5-1.5B-Instruct` local budget as `local-baseline`
  - that recipe shifts the tiny train subset to `64` citation-grounded moral answers, `24`
    reviewed relation explanations, `24` virtue concept explanations, and `16`
    passage-grounded doctrinal QA examples
  - the matching eval subset is now `32` examples with a citation-heavy but still mixed task
    distribution
  - wrapper scripts, Make targets, and docs now expose a one-command path:
    `make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop`
  - the frontier audit now names this recipe explicitly as the next under-five-hour local
    experiment instead of stopping at a generic recommendation
- The next public-release hardening pass is now tightening orientation and first-open trust rather
  than changing the dataset or model claim:
  - README now includes an explicit method overview instead of leaving the workflow implied across
    later sections
  - README now also names the expected outputs of the canonical local path, so reproducibility is
    defined in concrete artifacts rather than only in commands
  - `docs/repository_map.md` now exposes a small canonical public bundle section for reviewers who
    want the minimum set of files that define the release
  - key public-facing modules (`cli`, dashboard loader, tract registry, corpus ingest builder, and
    viewer loader) now carry top-level docstrings so a new reader can infer their role at file open
  - local `.DS_Store` files and `__pycache__` directories have been cleaned so the worktree reads
    more like a research release and less like a casual local workspace
- The public visual system is being tightened into one consistent research-release style instead of
  a mix of older and newer chart treatments:
  - the shared report renderers now add explicit axis titles, cleaner spacing, stronger hierarchy,
    and more legible legends
  - the training trace now labels actual logged steps rather than interpolated pseudo-steps like
    `8.8` or `12.5`
  - the citation-frontier figure now states its takeaway directly in the figure and uses a clearer
    0–100% scale for failure-mode interpretation
  - the timing-comparison asset has been restyled to match the same card, axis, and legend system
    as the other public SVGs
- The balanced-subset local rerun has now been inspected against its full held-out test results:
  - the new `local-baseline` train run is `20260420_160727`
  - the matching base and adapter eval runs are `20260420_162346` and `20260420_190542`
  - the matching comparison run is `20260420_193654`
  - overall held-out citation exact match improved from `0.137` on the older first-rows run to
    `0.356` on the balanced-subset rerun
  - the strongest new gains are now `0.656` on virtue concept explanation and `0.582` on reviewed
    relation explanation
  - the remaining major weakness is unchanged: `citation_grounded_moral_answer` stays at `0.000`
- The local 1.5B recipe now has an explicit, structured fix for its small-run subset bias:
  - `TrainingConfig` now exposes `train_subset_strategy` and `eval_subset_strategy`
  - the new deterministic `task_tract_round_robin` strategy is implemented in
    `src/summa_moral_graph/sft/sampling.py`
  - the Apple-Silicon `smoke`, `local-baseline`, and `extended` configs now opt into that
    balanced strategy by default
  - training runs now emit `subset_summary.json` plus matching subset metadata inside
    `train_metadata.json` and `run_manifest.json`
  - docs and report-generation logic now describe subset policy from run metadata instead of
    hardcoding the old first-rows behavior
- The current local `Qwen/Qwen2.5-1.5B-Instruct` baseline is being re-audited as a training recipe
  rather than treated as a fixed quality ceiling:
  - the public `local-baseline` rung is confirmed to be intentionally tiny at `128` train examples,
    `16` eval examples, and `20` optimizer steps
  - the strongest corrected gain now lands on virtue concept explanation (`65.6%` exact), with
    reviewed relation explanation also reaching `58.2%`
  - the weakest family remains `citation_grounded_moral_answer`
  - the immediate next optimization questions are therefore about recipe strength, task-balance,
    and trainer loss geometry rather than about expanding dataset scope
- The next-step research frontier is now implemented as a first-class fast audit instead of a vague
  note:
  - `src/summa_moral_graph/sft/frontier.py` now analyzes the held-out
    `citation_grounded_moral_answer` slice as the remaining bottleneck
  - `scripts/audit_christian_virtue_frontier.py` turns that analysis into a one-command local
    report and SVG figure
  - `make audit-christian-virtue-qwen2-5-1-5b-local-frontier` now runs the audit in seconds
  - the committed frontier report states the current local thesis clearly: keep the virtue dataset
    fixed, and target stable-id recovery on user-style moral QA as the next expansion
- The committed public surfaces are now synchronized to the stronger `20260420` canonical local
  baseline rather than the older `0.137` first-rows run:
  - README, fine-tune guide, dataset card, maintainer doc, experiment index, and flagship report
    now point to `20260420_160727` / `20260420_190542`
  - the top-level public result table now foregrounds the current `0.356` overall held-out exact
    plus the strongest virtue-aligned slices instead of the weaker older highlights
  - repo-surface tests were updated so they verify the new wording and numbers instead of pinning
    stale phrasing
- The canonical adapter package is now a better audit artifact in its own right:
  - `subset_summary.json` is copied into the published local adapter package alongside
    `train_metadata.json` and `run_manifest.json`
  - the package README and release notes now tell readers that they can inspect the exact balanced
    `(task_type, tract)` subset composition directly from the packaged files
- The SFT README opening is being tightened one step further around the dataset itself:
  - the dataset's purpose and merit are now being stated explicitly at the top instead of being
    inferred only from later sections
  - the former `Public Result` block is being renamed toward a clearer `Training Demo` framing
  - wording that understated the public claim, such as `narrow`, is being removed from the main
    README result surface
- The two public repo fronts are being polished so they feel more like a matched project pair:
  - the SFT README top now uses a compact `Start here / Companion graph` table instead of a plain
    cross-link quote
  - a small `At A Glance` block now gives the dataset, baseline-run, and audit-trail story in one
    quick scan
  - the effect is intentionally a bit cuter and more public-facing, but still compact enough to
    avoid turning the README into a wall of marketing copy
- The top-level repo surface is being decluttered so GitHub root reads less like a workbench:
  - the archival `aquinas_summa_moral_graph_implementation_plan.md` file has been moved under
    `docs/archive/`
  - `docs/repository_map.md` now points at the archived location
  - the aim is to keep public entry files visible at the top while still preserving historical
    planning context inside the docs tree
- The fine-tuning repo README is being tightened again around the dataset's unique intellectual
  contribution, not just its reproducibility surface:
  - the former `Three Purposes` block is being replaced with a denser five-point section that
    explains why the dataset is philosophically and technically unusual
  - the new numbered block foregrounds relational supervision, Aquinas-specific ontology,
    evidence-first grounding, inspectability, and clean reviewed-vs-candidate separation
  - this framing is intentionally being added only to the SFT repo surface, not mirrored into the
    main graph repo, so the downstream training story stays distinct from the primary dashboard
    story
- The README landing page is being tightened again around first-open clarity rather than feature
  enumeration:
  - redundant top-level sections are being collapsed into a shorter public narrative
  - the two key SFT graphs now appear immediately near the top of the README instead of after a
    long doctrinal and repository preamble
  - README is now being rewritten toward denser tables, shorter prose, and fewer repeated claims,
    so a new reader can identify the dataset, result, purpose, and reproduction path faster
- The public results story is being tightened again so the repo's main surfaces foreground the
  strongest Christian-virtue wins instead of diluting them with weaker slices:
  - README, experiment index, curated report generator, and adapter-package prose are now being
    narrowed toward the strongest held-out virtue slices
  - the main public comparison graphic is also being restricted to the strongest task families, so
    the central `40.6%` virtue-concept gain is easier to see at a glance
  - weaker or zero-gain slices are being left to deeper audit surfaces instead of staying in the
    first-screen executive readout
- The Hugging Face adapter page has now been resynced to the updated held-out comparison graphic
  without breaking the established public release identity:
  - the canonical adapter package was republished to
    `JennyZhu0822/summa-virtue-qwen2.5-1.5b` after the figure-layout polish
  - the first upload exposed a subtle publication trap: leaving `--release-tag` unset caused the
    generated package to point at a run-id-based GitHub release slug that the repo does not
    actually publish
  - the package was immediately republished with the canonical continuity tag
    `christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038`, so the HF page now has both
    the improved figure and the correct public release link
  - the repo-tracked package `README.md`, `package_manifest.json`, and `release_notes.md` are now
    being advanced to the current GitHub commit as well so the repo and HF surfaces stay in sync
- The held-out improvement graphic now states the small-model framing inside the figure itself and
  visualizes the gain direction explicitly:
  - the SVG now labels the benchmark as a `Qwen/Qwen2.5-1.5B-Instruct (1.5B)` small-model demo
  - each goal-aligned task slice now includes an improvement arrow from base to adapter plus a
    delta-in-points label
  - the regenerated report asset and packaged adapter asset now carry the same updated comparison
    figure, so GitHub and package-facing surfaces stay visually aligned
- The release workflow is now updated to current GitHub-hosted action majors after the successful
  clean-checkout recovery:
  - `.github/workflows/public-release-check.yml` now uses `actions/checkout@v6` and
    `actions/setup-python@v6`
  - repo-surface tests now lock those versions in so the workflow does not silently drift back to
    a Node-20-based action pair that GitHub has already marked for deprecation
- The clean-checkout publication surface now includes a committed minimal adapter package instead
  of only local ignored files:
  - `.gitignore` now selectively admits the canonical package `README.md`, `package_manifest.json`,
    `release_notes.md`, and the held-out comparison SVG under
    `artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/`
  - README and the core SFT docs now link to that package `README.md` directly instead of assuming
    a local directory exists on every checkout
  - local `pytest` publication-surface checks and `make public-release-check` are green again after
    the package-surface fix, so the next GitHub Actions run should be testing the real release
    contract rather than a local-only illusion
- The public release gate now supports both local rebuild mode and clean-checkout verification mode:
  - when canonical local run artifacts are present, `make public-release-check` still rebuilds the
    flagship report and local adapter package before verifying them
  - when `runs/` is absent, the same gate now verifies the committed public surfaces directly
    instead of pretending a fresh CI checkout can reconstruct unpublished local training outputs
  - `verify_publication_bundle` now records whether it verified against full local run artifacts or
    against the committed package manifest alone
- The first real post-release CI regression has now been fixed at the source:
  - GitHub Actions surfaced a stricter `mypy` environment than the local interactive loop had
    exposed for `importlib.util.find_spec(...)`
  - the SFT runtime, training, and inference modules now import `find_spec` explicitly instead of
    relying on `importlib.util` attribute access
  - local `mypy` now passes on those modules, and `make public-release-check` is green again after
    the fix
- The external publication loop is now complete and publicly inspectable:
  - the Hugging Face adapter page is live at
    `https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b`
  - the matching GitHub release page is live at
    `https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038`
  - `make public-release-check` is green on the same repo state, and
    `.github/workflows/public-release-check.yml` now enforces that contract on `main`
  - the public provenance story is now explicit rather than implied:
    - the adapter-producing run remains `20260419_154300`
    - the run commit remains `662c9d3`
    - the publication commit that refreshed repo-facing docs, package links, and CI is `21dcc7c`
    - the older GitHub release slug is still intentionally preserved for continuity
- The publication bundle has now been brought back into coherence after the corrected rerun:
  - the local adapter package has been rebuilt from train run `20260419_154300` and adapter eval
    `20260419_154757`
  - the package manifest, copied provenance files, model-card text, and release notes now all carry
    the corrected `0.137` held-out citation-exact headline
  - package surfaces now state explicitly that the GitHub release keeps its older distribution tag
    slug for continuity while the repo-local package and flagship report are the authoritative
    evaluation surfaces for the corrected run
  - publication verification is therefore being restored as a meaningful integrity gate rather than
    silently pointing at a stale package snapshot
  - the canonical repo check `make public-release-check` is now green again, which means lint,
    type-checking, report regeneration, package regeneration, publication-surface tests, and the
    standalone publication verifier all agree on one stable artifact story
- The first-run local reproduction path is now being hardened as a user-facing research interface,
  not just a maintainer helper:
  - the canonical `reproduce_christian_virtue_qwen2_5_1_5b_local.sh` wrapper now fails fast with a
    clear setup instruction if the pinned `.venv` has not been created yet
  - the same wrapper now prints the key output paths for the report, package, and latest run dirs
    at the end of a successful run
  - `scripts/README.md` and repo-surface tests now cover those expectations so the newcomer path is
    explicit rather than implicit
  - the `Makefile` now carries explicit canonical constants for the Hugging Face repo id and
    GitHub release slug used by the local publication path, so the public artifact identity cannot
    drift silently on the next regeneration
- The repo now has a formal CI gate for the same public release contract it claims locally:
  - `.github/workflows/public-release-check.yml` now runs the canonical `make public-release-check`
    path on pushes and pull requests to `main`
  - the README now exposes that workflow as a visible badge near the top of the page
  - repo-surface tests now assert both that the workflow exists and that it really calls the
    canonical release-quality make target
- The manuscript-style local-baseline report has now been reconciled against the corrected SFT
  artifact rather than the older optimistic benchmark snapshot:
  - the `excess_opposed_to` / `deficiency_opposed_to` polarity bug has been fixed in the template
    layer and regression-tested
  - both committed dataset exports (`christian_virtue_v1` and `christian_virtue_v1_ood`) have been
    rebuilt from the corrected templates
  - the canonical local-baseline training rung has been rerun from commit `662c9d3` as
    run `20260419_154300`
  - the corrected held-out adapter evaluation has been rerun as `20260419_154757`, and the fresh
    comparison report now lives at `runs/.../compare_test/20260419_160910/report.md`
  - the flagship markdown report and GitHub-visible figures have been regenerated from those fresh
    artifacts
  - the report generator now reads config snapshots instead of hardcoding method details, so the
    manuscript-style writeup is derived from the actual run configuration
- The flagship local-baseline report is now being audited against the actual dataset templates and
  generated run artifacts rather than treated as correct by default:
  - the largest consistency bug found so far is a polarity error in the
    `citation_grounded_moral_answer` template for `excess_opposed_to` /
    `deficiency_opposed_to` relations
  - in the current export, those user questions sometimes ask for the vice opposed to the vice
    subject, while the underlying annotation actually encodes a vice-to-virtue opposition
  - the relation wording and user-question template are therefore being corrected before the
    canonical report is rewritten, and the local baseline will be rerun on the corrected export so
    the manuscript-style writeup matches the true artifact
- The public SFT story is now being tightened around a clearer research-release framing:
  - the canonical public slugs have now been renamed to cleaner artifact names:
    - GitHub repo: `summa-virtue-alignment`
    - Hugging Face model: `summa-virtue-qwen2.5-1.5b`
  - the local 1.5B training surface is now also being normalized so the public repo no longer
    exposes weak-sounding rung names on the SFT path:
    - the official rung remains `local-baseline`
    - the heavier experimental rung is now `extended`
    - the old `pilot-lite` naming has been removed from public-facing configs, docs, assets,
      reports, packaged adapter surfaces, and the live local run-directory layout
  - first-screen public surfaces are being aligned to those names so the repo slug, README title,
    citation metadata, and release links read coherently instead of mixing polished prose with old
    fork-era identifiers
  - the 1.5B `local-baseline` run is being described explicitly as a deliberately small demo baseline
    whose job is to prove the pipeline works end to end
  - README, fine-tune guide, experiment index, flagship report, and generated package surfaces are
    being stripped of top-level weak-result wording that made the baseline sound smaller than it
    needs to sound
  - the public takeaway is now sharper: this repo proves the SFT pipeline and dataset work on a
    small reproducible model, while larger runs are the path to stronger final quality
- The public results surfaces are now being tightened around the actual Christian virtue goal
  rather than a looser generic benchmark story:
  - the training-trace SVG now renders readable y-axis values so the optimization claim can be
    inspected directly from GitHub instead of inferred from an unlabeled line
  - the held-out improvement SVG is now restricted to goal-aligned virtue task families only,
    instead of mixing in weaker non-central slices on the main publication graphic
  - README, experiment index, and flagship report executive tables are being aligned to foreground
    virtue-goal results first and keep broader overall metrics in later detailed sections
- The next publication-quality hardening pass is now aimed at repo readability rather than model
  scope:
  - several core SFT modules and viewer entrypoints are gaining missing top-level docstrings so a
    new reviewer can infer file purpose without reverse-engineering imports
  - `scripts/` is gaining a formal grouped README so the directory reads like an intentional entry
    surface rather than a pile of ad hoc helpers
  - the public reproducibility story is gaining one shorter memorable `make` target for final
    release checks instead of relying only on the longer canonical verify command name
- The README is now being reworked from first principles so the public landing page answers the
  right questions in the right order:
  - why Thomist moral virtue alignment needs a different dataset than generic theology chat
  - why the committed dataset is worth trusting
  - why the public `1.5B` run is a minimal example rather than the claimed ceiling
  - what the result actually proves for a reviewer or collaborator
  - the repo's three public purposes are now being made explicit near the top of the README so a
    first-time reader can identify the dataset, minimal SFT demo, and evidence-audit surfaces at a
    glance
  - README is now also being made more theologically grounded and human-readable:
    - representative Aquinas loci are being linked directly from the landing page
    - top-level prose is being softened away from technical shorthand toward more prudent,
      reviewer-facing explanation
    - visual hierarchy is being improved through denser tables and clearer section sequencing
    - the README title and opening summary are being aligned more explicitly to the real page
      identity: an evidence-first Thomist moral virtue alignment release rather than a merely
      branded project nickname
    - the repo is also being upgraded from “good branch” to “strong public artifact” by adding a
      clearer at-a-glance landing block and proper citation metadata for the release surface
- The repo's public GitHub surface is now being pushed harder toward an SFT-first story:
  - the README now presents the repo explicitly as the canonical guide, demo, and proof-of-work
    for Summa Moral Graph fine-tuning rather than treating SFT as only one section among many
  - a new `Start Here` table now points readers directly to the guide, reproduction path,
    published adapter, flagship report, and viewer depending on what they want to do
  - the held-out improvement figure is no longer squeezed beside the training curve on the README
    and experiment index; both figures now appear as full-width stacked visuals so the benchmark
    story is easier to see on GitHub
- The GitHub-facing results story is now being tightened so a reviewer can see the SFT success
  case without digging through the long report:
  - the README now foregrounds a compact held-out benchmark table instead of only listing the
    overall citation gain in prose
  - the README also now embeds the canonical training-curve SVG and base-vs-adapter comparison SVG
    directly inside the key-results section
  - the experiment index now mirrors that same quick-read table and figure pair so the repo has a
    second GitHub-visible results surface beyond the top-level README
- The external adapter page is now being treated as a first-class research surface instead of a
  thin post-hoc upload:
  - the Hugging Face model card template now emits a stronger abstract, snapshot table, benchmark
    summary, executive readout, usage snippet, reproducibility block, and explicit limitations
  - the canonical package now bundles the base-vs-adapter benchmark SVG directly into the adapter
    artifact so the public model page can show an actual figure rather than only headline text
  - the published Hugging Face README now includes the adapter URL, matching GitHub release,
    dataset/report links, and the final publication-verify command instead of stopping one step
    short of the full reproducibility contract
  - package tests and publication verification now cover those stronger package-surface contracts,
    so future model-card drift will fail locally before the public page regresses
- The final public-release polish pass is now closing portability and presentation gaps instead of
  widening scope:
  - committed docs, dataset manifests, review queues, and packaged adapter metadata are being
    normalized to repo-relative paths instead of leaking one local machine's filesystem layout
  - the publication verifier now scans public Markdown and JSON surfaces for machine-specific path
    leaks, so future release drift fails loudly rather than slipping into a publishable bundle
  - the adapter packaging path now sanitizes copied `environment.json`, `run_manifest.json`, and
    `train_metadata.json` before they become public-facing artifacts
  - the repository map now explicitly names the archival top-level implementation-plan memo so the
    root layout reads as intentional rather than leaving that file unexplained
- The next public-release polish pass is now focused on first-open trust rather than adding new
  modeling scope:
  - README is being rewritten around a research-release narrative with a clear problem statement,
    method overview, key results, repository map, and canonical reproduction path
  - a new `docs/repository_map.md` is being added so reviewers and collaborators can orient
    quickly without reverse-engineering the directory tree
  - the canonical local Apple-Silicon path is now gaining a pinned lockfile plus explicit
    `setup` / `reproduce` entrypoints rather than relying on ad hoc package installation
  - stale public corpus counts are being corrected so the repo consistently reports `6032`
    doctrinally usable `resp` / `ad` segments instead of the older all-sections figure
  - key public scripts and SFT modules are gaining top-level docstrings or comments so new readers
    can understand the execution surface from the file headers alone
- The repo is being locked around one official, publishable local demonstration path rather than a
  loose set of roughly equal training recipes:
  - the canonical local model is `Qwen/Qwen2.5-1.5B-Instruct`
  - the canonical local rung is `local-baseline`
  - the public story is now organized around one clean rerun, one base-vs-adapter comparison, one
    curated report, and one publication package
  - reporting utilities now generate:
    - a fixed goal-demo panel from held-out benchmark prompts
    - training-trajectory SVGs
    - base-vs-adapter comparison SVGs
    - a publishable markdown report that ties dataset, method, runtime, metrics, and qualitative
      samples to one run id
  - publication utilities now package the canonical adapter, write a model card and release notes,
    infer the current fork from the `origin` remote, and prepare synchronized Hugging Face / GitHub
    publication targets
  - release publication now also resolves its GitHub release target from the training run's
    recorded git commit instead of assuming the current `HEAD`, so a later documentation-only
    worktree state cannot silently detach a release from the actual adapter-producing run
  - the release-candidate branch has now been pushed to the user's fork and the next formal step is a clean rerun from that pushed commit so public artifacts point to a remote-backed state:
  - the clean rerun has now established the committed-state training artifact, and the next-step release path has been narrowed further after observing local inference throughput:
    - new canonical train run `20260418_193038` is tied to pushed commit `f9fd589`
    - a fresh base rerun was started as `20260418_193542`, but the first `31` predictions matched the prior complete base run exactly
    - because the base model and prompt path are unchanged, the repo will now reuse completed base run `20260418_143349` and spend remaining local time only on the new adapter evaluation
    - new adapter evaluation run `20260418_203546` advanced to `223 / 233` held-out prompts before
      bulk MPS generation stopped making forward progress
    - instead of discarding that canonical run id, the remaining `10` prompts are now being
      recovered through isolated single-example MPS subprocesses so the final artifact still has a
      truthful audit trail
    - pushed branch `feat/christian-virtue-sft-v1` now tracks `origin/feat/christian-virtue-sft-v1`
    - pushed commit is `f9fd589`
    - a fresh canonical rerun from `f9fd589` is now being launched before publication
  - the canonical local publication loop has now completed successfully:
    - train run `20260418_193038`
    - base test run `20260418_143349`
    - adapter test run `20260418_203546`
    - compare run `20260418_225541`
    - held-out citation exact moved from `0.000` on base to `0.150` on the adapter across `233`
      test prompts
  - the next polish step is now being treated as a public-artifact QA problem rather than a model
    problem:
    - a new publishable verification gate is being added to rebuild the canonical local report,
      refresh the local adapter package, and verify that README, guides, experiment index, curated
      report, and package manifest all point to the same published baseline
  - the remaining publication-sync gap is now narrower still:
    - the repo docs already expose the publishable verification gate
    - the generated Hugging Face model card and GitHub release notes are now being updated so the
      external publication surfaces show that same final verification command rather than stopping
      one step early
  - the next polish target is now document integrity itself:
    - the flagship report is being updated so its recommended reproduction path also ends at the
      verify gate
    - public Markdown surfaces are gaining explicit internal-link validation so the repo can fail
      loudly if a polished public doc points to a missing local artifact
  - the next coherence gap after that is the dataset surface itself:
    - the dataset card and `data/processed/sft/README.md` are now being promoted from “present” to
      “first-class public entry surfaces”
    - publication verification is being widened so those data-facing docs are checked alongside the
      README, fine-tune guide, maintainer doc, experiment index, and flagship report
  - the next polish target after surface coherence is report readability at research-lead level:
    - the flagship local report is now being upgraded with an executive readout that summarizes the
      strongest task slices, strongest tracts, persistent weak spots, and goal-demo scoreboard
      before the full evidence dump
    - the embedded comparison markdown is also being normalized so the report no longer contains an
      awkward nested top-level heading inside the comparison section
  - the next publishability gap after that is the external package surface:
    - the Hugging Face model card and GitHub release notes are now being upgraded from simple
      headline-metric stubs into compact executive summaries with strongest slice, weakest slice,
      and zero-gain tract readouts
    - the adapter package manifest is also being widened to carry the summary fields needed to keep
      those external surfaces deterministic and reproducible
    - publication verification is being extended so local package `README.md` and
      `release_notes.md` are checked alongside the repo docs
- The Christian virtue fine-tuning repo is now being reshaped around a local Apple-Silicon pilot in
  addition to the existing remote CUDA loop:
  - `Qwen/Qwen2.5-1.5B-Instruct` is being added as the first Mac MPS LoRA training path
  - the first full local `pilot` config has now proven too slow on the user's 16 GB Mac, so a
    smaller `local-baseline` rung is being added as the default practical local step between `smoke`
    and any heavier experiment
  - local adapter evaluation now resolves `local_baseline/latest` first and only falls back to
    `pilot/latest`, so the default Mac path no longer breaks after a successful `local-baseline` run
  - the first successful `local-baseline` training + base-test + adapter-test loop is now being written
    up as a full curated experiment report with method, data, training curves, result plots, and
    qualitative analysis under `docs/reports/`
  - the repo docs are now being tightened around the real SFT purpose:
    - faithful Aquinas-grounded virtue reasoning is the primary objective
    - evidence-bounded citation traceability is the guardrail, not the whole aim
  - training and inference configs now grow a shared `runtime_backend` / `torch_dtype` surface
  - the training runner is being split into a true dual path:
    - CUDA keeps the existing 4-bit QLoRA flow
    - MPS falls back to standard float16 LoRA without `bitsandbytes`
  - run artifacts are being upgraded to include `environment.json`, `train_log_history.jsonl`,
    richer `run_manifest.json` metadata, and timestamped run ids for the new local path
  - the current repo is being polished as the public fine-tuning entrypoint rather than requiring a
    companion repo:
    - committed dataset exports under `data/processed/sft/exports/christian_virtue_v1*`
    - a public `Fine-Tune With Summa Moral Graph` guide
    - an experiment index and clearer README entry path
- The small-model Christian virtue path is now being turned into a real remote-GPU research loop
  rather than just a loose collection of train/eval scripts:
  - `Qwen/Qwen3-0.6B` is now the first fully wired end-to-end baseline
  - Linux CUDA preflight checks are being added explicitly
  - a tiny smoke-train config is being added for cheap validation before the real run
  - standardized run outputs are being consolidated under `runs/christian_virtue/qwen3_0_6b/`
  - base-vs-adapter comparison reporting is being formalized as a maintained script instead of an
    ad hoc notebook step
  - Make targets and maintainer docs are being updated so a rented GPU box can follow one clean
    stepwise command path
- A smaller Christian virtue prototype track is now being added so remote training does not have to
  start at `Qwen/Qwen3-4B`:
  - the repo will add a `Qwen/Qwen3-0.6B` QLoRA config as the cheapest same-family training path
  - Make targets and maintainer docs will expose that smaller run directly
- The held-out Christian virtue benchmark is now being executed on the duplicate repo, and the
  inference runner is being made portable enough to run on Apple Silicon as well as CUDA:
  - the local machine does not expose CUDA, but it does expose `mps`
  - the generation path is therefore being updated to resolve its runtime device explicitly instead
    of assuming CUDA-style 4-bit loading
  - dry-run plans and generation manifests will now record the effective device, dtype, and whether
    4-bit quantization remained active or was safely disabled
  - generation now also writes incremental partial outputs so long benchmark runs can resume
  - an initial six-example held-out pilot on `Qwen/Qwen3-4B` has already shown the main base-model
    failure mode: broad Thomistic-sounding hallucination with zero passage-id citation grounding
- A new Christian virtue SFT pipeline is now being added inside the repo without disturbing the
  existing viewer or graph workflow:
  - the builder reads the canonical interim textual spine from `data/interim/`
  - it consumes only the selected reviewed doctrinal files from `data/gold/`
  - it filters to approved doctrinal supervision with `explicit_textual` and
    `strong_textual_inference` support
  - it emits four chat-style template families with stable passage ids and citation labels in both
    metadata and assistant outputs
  - deterministic grouped splits now use `question_id` within each tract, and an alternate config
    adds an explicit `temperance_closure_161_170` OOD holdout
  - prompt-only benchmark exports are now also being added for non-train splits so held-out
    evaluation can run without gold-answer leakage
  - a config-driven inference runner is now being added so base and adapter-backed models can
    generate prediction files directly from those benchmark prompts
  - a new `src/summa_moral_graph/sft/` package, config YAMLs, builder/train/eval/smoke scripts,
    Make targets, fixture-backed tests, and maintainer docs now carry this workflow
  - the current default build produces `1883` examples from `555` reviewed source annotations, and
    the local smoke path is already clean
- The overall-map `Center concept` filter is being repaired so the control actually affects the reviewed graph:
  - the shell had been discarding `center_concept` whenever map mode was `Overall map`, so the filter UI existed but the graph query silently ignored it
  - the overall map will now honor the selected center concept the same way the empty-state and evidence copy already imply
  - the generic `Overall Map` navigation path no longer silently inherits the current concept as a hidden center filter
  - the center-concept dropdown is now scoped to concepts actually present in the current map slice, which avoids a large class of misleading no-result selections
  - regression coverage now checks the route behavior, the scope-aware center options, the graph-edge filtering semantics, and the live rendered-edge narrowing path
  - the home `Open interactive map` route is now being corrected as well:
    - it had been forwarding the currently selected home concept into the map route
    - with the default home tract preset, that produced mismatched scopes such as `Faith tract + Charity center`, which yielded a blank map despite the overall map itself being healthy
    - the home map card will now open an actual overall map instead of a hidden concept-centered slice
- The overall-map default range is being restored to the opening reviewed span:
  - the default `Question span` is back to `1–46`
  - shell fallbacks, reset behavior, and live slider expectations still share the same `DEFAULT_MAP_RANGE` constant, but that constant is now intentionally conservative again
  - regression coverage continues to assert the live overall-map slider default directly, now against the restored `1–46` span
- The homepage and README Summa-structure note is being clarified again for readers:
  - the note now says more directly that only `resp` and `ad` are included here as Thomas's own answer
  - it now also says explicitly that no opening `obj` or `sc` material is included
  - the `obj / sc / resp / ad` acronyms now link out to a short public explainer page for the Summa article form
- The public-facing app and README now explain the Summa article structure more plainly:
  - both surfaces now note the conventional `obj / sc / resp / ad` article structure in one short line
  - they also now state explicitly that the viewer keeps only `resp` and `ad` because the opening objections / counter-position are not used as Aquinas's own doctrinal answer
- The doctrinal-content policy has now been tightened so objections can no longer leak into the corpus, graph, or app:
  - the parser still recognizes the full article structure for boundary detection, but exported usable segments are now limited to `I answer that` (`resp`) and `Reply to Objection ...` (`ad`)
  - opening objections (`obj`) and `On the contrary` / `sed contra` (`sc`) are now excluded from interim data, candidate generation, viewer filters, and downstream exports
  - interim passage volume has been reduced from the older all-sections export to `6032` usable doctrinal passages (`1482` respondeo + `4550` reply segments)
  - candidate/reviewed artifacts have been regenerated against the cleaned corpus, and explicit scans now fail if any exported passage id ends in `.objN` or `.sc`
  - dedicated regression coverage now checks both parser output and exported artifacts for objection leakage
- The favicon is being pushed further toward a monastery-seal direction:
  - the outer ring is now heavier again
  - the center motif has been simplified to a bold Latin cross with an open book in front of it
  - the cross has now been enlarged further so it reads first, even at favicon scale
  - the cross has also been shifted slightly downward so the seal feels less top-heavy
  - small interior ornament has been removed so the mark reads more like a medieval seal than a modern UI monogram
- The map shell is being tightened for narrow-column readability:
  - the home `Summa Virtutum` title is slightly smaller, so the masthead keeps its drama without crowding the first fold
  - overall-map quick-span buttons now receive a smaller, less wrap-prone treatment
  - selected-node cards and map-side action buttons now use shorter labels and smaller typography so ids and actions stop breaking awkwardly in the evidence rail
- The GitHub front page is being tightened again around one obvious public entry:
  - the live Streamlit link now leads the README with a stronger app-first badge treatment
  - duplicate top-of-page viewer links have been reduced so the README reads cleaner and faster
- The favicon is being simplified for recognizability at tiny sizes:
  - the portrait crop has been replaced with a monochrome `SV` seal-style icon
  - the new version uses black linework on a light ground so it still reads when zoomed out in a browser tab
  - the asset path stays the same, so the Streamlit app picks it up without further code changes
- The top-of-page layout is being tightened again around readability:
  - the redundant home helper sentence beneath the hero has been removed
  - overall-map top controls now allocate more width to quick spans and show shorter `Local` / `Overall` labels instead of wrapping `Local map` / `Overall map`
  - passage-list pagination now uses a wider three-part layout so `Results per page`, `Previous` / `Next`, and the page chip stop collapsing into awkward line breaks
  - the map canvas column has been widened slightly relative to the evidence column
- The browser-tab identity is being upgraded from a glyph to a real Aquinas icon:
  - a square-cropped Thomas Aquinas portrait asset now lives under `docs/assets/summa-virtutum-icon.png`
  - the Streamlit page icon now uses that local asset when present, falling back to `§` only if the file is missing
- The public entry copy is being tightened for search and first-time discovery:
  - the Streamlit browser title now names the app as an interactive map of Thomas Aquinas's moral corpus instead of only `Summa Virtutum`
  - the home hero and sidebar subtitle now mention Aquinas, concepts, passages, and maps in clearer search-friendly language
  - the README top section now puts the live Streamlit URL in a stronger first-screen position
- The passage explorer advanced filters are being hardened against stale cross-scope state:
  - question options now narrow to the active part or tract scope instead of always listing the whole corpus
  - article options now narrow to the active part/question scope instead of preserving incompatible article ids
  - stale `question` / `article` values are now cleared before search runs, so switching part or tract scope no longer traps the reader in a false `No passages matched` state
  - a small `Clear advanced filters` recovery action now appears directly in the empty state
- The landing-page start/download affordances are being clarified again around user intent:
  - the home and sidebar download panels now expose a dedicated `Tract preset` control inside `Download data`, so tract scope is clearly understood as export scope rather than a hidden global dependency
  - the home `IV Map` route no longer uses a page screenshot and now renders a small abstract interactive-map preview, which better signals that this route opens a live graph surface
  - the `Start` block row separator has been strengthened into a visibly readable horizontal divider so the two launch rows no longer blur together
- The home `Start` grid is being simplified again for faster first-glance reading:
  - each route now leads with its Roman numeral and title at the top of the card instead of placing the numeral mid-layout beside the copy
  - the 1–2 and 3–4 columns now use a stronger vertical divider so the two-column structure reads immediately
  - the map tile preview has been reduced to a quieter static panel with no floating chips or pseudo-interactive labels competing with the card title
- The start-route polish pass now leans more clearly into the map as the marquee entry:
  - the `Map` tile now uses a stable inline SVG preview instead of CSS-positioned decorative fragments that could feel broken
  - the map CTA now reads `Open interactive map`
  - the four home-route buttons now use a stronger, more product-like button treatment, with the map CTA carrying the deepest emphasis
- The map route preview is being stripped down again for visual cleanliness:
  - the outer preview frame and the inner SVG box have both been removed
  - the graph preview now sits directly on the page background with no nested panel effect
  - the preview height is slightly reduced so the map tile pulls upward and reads lighter
- The map CTA and tile spacing are being tightened one more step:
  - the home map button now renders as a true primary button so the gradient treatment is guaranteed rather than only CSS-dependent
  - the preview band is shorter and sits closer to the button, reducing dead vertical space in the bottom-right tile
- The start-card baseline is being tuned for a cleaner row finish:
  - small control spacers now normalize the distance from selector/preview to button across the four home cards
  - the tract row receives a deliberate spacer so its CTA baseline sits closer to the map CTA
  - the map button gradient has been deepened and brightened so it reads unmistakably as the marquee action
- The map CTA gradient is being refined toward a clearer center-weighted ribbon:
  - the button now uses a horizontal light-to-dark-to-light blue gradient
  - the outer blue stops are darker than before so the sides no longer feel washed out
  - the center stop has now been lifted slightly so the middle reads rich rather than overly dark
  - the center transition has now been softened again so the button reads smoother and less sharply pinched at the middle
- The home launch buttons are now being steered away from flat ribbons toward a more tactile treatment:
  - all four start buttons now use a diagonal highlight-to-shadow gradient with stronger lower-edge shadowing
  - the map CTA now places its darker weight toward the lower-right, so it reads more like a raised button than a striped band
- The button finish is being refined toward a more polished public-facing look:
  - lower-edge shadowing has been reduced so the buttons feel elevated but not chunky
  - both the neutral and map CTAs now use softer contrast and lighter depth cues for a more refined, high-end appearance
- The lower `Start` row is being nudged upward for cleaner baseline alignment:
  - the tract spacer is now smaller
  - the map preview band is shorter again
  - the `Open tract` and `Open interactive map` button wrappers now receive a small shared upward shift so their bottoms align more cleanly
- The repository has now been moved back to private visibility on GitHub while the Streamlit deployment remains a separate sharing surface that still needs to be made public from Streamlit Community Cloud settings.
- The repository visibility has now been iterated in support of launch testing:
  - it was briefly made public to validate public-facing repo copy and links
  - it has now been returned to private visibility while Streamlit app sharing is handled separately
- Streamlit Community Cloud dependency installation is now unblocked for Python 3.14:
  - `lxml` is no longer a hard dependency on Python 3.14 environments
  - ingest HTML parsing now falls back to Python's built-in `html.parser` when `lxml` is unavailable
  - this preserves parser behavior for local environments with `lxml` while avoiding Cloud build failures tied to missing system `libxml2/libxslt` headers
- The shell spacing is being refined again for cleaner first-fold readability:
  - the top navigator now sits a little lower so the `Guide` line no longer feels clipped against the app chrome
  - main section, route-card, and button spacing have been tightened so the downward shift does not make the page taller overall
  - the snapshot lift and start-grid spacing have been rebalanced together rather than moving only one block
  - the `Start` block now has a more legible horizontal divider between its top and bottom rows so the two launch bands read as distinct groups
  - the overall-map page no longer repeats the `Overall Map` title above the canvas, and its quick-span / question-span controls now sit in a tighter top row so the graph starts earlier
  - the overall-map quick spans are now a single row with the `All` shortcut removed, and the intro sentence sits closer to the title instead of floating in a loose block
  - the home-page `IV Map` route now includes a small overall-map preview image so the map entry reads visually as a graph destination rather than only a text button
- Map entry now re-enables relation labels on arrival:
  - `open_map()` now restores `Show relation labels` to on when users enter the overall map
  - this makes the default map reading mode more explicit even after a prior session turned labels off
  - regression coverage now protects the route-level default, not only initial session-state defaults
- The viewer is now being tightened around first-fold map visibility:
  - the Concept Explorer local map now sits higher in the reading order and uses a wider, taller canvas
  - the Overall Map now keeps only mode/range controls above the graph by default, with heavier filters moved behind an explicit `Show more filters` toggle
  - the home snapshot block has been lifted again so the landing page shows more signal before the first scroll
- The README top section is now being simplified toward one obvious public entry:
  - the live Streamlit app now replaces the earlier run/deploy choice cluster at the top of the README
  - fresh home and overall-map screenshots have been regenerated after the latest layout pass
  - GitHub, docs, and maintainer setup paths remain available, but no longer compete with the live viewer button in the first screen
- The README front page is now being pushed closer to a real public product surface:
  - the top section now includes badge-style metadata, stronger run/deploy calls to action, and a compact three-column viewer summary
  - freshly generated dashboard screenshots now appear near the top of the README for both the landing view and the overall map
  - the entry experience now reads more like a live viewer homepage than a plain repository preface
- The README top section now reads more like a live product landing path:
  - the first screen now leads with open/run/deploy routes and a stronger reader-facing summary
  - a short `Try this first` section now gives a concrete first-use path through concept, passage, and map navigation
  - the front page is now closer to the Aristotle repo's entry rhythm without copying its wording or branding
- The repo front page is being tightened again toward a more deployment-friendly, Aristotle-style reader README:
  - the top of `README.md` now leads with open/run/deploy routes instead of maintainer detail first
  - the Streamlit Community Cloud path is now documented explicitly as the GitHub-hosted deployment route
  - a minimal `requirements.txt` now exists so the repo is easier to wire into Streamlit Community Cloud from GitHub
- Relation labels are now on by default across the viewer's map surfaces:
  - the overall map `Show relation labels` control now defaults to enabled
  - the Concept Explorer local map now has the same relation-label control, also defaulting to enabled
  - session-state defaults and regression coverage now protect this reading-first behavior
- The Concept Explorer local-map bug has been fixed at the payload-normalization layer:
  - tract concept payloads that exposed `reviewed_incident_edges` and `editorial_correspondences` are now normalized into the viewer's canonical doctrinal/editorial edge keys
  - tract-scoped local maps for justice, religion, theological virtues, and similar overlays no longer collapse to the misleading `No local reviewed map` empty state when reviewed edges actually exist
  - regression coverage now checks the normalized doctrinal/editorial edge aliases as part of concept payload selection
- The home masthead spacing has been tightened again for a cleaner first fold:
  - the byline now reads `By Jenny Zhu` with the LinkedIn icon trailing the name
  - the `Start` section now sits closer to the corpus-scope/byline stack and uses slightly tighter divider spacing
  - the `Snapshot` section has been lifted more aggressively to reduce the dead vertical gap beneath the home split layout
- The home hero typography now uses a more unified classical treatment around the title itself:
  - the subtitle is now rendered as a larger serif italic line rather than plain body copy
  - the eyebrow and nearby corpus-scope line now use decorative rule treatments that echo the title
  - the author byline now shares the same small-caps / classical family instead of reading like generic metadata
- The overall-map graph now supports edge relation labels as an explicit reading aid:
  - the pyvis renderer can now show or hide simplified relation labels directly on edges
  - the map view now exposes a `Show relation labels` toggle instead of forcing labels on all the time
  - regression coverage now checks both the hidden and visible HTML paths
- The overall-map focus-tag control is now more stable and honest:
  - focus-tag options are derived from tract/range coverage rather than from already-filtered visible edges
  - reviewed spans with no tract-specific focus tags now show an explicit note instead of an empty broken-looking selector
  - regression coverage now checks both tagged spans and no-tag spans
- The home shell has received another presentation pass focused on the public-facing title and entry composition:
  - the `Summa Virtutum` hero now uses a more ornate classical display treatment
  - the decorative star in the title panel has been removed for a cleaner manuscript-like heading
  - the `Start` area now includes a clearer top horizontal divider in addition to the internal separators
  - the `Snapshot` block has been lifted upward to reduce the dead gap beneath the first fold
- The repository front page has now been rewritten as a finalized, user-facing README:
  - the most important links now appear at the top
  - the dashboard launch path is explicit and easy to find
  - reviewed scope, corpus scope, evidence discipline, and key docs are explained in plain language
- The dashboard visual shell now carries a more deliberate Summa-facing presentation layer:
  - top navigation no longer uses emoji-like labels and instead renders as a more classical small-caps navigator
  - home route badges now use Roman numerals instead of pictographic icons
  - hero, cards, and metric panels now share lighter inset borders and more bookish serif handling
- The home view now defaults the tract route to a real reviewed tract instead of a blank placeholder, so `Open tract scope` behaves like a usable entry path rather than a disabled card.
- The viewer typography now uses a more classical heading treatment for the public-facing shell:
  - `Summa Virtutum` and other primary headings now render with a more bookish serif face
  - small-caps route labels and kicker text now carry more of the intended Latin / scholastic character without changing the evidence-first structure
- The unified dashboard map now handles cross-tract question spans more honestly:
  - overall-map quick-span buttons now update the range through the same widget-safe state path used elsewhere in the shell
  - `graph_edges_for_view()` now aggregates reviewed edges across every tract adapter overlapping the selected range instead of assuming one tract family per span
  - cross-tract spans such as `57–122`, `141–170`, and `1–182` now render reviewed graph slices instead of collapsing to an empty prompt
  - interaction coverage now includes map quick-span and question-span regression tests
- The dashboard is now being reworked from a multi-page research operations surface into a
  unified reader-first Streamlit shell:
  - new root entrypoint: `streamlit_app.py`
  - new viewer layer under `src/summa_moral_graph/viewer/`
  - shared state, tract-adapter registry, and reusable render helpers now drive concept,
    passage, graph, and stats views from one app shell
  - legacy `app/Home.py` and `app/pages/*` files have been reduced to thin compatibility wrappers
- Milestone 0 scaffold is complete: packaging, docs, tests, CLI, repo guidance, and Make targets are in place.
- Milestone 1 textual ingest is complete for the in-scope corpus:
  - `296` questions
  - `1482` articles
  - `6032` usable doctrinal segments
  - `1603` explicit cross-reference records
- Interim artifacts are generated and validated under `data/interim/`.
- The next reviewed doctrinal block is now implemented for the prudence tract:
  - `II-II, QQ. 47–56`
  - `449` passages in tract scope
  - `156` reviewed doctrinal annotations
  - `152` reviewed doctrinal edges
  - `12` reviewed structural-editorial correspondences
  - `4` candidate mentions
  - `5` candidate relation proposals
- Verification is clean for the current repo state:
  - `build-prudence` succeeds
  - `build-pilot` now succeeds for the fixed vertical slice
  - pilot layer counts:
    - `12` questions
    - `792` passages
    - `66` registered concepts
    - `187` reviewed annotations
    - `29` doctrinal edges
    - `253` structural edges
  - `pytest` passes (`32` passed, `2` network tests skipped)
  - `ruff check` and `mypy` pass
- The repo now supports the full moral corpus as a structural and candidate-review workflow:
  - `296` included questions parsed
  - `1482` articles parsed
  - `6032` doctrinally usable passages available for full-corpus browsing
  - `128` corpus registry concepts
  - `25755` candidate mentions
  - `8977` candidate relation proposals
  - `501` reviewed annotations remain separate from the candidate layer
  - generated audit outputs:
    - `data/processed/corpus_manifest.json`
    - `data/processed/coverage_report.json`
    - `data/processed/candidate_validation_report.json`
    - `data/processed/corpus_review_queue.json`
  - the first full-corpus example review packet targets `I-II q.100`
  - verification is again clean:
    - `build-corpus` succeeds
    - `pytest` passes (`40` passed, `2` network tests skipped)
    - `ruff check` and `mypy` pass
- The first substantial reviewed doctrinal layer is now implemented for the theological virtues tract:
  - `II-II, QQ. 1–46`
  - `46` questions covered
  - `999` passages in tract scope
  - `58` registered concepts used in tract exports
  - `185` reviewed annotations
  - `54` reviewed doctrinal edges
  - `126` reviewed structural-editorial correspondences
  - `5832` candidate mentions in tract scope
  - `2161` candidate relation proposals in tract scope
  - generated tract outputs:
    - `data/processed/theological_virtues_coverage.json`
    - `data/processed/theological_virtues_validation_report.json`
    - `data/processed/theological_virtues_review_queue.json`
  - tract verification is currently clean:
    - `build-theological-virtues` succeeds
  - tract validation status is `ok`
  - root `pytest` now passes directly from the repo (`49` passed, `2` skipped)
  - `ruff check` and `mypy` pass after the theological-virtues filter/type cleanup
- The next research-grade reviewed doctrinal block is now implemented for the justice core tract:
  - `II-II, QQ. 57–79`
  - `23` questions covered
  - `452` passages in tract scope
  - `66` registered concepts used in tract exports
  - `299` reviewed annotations
  - `98` reviewed doctrinal edges
  - `186` reviewed structural-editorial correspondences
  - `1141` candidate mentions in tract scope
  - `459` candidate relation proposals in tract scope
  - doctrinal edge families currently counted in tract reports:
    - `11` justice-species relations
    - `21` harmed-domain relations
    - `7` restitution-related relations
    - `31` judicial-process / role-related relations
  - generated tract outputs:
    - `data/processed/justice_core_coverage.json`
    - `data/processed/justice_core_validation_report.json`
    - `data/processed/justice_core_review_queue.json`
  - tract verification is clean:
    - `build-justice-core` succeeds
    - tract validation status is `ok`
    - justice review packet now targets under-annotated `II-II q.59`
- The next research-grade reviewed doctrinal block is now implemented for the religion tract:
  - `II-II, QQ. 80–100`
  - `21` questions covered
  - `464` passages in tract scope
  - `42` registered concepts used in tract exports
  - `231` reviewed annotations
  - `63` reviewed doctrinal edges
  - `157` reviewed structural-editorial correspondences
  - `1400` candidate mentions in tract scope
  - `482` candidate relation proposals in tract scope
  - doctrinal edge families currently counted in tract reports:
    - `25` positive-act relations
    - `5` excess-opposition relations
    - `5` deficiency-opposition relations
    - `28` sacred-object / domain relations
  - generated tract outputs:
    - `data/processed/religion_tract_coverage.json`
    - `data/processed/religion_tract_validation_report.json`
    - `data/processed/religion_tract_review_queue.json`
  - tract verification is clean:
    - `build-religion-tract` succeeds
    - tract validation status is `ok`
    - religion review packet now targets under-annotated `II-II q.97`
- The next research-grade reviewed doctrinal block is now implemented for the owed-relation tract:
  - `II-II, QQ. 101–108`
  - `8` questions covered
  - `140` passages in tract scope
  - `27` registered concepts used in tract exports
  - `169` reviewed annotations
  - `38` reviewed doctrinal edges
  - `110` reviewed structural-editorial correspondences
  - `475` candidate mentions in tract scope
  - `166` candidate relation proposals in tract scope
  - doctrinal edge families currently counted in tract reports:
    - `6` origin-related due relations
    - `10` excellence-related due relations
    - `8` authority-related due relations
    - `9` benefaction-related due relations
    - `5` rectificatory relations
  - generated tract outputs:
    - `data/processed/owed_relation_tract_coverage.json`
    - `data/processed/owed_relation_tract_validation_report.json`
    - `data/processed/owed_relation_tract_review_queue.json`
  - tract verification is clean:
    - `build-owed-relation-tract` succeeds
    - tract validation status is `ok`
    - owed-relation review packet now targets under-annotated `II-II q.104`
- The next research-grade reviewed doctrinal block is now implemented for the connected virtues tract:
  - `II-II, QQ. 109–120`
  - `12` questions covered
  - `165` passages in tract scope
  - `23` registered concepts used in tract exports
  - `182` reviewed annotations
  - `44` reviewed doctrinal edges
  - `138` reviewed structural-editorial correspondences
  - `466` candidate mentions in tract scope
  - `174` candidate relation proposals in tract scope
  - doctrinal edge families currently counted in tract reports:
    - `21` self-presentation relations
    - `8` social-interaction relations
    - `11` external-goods relations
    - `4` epikeia / legal-equity relations
  - generated tract outputs:
    - `data/processed/connected_virtues_109_120_coverage.json`
    - `data/processed/connected_virtues_109_120_validation_report.json`
    - `data/processed/connected_virtues_109_120_review_queue.json`
  - tract verification is clean:
    - `build-connected-virtues-109-120` succeeds
    - tract validation status is `ok`
    - connected-virtues review packet now targets under-annotated `II-II q.109`
- The next research-grade reviewed doctrinal block is now implemented for the first detailed fortitude-parts tract:
  - `II-II, QQ. 129–135`
  - `7` questions covered
  - `106` passages in tract scope
  - `20` registered concepts used in tract exports
  - `150` reviewed annotations
  - `33` reviewed doctrinal edges
  - `97` reviewed structural-editorial correspondences
  - `346` candidate mentions in tract scope
  - `114` candidate relation proposals in tract scope
  - doctrinal tract counts currently reported:
    - `4` excess-opposition relations
    - `2` deficiency-opposition relations
    - `20` honor-related relations
    - `13` expenditure-related relations
  - generated tract outputs:
    - `data/processed/fortitude_parts_129_135_coverage.json`
    - `data/processed/fortitude_parts_129_135_validation_report.json`
    - `data/processed/fortitude_parts_129_135_review_queue.json`
  - tract verification is clean:
    - `build-fortitude-parts-129-135` succeeds
    - tract validation status is `ok`
    - fortitude-parts review packet now targets under-annotated `II-II q.130`
- The next research-grade reviewed doctrinal block is now implemented for the fortitude closure tract:
  - `II-II, QQ. 136–140`
  - `5` questions covered
  - `58` passages in tract scope
  - `23` registered concepts used in tract exports
  - `84` reviewed annotations
  - `31` reviewed doctrinal edges
  - `53` reviewed structural-editorial correspondences
  - `307` candidate mentions in tract scope
  - `115` candidate relation proposals in tract scope
  - doctrinal tract counts currently reported:
    - `10` patience relations
    - `10` perseverance relations
    - `4` opposed-vice relations
    - `6` gift-linkage relations
    - `9` precept-linkage relations
  - synthesis outputs now exist for the reviewed fortitude tract:
    - `data/processed/fortitude_tract_synthesis_nodes.csv`
    - `data/processed/fortitude_tract_synthesis_edges.csv`
    - `data/processed/fortitude_tract_synthesis.graphml`
  - tract verification is clean:
    - `build-fortitude-closure-136-140` succeeds
    - tract validation status is `ok`
    - fortitude-closure review packet now targets under-annotated `II-II q.137`
- The next large research-grade reviewed doctrinal block is now implemented for the major temperance tract, phase 1:
  - `II-II, QQ. 141–160`
  - `20` questions covered
  - `407` passages in tract scope
  - `48` registered concepts used in tract exports
  - `234` reviewed annotations
  - `67` reviewed doctrinal edges
  - `166` reviewed structural-editorial correspondences
  - `1258` candidate mentions in tract scope
  - `468` candidate relation proposals in tract scope
  - doctrinal tract counts currently reported:
    - `2` integral-part relations
    - `7` subjective-part relations
    - `7` potential-part relations
    - `10` food-related relations
    - `8` drink-related relations
    - `17` sex-related relations
    - `6` continence/incontinence relations
    - `8` meekness/anger relations
    - `5` clemency/cruelty relations
    - `3` modesty-general relations
  - synthesis outputs now exist for temperance phase 1:
    - `data/processed/temperance_phase1_synthesis_nodes.csv`
    - `data/processed/temperance_phase1_synthesis_edges.csv`
    - `data/processed/temperance_phase1_synthesis.graphml`
  - tract verification is clean:
    - `build-temperance-141-160` succeeds
    - tract validation status is `ok`
    - temperance review packet now targets under-annotated `II-II q.144`
- The next large research-grade reviewed doctrinal block is now implemented for the temperance closure tract:
  - `II-II, QQ. 161–170`
  - `10` questions covered
  - `161` passages in tract scope
  - `37` registered concepts used in tract exports
  - `148` reviewed annotations
  - `41` reviewed doctrinal edges
  - `107` reviewed structural-editorial correspondences
  - `563` candidate mentions in tract scope
  - `223` candidate relation proposals in tract scope
  - doctrinal tract counts currently reported:
    - `8` humility/pride relations
    - `10` Adam’s-first-sin case relations
    - `7` studiousness/curiosity relations
    - `10` external-modesty relations
    - `6` precept-linkage relations
  - synthesis outputs now exist for the full reviewed temperance tract:
    - `data/processed/temperance_full_synthesis_nodes.csv`
    - `data/processed/temperance_full_synthesis_edges.csv`
    - `data/processed/temperance_full_synthesis.graphml`
  - tract verification is clean:
    - `build-temperance-closure-161-170` succeeds
    - tract validation status is `ok`
    - temperance-closure review packet now targets under-annotated `II-II q.162`
- The Streamlit landing page now acts as a real dashboard rather than a raw JSON summary:
  - corpus backbone metrics, reviewed-block status, review-priority queues, and synthesis exports are aggregated through `src/summa_moral_graph/app/dashboard.py`
  - Home stays thin and evidence-first while reusing the same processed coverage/validation artifacts the tract reports already depend on
  - dashboard verification is covered by helper-level tests rather than brittle UI rendering tests
- The Streamlit app now has a product-grade shared UI layer rather than page-by-page default Streamlit styling:
  - `src/summa_moral_graph/app/ui.py` now centralizes page chrome, navigation, typography, metric cards, evidence rendering, and shared formatting helpers
  - `Home`, `Corpus Browser`, `Passage Explorer`, `Concept Explorer`, `Graph View`, and `Stats / Audit` now share one visual system and page rhythm
  - graph rendering in `src/summa_moral_graph/app/corpus.py` now uses a warmer, more readable presentation tuned for public-facing review rather than internal prototype defaults
- The public-facing dashboard pass now also addresses tab-by-tab usability rather than only visual polish:
  - `Graph View` now includes a fast-navigation guide, readable evidence-spotlight labels, and export actions for the current graph slice
  - the graph canvas itself now exposes navigation buttons plus richer node/edge tooltips so users can inspect layer, support, and traceability without leaving the visualization
  - page naming has shifted toward clearer first-time comprehension (`Executive Overview`, `Corpus Coverage`, `Evidence Browser`, `Concept Network`, `Relationship Map`, `Health & Audit`) rather than internal-tool terminology
  - filtered pages now expose reset controls, and the relationship map adds evidence-segment filtering so users can move faster without hand-clearing state
  - the landing page now includes a manager-facing quick compare mode and direct export actions for both data and an executive report
  - `Home`, `Corpus Browser`, `Passage Explorer`, `Concept Explorer`, and `Stats / Audit` all now expose explicit download actions so displayed tables are inspectable outside the app
  - the strongest remaining presentation emphasis is now on graph readability and evidence-first navigation, not on missing export affordances

## Surprises & Discoveries

- After the structure cleanup, the remaining trust gap was not more explanation but clearer claim
  boundaries:
  - the repo already had good evidence, reports, and commands
  - what it still lacked was one page that separated “what is currently proven” from “what is the
    broader project goal” and from “what is not yet claimed”
  - making that distinction explicit is especially valuable here because the baseline and the
    citation-frontier follow-up are both real results, but they support different public claims
- After the visual cleanup, the next weakest link was not figures or prose density but repo
  topology visibility:
  - the README already stated the goal, method, and result
  - but it still made a new reader infer where the code, data, reports, and package surfaces were
  - adding one concise structure table was higher-leverage than another paragraph of narrative
- The biggest remaining visual weakness was not the SVG charts themselves but markdown density:
  - the README still had too many signals competing at the top of the page
  - the flagship report's goal-demo panel was accurate but visually exhausting because every
    example was expanded inline
  - collapsing examples while keeping them committed preserves transparency without forcing the
    first reader through a wall of excerpts
- Once the citation-frontier report became a real public artifact, the main remaining weakness was
  not the report itself but the release contract around it:
  - repo-surface tests already checked that the new report exists and is linked
  - but `verify_publication_bundle` still treated only the baseline report as a first-class
    checked document
  - that would have allowed quiet drift in the new follow-up artifact even while
    `make public-release-check` stayed green
- The completed citation-frontier run improved exactly where the earlier audit said it should, but
  with a sharper tradeoff than the benchmark summary alone would suggest:
  - overall exact citation rose by about three points and every task family improved
  - the hard frontier moved off zero, which confirms the recipe change is causally meaningful
  - but the gains were not free, because `justice_core` and `strong_textual_inference` dropped
    substantially
  - that means the repo should present this as a completed follow-up result, not silently promote
    it to the new public baseline
- The biggest remaining gap after the code landed was not implementation but discoverability:
  - README and the frontier audit already named the new `citation-frontier` recipe
  - but the main fine-tune guide and repository map still read as if the frontier stopped at a
    static audit report
  - synchronizing those guide surfaces is therefore more valuable right now than adding another new
    helper or another new config
- The cleanest next experiment turned out not to require a new dataset slice or longer local run:
  - the existing train split already contains `435` `citation_grounded_moral_answer` examples, so
    the frontier can be targeted entirely by changing subset mixture
  - a quota-based selector is therefore a cleaner intervention than adding new prompt families or
    expanding doctrinal scope
  - keeping the same `128` examples and `20` steps makes the next run interpretable as a recipe
    change rather than a compute-budget change
- The remaining trust gap after the figure cleanup was not another missing chart but a missing
  contract:
  - the repo already had the right commands, outputs, and public artifacts
  - what it lacked was a sufficiently explicit statement near the top of the README about how those
    pieces fit together as one method and one release bundle
  - adding that contract improved first-open clarity more than another round of cosmetic edits
- The most visually misleading chart bug was not color or typography but axis semantics:
  - the training-trace renderer was linearly interpolating x-axis ticks between logged steps
  - on a four-point local run, that produced labels such as `8.8`, `12.5`, and `16.2`, which made
    a discrete optimization trace look more continuous than it really was
  - switching the x-axis to actual logged steps made the chart both clearer and more faithful to
    the underlying run artifact
- The balanced local rerun improved the real benchmark even though its tiny train-time eval looked
  worse than the earlier first-rows run:
  - the earlier run reported lower loss and higher token accuracy because it was effectively
    training and validating on a narrow easier slice
  - the new run has higher train/eval loss because it is solving a more diverse subset
  - the held-out full-test comparison is therefore the trustworthy decision surface here, and that
    surface improved sharply
- The current `eval_subset_strategy` still leaves one subtle blind spot at `max_eval_examples = 16`:
  - with `task_tract_round_robin` over `(task_type, tract)` buckets, a `16`-example cap covers all
    eight tracts but only the first two task families in bucket order
  - the new train subset is well balanced, but the tiny train-time eval subset is still not fully
    representative of all four task families
  - this does not invalidate the held-out `test` benchmark, but it does weaken the usefulness of
    train-time eval loss as a model-selection signal
- The stubborn `citation_grounded_moral_answer` failure mode is not simple theological ignorance:
  - many failing answers still produce doctrine-shaped prose
  - the common errors are wrong passage retrieval, unstable non-canonical citation formats, or
    drifting to plausible but uncited generalizations
  - this means the next improvement pass should target answer-format supervision and retrieval-like
    grounding behavior, not only more generic training steps
- The local-baseline cap was more biased than it first looked:
  - the first `128` rows of the committed `train.jsonl` export are all
    `citation_grounded_moral_answer`
  - the first `16` rows of `val.jsonl` are also all `citation_grounded_moral_answer`
  - this means the previous tiny local recipe was not merely small; it was effectively
    single-task for both train and eval
  - after switching to deterministic task/tract round-robin, the same `128`-example cap becomes a
    clean `4 task types × 8 tracts × 4 examples` balanced sample
- The present 1.5B local result is more capacity-limited by the blessed recipe than by the dataset
  itself:
  - the public local run only trains on the first `128` rows of the committed training split and
    stops after `20` steps
  - that makes the current baseline a proof-of-pipeline artifact, not a serious upper bound on
    what the Christian virtue supervision can teach the model
  - the strongest gain appearing anyway on virtue concept explanation is therefore evidence that the
    dataset signal is real even under a deliberately modest local recipe
- The trainer currently relies on TRL's default SFT path over a rendered full chat transcript:
  - the code does not yet add any repo-local assistant-only label masking or task-specific loss
    weighting
  - that means there is still realistic headroom from training mechanics alone, especially for the
    harder citation-grounded answer family
- The first CI failure after the latest README polish was not a real publication-surface break but a
  stale repo-surface assertion:
  - the README had already been updated from `Three Purposes` to `Why This Dataset Is Unusual`
  - GitHub Actions failed because one test still expected the old heading string
  - reproducing the exact `make public-release-check` target locally made the fix path trivial and
    confirmed that the rest of the release gate was still healthy
- The README had become accurate but sequentially inefficient.
  - most of the sentences were individually defensible
  - the real problem was that the landing page answered the right questions in the wrong order
  - moving the graphs and headline result upward improved readability more than another round of
    sentence-level polishing would have
- The strongest way to tell the truth here is not to hide the full matrix, but to separate public
  highlight surfaces from deep audit surfaces.
  - the full report can still carry the whole held-out matrix for reproducibility
  - the README, experiment index, figure, and package executive readout become more convincing
    once they stop giving equal visual weight to weak non-central slices
  - in practice, this makes the repo look more like a disciplined research release and less like a
    raw notebook dump
- Publication defaults can quietly diverge from the intentionally curated public story:
  - the packaging script defaults its release tag from the training run id
  - that is sensible for generic runs, but this repo deliberately preserves an older canonical
    release slug for continuity
  - HF publication therefore needed the explicit release tag passed through again, otherwise the
    model card would start pointing to a GitHub release URL that looks plausible but is not the
    repo's advertised public endpoint
- The figure itself needed to carry more of the interpretive burden:
  - a caption saying “small demo model” elsewhere in the repo was not enough
  - reviewers looking only at the chart could still miss that this was a 1.5B demonstration run
  - adding the model-size label and explicit gain arrows directly into the SVG makes the empirical
    claim much faster to read without changing any underlying metric
- Passing CI can still hide the next break if the workflow itself is on a deprecating runtime:
  - once the public-release check finally went green, GitHub immediately surfaced the next real
    issue as a Node 20 deprecation annotation on core marketplace actions
  - that made it clear the right endpoint is not merely “green today” but “green without an
    already-scheduled platform warning”
- Internal-link validation turned out to be strong enough to catch a subtle Git hygiene bug:
  - the repo already had the correct package files on one machine
  - because `artifacts/` was globally ignored, those files silently disappeared on GitHub Actions
  - the right fix was not to weaken validation but to version the smallest honest public package
    surface that the docs already claimed existed
- The real boundary in this repo is not “local vs CI” but “run artifacts vs public artifacts”:
  - `runs/` is correctly uncommitted
  - the public release gate therefore cannot require raw local run directories on GitHub Actions
  - the right CI contract is to verify committed public surfaces unless canonical local artifacts
    are actually present
- The first CI break after publication was not a logic bug but a type-stub mismatch:
  - local runtime behavior was fine
  - GitHub Actions caught that `mypy` does not reliably accept `importlib.util` as an attribute on
    the imported `importlib` module in this environment
  - importing `find_spec` directly is therefore the more portable choice for release-facing code
- External publication surfaced a real provenance nuance:
  - the adapter-producing training commit and the later publication-refresh commit are not the same
  - preserving both turned out to be the honest solution, because the release should still point
    back to the actual adapter-producing run while the current repo docs and package links move
    forward with the later publication commit
  - that is why the package surfaces now need both `git_commit` and `publication_git_commit`
- Fixing the benchmark defect did not simply move the headline in one direction:
  - the corrected local-baseline adapter now lands at `0.137` held-out citation exact instead of
    the earlier `0.150`
  - yet the fixed 12-prompt goal-demo panel improved from `3 / 12` to `5 / 12` exact citation wins
  - the corrected artifact therefore tells a more nuanced and more trustworthy story: the baseline
    is better than the untouched model in the intended virtue-reasoning slices, but its weakest
    user-style moral-QA slice still remains unresolved
- The untouched base model still produces zero passage-id citations even on the repaired
  vice-opposition prompt wording:
  - a four-prompt post-fix check on the only affected held-out base questions stayed at `0 / 4`
    exact matches
  - this made it safe to retain the prior full base benchmark surface while rerunning the adapter on
    the corrected export
- The highest-impact paper-versus-artifact discrepancy turned out not to be a markdown claim but a
  benchmark-template bug:
  - all in-scope `excess_opposed_to` and `deficiency_opposed_to` annotations in the Christian
    virtue subset are `vice -> virtue` relations
  - the exported citation-grounded questions nevertheless asked for the vice opposed to the vice
    subject in those cases, which makes that slice semantically ill-posed
  - this likely explains part of the zero-gain behavior on the
    `citation_grounded_moral_answer` task family in the current local-baseline report
- The strongest convincing story for this repo is not “look how high the numbers are” but “even a
  deliberately tiny reproducible demo run already shows the right directional gain.” Once that
  framing is explicit, the repo reads more confidently without needing to over-claim the current
  local baseline.
- Small visualization details can quietly weaken trust. The training curve already had the right
  data, but without labeled y-axis values it looked more like a placeholder than a research
  artifact; adding explicit axis ticks immediately made the optimization story easier to trust.
- “Only show the goal” is a real publication rule, not just a design preference. Once the held-out
  comparison figure and executive tables were narrowed to virtue-goal slices, the repo’s SFT story
  became sharper and more persuasive without changing a single metric.
- “Looks documented” is not the same as “is navigable.” Even after the README improved, the lack
  of top-level docstrings in a cluster of core SFT modules and the absence of a `scripts/README.md`
  still made the implementation surface feel denser than it needed to for a reviewer-grade repo.
- A README can contain the right facts and still underperform if it answers them in the wrong
  order. For this repo, reviewers need to see the problem, purpose, dataset discipline, minimal
  example framing, and empirical claim before they need the long command inventory.
- Making the SFT more prominent did not mainly require new metrics. The bigger usability win was
  narrative: readers needed a clearer first-action path and larger result figures more than they
  needed another paragraph about why the repo matters.
- For the GitHub repo page, “good results” were already present but not yet legible at first
  glance. The missing ingredient was not more experiments; it was a tighter visual/results summary
  that puts the training curve and base-vs-adapter improvement directly on the public landing
  surface.
- The weakest remaining public surface was not another missing experiment or repo doc. It was the
  live Hugging Face model page itself: even after the local package improved, the published README
  still undersold the project until the publication template, package tests, and actual Hub upload
  were all tightened together.
- The last portability leak was not in the README or dataset docs. It lived inside copied package
  metadata, where absolute run paths and venv details looked harmless locally but would have made
  the public adapter bundle feel machine-bound and less reproducible.
- The next weak point after report/package polish was not another missing experiment but a basic
  public-release issue: the top-level README still mixed older viewer copy, a stale `12,337`
  passage count, and a less-than-explicit reproduction path. For a reviewer-facing repo, first
  impression and factual consistency were now the real bottleneck.
- A simple editable install is not enough for a publishable local SFT recipe on Apple Silicon. The
  repo needed a pinned local lockfile and a dedicated setup entrypoint, because the canonical Mac
  path intentionally avoids the CUDA-oriented `bitsandbytes` extra even though the broader package
  still supports it on remote machines.
- The last operational edge case in the canonical local rerun was not training instability but
  long-tail adapter inference on Apple `mps`. Bulk generation advanced cleanly through most of the
  held-out benchmark, then stalled near completion at `223 / 233` examples. Recovering the last
  prompts through isolated single-example subprocesses turned out to be both honest and effective:
  the run kept its canonical id, every recovered example still completed on `mps`, and the public
  artifact path no longer depends on pretending the original bulk process was perfectly reliable.
- The last publishability gap was not another model feature but public artifact coherence: once the
  local pilot became stable, the missing pieces were a fixed goal-demo panel, a curated report
  generator, and a packaging path that ties a checkpoint, report, dataset card, and release tag
  back to the same run id.
- Once those publication pieces existed, the next weak point turned out to be drift between them.
  The repo needed one explicit QA gate for “package manifest, docs, report, and published URLs all
  still agree,” otherwise a later doc refresh could silently desynchronize the public story.
- Public naming drift can hide in more places than prose. Even after docs were renamed, the live
  local run folders and copied package metadata were still carrying `pilot_lite`, which meant the
  repo only looked polished until someone inspected the actual artifact bundle.
- Public and generated surfaces can drift independently. Even after the repo docs were corrected,
  the generated model card and release notes still reflected the older command surface until they
  were updated from the publication template itself.
- Public-doc polish can fail in a quieter way than stale metrics: a README or flagship report can
  look coherent while quietly pointing at a moved or missing local artifact. That kind of breakage
  is cheap to prevent once link validation is part of the publishable verification path.
- A dataset card can technically exist while still under-serving the public story. For this repo,
  the dataset itself is a headline product, so the dataset card and `data/processed/sft/README.md`
  also need to point readers toward the guide, flagship report, and canonical published baseline.
- A report can be exhaustive and still underperform publicly if it makes the reader work too hard
  for the top-line judgment. Once the flagship report had all the tables and examples, the next
  quality step was to surface an executive readout that says plainly where the adapter is strong,
  where it is weak, and what the goal-demo panel actually shows.
- External publication surfaces can lag behind repo quality even when they are generated from the
  same run. A model card or release note that exposes only one headline metric still undersells the
  actual research result compared with the flagship report, so those package surfaces need their
  own executive summary layer too.
- GitHub repo detection is trickier than it looks in a forked research workflow. `gh repo view`
  can resolve to the upstream repository in a way that is fine for browsing but wrong for release
  creation, so the publication path now trusts `git remote get-url origin` first and uses `gh` only
  as a fallback.
- The real local-research blocker was not dataset size but runtime mismatch: the existing training
  stack was written as though every serious run were CUDA + 4-bit QLoRA, while the user's actual
  first baseline machine is a 16 GB Apple-Silicon laptop.
- Committing the public Christian virtue dataset exports into the canonical repo is operationally
  reasonable here. The two export trees are only about `27 MB` together, so keeping data, docs, and
  training entrypoints in one GitHub repo is cleaner than splitting public usage across multiple
  repositories.
- For the local 1.5B path, good experiment hygiene matters as much as raw throughput. Timestamped
  run directories, config snapshots, environment captures, and train-log histories are the
  difference between “it ran once on my laptop” and a reusable pilot baseline.
- The latest operational bug on the Mac path was not model loading but adapter-path drift:
  `local-baseline` became the practical default, but one wrapper and one inference config were still
  wired to `pilot/latest`, so adapter evaluation failed even after a successful `local-baseline` run.
- Comparing the finished `local-baseline` run against the earlier interrupted full `pilot` showed that
  the main failure mode was runtime pathology, not optimization collapse:
  - both runs showed a healthy downward loss curve through step 20
  - the heavier full `pilot` even reached slightly better step-20 eval loss on its larger eval
    slice
  - but its per-step wall time became wildly unstable on MPS, with multi-hour jumps appearing by
    steps 17 and 20, while `local-baseline` stayed in a consistent seconds-per-step regime
- The last mile for research reproducibility was not the model code itself but the operator path:
  without standardized run directories, preflight failure messages, and an explicit base-vs-adapter
  comparison report, it is too easy for a “successful” experiment to remain hard to rerun or hard
  to compare honestly a week later.
- For this repo, the best “small model” choice is not a random tiny instruct model but a smaller
  member of the same family. `Qwen/Qwen3-0.6B` keeps the same chat-template / thinking-mode
  behavior as the 4B baseline while materially lowering remote training cost and benchmark time.
- The first real benchmark run exposed a portability gap rather than a data bug: this machine has
  Apple `mps` but no CUDA, and the original inference path treated `load_in_4bit: true` as though
  that implied a CUDA-capable runtime. For this repo, the honest fix is to make the runner
  device-aware and record when it falls back to full-weight generation on non-CUDA hardware.
- The first local `Qwen/Qwen3-4B` generations also exposed two evaluation-quality hazards:
  - Qwen3 will happily emit `<think> ... </think>` traces unless the chat template explicitly
    disables that mode
  - copied benchmark metadata can accidentally look like a model-predicted relation label if the
    evaluator is too permissive about fallback fields
- The reviewed doctrinal files are structurally consistent on the essentials, but not on every
  convenience field. In particular, some tract files omit `edge_layer`, so the SFT loader has to
  default that field to doctrinal at load time rather than assuming the JSONL rows are perfectly
  uniform.
- `question_id` is the right split boundary here because concept-explainer examples synthesize
  multiple annotations from one question. Grouping at the row level would leak the same doctrinal
  locus across train and eval even if the annotations themselves were distinct.
- A tract-wide OOD holdout is more informative than a random hard subset for this first pass. The
  `temperance_closure_161_170` block is coherent enough to act as a real transfer test while still
  leaving the core virtue set broad in train/val/test.
- Once the dataset export exists, the next research bottleneck is not another template family but a
  leakage-safe way to run actual generations. Without prompt-only benchmark files, it is too easy
  to evaluate against exports that already contain the gold assistant answer.
- A control can look perfectly wired in Streamlit while still being a semantic no-op if the shell drops its value before the data query. That is exactly what happened with `Center concept` in Overall Map: the selectbox updated session state, but the graph call path forcibly replaced it with `None`.
- The next layer of confusion was subtler: generic navigation into `Overall Map` was also carrying the currently selected concept into map state, so users could arrive in what looked like a global view that was already secretly centered on one node.
- For a map-centered filter, scope-aware options matter almost as much as the filtering itself. Offering every concept in the whole registry made it too easy to choose a concept that had no edges in the current span and conclude the control was broken.
- The home `Open interactive map` route had the same hidden-state smell in a different form: it combined the selected home concept with the selected home tract preset. Under the default home settings that produced mismatches like `Faith tract + Charity center`, which looked to users like a broken overall map even though the renderer was behaving correctly.
- Default-range changes are easy to half-apply in this viewer because map range is referenced in state defaults, reset actions, shell fallbacks, and live slider tests. The range can be switched back to `1–46`, but only if every one of those paths follows the same constant.
- For this icon, a cross works best when it is structural rather than decorative. Putting the cross behind the book makes the mark read faster and feel more monastic than adding a tiny floating cross elsewhere.
- The remaining “prototype feel” was coming from narrow-column typography more than from any major layout bug. A few oversized labels in the map evidence rail made the whole page feel less polished than the underlying structure already was.
- On a public-facing README, one strong viewer entry works better than several medium-strength links. Repeating the same app URL in different visual styles made the top of the page feel busier rather than more useful.
- For favicon-scale medieval styling, subtraction helps more than addition. A heavier seal ring and one simple central symbol read better than multiple tiny ornaments.
- A tab icon can be recognizable without being typographic. For this project, a book-centered seal reads more “scholarly press” than initials alone.
- A favicon that works at art-book scale can still fail at browser-tab scale. For this app, recognizability matters more than portrait fidelity once the icon shrinks to a few pixels.
- Very small wording choices matter in narrow dashboard rails: `Local map` is semantically fine, but `Local` reads much better once the control has to live beside quick spans and a range slider.
- For this project, a portrait-based favicon works better than a symbolic glyph because the product is already visually anchored around Aquinas rather than abstract data tooling.
- The homepage title can stay literary while search-critical wording moves into the page title, subtitle, and first supporting sentence. That gives better discoverability without flattening the product voice.
- In passage search, the most common “broken filter” feeling did not come from search itself. It came from valid-looking question/article widget values that no longer belonged to the currently selected part or preset scope.
- Streamlit Community Cloud currently provisions Python `3.14.x`, and `lxml==5.4.0` may not install there without system `libxml2/libxslt` development headers.
- The current repository only needs BeautifulSoup parsing behavior for app runtime; a hard `lxml` dependency is not required to run the dashboard.
- In a graph-centered scholarly dashboard, an expanded filter container can do more harm than a missing control. If the first fold does not show the graph itself, users read the page as a control panel instead of a map.
- The auto-carried center concept was enough to make the old overall-map filter panel feel “active” even when the user had not intentionally narrowed anything. That made the page look busier than it really was.
- README top-level choice overload matters quickly once the app is already live. After deployment exists, a public-facing repo front page benefits from one obvious “open the app” path and demoting run/deploy/setup choices beneath it.
- The site feels much more “AI dashboard” than “finished scholarly object” when icons are emoji-forward. Classical typography and restrained ornament do more work here than adding more decorative graphics.
- On the landing page, a disabled route button reads to users as a broken button, not as a helpful guardrail. The tract card works better when it always starts from a real reviewed tract.
- The recent overall-map bug was not mainly a widget problem; the deeper failure was that range rendering still assumed a single tract family even after the UI had grown cross-tract quick spans and free-form question sliders.
- New Advent part landing pages are structurally usable for scope discovery.
- Question pages expose article structure through `h2#articleN` anchors and labeled paragraphs.
- Some explicit *Summa* cross-references appear inside malformed anchor markup, so visible-text extraction is safer than relying only on `href` attributes.
- At least one live page (`I-II q.40 a.1`) contains duplicated reply numbering in the source HTML, so exported `obj` and `ad` ordinals need normalization by occurrence order.
- At least one live page (`I-II q.87 a.7`) repeats `On the contrary` across multiple paragraphs, and another (`I-II q.89 a.1`) incorrectly reuses `On the contrary` inside a reply.
- At least one live page (`II-II q.172 a.1`) uses `Objection 2.` inside the replies section, so objection labels cannot be trusted blindly once an article has entered its response/reply phase.
- Because raw HTML redistribution is unclear, fixture strategy uses synthetic structural HTML plus optional live-network smoke tests instead of committed full source pages.
- The prudence tract required a more precise part taxonomy than a generic `part_of` edge, so the reviewed layer now distinguishes `integral_part_of`, `subjective_part_of`, and `potential_part_of`.
- Several prudence terms required explicit normalization notes rather than silent flattening:
  - `reason` vs `reasoning`
  - `understanding or intelligence` vs the gift of understanding elsewhere
  - `political economy` / `domestic economy` vs normalized prudence labels
- The strongest under-annotated question after the first prudence pass is `Q56`, not because parsing failed, but because precept material is doctrinally narrower and easier to overstate.
- The broader pilot slice needed a separate concept registry rather than a growing pile of ad hoc annotation labels.
- Article-level `treated_in` annotations work best when evidence extraction can fall back to a stable snippet instead of failing on exact alias matches.
- A few labels needed explicit ambiguity declarations in the alias table before validation would stay honest:
  - `love`
  - `law`
  - `grace`
  - `virtue`
- In the temperance closure tract, precept focus tags could not safely be inferred from every concept that later appears as a precept target. The first pass falsely labeled humility/pride edges as precept material until focus tags were restricted to `q.170`, precept relations, and precept nodes themselves.
- A dashboard built directly from tract summaries can accidentally foreground candidate activity as if it were doctrinal structure. Tract highlight extraction needed to suppress generic `candidate_relation_count` so the landing page would surface tract-specific reviewed relation families instead of workflow volume.
- The main UX problem in the Streamlit app was not a single broken page but a shared product smell:
  - raw schema fields were exposed directly to users
  - filters lived inline in the content flow rather than in a stable control rail
  - reviewed, editorial, and candidate layers were technically separate in data but visually flattened in the UI
  - default Streamlit spacing and typography made the app read like an internal console rather than a public research product
- A polished graph treatment needed more than better colors:
  - users need a visible narrowing workflow before they trust the canvas
  - raw edge ids are too opaque for evidence selection
  - public-facing pages feel unfinished if tables cannot be exported directly from the active view
  - users also need explicit in-canvas controls and higher-signal tooltips, otherwise even a visually improved graph still feels like a black box
- Several original page names were accurate but not helpful:
  - `Graph View` undersold that this is the primary relationship map
  - `Stats / Audit` sounded internal rather than decision-useful
  - `Passage Explorer` and `Concept Explorer` benefited from plainer evidence/network framing
- Manager-facing users benefit from comparison and export more than from raw candidate volume. Candidate counts still matter, but they belong in diagnostic sections, not at the top of the main overview.
- `qq.163–165` worked better as a tract-local doctrinal case node (`concept.adams_first_sin`) than as either a generic pride alias or a person-instance graph.
- `qq.168–169` confirmed that `modesty_general` from `q.160` cannot simply absorb later external-modesty species; outward behavior/play and outward attire need separate reviewed concepts and filters.
- The pilot app search and evidence views exposed that result ordering should not assume the first matching passage is annotated.
- Strict type-checking surfaced a useful maintenance issue: curated seed payloads needed clearer typing and less variable reuse to stay auditable.
- The first corpus-wide candidate pass shows exactly why reviewed and candidate layers must stay separate:
  - candidate volume is useful for discovery, but far too large to read as doctrine
  - law/precept material and broad virtue language generate especially high ambiguity
- Explicitly excluded `II-II qq. 183–189` are best preserved as `excluded` manifest rows rather than silently omitted, because that makes scope auditing visible in the browser and reports.
- A single question outside the pilot subset can produce a legitimately useful review packet; `I-II q.100` became the first good example because it is high-density, structurally parsed, and not yet doctrinally reviewed.
- The theological virtues block forced a sharper distinction between reviewed doctrinal claims and reviewed structural/editorial treatment correspondences. Question-level `treated_in` can be explicit without thereby becoming doctrinal graph truth.
- Broad tract terms such as `God`, `neighbor`, `peace`, `mercy`, `despair`, and `hatred` are useful registry concepts but dangerous full-corpus detection labels. Candidate extraction now needs suppression/alias discipline rather than assuming every added concept should become a broad mention target.
- The tract naturally reuses pilot-reviewed material in `II-II q.1` and `q.23`, so combined tract exports work best when they inherit stable pilot ids rather than rewriting those earlier records.
- Merged reviewed edges can carry support from more than one question in the same tract, so question-range graph filters need to trim evidence bundles, not merely decide whether an edge is included.
- The justice tract forced a stronger ontology split than earlier blocks:
  - wrong acts are not interchangeable with vice labels
  - harmed domains are not interchangeable with virtues or objects
  - judicial roles and judicial process concepts need their own node types to keep court-related questions inspectable
- Reusing tract-reviewed concepts inside the shared app bundle needed an overlay compatibility layer, because older prudence concept files use a tract-local schema rather than the newer corpus concept schema.
- The first pass of justice review showed that `q.58` can still rank as under-annotated despite earlier pilot work, because the justice tract is much denser than the original pilot slice; the review queue now intentionally targets lighter non-pilot justice questions first.
- `q.59` and `q.79` emerged as the clearest early human-review pressure points:
  - `q.59` because generic injustice is foundational but easy to overgeneralize
  - `q.79` because omission/transgression sit uneasily between tract-local and broader moral classification
- The religion tract needed a new ontology split beyond generic virtue/vice language:
  - positive acts of religion are not interchangeable with the virtue of religion itself
  - superstition-side excesses are not interchangeable with deficiency-side irreligion
  - sacred-object modeling is necessary to keep perjury, sacrilege, and simony inspectable
- `q.80` works best as a structural and doctrinal gateway rather than a dense doctrinal question on its own, so its reviewed layer stays intentionally light.
- `oath`, `vow`, and `adjuration` create real normalization pressure because all three use reverential or divine-name language without naming the same act.
- `sacred_time` looked tempting as a reviewed node, but the current tract support was cleaner for sacred things, persons, places, sacraments, and spiritual offices.
- `q.97` emerged as the first clear human-review pressure point in the tract, not because parsing failed, but because temptation-of-God material is doctrinally central while still sparsely reviewed.
- The owed-relation block needed an explicit due-mode field rather than a loose note:
  - origin, excellence, authority, benefaction, and rectificatory debt all appear in the tract
  - collapsing them into generic respect language would have hidden the doctrinal point of the block
- The actual question headings matter more than thematic summaries here:
  - `Piety`
  - `Observance, considered in itself, and its parts`
  - `Dulia`
  - `Obedience`
  - `Disobedience`
  - `Thankfulness or gratitude`
  - `Ingratitude`
  - `Vengeance`
- `q.103` creates a real normalization problem because `dulia` can name broad reverence to excellence and also narrower service to a human lord.
- `q.106` and `q.107` remain partially parsed, so benefaction-related review is usable but still lighter than the surrounding tract.
- `q.104` emerged as the clearest first human-review pressure point in the tract because authority/command structure is central while candidate density is much higher than current reviewed coverage.
- The connected-virtues tract needed an explicit sub-cluster field rather than a loose note:
  - self-presentation
  - social interaction
  - external goods
  - legal equity
- `truth` in `q.109` is a real normalization hazard because the English label can drift toward faith-tract or generic truth unless the tract context stays explicit.
- `q.109`, `q.110`, and `q.111` remain partially parsed, so the self-presentation block is usable but still visibly lighter than the surrounding tract.
- `irony` in `q.113` is easy to misread in a modern rhetorical sense, so the registry now keeps its tract-local moral meaning explicit.
- `q.120` is structurally clear but semantically risky because `epikeia` can drift into generic fairness unless its legal-letter and lawgiver-intent structure stay explicit in schema and UI.
- The fortitude-parts tract needed stronger distinction pressure than the earlier connected-virtues block:
  - `magnanimity` and `magnificence` cannot share a convenience node
  - `presumption` in `q.130` cannot be allowed to collapse into the hope-tract `presumption`
  - honor-related structure and expenditure-related structure need distinct tract-local concepts and filters even when both concern “greatness”
- `q.129` remains structurally dense because honor, worthiness, confidence, assurance, and goods of fortune all cluster around magnanimity without being identical.
- `q.135` confirmed that tract-local expenditure excess should stay distinct from generic prodigality; the magnificence questions are about proportion between work and expense, not simply about spending a lot.
- The fortitude closure tract surfaced a second fortitude-specific normalization hazard:
  - the corpus already had an act-level `perseverance`, so the closure tract needed a distinct virtue-level `concept.perseverance_virtue`
  - `gift of fortitude` and virtue-level `fortitude` share English wording but cannot share a concept id
  - the first honest fortitude synthesis view is doctrinally strong for `qq. 129–140`, but `qq. 123–128` remain only structurally framed until their own reviewed block exists
- The temperance phase-1 tract surfaced a similarly sharp taxonomy hazard:
  - `q.143` names `shamefacedness` and `honesty` as integral parts, `abstinence` / `sobriety` / `chastity` / `purity` as subjective parts, and `continence` / `meekness` / `modesty` as potential parts
  - that means `fasting`, `virginity`, and `clemency` cannot be auto-promoted into the same part taxonomy merely because they sit in neighboring questions
- `anger` needed an explicit ambiguity override in this tract because the same English label can name passion-level anger or vice-level anger depending on the local passage.
- The major under-annotated questions are lighter doctrinally, not structurally broken:
  - `q.144`
  - `q.145`
  - `q.147`
  - `q.152`
  - `q.155`
  - `q.158`
- The remaining parse-partial questions are visible but usable:
  - `q.143`
  - `q.148`
  - `q.149`
- `q.154` strongly rewards conservative species handling: the tract supports real parts-of-lust structure, but it is still easy to over-project more detailed taxonomy than the reviewed passages actually warrant.

## Decision Log

- Add a public claim map and make it part of the checked publication bundle.
  Reason:
  - the repo is already strong enough that the next gain comes from explicit claim discipline, not
    another cosmetic tweak
  - reviewers should not have to infer the difference between the canonical baseline claim, the
    citation-frontier follow-up claim, and the project’s longer-term ambition
  Consequence:
  - the release now has one public page that maps claims to artifacts, commands, and boundaries
  - `make public-release-check` now verifies that this page remains present and internally linked
- Add repo-structure and reproducibility-contract sections to the README rather than pushing all
  topology guidance into `docs/repository_map.md`.
  Reason:
  - a reviewer should understand the public artifact layout before they leave the main page
  - `docs/repository_map.md` is still valuable, but it should deepen orientation rather than carry
    the whole burden
  Consequence:
  - the README now covers problem, method, result, structure, and exact reproduction contract in
    one public surface
- Favor collapsible qualitative examples over deleting them from the flagship report.
  Reason:
  - the goal-demo panel is genuinely useful evidence for reviewers and collaborators
  - the problem was layout density, not the underlying examples
  Consequence:
  - the report now stays auditable in full while reading much more cleanly on first open
- Replace code-style labels with publication labels in the citation-frontier follow-up report.
  Reason:
  - tables such as `temperance_141_160` and `strong_textual_inference` are technically correct but
    visually weaker for public reading
  Consequence:
  - the follow-up report now uses tract-display labels and readable support-type labels while
    preserving the same metrics
- Extend the publication verifier to cover the citation-frontier audit and follow-up report.
  Reason:
  - the repo now presents those artifacts as part of its public research story
  - leaving them outside the verification bundle would create an avoidable trust gap
  Consequence:
  - `make public-release-check` now enforces the completed follow-up surfaces as well as the
    canonical baseline ones
- Keep the canonical public baseline unchanged even after the completed citation-frontier win.
  Reason:
  - the follow-up is genuinely better on the overall held-out benchmark and on the hard citation
    slice
  - but it also introduces regressions large enough that replacing the public baseline would blur
    the real empirical picture
  Consequence:
  - the baseline remains the public distribution artifact
  - the citation-frontier run is now documented as a completed follow-up report with its own
    strengths, costs, and next-step thesis
- Prioritize documentation coherence for the new citation-frontier path before launching another
  round of implementation.
  Reason:
  - the repo already had the core code, configs, wrappers, and Make targets
  - the most likely next failure mode for a new reader was choosing the old baseline path and never
    seeing the formalized next-step experiment
  Consequence:
  - the main guide and repository map now make the research frontier discoverable from first-open
    documentation, not only from the audit report or Makefile grep
- Implement the next citation-frontier step as a quota-based same-budget recipe rather than as a
  heavier run or a broader dataset.
  Reason:
  - the remaining weakness is concentrated in one task family, not in overall virtue scope
  - a same-budget mixture change makes causal interpretation cleaner on the current laptop
  - the user explicitly asked for a logical next step that stays within a bounded local runtime
  Consequence:
  - the repo now has a dedicated `citation-frontier` training rung, adapter-eval path, comparison
    path, and audit path
  - the next research claim can be “does a more citation-heavy small-run mixture improve stable-id
    recovery?” instead of “does more total compute help?”
- Prioritize explicit public-surface contracts over further decorative polish once the figures are
  already readable.
  Reason:
  - reviewers and collaborators decide trust quickly from whether a repo states its method,
    outputs, and artifact boundaries clearly
  - by this stage, missing structure cues were a larger problem than missing visual tweaks
  Consequence:
  - the README now names the pipeline stages and expected outputs directly
  - the repository map now names the canonical public bundle directly
  - the next audit pass can focus on any truly missing public surface rather than on layout guesswork
- Standardize all public SFT figures around one shared visual language rather than leaving one-off
  assets in older styles.
  Reason:
  - mixed chart treatments weaken first-open trust even when the underlying results are solid
  - public readers should not have to infer which figures are current or canonical from styling
    differences
  Consequence:
  - the training trace, held-out comparison, citation-frontier audit, and timing comparison now
    present as one coherent release bundle
- Trust the full held-out benchmark more than the tiny train-time eval slice when auditing local
  recipe changes.
  Reason:
  - the current `16`-example eval cap is too small to represent all four task families under the
    new balanced bucket strategy
  - the held-out `test` split is the only surface here that fully reflects the repo's public SFT
    goal
  Consequence:
  - report-level conclusions should be drawn from `base_test` / `adapter_test` / `compare_test`
    rather than from training loss alone
- Treat `citation_grounded_moral_answer` as the next targeted optimization frontier.
  Reason:
  - the balanced rerun already proves strong gains on virtue concept explanation,
    reviewed relation explanation, and passage-grounded doctrinal QA
  - the remaining ceiling is now concentrated in one task family with clear formatting and passage
    selection failures
  Consequence:
  - the next recipe improvement should likely add stronger answer-shape supervision for user-style
    moral QA rather than broadening doctrinal scope
- Fix the local small-run bias at the training-recipe layer instead of changing dataset order.
  Reason:
  - the committed export order is part of the reproducible dataset artifact and should remain
    stable
  - the real bug was the trainer assuming that “first N rows” was a harmless small-run cap
  Consequence:
  - future small runs can be more representative without mutating the dataset export itself
- Make subset selection an explicit config field and a first-class run artifact.
  Reason:
  - hidden sampling behavior is hard to audit and easy to forget when reading old reports or new
    configs
  - the user explicitly wanted structured logging for the training path
  Consequence:
  - dry-run output now shows subset strategy
  - training metadata now records the exact selected task/tract mix
  - docs can point readers to `subset_summary.json` instead of relying on prose alone
- Treat the current `local-baseline` result as a minimum viable public demonstration, not as the
  recipe to optimize against indefinitely.
  Reason:
  - the blessed local rung is intentionally constrained for reproducibility on a `16 GB` Apple
    Silicon laptop
  - its `128`-example / `20`-step budget is too small to answer the question “how good can this
    dataset make the model?” in any strong sense
  Consequence:
  - future quality-improvement work should first strengthen the recipe itself before drawing
    negative conclusions about the dataset or the theological supervision design
- Prioritize three improvement levers before any dataset-scope expansion: stronger local recipe,
  better task balancing, and closer inspection of loss masking / supervision geometry.
  Reason:
  - the corrected report already shows which task family is strongest and which remains weak
  - those levers preserve the repo's evidence-first scope while directly targeting the current
    bottlenecks
  Consequence:
  - the next serious optimization pass can remain within the same `christian_virtue_v1` export
    while still plausibly improving held-out Thomist virtue behavior
- When a public README heading is intentionally renamed, update the repo-surface assertions in the
  same change rather than treating them as follow-up cleanup.
  Reason:
  - this repo uses publication-surface tests as part of the actual release contract
  - leaving a stale string assertion behind creates a noisy CI failure even when the public surface
    itself is correct
  Consequence:
  - the repo-surface test now checks the new `Why This Dataset Is Unusual` section and its key
    phrases instead of the retired `Three Purposes` label
- Prefer a shorter README with earlier empirical payoff over a more exhaustive README with repeated
  justification sections.
  Reason:
  - the repo already has a full guide, dataset card, repository map, maintainer doc, and flagship
    report
  - the README should act as a landing page, not as a second full report
  Consequence:
  - duplicate sections such as repeated purpose/method/value explanations are being merged
  - the README now spends its early screen space on the public result, graphs, and start paths
- Keep the weak-slice metrics in the deeper report and package manifest, but remove them from the
  main public executive surfaces.
  Reason:
  - the repo's top-level claim is about Thomist moral-virtue alignment, not about exhaustively
    leading with every weak sub-benchmark
  - the strongest honest public evidence is the `40.6%` virtue-concept slice plus the supporting
    reviewed-relation and theological-virtues gains
  Consequence:
  - README, experiment index, report executive readout, held-out SVG, and HF/release package prose
    will foreground the strongest slices only
  - the full held-out matrix remains available lower in the flagship report for auditability
- Keep passing the canonical continuity release tag when republishing the HF adapter, even after
  purely presentational updates.
  Reason:
  - the public HF page should inherit the improved package surfaces
  - the repo still intentionally uses the older GitHub release slug as its stable external release
    endpoint
  Consequence:
  - HF can be updated incrementally without fragmenting the publication story
  - the tracked package metadata must be committed after HF republish so GitHub and HF keep the
    same provenance links
- Put the small-model framing and improvement direction inside the held-out SVG instead of leaving
  both points only to surrounding prose.
  Reason:
  - the chart is reused across README, report, and adapter package surfaces
  - the public claim is specifically that a small 1.5B demo model still improves in the right
    virtue-aligned direction
  Consequence:
  - the comparison figure now self-identifies as a small-model demo
  - per-slice arrows and delta labels now make the base-to-adapter movement legible at a glance
- Upgrade the release workflow to the current stable `actions/checkout@v6` and
  `actions/setup-python@v6` pair once the clean-checkout gate is green.
  Reason:
  - GitHub Actions now warns that the older Node 20 based action majors are on a deprecation path
  - the public release workflow should be forward-stable, not merely currently passing
  Consequence:
  - the workflow no longer carries an avoidable platform-warning annotation
  - repo-surface tests now treat the current action majors as part of the release-quality contract
- Commit a minimal repo-visible adapter package surface instead of requiring CI to infer it from
  ignored local files.
  Reason:
  - the public docs already point readers to a canonical local adapter package
  - clean-checkout CI can only verify what the repo truly versions
  - committing the whole local package would add unnecessary binary/tokenizer weight to the repo
  Consequence:
  - the canonical package now has a stable repo-visible `README.md`, `package_manifest.json`,
    `release_notes.md`, and held-out comparison SVG
  - heavy adapter binaries remain local/Hugging Face concerns rather than bloating the Git repo
  - public docs now link to the package README file directly, which is both clearer for readers and
    safer for link validation
- Make the publication verifier two-mode instead of all-or-nothing.
  Reason:
  - local maintainers still need a strong rebuild-and-verify path when canonical run artifacts are
    available
  - GitHub Actions runs on a clean checkout where `runs/` is intentionally absent
  - requiring uncommitted run directories in CI would make the public-release gate structurally
    impossible to satisfy
  Consequence:
  - the Makefile now rebuilds report/package only when canonical run artifacts are present
  - the public-artifact verifier now falls back to package-manifest verification when run dirs are
    absent
  - focused tests now lock that repo-only verification mode in place
- Prefer explicit `from importlib.util import find_spec` imports in the SFT execution surface.
  Reason:
  - it preserves identical runtime behavior
  - it is clearer to read
  - it avoids `mypy` environment drift between local runs and GitHub Actions
  Consequence:
  - the CI-visible SFT modules no longer depend on `importlib.util` attribute resolution
  - `public-release-check` is more trustworthy as a cross-environment gate
- Keep the public release identity stable while distinguishing run provenance from publication
  provenance.
  Reason:
  - the existing GitHub release slug is already linked across the repo and external publication
    surfaces
  - the adapter itself was produced from run commit `662c9d3`, which should remain the authoritative
    training provenance
  - the later repo polish and publication sync landed at `21dcc7c`, which should remain visible as
    the publication-refresh commit
  Consequence:
  - generated package surfaces now carry both commit roles explicitly
  - the live Hugging Face page and GitHub release can stay stable without pretending the training
    run and publication refresh happened on one identical commit
- Treat the repo-local adapter package and flagship report as the canonical evaluation surfaces for
  the corrected rerun even before the public distribution endpoints are refreshed.
  Reason:
  - the corrected rerun is now the truth-bearing artifact inside the repo
  - the Hugging Face repo and GitHub release still matter as stable download endpoints
  - keeping the older GitHub release slug is acceptable if the repo states clearly which surfaces
    carry the authoritative corrected numbers
  Consequence:
  - `package_manifest.json`, package `README.md`, and `release_notes.md` now point to the corrected
    run ids and metrics
  - the README, fine-tune guide, experiment index, dataset card, and maintainer workflow now all
    describe the same artifact-status split instead of competing stories
- Treat the older `0.150` local-baseline adapter score as superseded once the corrected
  vice-opposition prompt rerun completed.
  Reason:
  - that score came from a benchmark with a real question-polarity defect
  - the corrected rerun now exists and is cheap enough to be the canonical manuscript artifact
  Consequence:
  - the flagship report, regenerated figures, and comparison markdown now use the corrected
    adapter run `20260419_154757`
  - the report now states the weaker aggregate headline (`0.137`) together with the stronger
    goal-demo improvement (`5 / 12`) so the artifact stays exact rather than selectively upbeat
- Treat the polarity error in `excess_opposed_to` / `deficiency_opposed_to` template rendering as
  a code bug, not merely a documentation bug:
  - the gold annotations are internally coherent
  - the question/answer templates are what invert the intended virtue-opposition direction
  - leaving the export untouched and only narrowing the report would preserve a known benchmark
    defect inside the canonical public artifact
  - therefore the correct next step is to fix the template layer, rebuild the export, rerun the
    canonical local baseline, and then revise the manuscript-style report against the corrected run
- Keep the public framing of the canonical 1.5B run intentionally narrow and strong:
  - describe it as a small reproducible demo baseline
  - emphasize that it proves the dataset and SFT workflow work end to end
  - reserve more diagnostic weak-slice language for deeper report detail rather than top-level
    README/model-card summaries
- Reserve `pilot` terminology for the older corpus/review overlay where it is historically
  meaningful, but remove it from the public 1.5B SFT recipe surface:
  - the official local rung is `local-baseline`
  - the heavier experimental rung is `extended`
  - package metadata and copied run artifacts should be sanitized so those names remain coherent
    even when the original training run was created under older local naming
- Treat the repo root itself as the primary SFT landing page for outsiders. The README should make
  it obvious that this repository is:
  - the guide for how to fine-tune on Summa Moral Graph
  - the demo showing that the pipeline runs end to end
  - the proof surface showing held-out gains, training curves, and public artifacts
- Treat the GitHub README and experiment index as results surfaces, not only navigation docs. They
  should show:
  - one compact held-out benchmark table
  - one visible training-curve figure
  - one visible base-vs-adapter comparison figure
  - one short interpretive sentence that explains why those visuals support the SFT claim
- Treat unlabeled axes and off-goal benchmark slices as publication-quality failures on the public
  SFT figures:
  - the training trace should always expose readable y-axis values
  - the main held-out comparison graphic should foreground only the virtue-goal task families that
    match the stated Christian virtue assistant objective
  - broader overall metrics can remain in deeper detailed sections, but not in the first public
    comparison table or figure
- Treat entrypoint discoverability as part of the artifact contract:
  - major public modules and scripts should carry top-level docstrings
  - `scripts/README.md` should explain which entrypoints are public quickstart surfaces and which
    ones are maintenance helpers
  - a short memorable public-release check target is worth adding even if the longer specialized
    verify command remains available
- Treat README framing as part of the research claim itself:
  - the landing page should say explicitly that the `1.5B` adapter is a minimal example
  - it should explain that the purpose is Thomist moral virtue alignment, not generic theology chat
  - it should explain why the dataset is trustworthy before asking the reader to trust the result
- Treat the Hugging Face model page as part of the review-grade publication surface, not as a
  secondary mirror. The generated model card should include:
  - a strong abstract and snapshot table
  - direct dataset/report/release links
  - an embedded benchmark figure when available
  - a concrete usage snippet
  - the final publication-verify command
  - explicit limits so the page does not over-claim what the adapter proves
- Treat machine-specific filesystem paths as a release-quality failure, not a cosmetic annoyance.
  Public docs, committed manifests, review queues, and packaged adapter metadata should all prefer
  repo-relative paths where possible, and the publication gate should verify that contract.
- Treat the archived `docs/archive/aquinas_summa_moral_graph_implementation_plan.md` file as
  historical project context rather than root-level clutter, and keep the live execution history
  in `docs/execplans/summa-moral-graph.md`.
- Add one explicit setup surface for the canonical public local baseline:
  - `make setup-christian-virtue-local`
  - it should install the pinned Apple-Silicon lockfile and then install the repo editable without
    re-resolving dependencies
- Add one explicit one-command reproduction surface for the canonical public local baseline:
  - `make reproduce-christian-virtue-qwen2-5-1-5b-local`
  - it should run build, smoke, local-baseline, base eval, adapter eval, comparison, report rebuild,
    and publication verify in order
- Treat the repository map as a first-class public document and include it in publication-surface
  verification alongside the README, guides, dataset card, and flagship report.
- Fix legacy public pointers that escape the repo itself. `AGENT.md` should point to local
  `./AGENTS.md`, not an absolute path on one developer machine.
- Keep the committed-state train run `20260418_193038` as canonical, reuse the already validated
  base test run `20260418_143349`, and finish only the new adapter evaluation against commit
  `f9fd589` rather than burning more local time on duplicate base generations.
- Preserve the stalled adapter-eval run id `20260418_203546` and recover its final missing rows
  instead of discarding it and pretending the completed public artifact came from a different run.
  Recovery should:
  - write full recovered prediction rows to disk immediately
  - keep a separate recovery log
  - note the recovery method in the final run manifest
- Keep one official public local recipe instead of documenting multiple equally blessed Mac
  training rungs:
  - `smoke` stays a debug sanity check
  - `local-baseline` is the only canonical local training rung in README, guides, and report index
  - heavier local `pilot` remains in-repo but is explicitly experimental
- Keep the public purpose statement consistent across README, guides, reports, and model packaging:
  train an Aquinas-grounded Christian virtue assistant that answers within reviewed evidence, uses
  Aquinas's moral categories, and preserves source traceability.
- Add a fixed qualitative goal-demo panel for the public report, but keep it separate from the
  training set and use it only for held-out manual review and publication-facing comparison.
- Treat Hugging Face Hub as the primary adapter host and GitHub releases as the public mirror layer,
  with both pointing back to the same run id, commit hash, dataset export, and report.
- Add a first-class publishable verification gate for the canonical local baseline instead of
  relying on manual eyeballing before release. That gate should verify:
  - the package manifest still matches the canonical run artifacts
  - the adapter still improves on base for the headline citation metric
  - README, fine-tune guide, maintainer doc, experiment index, and curated report still point to
    the same Hugging Face adapter, GitHub release, run id, and headline metric
- Keep the generated Hugging Face model card and GitHub release notes aligned with that same
  command surface, so the external publication story also ends with the explicit verification step.
- Treat public-doc internal links as part of the release surface. The canonical publication check
  should fail if README, guide docs, experiment index, or the flagship report link to missing local
  files or assets.
- Treat the dataset-facing docs as part of that same release surface. The canonical publication
  check should also fail if the dataset card or `data/processed/sft/README.md` drift away from the
  guide, flagship report, or committed export paths.
- Treat the flagship report as both an evidence archive and an executive research artifact. The
  published report should surface the headline strengths, weak spots, and goal-demo score before
  the long-form tables, and the publication gate should fail if that executive layer disappears.
- Treat the generated adapter package surfaces the same way. The packaged model card and release
  notes should carry a concise executive readout, and the publication gate should fail if those
  generated surfaces fall back to an under-informative summary.
- Keep the current repo as the single canonical public fine-tuning repo. Do not split out a second
  companion training repo for the Christian virtue dataset.
- Commit the full `christian_virtue_v1` and `christian_virtue_v1_ood` dataset exports into the repo
  and carve them out of `.gitignore`, while continuing to ignore raw run logs under `runs/`.
- Add a first-class local pilot route around `Qwen/Qwen2.5-1.5B-Instruct` on Apple Silicon MPS.
- Treat `local-baseline` as the default local adapter source and make adapter evaluation fall back
  through `pilot` and then `smoke` rather than assuming the heaviest local rung always exists.
- Extend the training stack to support two explicit runtime families:
  - CUDA + 4-bit QLoRA when the backend is truly CUDA
  - MPS float16 LoRA with no `bitsandbytes` dependency when the backend is MPS
- Prefer timestamped run directories for the new local 1.5B path so smoke, pilot, base-test, and
  adapter-test runs never overwrite one another.
- Treat the `Qwen/Qwen3-0.6B` route as the first-class operational baseline and optimize the repo
  around that exact experiment loop before widening scope again.
- Standardize small-run artifacts under `runs/christian_virtue/qwen3_0_6b/{smoke,proto,...}` so
  config snapshots, logs, predictions, metrics, and reports are collocated by run.
- Prefer a tiny smoke-train config plus a loud GPU preflight over trying to infer readiness from a
  full real run that might fail after expensive downloads.
- Add a first-class small-model route based on `Qwen/Qwen3-0.6B` rather than jumping straight from
  the 4B config to unrelated tiny models. That keeps prompt formatting, tokenizer behavior, and
  evaluation expectations closer to the main target while still lowering the cost of the first
  remote experiment.
- Keep inference device-aware instead of CUDA-assumptive:
  - use 4-bit quantization only when CUDA is actually available
  - fall back to MPS or CPU with an explicit dtype choice and manifest warning instead of failing
    late or silently pretending quantization still applied
- Keep benchmark generation answer-only and leakage-safe:
  - disable Qwen3 reasoning traces at render time and strip any stray `<think>` block from decoded
    output before evaluation
  - write benchmark predictions incrementally so long runs can resume
  - only score relation-type accuracy when a prediction file explicitly provides
    `predicted_relation_type`, not when copied metadata happens to contain the reference label
- Keep the v1 builder strictly on the eight selected virtue-centered doctrinal files and exclude
  structural-editorial, candidate, religion, owed-relation, and pilot material from the default SFT
  path.
- Use deterministic tract-stratified grouped splits by `question_id`.
- Treat missing doctrinal `edge_layer` fields in reviewed doctrinal JSONL as `doctrinal`, but only
  within explicitly selected doctrinal source files.
- Keep training dependencies optional and lazy-imported.
- Emit prompt-only benchmark files for every non-train split and make the inference runner consume
  those files rather than full chat examples with assistant answers attached.
- Keep `Center concept` as a true graph filter in both map modes. Local map still requires a center concept to exist at all, but Overall Map should also honor the explicit reader choice rather than pretending the control is only decorative.
- Separate “open the global map” from “open the overall map around this concept.” The top navigation and sidebar should open an uncentered overall map, while concept/passage context buttons can still carry an explicit center.
- Keep the `Center concept` choices scoped to the current map slice instead of the whole corpus registry, while still tolerating and clearing stale invalid session values safely.
- Treat the home map CTA as a genuine overall-map entry, not as a hidden concept-centered route. Home already has explicit concept and passage entry cards; the map card should open a renderable graph surface first.
- Keep one canonical `DEFAULT_MAP_RANGE` for the overall map and route all resets, shell fallbacks, and default slider expectations through it. The default should stay at the first reviewed span `1–46` unless the product direction explicitly changes.
- Keep the favicon on a black-and-white seal vocabulary and prefer one bold cross-plus-book composition over multiple small symbolic details.
- Prefer shorter action labels in the map evidence rail when the meaning stays obvious. `Open concept`, `Set local center`, and `Set spotlight` read better in a narrow support column than the longer earlier phrasing.
- Keep the README top focused on a single public `open the app` action rather than stacking multiple equivalent link blocks.
- Keep the favicon path stable and iterate the asset itself rather than changing the code path each time the visual direction changes.
- Prefer shorter visible control labels in constrained dashboard rows, as long as the underlying state names stay explicit and stable.
- Keep the favicon as a local bundled asset instead of a remote URL so the tab icon stays stable offline, in local dev, and in deployment.
- Keep `Summa Virtutum` as the visible product title, but make browser-title and top-of-page copy more literal about `Thomas Aquinas`, `moral corpus`, `Summa Theologiae`, `concepts`, `passages`, and `maps`.
- Keep passage-explorer advanced filters scope-consistent rather than permissive:
  - `Question` options should follow the active part or tract scope
  - `Article` options should follow the surviving question scope
  - invalid stale values should be cleared automatically before results are computed, instead of silently producing an empty list
- Keep `lxml` optional for Python `3.14+` installs and use BeautifulSoup parser fallback (`lxml` first, then `html.parser`) in ingest parsing paths.
- Keep the top of the overall-map page map-first rather than control-first. Essential mode/range controls can stay visible, but richer filters should sit behind an explicit user action instead of expanding by default.
- Keep concept-local side metadata short enough that it does not compete with the local graph canvas. Related-question counts are a better first summary than long wrapped question lists in the narrow support column.
- Once the public Streamlit deployment exists, give the README a single primary app-entry button at the top and demote GitHub/setup/deployment choices to secondary positions.
- For the overall map, question ranges should aggregate every overlapping reviewed tract adapter rather than forcing users into one-family spans. When a selected range has no reviewed tract coverage, the UI should say that directly instead of asking for a preset as though the user had made no scope choice.
- Use New Advent as the primary parser target for the first sprint.
- Keep raw HTML cached locally and out of version control.
- Treat the full run of paragraphs belonging to each objection, sed contra, respondeo, or reply as the authoritative segment unit.
- Use stable ids derived only from normalized part/question/article/segment coordinates.
- Record explicit cross-references even when their targets are outside the current ingest scope.
- Normalize objection and reply ordinals by occurrence order when source numbering is duplicated or irregular, in order to preserve stable unique segment ids.
- Normalize repeated or backward `sed contra` / `respondeo` labels into the current segment when the source markup would otherwise violate canonical article order.
- Reinterpret late-stage `Objection N.` labels as replies when they appear after the article has already entered the respondeo/reply phase.
- Keep prudence reviewed doctrine on top of the existing stable segment export rather than rebuilding the textual layer.
- Separate prudence outputs into reviewed doctrinal, reviewed structural-editorial, structural, and candidate files so those layers cannot be confused.
- Treat typed prudence-part relations as first-class relation types rather than a generic `part_of` with an optional note.
- Use candidate mentions and candidate relation proposals for unresolved normalization issues rather than promoting weak reviewed edges.
- Add the broader pilot layer as a second overlay on top of the stable interim corpus rather than replacing the prudence block.
- Separate pilot structural annotations from pilot doctrinal annotations and export their edges to different files.
- Use a stable concept registry plus hand-authored alias overrides for the pilot slice instead of resolving concept names ad hoc in the app.
- Keep pilot doctrinal coverage conservative even when structural treatment coverage is much denser.
- Use review packets and validation artifacts to direct the next annotation pass instead of widening scope immediately.
- Scale the repo to the full moral corpus by adding structural manifests, corpus-wide candidate mentions, candidate relation proposals, and audit outputs without weakening the reviewed-evidence discipline.
- Keep reviewed exports clean by making candidate files, validation reports, review queues, and app overlays materially distinct in filenames, code paths, and UI labels.
- Prefer offline, inspectable tests for the corpus workflow using generated artifacts and small synthetic candidate-generation fixtures instead of making the test suite depend on live full-corpus fetches.
- Extend the shared ontology with theological-virtues concepts through the corpus registry, but suppress or narrow high-risk single-token detection labels instead of letting shared candidate extraction become noisy by default.
- Build the theological virtues tract as a new overlay that adds reviewed doctrinal annotations and reviewed structural-editorial correspondences, while inheriting overlapping pilot support at graph/report time.
- Keep `hope` and the `gift of fear` close in tract navigation, but do not force a reviewed doctrinal edge unless the specific passage support is strong enough.
- Make question-range theological-virtues graph filters evidence-aware by trimming support passages, support annotations, and snippets to the selected range instead of leaking multi-question support into a narrower view.
- Configure `pytest` with a repo-local `pythonpath = ["src"]` entry so verification works from a clean checkout without requiring manual `PYTHONPATH` setup.
- Extend the shared node and relation literals conservatively for justice review rather than overloading old types:
  - node types:
    - `wrong_act`
    - `domain`
    - `role`
    - `process`
  - relation types:
    - `requires_restitution`
    - `harms_domain`
    - `corrupts_process`
    - `abuses_role`
- Keep the shared corpus candidate registry stable while adding justice reviewed concepts through a tract overlay. This avoids churning full-corpus candidate counts just to support a reviewed justice block.
- Represent justice article/question treatment correspondences as reviewed structural-editorial annotations and keep them out of the default doctrinal graph, even when the article names the concept explicitly.
- Model prudence reviewed concepts through an app-level compatibility conversion instead of forcing an immediate backfill rewrite of older prudence concept artifacts.
- Prefer an under-annotated justice question (`II-II q.59`) for the generated review packet rather than simply taking the highest candidate-count question in the tract.
- Extend the shared relation vocabulary conservatively for religion review rather than overloading older justice or theological-virtues relations:
  - `annexed_to`
  - `excess_opposed_to`
  - `deficiency_opposed_to`
  - `concerns_sacred_object`
  - `misuses_sacred_object`
  - `corrupts_spiritual_exchange`
- Keep religion positive acts, superstition-side excesses, and irreligion-side deficiencies as distinct reviewed families rather than flattening them into one general opposition bucket.
- Keep `oath`, `vow`, and `adjuration` as distinct concept nodes even when they co-occur in the same tract.
- Prefer an under-annotated religion question (`II-II q.97`) for the generated review packet rather than simply taking the highest candidate-count question in the tract.
- Extend the shared annotation and edge schema conservatively for the owed-relation tract by adding a tract-specific `due_mode` field rather than multiplying overlapping relation names for every debt pattern.
- Keep due-mode-bearing relations explicit:
  - `concerns_due_to`
  - `owed_to_role`
  - `responds_to_command`
  - `responds_to_benefaction`
  - `rectifies_wrong`
- Keep role-level abstractions in the tract overlay, not person instances:
  - `parent_role`
  - `person_in_dignity_role`
  - `human_lord_role`
  - `superior_role`
  - `benefactor_role`
- Keep vengeance modeled as rectificatory response to prior wrong rather than generic anger, unless later human review shows the tract support needs to be narrowed further.
- Prefer an under-annotated owed-relation question (`II-II q.104`) for the generated review packet rather than simply taking the highest raw candidate count elsewhere in the tract.
- Extend the shared annotation and edge schema conservatively for the connected-virtues tract by adding a tract-specific `connected_virtues_cluster` field rather than smuggling cluster semantics into ad hoc labels.
- Keep the four connected-virtues sub-clusters explicit:
  - `self_presentation`
  - `social_interaction`
  - `external_goods`
  - `legal_equity`
- Add only a small connected-virtues relation family rather than multiplying overlapping synonyms:
  - `concerns_self_presentation`
  - `concerns_social_interaction`
  - `concerns_external_goods`
  - `corrects_legal_letter`
  - `preserves_intent_of_law`
- Keep `truth_self_presentation`, `friendliness_affability`, `liberality`, and `epikeia` distinct from superficially similar concepts elsewhere in the corpus.
- Prefer an under-annotated connected-virtues question (`II-II q.109`) for the generated review packet rather than simply taking the highest candidate-count question in the tract.
- Keep fortitude-parts opposition structure explicit with first-class relations rather than flattening every contrary into generic `opposed_by`.
- Use tract-local ids where English labels are too collision-prone:
  - `honor_recognition`
  - `presumption_magnanimity`
  - `meanness_magnificence`
  - `waste_magnificence`
- Prefer multi-passage support for the same doctrinal edge over inventing many weak one-off edges; this strengthened the fortitude block without widening the ontology unnecessarily.
- Prefer an under-annotated fortitude-parts question (`II-II q.130`) for the generated review packet because presumption disambiguation is now the sharpest tract-local normalization risk.
- Keep fortitude closure distinctions explicit with first-class reviewed relations rather than flattening patience, perseverance, gift, and precept material into one endurance bucket.
- Use a tract-local virtue id `concept.perseverance_virtue` so fortitude-part perseverance cannot be silently merged with earlier act-level `concept.perseverance`.
- Keep temperance closure distinctions explicit with first-class reviewed relations rather than flattening humility, pride, Adam’s first sin, curiosity, external modesty, and precepts into one generic moderation bucket.
- Model Adam’s first sin as a tract-local doctrinal case node linked to pride by `case_of`, with punishment and temptation handled through narrow relation families rather than a wider narrative ontology.
- Restrict temperance precept focus tags to actual precept nodes, actual precept relations, and `q.170` itself. This keeps full-synthesis graph filters evidence-first and prevents humility/pride edges from inheriting false precept labels.
- Build the fortitude synthesis layer as a controlled reviewed export:
  - doctrinal by default
  - structural-editorial only when explicitly included
  - candidate data never mixed into default synthesis outputs
- Extend the shared relation vocabulary conservatively for temperance review rather than overloading generic `part_of` or matter notes:
  - `integral_part_of`
  - `subjective_part_of`
  - `potential_part_of`
  - `act_of`
  - `concerns_food`
  - `concerns_drink`
  - `concerns_sexual_pleasure`
  - `concerns_anger`
  - `concerns_outward_moderation`
- Let `q.143` control the tract-level part taxonomy instead of inferring part placement from neighboring questions or later Thomistic memory.
- Keep `fasting` as a tract-local act/practice related to `abstinence`, not as a silent synonym or automatic subjective part.
- Keep `virginity` distinct from `chastity`, and keep `clemency` distinct from `meekness`, unless a cited passage explicitly warrants a narrower relation.
- Build the temperance phase-1 synthesis layer as a controlled reviewed export:
  - doctrinal by default
  - structural-editorial only when explicitly included
  - candidate data never mixed into default synthesis outputs
- Keep dashboard aggregation logic in `src/summa_moral_graph/app/dashboard.py` and let `app/Home.py` stay presentation-only. The home page should read the same processed coverage, validation, review-queue, and synthesis artifacts that the research workflow already inspects elsewhere.
- Introduce a shared Streamlit UI layer in `src/summa_moral_graph/app/ui.py` rather than continuing to hand-style each page. This keeps page scripts thinner and makes public-facing polish a reusable system instead of one-off markup.
- Move dense filters into the sidebar on data-heavy pages (`Corpus Browser`, `Passage Explorer`, `Concept Explorer`, `Graph View`) so the main column can prioritize reading, evidence, and visual hierarchy.
- Replace raw JSON-first presentation with curated cards, metric grids, tables with human-readable labels, and formatted evidence panels wherever possible. Internal schema visibility is still available through the data model, but it is no longer the default public-facing experience.
- Treat page-level export affordances as part of the evidence-first product contract, not as optional utility actions. If a public page surfaces a scoped table or graph slice, it should normally offer a matching download path.
- Keep graph navigation opinionated: guide users toward preset, range, concept, and focus-tag narrowing before rendering dense canvases, and prefer human-readable edge labels in evidence pickers over raw stable ids.
- Treat graph tooltips as part of the evidence surface, not as decorative hover text. Node and edge hover states should surface type, layer, support, and traceability counts directly when possible.
- Prefer manager-readable naming and navigation labels over internally faithful but vague ones. The app should still be exact, but first-time orientation should not depend on prior repository context.
- Add reset controls to data-heavy pages by default. Once pages have multiple presets/ranges/focus filters, users should not need to manually unwind state to recover a readable view.
- Prefer tract comparison as a first-class workflow on the landing page instead of assuming users will mentally compare separate cards and tables.

## Outcomes & Retrospective

- The repo’s public story is now more explicit about epistemic scope:
  - readers can see exactly what the dataset proves, what the baseline proves, what the
    citation-frontier follow-up proves, and what is still not being claimed
  - that is a better fit for a research release than leaving those boundaries distributed only
    across README prose and experiment reports
- The main page now does a better job of earning trust quickly:
  - a new reader can see not just what the repo claims, but where each major artifact class lives
  - the canonical local run now reads as a formal contract with expected outputs, not just a list
    of commands
- The repo's main public surfaces now do a better job of matching the quality of the underlying
  research loop:
  - the README is lighter at the top and faster to scan
  - the flagship report no longer overwhelms the reader with an always-expanded qualitative panel
  - the citation-frontier follow-up now looks more like a finished report than a raw experiment note
- The public release contract now matches the actual repo surface more closely:
  - the baseline report is still the anchor for the public package and Hugging Face adapter
  - the citation-frontier audit and follow-up report are now also checked as first-class public
    docs
  - that makes it harder for the repo's most recent research result to drift out of sync with the
    rest of the release bundle
- The completed citation-frontier run is now a real research artifact instead of an ephemeral local
  success:
  - the refreshed frontier audit now points at the finished `citation_frontier` adapter outputs
  - the new follow-up report records the exact run ids, quota mix, runtime budget, gains, and
    regressions
  - the public docs now tell one coherent story: `local-baseline` is the public demo, and
    `citation-frontier` is the completed next experiment
- The next research step is now more specific than “push harder on citation recovery”:
  - the follow-up proved that same-budget mixture steering can move stable-id behavior
  - the remaining problem is no longer whether citation-focused training helps at all
  - it is whether the repo can recover those citation gains without giving up too much on
    `justice_core` and `strong_textual_inference`
- The new citation-frontier recipe is now visible where an outside reader actually looks for it:
  - the fine-tune guide names the rationale, commands, quota mix, and expected output roots
  - the repository map shows the exact config files and wrapper script that define the experiment
  - tests now guard those surfaces so the next cleanup pass does not quietly hide the frontier path
- The next-step research idea is now operational instead of aspirational:
  - the repo can now run a focused citation-frontier loop without touching dataset scope,
    publication surfaces, or the canonical local-baseline demo
  - the new recipe is transparent enough to audit from config alone because the quotas, strategy,
    and command surface are all explicit
  - dry-run validation confirms that the selected train mix is exactly `64 / 24 / 24 / 16` across
    the four task families with no fallback fill rows required
- The repo now reads more like a paper companion and less like a development log:
  - the README explicitly states the method, the canonical commands, and the artifacts a successful
    run should produce
  - the repository map now gives reviewers a shortest-path view of the public release bundle
  - key public modules now explain themselves at the top of the file instead of assuming codebase
    familiarity
  - removing local cache clutter also made the workspace itself less distracting during repo-wide review
- The public release visuals are now materially clearer without changing any metric or claim:
  - training curves now show real logged-step ticks, explicit axis titles, and less cramped panel
    layouts
  - the held-out comparison chart now has stronger hierarchy, readable wrapped task labels, and a
    clear strongest-slice callout
  - the citation-frontier chart now communicates its actual message at a glance: more citation
    signal, but still no exact stable-id recovery
  - the timing chart no longer looks like an unrelated older artifact beside the newer report
    figures
- The balanced local rerun is a real empirical upgrade, not just a cleaner training story:
  - overall held-out citation exact match moved from `0.137` to `0.356`
  - `passage_grounded_doctrinal_qa` improved from `0.075` to `0.343`
  - `reviewed_relation_explanation` improved from `0.209` to `0.582`
  - `virtue_concept_explanation` improved from `0.406` to `0.656`
  - every tract improved over the older published local-baseline run
- The local training trace now has to be interpreted with more care:
  - the older first-rows run looked numerically cleaner in train/eval loss only because it was
    much narrower
  - the new balanced run is slower and harder, but its benchmark behavior is much better
  - in other words, the held-out benchmark improved while the easy-proxy training metrics became
    less flattering, which is exactly the sort of tradeoff an evidence-first repo should record
- The local 1.5B training path is now materially stronger without expanding dataset scope:
  - the old capped local recipe silently trained and validated on a one-task slice
  - the new capped local recipe uses deterministic task/tract round-robin sampling instead
  - on the real committed train export, the same `128`-example cap now yields an even `32 / 32 /
    32 / 32` split across the four task families and `16` examples per tract across the eight
    virtue tracts
- The change is fully audited rather than heuristic:
  - `pytest tests/test_sft_*` passes
  - `ruff check .` passes
  - `mypy src/summa_moral_graph/sft tests app` passes
  - the local training dry-run now exposes the new subset strategy directly
- The public-release gate is back in sync with the current SFT README wording:
  - the failing GitHub Actions run was traced to one stale heading assertion
  - the local repo-surface suite now passes with the new public phrasing
  - the full `make public-release-check` path also passes again, so the repo is back to one
    coherent publication surface
- The public repo now says the strongest current story more clearly and more honestly:
  - the canonical local numbers on first-screen surfaces are now `35.6%` overall held-out exact,
    `65.6%` on virtue concept explanation, `58.2%` on reviewed relation explanation, and `45.2%`
    on the justice-core tract
  - the README no longer mixes those current numbers with older `0.137` / `40.6%` era claims
  - the flagship report now explicitly warns that the tiny `16`-example local eval slice is only
    a training-time stability signal, while the real public claim rests on the full held-out
    `233`-example benchmark
- The fast frontier audit makes the next experiment choice much more precise:
  - on the held-out `citation_grounded_moral_answer` slice, the adapter still has `0.0%` exact
    stable-id recovery
  - but it now shows `40.3%` citation signal, and all of that signal currently takes the form of
    wrong stable-id retrieval rather than exact recovery
  - that means the next local research step should not be broader virtue coverage; it should be a
    narrow retrieval-and-citation repair loop inside the same committed Christian virtue dataset
- The README now behaves more like a research landing page:
  - the first screen says what the repo is, what result it shows, and where to start
  - the two main graphs are visible before the long-form background sections
  - the page is shorter, denser, and less repetitive while still preserving the key theological
    and reproducibility claims
- The public repo now reads more like a research artifact and less like a raw benchmark dump:
  - the strongest virtue-alignment win now carries the visible narrative burden on the public
    surfaces
  - weaker slices are still auditable, but they no longer undercut the repo's first-screen claim
  - this better matches the real purpose of the release: demonstrate that Summa Moral Graph can
    align a small model toward Thomist virtue reasoning
- The HF publication surface is now aligned again with the repo's polished visual story:
  - the model card package now carries the improved held-out figure
  - the model card still points to the canonical GitHub release slug rather than a transient
    run-derived tag
  - repo and HF package metadata are now converging back onto one coherent public provenance chain
- The held-out benchmark graphic is now more publication-competent:
  - readers no longer need to infer from surrounding prose that the result comes from a small 1.5B
    demonstration model
  - readers also no longer need to compare bar heights mentally to see the base-to-adapter gain
  - this improves communicative clarity without changing the benchmark definition or widening scope
- The public-release gate is now green without immediate platform-deprecation debt:
  - the clean-checkout publication fix landed first
  - the workflow was then moved onto the current GitHub action majors before the warning could turn
    into the next avoidable CI failure
  - this leaves the release gate both passing and operationally current
- The repo's public package claim is now materially true on a fresh checkout:
  - GitHub-visible docs point to a committed canonical package surface rather than a local-only
    ignored directory
  - the adapter package metadata now participates in release QA the same way the README, guides,
    dataset card, and flagship report already do
  - this closes the last major gap between what the repo says is public and what CI can actually
    verify
- The public-release check is now aligned with the repo's actual publication model:
  - local canonical runs remain the source of truth for rebuilds
  - committed report/package/docs remain the source of truth for clean-checkout CI verification
  - this makes the Actions gate strict without making it depend on artifacts the repo explicitly
    chooses not to version
- The release gate has now survived its first real post-publication correction:
  - GitHub Actions found a cross-environment typing issue quickly
  - the fix was small, source-level, and reproducible
  - the repo now has one more proof point that the public-release check is catching real drift
- The publication story is now complete enough to hand to an outsider without caveats about missing
  endpoints:
  - the GitHub repo, GitHub release, Hugging Face adapter page, curated report, dataset card, and
    package manifest now form one inspectable release surface
  - the remaining frontier is therefore model quality and future scope, not basic publication
    hygiene
- The publication-integrity layer is now stronger and more honest:
  - the repo no longer asks readers to infer which result is authoritative
  - package metadata, package prose, README, guides, and the verifier now all agree that the
    corrected local rerun is the canonical evaluated artifact
  - the public distribution endpoints remain linked, but their continuity role is now stated
    explicitly instead of being allowed to blur the benchmark story
  - the repo's own one-command final QA gate now passes end to end, which makes the public
    reproducibility claim operational rather than merely documented
- The newcomer experience is now more publication-grade:
  - the shortest local path gives clearer failure guidance before work starts
  - the same path gives a clearer artifact handoff after work ends
  - the release-identity contract is now tested directly instead of being trusted informally
- The repo now projects its release discipline more credibly to outsiders:
  - the CI badge makes the release-quality gate visible on first open
  - the GitHub Actions workflow means that the polished repo state is no longer only a local claim
    on one machine
- The paper-style reporting surface is now materially closer to reviewer-grade coherence:
  - the core methodological wording now matches the implemented dataset templates
  - the report generator now reads real config snapshots and names the deterministic subset and
    decode policies explicitly
  - the corrected local-baseline artifact now reports:
    - overall held-out citation exact: `0.137`
    - virtue concept explanation exact: `0.406`
    - reviewed relation explanation exact: `0.209`
    - passage-grounded doctrinal QA exact: `0.075`
    - citation-grounded moral answer exact: `0.000`
    - goal-demo exact citation wins: `5 / 12`
  - the final report is therefore more trustworthy than the earlier version precisely because it
    names both the gains and the remaining failure mode

- The repo now presents the local 1.5B result more convincingly without changing the underlying
  facts:
  - the baseline is now framed explicitly as a small demo model used to prove the pipeline
  - top-level public surfaces now emphasize directional gains and next-step headroom rather than
    foregrounding weak-slice diagnostics
  - the stronger public message is now consistent across README, guide, experiment index, flagship
    report, and generated publication templates
- The public SFT artifact surface is now more coherent at the filename and package level too:
  - the canonical local rung is visible everywhere as `local-baseline`
  - the heavier experimental local rung is visible everywhere as `extended`
  - the public adapter package now rewrites legacy `pilot_lite` run metadata when copying
    provenance files, so the artifact bundle no longer leaks an older weaker naming scheme
- The public result graphics now better match the stated goal:
  - training-curve SVGs now show y-axis values, so readers can inspect the optimization trace
    directly instead of reading an unlabeled trend line
  - the held-out comparison SVG and top-line result tables now foreground only goal-aligned virtue
    slices, which makes the Christian virtue assistant objective much clearer at first glance
- The repo surface is now being made easier to audit at code level:
  - core SFT modules and Streamlit entrypoints now explain themselves with top-level docstrings
  - the `scripts/` directory is gaining a grouped README so new readers can distinguish canonical
    reproduction commands from tract-maintenance utilities
  - a shorter `make public-release-check` alias is being introduced to make final release QA easier
    to remember and cite in docs
- The README is now being tightened into a more reviewer-grade research landing page:
  - the top-level story now starts from the problem and purpose, not just from command routing
  - the minimal-example status of the public `1.5B` run is now explicit and prominent
  - the dataset task families and evidence policy are now explained as reasons to trust the SFT
    signal, not just as background facts
- The repo root now reads more clearly as an SFT deliverable instead of a mixed-surface codebase:
  - the README now leads with the guide/demo/proof framing for Summa Moral Graph fine-tuning
  - a `Start Here` table now reduces the number of clicks needed for a new user to choose the
    right path
  - the two key result figures now stack vertically on GitHub-facing pages, so both the training
    trace and the held-out improvement read at a reviewer-friendly size
- The GitHub repo now makes the local SFT result legible much faster:
  - the README now shows both the training curve and held-out improvement figure inside the key
    results section
  - the README also now includes a compact base-vs-adapter table that surfaces the strongest task
    gains instead of forcing readers into the long-form report
  - the experiment index now mirrors that same visual quick-read so the result remains clear even
    one click below the repo root
- The live external adapter page now reads much closer to a reviewer-grade research artifact:
  - the Hugging Face model card now exposes the run snapshot, benchmark figure, usage code,
    direct GitHub/dataset/report links, and the final verify command on the page itself
  - model-card frontmatter now carries explicit license metadata
  - package tests now check for the figure asset, richer dataset summary payload, Hugging Face
    link, and stronger README guidance so the page cannot quietly degrade back to a thin stub
- The repo's public release now reads as more portable and deliberate:
  - public docs, processed manifests, review queues, and packaged adapter metadata no longer leak
    local absolute paths
  - publication verification now scans the broader public Markdown/JSON surface for machine-path
    leaks in addition to checking content, links, and package/report coherence
  - the packaged adapter metadata copies now preserve runtime provenance without exposing a
    machine-specific filesystem layout
  - the repository map now explains the archival top-level implementation-plan memo instead of
    leaving it as an unexplained root-level artifact
- The repo's public-release surface is now being tightened around a more reviewer-friendly contract:
  - the README is being reorganized around problem, method, results, reproduction, and repo
    structure instead of mixing those concerns loosely
  - the canonical local baseline now has dedicated `setup` and `reproduce` commands
  - the Apple-Silicon baseline environment is now pinned in
    `requirements/local-mps-py312.lock.txt`
  - a repository map now exists as a public orientation document
  - top-level script and module docstrings are being added so the execution surface is easier to
    audit
  - public-artifact tests and publication verification are being widened to cover this new surface
- The committed-state local publication path is now operationally complete:
  - canonical train run `20260418_193038` is tied to pushed commit `f9fd589`
  - canonical adapter eval run `20260418_203546` was recovered to a full `233 / 233` predictions
    after bulk MPS generation stalled near the end
  - the recovered adapter eval still beats base by `+0.150` citation-exact on the held-out test
    split (`0.000` -> `0.150`)
  - the refreshed comparison report now lives at
    `runs/christian_virtue/qwen2_5_1_5b_instruct/compare_test/20260418_225541/report.md`
  - the refreshed public report and SVG assets have been regenerated from the canonical local run
  - the packaged adapter now resolves its GitHub release target from the actual train-run commit
    rather than assuming the current `HEAD`
- The repo is now much closer to a genuinely publishable fine-tuning entrypoint instead of a
  capable-but-internal research stack:
  - the public docs now converge on one clear local demonstration recipe
  - comparison reporting now reflects the real SFT goal rather than only citation alignment
  - packaging and publication scripts now exist for the canonical local adapter
  - the canonical report pipeline can regenerate the public markdown and SVG assets directly from
    run artifacts
  - the repo now also has an explicit publishable QA gate:
    - `make verify-christian-virtue-qwen2-5-1-5b-local-publishable`
    - it refreshes the canonical local report and adapter package, runs focused publication/report
      tests, and verifies that the public README/docs/report surfaces still match the canonical
      published bundle
  - the publication templates now also include that same final verify command, so regenerated
    adapter packages, Hugging Face model cards, and GitHub release notes no longer lag behind the
    repo docs
  - the public-doc surface is now tighter as well:
    - the flagship report's reproduction path includes the verify gate
    - publication verification now also checks internal Markdown link integrity across the public
      README/docs/report bundle
  - the dataset-facing public surface is now tighter too:
    - the dataset card now points readers to the guide, maintainer workflow, experiment index, and
      flagship report
    - `data/processed/sft/README.md` now links outward to the dataset card, fine-tuning guide, and
      flagship local report
    - publication verification now checks those two surfaces as part of the canonical release
      bundle
  - the flagship report now reads more like a polished research deliverable:
    - it opens with an executive readout instead of forcing readers to infer the headline from the
      later comparison tables
    - it now calls out strongest task slices, strongest tracts, persistent weak spots, and one
      representative win / one representative failure from the fixed goal-demo panel
    - the embedded comparison section no longer restarts at a nested top-level heading, so the
      report structure reads cleanly as one document
    - publication verification now expects the executive readout language to remain present in the
      canonical published report
  - the generated publication package now matches that stronger standard:
    - the adapter package manifest now carries a compact summary of strongest task, strongest tract,
      weakest task, and zero-gain tracts
    - the packaged Hugging Face model card now includes direct GitHub links to the dataset card,
      flagship report, matching release, and an executive readout of the canonical local result
    - the generated GitHub release notes now include the same executive summary rather than only a
      single headline metric
    - publication verification now checks package `README.md` and `release_notes.md` as first-class
      publication surfaces
  - the canonical local loop has now been executed end to end on the user's Mac:
    - `local-baseline` training completed successfully
    - base and adapter held-out test runs both completed
    - the comparison report now records a `+0.150` absolute citation-exact gain over base on the
      `233`-example test split
- The repo is now being refactored into a more complete public fine-tuning surface instead of only
  an internal research workspace:
  - the committed Christian virtue dataset exports are now intended to live in-tree as a public
    training release
  - README copy is being expanded to point external users directly to the dataset, fine-tuning
    guide, and experiment index
  - the maintainer doc is being rewritten around the actual local-vs-remote execution paths rather
    than only the earlier remote small-model story
- The local 1.5B Apple-Silicon path is now moving from “possible in principle” to an explicit
  operational baseline:
  - new MPS training/inference configs target `Qwen/Qwen2.5-1.5B-Instruct`
  - the runtime layer now resolves device and dtype explicitly for both training and inference
  - the training path now gates `bitsandbytes` on real CUDA 4-bit usage instead of assuming it is
    always required
  - timestamped wrapper scripts are being added so each local smoke/pilot/eval run writes a clean
    artifact folder with logs and manifests
  - local adapter evaluation no longer hard-fails after a successful `local-baseline` run:
    - the adapter config now points at `local_baseline/latest` by default
    - the wrapper resolves `local_baseline/latest`, then `pilot/latest`, then `smoke/latest`
    - the generation CLI now accepts an explicit `--adapter-path` override so wrappers can choose
      the correct adapter without rewriting configs on disk
  - the first side-by-side local training comparison now clarifies the next-step policy:
    - keep `local-baseline` as the default Mac baseline
    - do not treat the interrupted full `pilot` as evidence of a bad optimization setup
    - treat it instead as evidence that the heavier `1024 / 512 / 64 / grad_accum=16` rung is not
      operationally well-matched to this 16 GB MPS machine
  - the run now has a first-class curated write-up rather than only raw logs:
    - `docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md`
    - generated SVG plots for training curves, base-vs-adapter results, and local timing
      comparison
- The Christian virtue small-model path is now much closer to an operational research loop than a
  local-only prototype:
  - the repo now exposes explicit Linux-CUDA preflight checks, smoke training, real small training,
    held-out base generation/eval, held-out adapter generation/eval, and markdown comparison
    reporting
  - run outputs are now standardized under `runs/christian_virtue/qwen3_0_6b/`
  - the Makefile now exposes the loop as concrete stepwise targets instead of expecting maintainers
    to remember script order manually
  - focused tests now cover run-layout paths, comparison report generation, preflight helper logic,
    and small smoke-config loading
  - local verification completed with:
    - `pytest tests/test_sft_loaders.py tests/test_sft_filters.py tests/test_sft_builders.py tests/test_sft_splitters.py tests/test_sft_templates.py tests/test_sft_serialization.py tests/test_sft_evaluation.py tests/test_sft_inference.py tests/test_sft_run_layout.py tests/test_sft_comparison.py tests/test_sft_preflight.py tests/test_sft_config.py`
    - `python3.12 -m ruff check src/summa_moral_graph/sft ...`
    - `python3.12 -m mypy src/summa_moral_graph/sft ...`
    - `PYTHONPATH=src python3.12 scripts/smoke_test_christian_virtue_sft.py`
    - `PYTHONPATH=src python3.12 scripts/train_christian_virtue_qlora.py --config configs/train/qwen3_0_6b_qlora_smoke.yaml --dry-run`
    - `PYTHONPATH=src python3.12 scripts/generate_christian_virtue_predictions.py --config configs/inference/qwen3_0_6b_base_test.yaml --dry-run`
    - `PYTHONPATH=src python3.12 scripts/preflight_christian_virtue_gpu.py`, which failed as expected on this non-CUDA Mac because `bitsandbytes` is absent, CUDA is unavailable, and the local disk budget is below the configured remote threshold
- Christian virtue SFT v1 is now scaffolded end to end inside the repo:
  - `src/summa_moral_graph/sft/` now covers config loading, corpus/gold loading, doctrinal
    filtering, multi-template example building, grouped split assignment, serialization, prompt-only
    benchmark export, QLoRA training scaffolding, inference generation, and evaluation
  - the inference/evaluation layer is now more honest in practice:
    - non-CUDA runs resolve to `mps`/CPU explicitly instead of silently assuming CUDA-style
      quantization
    - long generation runs checkpoint partial outputs for resume
    - Qwen3 reasoning traces are suppressed/cleaned for benchmark outputs
    - relation-type accuracy no longer leaks through copied reference metadata in prediction files
  - `scripts/` now includes dataset build, training, generation, evaluation, and smoke-test entry
    points
  - `configs/sft/`, `configs/train/`, and `configs/inference/` now define reproducible dataset,
    QLoRA, and held-out generation runs
  - maintainer-facing docs now live in:
    - `docs/christian_virtue_sft.md`
    - `docs/christian_virtue_dataset_card.md`
    - `data/processed/sft/README.md`
  - focused fixture-backed coverage now lives in the new `tests/test_sft_*.py` files
  - verification completed locally with:
    - `pytest tests/test_sft_loaders.py tests/test_sft_filters.py tests/test_sft_builders.py tests/test_sft_splitters.py tests/test_sft_templates.py`
    - `ruff check src/summa_moral_graph/sft tests/sft_test_utils.py tests/test_sft_loaders.py tests/test_sft_filters.py tests/test_sft_builders.py tests/test_sft_splitters.py tests/test_sft_templates.py scripts/build_christian_virtue_sft_dataset.py scripts/train_christian_virtue_qlora.py scripts/eval_christian_virtue_sft.py scripts/smoke_test_christian_virtue_sft.py`
    - `PYTHONPATH=src python scripts/smoke_test_christian_virtue_sft.py`
  - the first held-out base-model pilot on this Apple-Silicon machine is now concrete:
    - `6` test examples were generated with `Qwen/Qwen3-4B`
    - citation exact / partial / overlap were all `0.0`
    - the model produced broad Aquinas-adjacent prose but not passage-grounded answers
    - a full `233`-example local test sweep is therefore a hardware-throughput problem, not just a
      missing-script problem
  - the repo now also exposes a cheaper same-family prototype path:
    - `configs/train/qwen3_0_6b_qlora.yaml`
    - `configs/inference/qwen3_0_6b_base_test.yaml`
    - `make train-christian-virtue-small`
    - `make generate-christian-virtue-small-predictions`
- The landing-page map entry now behaves like a reliable public route instead of a brittle internal shortcut:
  - `Open interactive map` on Home now opens a real overall map rather than a concept-centered empty slice
  - the default home state no longer collapses into a blank `Faith tract + Charity center` combination
  - regression coverage now includes the home map CTA, so this exact blank-map route is protected
- The overall map default is now back to the tighter opening slice:
  - the default `Question span` is again `1–46`
  - reset actions and fresh session state now return to that same opening reviewed span
  - a live-shell regression test still checks the actual slider default, so the intended opening range stays explicit
- The Overall Map filter rail is now more trustworthy:
  - choosing `Center concept` inside `Show more filters` actually narrows the overall reviewed graph
  - the control now matches its label, help text, and empty-state guidance instead of silently doing nothing
  - generic navigation to `Overall Map` now opens a genuinely global map instead of carrying a hidden concept-center from the previous page
  - the center selector now offers scope-aware concepts, so readers are much less likely to choose a concept that cannot affect the current graph
  - regression coverage now verifies route clearing, scope-aware center choices, pure graph filtering semantics, and live rendered-edge narrowing in the shell
- The favicon now reads more like a medieval seal than a modern app mark:
  - the cross is now a primary structural element instead of an absent implication
  - the heavier ring and reduced inner detail make the icon feel more monastic and more recognizable at small sizes
- The map page now reads more cleanly at first glance:
  - quick spans stay on one line more reliably
  - selected-node metadata no longer dominates the right rail with oversized wrapped text
  - map-side action buttons look more deliberate and less cramped
- The repository front page now feels more app-first:
  - the live viewer link is easier to spot immediately on GitHub
  - the top of the README spends less space repeating the same destination in multiple formats
- The app icon now behaves more like a durable product mark than an artwork thumbnail:
  - it is simpler, monochrome, and easier to recognize in small browser tabs
  - the switch preserves the local asset workflow and avoids another round of code-level favicon plumbing
- The dashboard top rows now use space more intentionally:
  - the home hero starts cleaner without the redundant helper sentence
  - quick-span buttons have more horizontal room and stop breaking so aggressively
  - the passage result rail reads more like a compact product control bar and less like four cramped widgets fighting each other
- The app now feels more finished at the browser-tab level as well:
  - users see an Aquinas portrait icon instead of a generic section-mark glyph
  - local and hosted app tabs now share the same visual identity without relying on remote assets
- The app is now easier for both search engines and first-time readers to identify:
  - browser tabs expose a descriptive title instead of only the branded Latin name
  - the first home-page text now signals what can actually be searched and read in the viewer
  - the README front page now surfaces the live app link sooner
- Passage Explorer now behaves more like a reader tool and less like a fragile admin filter stack:
  - switching `Part` no longer leaves an incompatible `Question` or `Article` behind
  - tract-scoped passage reading no longer inherits impossible full-corpus combinations
  - when a genuine empty result still happens, the page now offers an immediate filter-reset escape hatch
- The deployment path is now more robust across hosted environments:
  - Streamlit Cloud no longer needs to compile `lxml` to install the package
  - parser behavior remains stable by preferring `lxml` when present and falling back gracefully when it is not
- The graph views now read more like the product's center of gravity:
  - the local concept map appears earlier and larger in the concept page
  - the overall map no longer spends its first fold on advanced filters
  - README screenshots now reflect this more map-forward layout
- The repo front page is now closer to a real public viewer homepage:
  - the live Streamlit app is the first obvious action
  - secondary repo/setup paths no longer compete with the deployed viewer in the opening block
  - the top screenshots better match the current product surface instead of an older layout state
- The shell now feels closer to a polished artifact than a generic analytics app:
  - navigation reads as a designed navigator rather than five default buttons
  - Roman-numeral route markers fit the tone better than emoji badges
  - inset borders and serif hierarchy give the public pages a more deliberate Summa-like visual finish
- The landing page now reads more intentionally as a formal work rather than a prototype utility:
  - the tract route behaves like a real first-click path
  - the home heading system feels more classical and less generic
  - the right-side summary block now uses `At a glance`, which reads more naturally than `Key numbers`
- The overall map is now materially more stable for real browsing:
  - later quick-span buttons no longer look broken simply because they cross tract boundaries
  - the question-range slider now keeps working when users choose broader reviewed spans
  - regression protection now covers both the cross-tract edge-selection logic and the live Streamlit controls that drive it
- The sprint finished with a clean editable install on Python `3.12`, deterministic interim artifacts, explicit source/data-model documentation, and wired validation/test/type-check/lint entry points.
- Offline fixture tests pass, and optional live smoke tests against New Advent pass.
- The parser now defends against several real-world source irregularities without weakening the canonical article model.
- The next milestone should build on these exported records rather than reparsing the corpus ad hoc.
- The prudence tract now has a research-grade reviewed block with tract-specific coverage and validation reports, typed part-taxonomy relations, and a separate candidate queue.
- The reviewed doctrinal export is intentionally conservative in places where theological precision matters more than annotation count, especially around false prudence, solicitude, and higher-principle judgment.
- The repo now has a clean verification baseline for continuing the prudence tract by review packet rather than by broad rework.
- The repo now also has a broader pilot research prototype with a stable concept registry, conservative alias normalization, evidence-backed doctrinal edges, structural graph exports, validation reporting, and a thin multi-page Streamlit explorer.
- The pilot doctrinal layer is still intentionally smaller than the structural layer; that imbalance is acceptable for now because the goal is a trustworthy research slice, not a falsely complete concept graph.
- The repo now has a serious full-corpus research workflow on top of the textual spine: structural coverage, parse audits, conservative candidate extraction, review packets, and a corpus browser that distinguishes reviewed from candidate knowledge.
- The next useful work is no longer “whether to widen scope,” but “which tract to review next using the new corpus queue.” The leading near-term candidate is the law/precept block beginning with `I-II q.100`.
- The theological virtues block makes the project feel like a defensible doctrinal graph rather than only a structural prototype. It is still intentionally conservative, especially around the sin-against-the-Spirit material, war, and the exact reviewed relation between hope and the gift of fear.
- The app now needs only incremental tract-specific refinements for future reviewed blocks rather than another round of foundation work.
- The dashboard now reads more like a mature public research product than an internal prototype:
  - each primary page has a clearer read/filter/export loop
  - the graph view is easier to enter quickly because it explains how to narrow scope before asking the user to interpret network structure
  - evidence inspection is faster because selectable edges are described in human language rather than raw ids alone
  - the graph no longer relies on guesswork for interaction because zoom/fit controls and richer hover context are available in the canvas itself
  - first-time navigation is clearer because page names, quick actions, reset controls, and tract comparison now behave more like a decision-support product than a raw research console
- The latest cleanup round tightened the tract viewer without changing the reviewed counts: preset/range views now present only in-range evidence for merged doctrinal edges, and the repo-level verification commands run cleanly again.
- The justice core block makes the reviewed graph materially more useful for legal, social, and injury-related questions. The harmed-domain and judicial-process modeling proved worth the extra schema precision because it kept theft, false accusation, false witness, reviling, and usury from collapsing into one generic injustice bucket.
- The new tract also exposed where the project still needs deliberate human theology review rather than more automation:
  - foundational injustice in `q.59`
  - restitution propagation in `q.62`
  - judicial-role/process normalization in `qq. 68–71`
- The religion tract confirmed that distinct act, vice, and sacred-object layers make later annexed-virtue work much safer. That investment carried forward directly into the owed-relation block.
- The owed-relation tract now gives the project a more defensible account of annexed virtues concerned with what is due:
  - origin-related debt in piety
  - excellence-related debt in observance and dulia
  - authority-related debt in obedience and disobedience
  - benefaction-related debt in gratitude and ingratitude
  - rectificatory debt in vengeance
- The tract remains intentionally conservative where precision matters most:
  - `q.103` dulia still needs careful human review because broad honor and narrower lord-service can drift together too easily
  - `qq. 106–107` need more review once the partial parse pressure is reduced
  - `q.108` needs continued review so rectificatory response does not drift into generic anger language
- The app now has a reusable pattern for tract-local subtype filters that should scale into later annexed-virtue work without rebuilding the reviewed/candidate separation.
  - omission/transgression in `q.79`
- The religion tract adds a second annexed-to-justice block with a materially different ontology from the justice core itself. The new act, sacred-object, and opposition-mode distinctions were worth the extra schema precision because they kept religion, prayer, sacrifice, idolatry, perjury, sacrilege, and simony from collapsing into one vague worship bucket.
- The next high-value human review is no longer just “more annexed virtues,” but specifically the low-density religion questions:
  - `qq. 81–83` on religion, devotion, and prayer
  - `qq. 87–89` on tithes, vows, and oaths
  - `q.97` on temptation of God
  - `q.100` on simony and sacred exchange
- The connected-virtues tract now gives the project a defensible reviewed layer for four justice-adjacent clusters without flattening them into one social-virtue bucket:
  - truth and false self-presentation
  - ordinary social interaction
  - right use of external goods
  - epikeia as correction of rigid legal literalism
- The tract remains intentionally conservative where precision matters most:
  - `qq. 109–111` need more review once the partial parse pressure is reduced
  - `q.117` and `q.118` need more review so liberality does not drift into mercy, almsgiving, or generic money-language
  - `q.120` needs continued review so epikeia does not drift into generic fairness or generic justice
- The app now has a second reusable pattern for tract-local cluster filters that should scale into later annexed-virtue work without weakening reviewed/candidate separation.
- The next high-value human review is no longer just “more annexed virtues,” but specifically the lighter connected-virtues questions:
  - `q.109` on truth
  - `q.110` on lying
  - `qq. 117–118` on liberality and covetousness
  - `q.120` on epikeia and the letter of the law
- The fortitude-parts tract now gives the project a defensible first detailed fortitude overlay without collapsing honor-related and expenditure-related structure into one greatness bucket:
  - magnanimity and its opposed excesses/deficiency
  - magnificence and its opposed excess/deficiency
  - tract-local act/domain support around confidence, assurance, honor, glory, great work, and great expenditure
- The tract remains intentionally conservative where precision matters most:
  - `q.129` still needs more review so honor, worthiness, confidence, and assurance do not flatten together
  - `q.130` still needs more review so tract-local presumption does not drift into the hope tract
  - `q.132` still needs more review so glory and vainglory do not collapse into generic pride language
  - `q.135` still needs more review so waste is not silently rewritten as generic prodigality
- The app now has another reusable pattern for tract-local opposition-mode and cluster filters that should carry forward into the later patience and perseverance questions without weakening reviewed/candidate separation.
- The fortitude closure tract now completes the currently reviewed fortitude material without collapsing patience and perseverance, gift and virtue, or doctrinal and editorial synthesis:
  - patience and perseverance remain distinct fortitude-part virtues
  - effeminacy and pertinacity remain distinct opposed vice concepts
- The temperance closure tract now completes the currently reviewed temperance material without collapsing humility into modesty, pride into Adam’s first sin, curiosity into neutral inquiry, or precepts into a vague summary layer:
  - humility and pride now have a reviewed tract-local spine
  - Adam’s first sin is modeled as a conservative doctrinal case under pride
  - studiousness and curiosity remain distinct moral orderings of inquiry
  - external behavior and outward attire remain distinct modesty species
  - the full temperance synthesis now spans `qq. 141–170` while preserving both phase-1 taxonomy metadata and closure-focus metadata
- The Streamlit app now opens on a usable research dashboard instead of raw summary dumps. A user can see corpus coverage, reviewed tract health, synthesis exports, and current review packets from one landing page without blurring doctrinal, editorial, and candidate layers together.
- The app now feels materially closer to a polished public research product than a prototype:
  - shared typography, color, spacing, and card patterns create a coherent visual identity
  - each page now has a clearer job and a more legible information hierarchy
  - evidence panels and support passages are easier to inspect without reading raw JSON blobs
  - graph, concept, passage, and stats workflows now share one consistent interaction model
- The tract remains intentionally conservative where precision matters most:
  - `q.162` still needs more direct doctrinal review because it is candidate-dense and under-annotated
  - `qq.163–165` still need continued human review so punishments and temptation do not drift into a broader original-sin ontology
  - `qq.168–169` still need continued human review so outward-modesty species do not collapse back into `modesty_general`
  - `q.170` still needs continued review so precept-linkage stays narrow and evidence-backed across the full temperance synthesis
  - the gift of fortitude remains distinct from virtue-level fortitude
  - precept linkages are present, but stay narrowly tied to what `q.140` actually supports
- The fortitude synthesis export is now honest and usable:
  - reviewed doctrinal synthesis covers the existing reviewed fortitude material in `qq. 129–140`
  - reviewed structural-editorial correspondences can be layered in separately
  - `qq. 123–128` are visibly inside the tract frame, but not falsely presented as already doctrinally reviewed
- The next high-value human review is no longer generic fortitude expansion, but specifically:
  - `q.137` on perseverance
  - `q.136` on patience, longanimity, and constancy
  - `q.139` on gift linkage
  - `q.140` on precept linkage
- The temperance phase-1 tract now gives the project a full backbone for the major temperance questions without flattening part taxonomy or matter domain:
  - temperance itself and its contrary vices
  - integral parts in general
  - subjective parts around food, drink, and sex
  - potential parts through continence, meekness, clemency, and modesty in general
- The new tract remains intentionally conservative where precision matters most:
  - `q.143` controls the taxonomy, so neighboring questions do not get auto-promoted into the wrong part level
  - `q.154` keeps the parts-of-lust structure real but deliberately narrower than a fully elaborated sexual vice ontology
  - `q.157` keeps clemency and meekness adjacent without forcing them into one concept
- The temperance synthesis export is now honest and usable:
  - reviewed doctrinal synthesis covers `qq. 141–160`
  - reviewed structural-editorial correspondences can be layered in separately
  - candidate data stays out of default synthesis exports
- The next high-value human review is no longer generic temperance expansion, but specifically:
  - `q.144` on shamefacedness
  - `q.145` on honesty
  - `q.147` on fasting and abstinence
  - `q.152` on virginity and chastity
  - `q.155` on continence
  - `q.158` on anger and meekness
