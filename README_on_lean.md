# Lean verification of `combine_v2-2.tex`

**Verification status: PASS (11 October 2026, Hong Kong).** All eight merged OAI foundation files and both manuscript proof files passed fresh strict replay with Lean 4.34.1. All seven generated final-signature checks also passed. The 312 audited declarations use only `propext`, `Classical.choice`, and `Quot.sound`. The verification record binds the actual sequential source replays to the release source hashes, output and log hashes, and dependency paths. It does not claim a second complete invocation of the packaged checker.

This local verification reused pinned external package artifacts and excluded the original OAI module caches. A clean network bootstrap of the external dependencies was not exercised. The manuscript also compiled successfully with the desktop LaTeX compiler.

The upload package has **ten Lean proof files and thirteen files in total**: eight merged OAI foundation files and two manuscript files, plus the archive, checker, and this README. Upload this entire folder. Generated dependencies, compiled files, and logs are kept outside it.

| File | Purpose |
|---|---|
| `OAI01.lean`–`OAI08.lean` | The 2,925 required OAI modules merged in dependency order, with their original namespaces and attribution. |
| `PartsI_III.lean` | Consolidated proof chain and theorem exports for Parts I–III. |
| `PartIV.lean` | Extended physical moment induction, actual counts and probe estimates, limiting zero-free bound, exact arithmetic, iteration, and scalar optimality. |
| `foundations.tar.gz` | Apache license, pinned Lean/Lake configuration, compatibility patches, source provenance, and proof manifest. |
| `check.py` | Dependency validation, strict source replay, and axiom audit. |
| `README.md` | Scope and replay instructions. |

## Mathematical conclusion

The final exported theorems prove

\[
\beta_*\le B_\infty=\frac{18\xi_\infty+7}{18\xi_\infty+9}
=0.874957019420098946\ldots,
\]

where `xiInf` is the isolated root of
\(1188X^3-2160X^2+171X+190\) in \([0.38858,0.38859]\).

`CombineV22.hecke_nonzero`, `CombineV22.dirichlet_nonzero`, and `CombineV22.zeta_nonzero` give nonvanishing for **Re(s) > B∞**, with the stated principal-pole exclusions. These final declarations do not assume the desired moment, counting, probe, or zero-free conclusions. The one-step theorem constructs the actual geometric instances and uses the proved physical analytic estimates; the limiting theorem starts from the proved 7/8 bound.

This proves neither the Riemann hypothesis nor nonvanishing on the boundary Re(s) = B∞.

## Proof map

The main files contain marked source blocks, preserving the original theorem namespaces. Search for the following declarations:

| Paper material | Lean declarations / namespaces |
|---|---|
| Part I: original 7/8 bound and transfers | `CombinedPaper.original_family_bound`, `original_hecke_nonzero`, `original_dirichlet_nonzero`, `original_zeta_nonzero`; the pinned OAI analytic foundation. |
| Part II: rational bound and uniform endpoint | `CombinedPaper.rational_family_bound`, `rational_endpoint`, and the `RHZeroFreeExtension` physical proof chain. |
| Part III: radical bound, endpoint, and scalar obstruction | `CombinedPaper.algebraic_family_bound`, `algebraic_endpoint`, `scalar_obstruction`; `RHV2`. |
| Part IV: extended physical moment induction | `OAI.SevenEighths.CenteredMomentEnergyCertifiedExistenceIV.terminal_certificate` and `...IVNF.terminal_certificate` without the auxiliary β≥51/100 hypothesis. |
| Part IV: actual detector and source counts | `IVHeckeDetectorCountFromMoments`, `IVProbeFinalAssembly`, and their `IVFull` counterparts. |
| Part IV: exact uniform polynomial and side certificates | `CombineV22.Uniform`, `CombineV22.Checkpoint`, `CombineV22.EndpointGeometry`, `CombineV22.CheckpointGeometry`. |
| Part IV: actual one-step analytic theorem | `RHZeroFreeExtension.AnalyticHigh.IV.beta_le_of_previous_bound`, `CombineV22.one_step`. |
| Part IV: finite iteration and limiting bound | `CombineV22.Iteration.{K_converges,X_converges,Bseq_converges,B_zero}`, `CombineV22.bootstrap_finite_bounds`, `CombineV22.beta_star_le`. |
| Part IV: independent rational one-step proof | `CombineV22.rational_checkpoint_one_step`. |
| Part IV: explicit root and certified decimals | `CombineV22ExplicitRoot.xiInf_explicit`, `CombineV22.ParameterDecimals`. |
| Part IV: minimax, auxiliary choices, and optimality | `CombineV22.System`, `CombineV22.SystemEndpoint`. |
| Part IV: rational approximation and nonattainment | `CombineV22.SystemEndpoint.{rational_system_infimum,rational_lengths_infimum,equality_rigidity,rational_length_not_attaining}`. |
| Part IV: cubic eliminations, irreducibility, and field degrees | `CombineV22.AlgebraicParameters`. |

The original 11/12 **statement** is exported as `CombinedPaper.preliminary_family_bound`, deduced from the proved 7/8 theorem; this export does not reproduce the historical preliminary proof separately. Parts I–III consolidate 219 local source modules. The required original OAI proofs are in `OAI01.lean`–`OAI08.lean` and are replayed before the manuscript files.

### Exact scope of the optimality formalization

`DisplayedCertificate` encodes a critical-class relaxation of the paper's comparison system. Its lower bound applies to every certificate satisfying these necessary constraints. `FullCentralCertificate` adds all central endpoint comparisons over the class rectangle. The formalized lower bound, its attained central infimum, the independent uniform side certificates, and the actual analytic construction together supply the paper's lower-bound/attainment argument. The structures are not presented as a literal encoding of every analytic domain condition in the manuscript.

The optimality is for the **specified system of supplied estimates**, including the formalized detector, moment-width, floor, contour, and loss obstructions. It is not an optimality assertion about all possible analytic methods or actual zero distributions. Physical source theorems retain the original coefficient, mask, row, support, and geometry hypotheses. The final L-function conclusions discharge the required hypotheses through the actual source construction.

## Replay

Install Python 3, Git, and Lean's `elan`/`lake` tooling, then run:

```sh
python3 combine_v2-2_lean/check.py
```

The script extracts its configuration archive to a temporary build directory, fetches the exact external dependency revisions in the archived manifest, applies the two recorded compatibility patches, and builds the required external packages. It then freshly replays `OAI01` through `OAI08`, followed by `PartsI_III` and `PartIV`. The first run needs network access and can take substantially longer than a replay with existing external package artifacts. To choose the output location:

```sh
python3 combine_v2-2_lean/check.py --build-dir /absolute/path/to/build-output
```

An existing checkout with exactly the recorded configuration and external dependency pins can supply its external package artifacts:

```sh
python3 combine_v2-2_lean/check.py \
  --foundation /absolute/path/to/formalization \
  --build-dir /absolute/path/to/replay-output
```

This mode performs no Git fetch and reuses **external package artifacts only**. All eight merged OAI files and both manuscript files are freshly replayed in a new, empty proof-output directory in either mode. The original project's compiled artifacts, including individual OAI module caches, are excluded from Lean's search path. The checker inspects `lean --deps` for each replayed file and permits only already replayed merged files, pinned external packages, and the pinned Lean toolchain. The default mode builds external packages through Lake, which may reuse their earlier artifacts. Neither mode claims fresh source elaboration of every external package dependency.

Both modes clear ambient Lean search-path overrides, validate all ten source hashes and dependency revisions, reject original `OAI.…` imports and proof placeholders/custom axioms in those ten sources, and invoke the pinned Lean executable directly with:

```text
--trust=0 -DautoImplicit=false -DwarningAsError=true -DmaxHeartbeats=0
```

The checker then generates seven small signature checks in the build directory. These explicitly name the external Hecke and Dirichlet L-functions and root-namespace Riemann zeta function, and check the boundary formula, cubic equation, trigonometric root expression, and decimal bracket. They add no upload files.

Every printed axiom report must use only `propext`, `Classical.choice`, and `Quot.sound`; the expected main theorem reports must be present. `sorryAx`, `sorry`, `admit`, and `native_decide` are rejected. Lean style-only linter options are locally disabled where appropriate; proof checking and warnings-as-errors remain enabled.

A successful run writes `result.json` and `replay-logs/` **outside this upload folder**. The result contains the exact source/archive hashes, manuscript hash, Lean version, replay order, filtered search path, resolved dependency artifacts, external package mode, and axiom reports. Missing output or a nonzero exit is not a successful verification.

## Pins and attribution

- Lean: **4.34.1**.
- mathlib: `d13f23b723b8a846827a245b89c10fc7d3f11612`.
- OAI analytic source: `openai/math`, revision `adc7f1241b42e322a6451854ab7e4b4c146bf78a`.
- Other dependencies and the two compatibility patches are pinned in the archive.

The OAI foundation is source material, not an axiom replacing its theorems. Its Apache-2.0 license is retained as `vendor/LICENSE` inside the archive. The merged files identify their original source blocks and consolidation changes. Original module hashes are provenance verified during assembly against the pinned source manifest; replay independently checks the hashes of the merged release files. Consolidation required qualifying 462 `PrimeIdeal` references in 118 original modules to `OAI.SevenEighths.ProbePhysical.PrimeIdeal`; an independent audit checked each original import scope and confirmed that reversing these qualifications recovers the original module bodies. No other proof-body edits were made to the OAI foundation. Extended Part IV modules identify the copied/generalized source blocks and preserve attribution. No new license is assigned here to the newly authored local proof files.
