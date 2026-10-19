"""Build P5 submission tables, figures and supplement from aggregate saved outputs only."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "projects/P5_asd_adhd_replication"
OUT = BASE / "submission"
BLUE, ORANGE, INK, MUTED, GRID = "#245b87", "#ad6b26", "#1f1f1e", "#6b6a63", "#e4e3dd"
SENSES = [("visual", "Sight"), ("auditory", "Sound"), ("smell", "Smell"), ("taste", "Taste"), ("touch", "Touch"), ("movement", "Movement")]


def ci(values, digits=2, signed=True):
    low, high = values
    fmt = f"{{:+.{digits}f}}" if signed else f"{{:.{digits}f}}"
    return f"{fmt.format(low)} to {fmt.format(high)}"


def est(block, digits=2):
    return f"{block['estimate']:+.{digits}f} ({ci(block['ci95'], digits)})"


def pval(p):
    return "< .001" if p < .001 else f"{p:.3f}".lstrip("0") if p < .995 else "1.00"


def main():
    results = ROOT / "runs/latest/P5"
    diagnostics = json.loads((results / "p5_diagnostics.json").read_text())
    details = diagnostics["details"]
    rows = list(csv.DictReader((results / "p5_estimates.csv").open()))
    get = lambda model, term: next(r for r in rows if r["model"] == model and r["term"] == term)
    five = json.loads((BASE / "review/validation/five_sense_check.json").read_text())
    validation = json.loads((BASE / "review/validation/numerical_validation.json").read_text())
    explore = json.loads((results / "p5_exploratory.json").read_text())
    dance = json.loads((results / "p5_dance_traits.json").read_text())
    bench = json.loads((results / "p5_shift_benchmark.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    table = []
    for label in diagnostics["primary_sequence"]:
        r = get(label, "in_group")
        d = details["primary"][label]
        table.append({"hypothesis": label, "estimate": r["coef"], "ci95_low": r["ci_low"], "ci95_high": r["ci_high"],
                      "n_complete_cases": r["n"], "p_one_sided_registered": d["one_sided_p"],
                      "passed_fixed_sequence": d["confirmatory_support"], "effect_scale": r["effect_kind"]})
    with (OUT / "table1_primary.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    secondary = details["secondary"]
    secondary_definitions = {
        "S1_chemosensory_minus_visual": ("Autism: smell/taste difference minus sight difference", "S1_modality_profile_asd", "chemosensory_minus_visual"),
        "S1_omnibus": ("Autism: difference varies across the six senses", None, None),
        "S2_asd_minus_adhd_only": ("Autism minus ADHD-only, overall score", "S2_specificity_three_group", "asd_minus_adhd_only"),
        "S3_visual_absence": ("Absent visual imagery, autism vs comparison", "S3_visual_absence_asd", "in_group"),
        "S4_adhd_chemosensory_minus_visual": ("ADHD-only: smell/taste difference minus sight difference", "S4_modality_profile_adhd_only", "chemosensory_minus_visual")}
    short_labels = dict(zip(secondary_definitions, ["S1(a)", "S1(b)", "S2", "S3", "S4"]))
    with (OUT / "table2_secondary.csv").open("w") as f:
        writer = csv.writer(f); writer.writerow(["test", "definition", "estimate", "ci95_low_unadjusted", "ci95_high_unadjusted", "effect_scale", "p_two_sided", "p_Holm_adjusted", "supported_at_05"])
        for label, p in secondary["two_sided_p"].items():
            q = secondary["holm_adjusted_p"][label]
            definition, model, term = secondary_definitions[label]
            r = get(model, term) if model else None
            estimate = r["coef"] if r else secondary["S1_modality_profile_asd"]["omnibus_group_by_modality_wald_chi2"]
            writer.writerow([label, definition, estimate, r["ci_low"] if r else "", r["ci_high"] if r else "", r["effect_kind"] if r else "chi_square_df5", p, q, q < .05])
    shutil.copyfile(results / "p5_estimates.csv", OUT / "supplement_registered_estimates.csv")

    # Figure 1: registered six-sense and exploratory five-sense overall differences.
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    figure_values = []
    for model, label in [("H1_general_imagery_shift", "New: registered six senses"),
                         ("XS_arnold_general_imagery_shift", "Arnold: registered six senses")]:
        r = get(model, "in_group")
        figure_values.append((label, float(r["coef"]), float(r["ci_low"]), float(r["ci_high"]), BLUE))
    for key in ["New", "Arnold"]:
        d = five[key]
        figure_values.append((f"{key}: five-sense check", d["adjusted_difference_reference_SD"], *d["ci95"], ORANGE))
    for pos, (label, value, low, high, colour) in enumerate(figure_values):
        y = 3-pos
        ax.errorbar(value, y, xerr=[[value-low], [high-value]], fmt="o", color=colour, capsize=4, lw=1.6)
    ax.axvline(0, color="#777777", linewidth=.8)
    ax.set_yticks([3,2,1,0], [v[0] for v in figure_values])
    ax.set_xlabel("Autism minus comparison, adjusted (comparison-group SD), with 95% CI")
    ax.set_xlim(-.8, .12)
    ax.set_ylim(-.5, 3.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.18)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    fig.savefig(OUT / "figure1_overall_imagery.png", dpi=300)
    plt.close(fig)

    # Figure 2 (exploratory): where the gap sits, in both studies.
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.15, 1]})
    for block, colour, label, offset in ((explore, BLUE, "New et al.", -0.6), (explore["arnold"], ORANGE, "Arnold et al.", 0.6)):
        curve = block["E3_percentile_curve_unadjusted"]
        x = np.array([row["percentile"] for row in curve]) + offset
        y = np.array([row["difference"] for row in curve])
        left.vlines(x, [row["ci95"][0] for row in curve], [row["ci95"][1] for row in curve], color=colour, linewidth=1.2, alpha=0.55)
        left.plot(x, y, color=colour, linewidth=2, marker="o", markersize=3.5, label=label)
    left.axhline(0, color=MUTED, linewidth=0.8)
    left.set_xlabel("Percentile of overall imagery")
    left.set_ylabel("Autism minus comparison (SD)")
    left.set_xticks([5, 25, 50, 75, 95])
    left.grid(axis="y", color=GRID, linewidth=0.6)
    left.legend(frameon=False, fontsize=7.5, loc="lower right")
    left.set_title("A. Where the difference sits", loc="left", fontsize=9, color=INK)
    comparable = SENSES[:5]
    width = 0.38
    positions = np.arange(len(comparable))
    for block, colour, label, shift in ((explore, BLUE, "New et al.", -width / 2), (explore["arnold"], ORANGE, "Arnold et al.", width / 2)):
        style = block["E1_answering_style"]
        right.bar(positions + shift, [style[k]["floor"]["autism_pct"] for k, _ in comparable], width - 0.04, color=colour, label=f"{label}, autism")
        right.scatter(positions + shift, [style[k]["floor"]["comparison_pct"] for k, _ in comparable], s=20, color="white",
                      edgecolor=colour, linewidth=1.4, zorder=3, label=f"{label}, comparison")
    right.set_xticks(positions, [name for _, name in comparable])
    right.set_ylim(0, 18)
    right.set_ylabel("Absent imagery in that sense (%)")
    right.grid(axis="y", color=GRID, linewidth=0.6)
    right.set_axisbelow(True)
    right.legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    right.set_title("B. How often imagery is absent", loc="left", fontsize=9, color=INK)
    for axis in (left, right):
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "figure2_where_the_gap_sits.png", dpi=300)
    plt.close(fig)
    plt.rcdefaults()

    # Figure S1: descriptive effects for the five comparable senses.
    arnold_rows = list(csv.DictReader((ROOT / "runs/latest/P3/p3_estimates.csv").open()))
    senses = ["visual", "auditory", "smell", "taste", "touch"]
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    for label, model, offset, colour, source, term in [
        ("New: autism", "descriptive_hedges_g_asd", .2, BLUE, rows, "asd_vs_reference"),
        ("New: ADHD-only", "descriptive_hedges_g_adhd_only", 0, "#71767c", rows, "adhd_only_vs_reference"),
        ("Arnold: autism", "all_self_reported_formal_dx_hedges_g", -.2, ORANGE, arnold_rows, "formal_autism_group")]:
        for i, sense in enumerate(senses):
            r = next(r for r in source if r["model"] == model and r["term"] == term and r["outcome"] == sense + "_score")
            value, low, high = [float(r[k]) for k in ["coef", "ci_low", "ci_high"]]
            ax.errorbar(value, len(senses)-1-i+offset, xerr=[[value-low], [high-value]], fmt="o", color=colour, capsize=3, label=label if i == 0 else None)
    ax.axvline(0, color="#777777", linewidth=.8)
    ax.set_yticks(range(5), ["Sight" if s == "visual" else "Sound" if s == "auditory" else s.title() for s in reversed(senses)])
    ax.set_xlabel("Unadjusted Hedges g (pooled SD), with 95% CI")
    ax.set_ylim(-.6, 5.6); ax.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.18); ax.tick_params(axis="y", length=0)
    fig.tight_layout(); fig.savefig(OUT / "figureS1_sensory_descriptives.png", dpi=300); plt.close(fig)
    (OUT / "figure2_sensory_descriptives.png").unlink(missing_ok=True)

    descriptive = list(csv.DictReader((OUT / "table0_participants_outcomes.csv").open()))
    lookup = lambda measure, group: next(r for r in descriptive if r["measure"] == measure and r["group"] == group)
    groups = ["Comparison", "Autism", "ADHD-only"]

    # Main Table 1: participants.
    style = explore["E1_answering_style"]
    absent_any = {"Comparison": style["any_sense_absent"]["comparison_pct"], "Autism": style["any_sense_absent"]["autism_pct"],
                  "ADHD-only": explore["E1_any_sense_absent_adhd_only"]["adhd_only_pct"]}
    t1 = ["Table 1. Participants in New et al.'s survey", "",
          "| | Comparison | Autism | ADHD-only |", "|---|---:|---:|---:|",
          "| People | " + " | ".join(lookup("Retained participants", g)["n"] for g in groups) + " |",
          "| Also reported ADHD | - | 46 | - |",
          "| Female | " + " | ".join(f"{100 * bench['new_sex_codes_by_group'][code].get('0', 0) / sum(bench['new_sex_codes_by_group'][code].values()):.0f}%" for code in ("reference", "asd", "adhd_only")) + " |",
          "| Age, mean (SD) | " + " | ".join(f"{float(lookup('Age (years)', g)['mean']):.1f} ({float(lookup('Age (years)', g)['sd']):.1f})" for g in groups) + " |",
          "| Overall imagery, mean (SD) | " + " | ".join(f"{float(lookup('Registered composite (comparison SD)', g)['mean']):+.2f} ({float(lookup('Registered composite (comparison SD)', g)['sd']):.2f})" for g in groups) + " |",
          "| Absent imagery in at least one sense | " + " | ".join(f"{absent_any[g]:.1f}%" for g in groups) + " |",
          "", "Overall imagery is in comparison-group standard deviations, so the comparison group has mean 0 and SD 1. Absent imagery means the lowest possible score in a sense. Sex was recorded as female, male or other; two respondents in these groups chose other. Ages ranged from 18 to 32: New et al.'s eligibility was 18-30, but three retained respondents gave older ages. One comparison respondent had no recorded age. Table S1 gives each sense's raw score."]
    (OUT / "table_main1_participants.md").write_text("\n".join(t1) + "\n")

    # Main Table 2: registered tests.
    names = dict(zip(diagnostics["primary_sequence"], ["H1. Overall imagery, autism vs comparison", "H2a. Absent smell imagery", "H2b. Absent taste imagery"]))
    t2 = ["Table 2. Registered tests in New et al.'s survey", "",
          "| Test | Estimate (95% CI) | One-sided p | Holm-adjusted p | Supported |", "|---|---|---:|---:|---|"]
    for r in table:
        scale = "SD" if "general" in r["hypothesis"] else "OR"
        value = float(r["estimate"])
        text = f"{value:+.2f} SD" if scale == "SD" else f"OR {value:.2f}"
        low, high = float(r["ci95_low"]), float(r["ci95_high"])
        bounds = f"{low:+.2f} to {high:+.2f}" if scale == "SD" else f"{low:.2f} to {high:.2f}"
        t2.append(f"| {names[r['hypothesis']]} | {text} ({bounds}) | {pval(r['p_one_sided_registered'])} | - | Yes |")
    for label, p in secondary["two_sided_p"].items():
        definition, model, term = secondary_definitions[label]
        q = secondary["holm_adjusted_p"][label]
        if model:
            r = get(model, term)
            value, low, high = float(r["coef"]), float(r["ci_low"]), float(r["ci_high"])
            text = f"OR {value:.2f} ({low:.2f} to {high:.2f})" if "odds" in r["effect_kind"] else f"{value:+.2f} SD ({low:+.2f} to {high:+.2f})"
        else:
            text = f"chi-square {secondary['S1_modality_profile_asd']['omnibus_group_by_modality_wald_chi2']:.2f}, 5 df"
        t2.append(f"| {short_labels[label]}. {definition} | {text} | - | {pval(q)} | {'Yes' if q < .05 else 'No'} |")
    t2 += ["", "H1-H2b are the primary tests, run in a fixed order with one-sided p values. S1-S4 are secondary tests with two-sided, Holm-adjusted p values. Their confidence intervals are not adjusted for multiple tests, so an interval can exclude zero (as for S2) while the adjusted test is not significant. All models adjust for age and sex. SD: comparison-group standard deviations. OR: odds ratio. n = 898 for H1-H2b, S1 and S3; 982 for S2; 832 for S4."]
    (OUT / "table_main2_registered.md").write_text("\n".join(t2) + "\n")

    # Main Table 3: exploratory, where the gap sits.
    arnold = explore["arnold"]
    t3 = ["Table 3. Where the difference sits (exploratory)", "",
          "| Measure | New et al. | Arnold et al. |", "|---|---|---|",
          f"| Absent imagery in at least one sense, autism vs comparison | {style['any_sense_absent']['autism_pct']:.1f}% vs {style['any_sense_absent']['comparison_pct']:.1f}% (Fisher p {pval(style['any_sense_absent']['fisher_p'])}) | {arnold['E1_answering_style']['any_sense_absent']['autism_pct']:.1f}% vs {arnold['E1_answering_style']['any_sense_absent']['comparison_pct']:.1f}% (Fisher p {pval(arnold['E1_answering_style']['any_sense_absent']['fisher_p'])}) |",
          f"| Extra senses with absent imagery, per person | {est(style['n_floor_per_person']['adjusted_difference'])} | {est(arnold['E1_answering_style']['n_floor_per_person']['adjusted_difference'])} |",
          f"| Extra senses with the top score, per person | {est(style['n_ceiling_per_person']['adjusted_difference'])} | {est(arnold['E1_answering_style']['n_ceiling_per_person']['adjusted_difference'])} |"]
    for q in ["q10", "q25", "q50", "q75", "q90"]:
        t3.append(f"| Difference at the {q[1:]}th percentile (SD) | {est(explore['E3_adjusted_quantile_regression'][q])} | {est(arnold['E3_adjusted_quantile_regression'][q])} |")
    key = "E3_H1_among_people_with_imagery_in_all_six_senses"
    t3 += [f"| Difference among people with imagery in every sense (SD) | {est(explore[key])}, n = {explore[key]['n']} | {est(arnold[key])}, n = {arnold[key]['n']} |",
           "", f"The first row gives percentages. The other rows are autism-minus-comparison differences, adjusted for age and sex, with 95% confidence intervals. Percentile differences come from quantile regression. Each dataset uses its own six senses and is standardised against its own comparison group; Arnold et al.'s sixth sense is bodily sensation rather than movement. Groups: New et al., 150 autism and 749 comparison (898 with age recorded); Arnold et al., 327 and 327. These analyses were not registered."]
    (OUT / "table_main3_tails.md").write_text("\n".join(t3) + "\n")

    # Main Table 4 (exploratory): what a whole-group shift would predict.
    t4 = ["Table 4. Observed autism group versus two whole-group models (exploratory)", "",
          "| Dataset and measure | Observed (95% CI) | Shift | Shift + stretch |", "|---|---|---:|---:|"]
    rows4 = [("Absent imagery in at least one sense", "any_absent_pct", "{:.1f}%"), ("Difference at the 10th percentile (SD)", "q10", "{:+.2f}"),
             ("Difference at the median (SD)", "q50", "{:+.2f}"), ("Difference among people with imagery in every sense (SD)", "all_present_difference", "{:+.2f}")]
    for study, title in (("new", "New et al."), ("arnold", "Arnold et al.")):
        b = bench[study]
        for name, k, f in rows4:
            low, high = b["observed_bootstrap_ci95"][k]
            t4.append(f"| {title}: {name} | {f.format(b['observed_autism'][k])} ({f.format(low)} to {f.format(high)}) | {f.format(b['predicted_shift'][k])} | {f.format(b['predicted_shift_plus_stretch'][k])} |")
    t4 += ["", f"Shift: every comparison respondent's score in each sense lowered by the autism-comparison mean difference for that sense. Shift + stretch: each sense also rescaled to the autism group's standard deviation. Scores were rounded and kept within the scale. Comparison-group rates of absent imagery were {bench['new']['comparison']['any_absent_pct']:.1f}% (New et al.) and {bench['arnold']['comparison']['any_absent_pct']:.1f}% (Arnold et al.). All values are unadjusted; intervals are from 2,000 bootstrap resamples of the autism group. Added after an internal review on 18 October 2026, after all other results were known."]
    (OUT / "table_main4_benchmark.md").write_text("\n".join(t4) + "\n")

    # Supplement.
    participant_lines = ["| Measure | Comparison | Autism | ADHD-only |", "|---|---:|---:|---:|"]
    for measure in dict.fromkeys(r["measure"] for r in descriptive):
        selected = [lookup(measure, g) for g in groups]
        values = [r["n"] if not r["mean"] else f"{float(r['mean']):.2f} ({float(r['sd']):.2f})" for r in selected]
        participant_lines.append("| " + " | ".join([measure.replace("Registered composite", "Overall imagery").replace("Visual", "Sight").replace("Auditory", "Sound"), *values]) + " |")
    ages = [r for r in descriptive if r["measure"] == "Age (years)"]
    age_note = "; ".join(f"{r['group']} {float(r['min']):.0f}-{float(r['max']):.0f} years (n = {r['n']})" for r in ages)
    primary_lines = ["| Test | Estimate | 95% CI | One-sided p | Supported |", "|---|---:|---|---:|---|"]
    for r in table:
        primary_lines.append(f"| {names[r['hypothesis']]} | {float(r['estimate']):.3f} | {float(r['ci95_low']):.3f} to {float(r['ci95_high']):.3f} | {r['p_one_sided_registered']:.3g} | Yes |")
    lines = ["# Supplementary material", "",
             "## Table S1. Participants and raw scores", "", *participant_lines, "",
             f"Means (standard deviations), except participant counts. Ages: {age_note}. Each sense score is the sum of five 1-7 ratings (range 5-35). Movement is New et al.'s sixth sense. Sex is shown in Table 1. The archive codes sex as 0, 1 and O; we read 0 as female and 1 as male because the coded totals across New et al.'s two studies (992, 952 and 8) match their published counts of female, male and other respondents in that order.", "",
             "## Table S2. Registered primary tests, full precision", "", *primary_lines, "",
             "The first estimate is a difference in comparison-group standard deviations; the others are odds ratios. The file supplement_registered_estimates.csv stores two-sided p values for every model; the one-sided p values above are the registered tests.", "",
             "## Table S3. Registered secondary tests", "", "| Test | Definition | Two-sided p | Holm-adjusted p |", "|---|---|---:|---:|"]
    for label, p in secondary["two_sided_p"].items():
        lines.append(f"| {short_labels[label]} | {secondary_definitions[label][0]} | {p:.3g} | {secondary['holm_adjusted_p'][label]:.3g} |")
    adhd = get("S2_specificity_three_group", "adhd_only_indicator")
    lines += ["", f"The ADHD-only versus comparison difference in the three-group model was {float(adhd['coef']):+.3f} SD (95% CI {float(adhd['ci_low']):+.3f} to {float(adhd['ci_high']):+.3f}).",
              "S1 and S4 use one row per person per sense (5,388 rows for 898 people in S1; 4,992 rows for 832 people in S4)."]
    model_labels = {
        "SENS_asd_without_adhd": ("New: autism group without co-reported ADHD", "SD; people"),
        "SENS_raw_score_composite": ("New: raw six-sense mean", "Points on 5-35 scale; people"),
        "SENS_age_18_30": ("New: ages 18-30 only", "SD; people"),
        "SENS_unadjusted": ("New: no age/sex adjustment", "SD; people"),
        "SENS_asd_without_adhd_smell_absence": ("New: absent smell, without co-reported ADHD", "Odds ratio; people"),
        "SENS_asd_without_adhd_taste_absence": ("New: absent taste, without co-reported ADHD", "Odds ratio; people"),
        "SENS_modality_profile_nuisance": ("New: sight difference, age/sex effects allowed to vary by sense", "Sight SD; person-sense rows"),
        "XS_arnold_general_imagery_shift": ("Arnold: overall imagery, six senses", "SD; people"),
        "XS_arnold_modality_profile": ("Arnold: sight difference in the per-sense model", "Sight SD; person-sense rows")}
    lines += ["", "## Table S4. Registered sensitivity analyses and Arnold et al. reanalysis", "", "| Analysis | Estimate | 95% CI | Units | n |", "|---|---:|---|---|---:|"]
    for r in rows:
        if r["model"] in model_labels and r["term"] == "in_group":
            name, units = model_labels[r["model"]]
            lines.append(f"| {name} | {float(r['coef']):.3f} | {float(r['ci_low']):.3f} to {float(r['ci_high']):.3f} | {units} | {r['n']} |")
    lines += ["", "In the per-sense models, sight is the reference sense, so the group coefficient is the difference for sight only. New et al.'s 5,388 rows are 898 people; Arnold et al.'s 3,924 rows are 654 people. All rows, including interaction terms, are in supplement_registered_estimates.csv.", "",
              "## Table S5. Five-sense check (exploratory)", "", "| Dataset | Difference (SD) | 95% CI | Two-sided p | n |", "|---|---:|---|---:|---:|"]
    for key5 in ["New", "Arnold"]:
        d = five[key5]
        lines.append(f"| {key5} et al. | {d['adjusted_difference_reference_SD']:.3f} | {d['ci95'][0]:.3f} to {d['ci95'][1]:.3f} | {d['p_two_sided_exploratory']:.3g} | {d['n']} |")
    lines += ["", "Uses sight, sound, smell, taste and touch only, standardised against each dataset's comparison group, with the same age/sex-adjusted model as H1. Specified in the deviations log on 17 October 2026, after the registered results were known.", "",
              "## Table S6. Lowest and highest scores by sense (exploratory)", "",
              "| Sense | New: absent, autism / comparison | New: top score, autism / comparison | Arnold: absent, autism / comparison | Arnold: top score, autism / comparison |", "|---|---|---|---|---|"]
    for k, name in SENSES:
        cells = []
        for block in (explore, arnold):
            s = block["E1_answering_style"][k]
            cells += [f"{s['floor']['autism_pct']:.1f}% / {s['floor']['comparison_pct']:.1f}%", f"{s['ceiling']['autism_pct']:.1f}% / {s['ceiling']['comparison_pct']:.1f}%"]
        lines.append(f"| {name if k != 'movement' else 'Movement (New) / bodily sensation (Arnold)'} | " + " | ".join(cells) + " |")
    lines += ["", "Absent: the lowest possible score in that sense (5 of 35 in New et al.; 0 of 50 in Arnold et al.). Top score: the highest possible score (35; 50). New et al.: 150 autism, 749 comparison. Arnold et al.: 327 each."]
    aq = explore["arnold_aq26_subset"]
    within = explore["arnold_within_autistic_traits_vs_any_absent"]["AQ_nonimagination"]
    pooled = explore["E3_pooled_two_studies_people_with_imagery_in_all_senses"]
    e4 = explore["E4_new_only_senses"]
    e5 = explore["E5_adjusted"]
    e6 = explore["E6_empathy_item"]
    inventory = [
        ("New: overall difference among people who repeated all five activities in the attention check", est(explore["E2_all_attention_checks_passed"]) + " SD", explore["E2_all_attention_checks_passed"]["n"]),
        ("New: emotion imagery (not in the overall score)", est(e4["emotion"]) + f" SD, Holm p {pval(e4['emotion']['holm_p'])}", e4["emotion"]["n"]),
        ("New: voice imagery", est(e4["voice"]) + f" SD, Holm p {pval(e4['voice']['holm_p'])}", e4["voice"]["n"]),
        ("New: inner-body imagery", est(e4["interoception"]) + f" SD, Holm p {pval(e4['interoception']['holm_p'])}", e4["interoception"]["n"]),
        ("New: overall difference, also adjusted for current treatment", est(e5["current_treatment"]) + " SD", e5["current_treatment"]["n"]),
        ("New: overall difference, also adjusted for education", est(e5["education"]) + " SD", e5["education"]["n"]),
        ("New: empathy self-rating (1-7), autism minus comparison", est(e6["adjusted_difference_raw_points"]) + " points", e6["adjusted_difference_raw_points"]["n"]),
        ("New: overall difference, also adjusted for the empathy rating", est(e6["H1_adjusted_for_empathy"]) + " SD", e6["H1_adjusted_for_empathy"]["n"]),
        ("New: absent imagery in at least one sense, ADHD-only vs comparison", f"{explore['E1_any_sense_absent_adhd_only']['adhd_only_pct']:.1f}% vs {style['any_sense_absent']['comparison_pct']:.1f}%, Fisher p {pval(explore['E1_any_sense_absent_adhd_only']['adhd_only_vs_comparison']['fisher_p'])}", 833),
        ("New: absent imagery in at least one sense, autism vs ADHD-only", f"OR {explore['E1_any_sense_absent_adhd_only']['autism_vs_adhd_only']['odds_ratio']:.2f}, Fisher p {pval(explore['E1_any_sense_absent_adhd_only']['autism_vs_adhd_only']['fisher_p'])}", 234),
        ("Arnold, AQ 26 or more only: absent imagery in at least one sense", f"{aq['E1_answering_style']['any_sense_absent']['autism_pct']:.1f}% vs {aq['E1_answering_style']['any_sense_absent']['comparison_pct']:.1f}%", 569),
        ("Arnold, AQ 26 or more only: median difference", est(aq["E3_adjusted_quantile_regression"]["q50"]) + " SD", aq["E3_adjusted_quantile_regression"]["n"]),
        ("Arnold, AQ 26 or more only: difference among people with imagery in every sense", est(aq[key]) + " SD", aq[key]["n"]),
        ("Arnold, autistic adults: AQ without imagination items, absent imagery in any sense vs none", f"{within['mean_absent']:.1f} vs {within['mean_present']:.1f}, d = {within['cohen_d']:.2f}, Mann-Whitney p {pval(within['mann_whitney_p'])}", within["n_absent"] + within["n_present"]),
        ("Both datasets pooled: difference among people with imagery in every sense", f"{pooled['estimate']:+.2f} SD ({ci(pooled['ci95'])}); two one-sided tests against +/-0.2 SD, p {pval(pooled['tost_p'])}", explore[key]["n"] + arnold[key]["n"]),
        ("Dance et al. (2021), people without aphantasia: AQ vs six-sense imagery", f"Spearman rho = {dance['exp1_non_aphantasic']['six_sense_mean']['rho']:.2f}, p {pval(dance['exp1_non_aphantasic']['six_sense_mean']['p'])}", dance["exp1_non_aphantasic"]["n"]),
        ("Dance et al. (2021), people with aphantasia: AQ vs six-sense imagery", f"Spearman rho = {dance['exp1_aphantasic']['six_sense_mean']['rho']:.2f}, p {pval(dance['exp1_aphantasic']['six_sense_mean']['p'])}", dance["exp1_aphantasic"]["n"]),
        ("Dance et al. (2021), general population: AQ vs visual imagery (VVIQ)", f"Spearman rho = {dance['exp2_general_population_vviq']['rho']:.2f}, p {pval(dance['exp2_general_population_vviq']['p'])}", dance["exp2_general_population_vviq"]["n"])]
    lines += ["", "## Table S7. All other exploratory analyses", "",
              "Every exploratory analysis run on these data after the registered results were known, including those not discussed in the main text. Differences are autism minus comparison, adjusted for age and sex, with 95% confidence intervals, unless stated otherwise.", "",
              "| Analysis | Result | n |", "|---|---|---:|"]
    lines += [f"| {a} | {b} | {n} |" for a, b, n in inventory]
    lines += ["", "Why these analyses were run. Attention check: to see whether careless responding explains the difference. Emotion, voice and inner-body imagery: the three kinds of imagery New et al. measured that are not in the overall score. Treatment and education: possible confounders recorded in the survey. Empathy self-rating: the survey's only non-imagery 1-7 rating, used to check whether autistic respondents simply rate themselves lower on any 1-7 item; adjusting for it reduced the difference from -0.42 to -0.34. AQ 26 or more: Arnold et al.'s own selection. AQ without imagination items: whether absent imagery goes with autistic traits beyond the items that ask about imagination (Bouyer et al., 2025). Dance, Ward and Simner (2021): a public dataset with AQ and six-sense imagery in people with and without aphantasia (OSF h24vm; their AQ total omits item 3). The pooled estimate uses fixed-effect inverse-variance weights across two questionnaires whose sixth senses differ, and it selects people by their scores; the +/-0.2 SD bound is a conventional 'small' effect, chosen after the results were known.", "",
              "[FIGURE figureS1_sensory_descriptives.png | Figure S1. Unadjusted differences in each of the five senses measured in both questionnaires (Hedges g with pooled standard deviations and 95% confidence intervals). This scale differs from the adjusted overall score in the main text. These are descriptive, not additional tests.]", "",
              "## Reproduction and checks", "",
              f"All {validation['reproduction_rows']} registered estimate rows were reproduced exactly in a separate run (largest absolute difference {validation['reproduction_max_absolute_difference']}). The frozen plan's SHA-256 is {validation['plan_sha256']}, and the original output files were unchanged.", "",
              "The overall-score regression was rebuilt independently with statsmodels (OLS, HC3, t inference) and agreed. Holm adjustment was rechecked with statsmodels. The five Firth fits were refitted in R 4.6.1 with brglm2 1.1.1 (mean bias reduction). Coefficients, covariance matrices, Wald intervals and p values agreed: the largest coefficient difference was " + f"{max(c['max_abs_beta_difference'] for c in validation['Firth_checks']):.2g}" + " and the largest covariance difference " + f"{max(c['max_abs_covariance_difference'] for c in validation['Firth_checks']):.2g}" + ". To converge with the small 'other' sex category, the R fit needed an intercept-only start and step size 0.25.", "",
              "The code, run order and checks are documented in the repository; no participant-level rows are written.", "",
              "## Source measures", "",
              "New et al.: OSF project 2bdn6. The data file for Study 2 is named Exp3.1020.txt in the archive. The questionnaire (Study2.Questionnaires.pdf in the archive) is the 45-item QMI + VocEmo, New et al.'s extension of the Questionnaire upon Mental Imagery with vocal and emotional items. The six senses used here are its sight, sound, smell, taste, touch and movement scales. Its emotion, voice and inner-body scales are not in the overall score. New et al.'s attention rule keeps people who repeated at least three of their five favourite activities.", "",
              "Arnold et al.: the public workbook labels its six PSI-Q columns visual, auditory, smell, taste, touch and bodily sensation. All 327 autistic records in Arnold et al.'s analysis code match the workbook on imagery scores, AQ and age, and all have the maximum attention score (13). How the comparison group was recruited is not documented in these files.", "",
              "## Table S8. Deviations from the registered plan", "",
              "| Date | Change | Effect |", "|---|---|---|",
              "| 10 Oct 2026 | The plan gave the effect Arnold et al.'s study had a 33% chance of detecting (used to judge a null H1) as about 0.12 SD; the registered code computed 0.139 SD. | None: only used if H1 had failed. |",
              "| 10 Oct 2026 | Firth regression used for H2a, H2b, S3 and their sensitivity analyses, as the plan allowed, because the 'other' sex category perfectly predicted the outcome. | None; reported as planned. |",
              "| 11 Oct 2026 | The plan's SHA-256 for the New et al. data file was the archive's fingerprint, not the file's. Label corrected. | None; same data. |",
              "| 17 Oct 2026 | The plan treated Arnold et al.'s sixth sense (bodily sensation) as movement. Registered results kept as run; five-sense check added. | Registered six-sense results are not matched across questionnaires. |",
              "| 17 Oct 2026 | Registered analysis reproduced in a separate directory; Firth fits checked against R. | Numerical check only; no discrepancies. |",
              "| 18 Oct 2026 | Shift benchmark (Table 4) added after an internal review. | Exploratory. |", "",
              "The full deviations log is in the repository alongside the registered plan.", "",
              "## Comparing the two datasets", "",
              "The registered six-sense differences were -0.42 SD (New) and -0.18 SD (Arnold). Their difference, -0.24 SD, had a two-sided p of .11 under a normal approximation. This comparison treats the samples as independent and the two composites as comparable; neither is established, so we do not interpret it."]
    (OUT / "supplement.md").write_text("\n".join(lines) + "\n")
    manifest = {}
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name != "manifest_sha256.json": manifest[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / "manifest_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Generated tables, figures, supplement and manifest.")


if __name__ == "__main__":
    main()
