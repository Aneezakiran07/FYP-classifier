# Hash verification of the diff3 dataset

Written 2026-11-14 by Aneeza. Script: `scripts/verify_diff3_hashes.py`. It only reads its inputs and needs no clone, no network and no API call.

## Names used here

The report and the repo name the two populations differently, so this file uses the report names.

| Report name | Pull requests | Marker regions | Where it lives |
|---|---|---|---|
| final dataset | 4,266 | 54,641 (27,690 in .ts and .tsx) | `AgenticFlict/data/reproduced_aneeza_success.jsonl` plus `reproduced_fatima_success.jsonl` (outside the repo) |
| eligible pool | 4,119 | 35,241 (17,979 in .ts and .tsx) | `data/raw/final_dataset.jsonl` |

The AgenticFlict side is `AgenticFlict/data/clean/agenticflict_regions_clean.csv`. It holds, for each region, the line numbers, the number of ours and theirs lines and the SHA-256 of the ours and theirs text. It holds no text and no base hash.

## The problem

The first reproduction used Git's default conflict style and matched AgenticFlict on every region. The final dataset was rebuilt with the diff3 style, so that the base text could be kept. Comparing it the same way, by `(pr_key, file_path, conflict_index)`, matched only 14,660 of 54,641 regions (26.8 percent). The report said the reason was not known and left a second check to FYP-II.

## What we found

The mismatch comes from the conflict style, not from wrong text. Git builds region boundaries differently in the two styles.

1. **The default style trims.** Lines at the edge of a conflict that are the same on both sides are moved out of the region. The diff3 style keeps them, because the base block needs them. So the same conflict hashes differently.
2. **The default style splits.** A conflict with a run of identical lines in the middle becomes two regions in the default style and stays one region in diff3.
3. **The default style joins.** Two conflicts close together become one region in the default style when the lines between them are three or fewer, or have no letters or digits (for example a closing brace). Diff3 keeps them apart.

Points 2 and 3 change how many regions a file has, so `conflict_index` stops lining up and the index join compares the wrong regions. In the final dataset, 5,547 of 17,526 files have a different region count in the two datasets.

Evidence that this is the cause: for every region we computed its line position on the ours side and on the theirs side, which is the same in both styles. On the 14,660 regions that already matched, the positions agree for 14,457 (98.6 percent), so position matching works. Of the 25,967 AgenticFlict regions that have no diff3 region with the same identifier, 25,947 (99.9 percent) overlap a diff3 region by position. They are the same conflicts, numbered differently.

## How the hashes were made to match

Each step is a real hash match. A region counts as verified only when the SHA-256 of both its ours text and its theirs text equal the AgenticFlict hashes. The steps run in order and each one only looks at regions the earlier steps left.

1. **Same identifier.** The stored hashes match under the same `(pr_key, file_path, conflict_index)`. This is the original check.
2. **Other index in the same file.** The stored hash pair matches some AgenticFlict region of the same file. This fixes the shifted indexes.
3. **Re-merge in the default style.** Each diff3 region holds its own base, ours and theirs text. We run `git merge-file` on those three texts with the default conflict style (Git 2.49). Git itself trims and splits the conflict. Every region it produces must match a hash of the same file.
4. **Joined regions.** Where AgenticFlict has one region and diff3 has several, we place the diff3 text on its side line positions inside the AgenticFlict region. The lines between the diff3 regions are not stored anywhere in our data, but their count is known from the positions. When there are one to three of them, we try lines with no letters or digits taken from the dataset itself (6,702 such lines in the final dataset). A guess counts only if both the ours and the theirs hash match. A wrong guess cannot match a SHA-256, so a match is verification, not an estimate.

## Results

Running share verified after each step.

| After step | Final dataset (54,641) | .ts and .tsx (27,690) | Eligible pool (35,241) | .ts and .tsx (17,979) |
|---|---|---|---|---|
| 1. same identifier | 14,660 (26.8%) | 11,339 (40.9%) | 10,217 (29.0%) | 7,790 (43.3%) |
| 2. other index | 22,843 (41.8%) | 13,126 (47.4%) | 14,906 (42.3%) | 8,926 (49.6%) |
| 3. re-merge | 37,906 (69.4%) | 20,561 (74.3%) | 24,440 (69.4%) | 13,358 (74.3%) |
| 4. joined regions | **41,087 (75.2%)** | **22,504 (81.3%)** | **26,620 (75.5%)** | **14,667 (81.6%)** |

The report gives 11,339 of 27,690 as 41.0 percent. It is 40.95 percent, so 40.9 to one decimal.

## What is left

Final dataset, 13,554 regions (24.8 percent) not hash verified.

| Reason | Regions | Share |
|---|---|---|
| Joined region, gap of one to three lines not found (the gap holds letters or digits, so it cannot be guessed) | 6,765 | 12.4% |
| Joined region, gap longer than three lines | 5,445 | 10.0% |
| Re-merge matches only some of the pieces | 559 | 1.0% |
| No joined AgenticFlict region found | 303 | 0.6% |
| Joined region, the gap size differs between ours and theirs | 237 | 0.4% |
| Re-merge gives no conflict | 207 | 0.4% |
| No base text, so no re-merge | 35 | 0.1% |
| Other | 3 | 0.0% |

About 22.4 percent of the final dataset (12,210 regions) sits inside a joined AgenticFlict region and only lacks the lines between the conflicts. Only 1,344 regions (2.5 percent) are not explained by the boundary effect.

Eligible pool: 8,621 regions (24.5 percent) left, of which 7,746 are joined regions with an unknown gap.

## Limits of the claim

- Steps 3 and 4 verify the lines that lie inside the default style region. The edge lines Git trims are identical on both sides and are outside the AgenticFlict hash, so the hash says nothing about them.
- A region the re-merge fails to match is not evidence of wrong text. Re-merging three snippets without the rest of the file can line up lines differently from a whole file merge.
- The base text is still outside the claim, since AgenticFlict has no base hash.
- The gap lines in step 4 come from the dataset itself. They are search candidates, never stored as data.

## What is left to do to verify more

Everything left needs the lines around the regions, which only the repositories hold.

1. Re-clone the repositories of the pull requests that still have unverified regions, merge again in the default style and hash the full regions. This would cover the joined regions (22.4 percent). It needs network and disk, and takes about as long as the original reconstruction for those repositories.
2. If the full re-clone is too slow, do it on a seeded random sample of about 50 pull requests and report the match rate as an estimate for the rest.
3. Check the 303 regions with no joined AgenticFlict region and the 559 partly matched ones by hand on a few examples.

## How to rerun

```
python scripts/verify_diff3_hashes.py AgenticFlict/data/clean/agenticflict_regions_clean.csv AgenticFlict/data/reproduced_aneeza_success.jsonl AgenticFlict/data/reproduced_fatima_success.jsonl
python scripts/verify_diff3_hashes.py AgenticFlict/data/clean/agenticflict_regions_clean.csv data/raw/final_dataset.jsonl
```

Each run takes about 10 to 15 minutes on Aneeza's laptop. It needs `git` on the path. The re-merge runs in a system temp folder that is deleted at the end.
