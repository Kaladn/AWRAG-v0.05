# Native-Aware Formula Rework

This corrects the earlier report-side formula layering after exposing the current AW topK position key.

## Locked Definition

```text
Native AW weight number = score
Native AW ranking decision = sort by direct_hit_count desc, density_score desc, score desc, block_ordinal asc
```

So:

```text
score = native weight number
rank = position after sorting by the full native topK key
```

## Corrected Layering

1. Native decision: compare candidates by the full topK sort key.
2. Native weight: expose `score` as the native AW weight number inside that key.
3. Secondary explanation: use the previous weighted field formula only as after-the-fact interpretation.

The previous report-side formula is not AW native scoring and must not be used as the ranking truth.

## Native Decision Counts

- aw_rank1_outranks_gold_by_native_key: 10

## Secondary Explanation Alignment

- secondary_explanation_does_not_support_native_choice: 3
- secondary_explanation_supports_native_choice: 6
- secondary_explanation_unclear: 1

## Cases

| QID | Native Decision | AW Doc | AW Direct | AW Density | AW Score | Gold Doc | Gold Rank | Gold Direct | Gold Density | Gold Score | Secondary Explanation |
|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| 870 | aw_rank1_outranks_gold_by_native_key | 11414664 | 3 | 1.379810097558122 | 13.017102426184504 | 195689316 | 1428 | 0 | 0.023675635857724607 | 0.4782244025279039 | secondary_explanation_does_not_support_native_choice |
| 623 | aw_rank1_outranks_gold_by_native_key | 25599283 | 9 | 1.787779631303737 | 26.757035453566484 | 17000834 | 229 | 3 | 1.0911880564130296 | 14.435061154363979 | secondary_explanation_supports_native_choice |
| 1199 | aw_rank1_outranks_gold_by_native_key | 7454794 | 9 | 3.2283969737558147 | 38.06223897515282 | 16760369 | 1667 | 2 | 0.19634062183474302 | 3.440165608399288 | secondary_explanation_supports_native_choice |
| 1280 | aw_rank1_outranks_gold_by_native_key | 29214508 | 7 | 6.617265189479794 | 95.89328289019633 | 4387784 | 673 | 1 | 0.7773417841369994 | 10.965755314783081 | secondary_explanation_does_not_support_native_choice |
| 783 | aw_rank1_outranks_gold_by_native_key | 8246922 | 7 | 3.3105551555447046 | 46.229386870163076 | 40632104 | 351 | 2 | 0.5798462089109786 | 7.288553828172817 | secondary_explanation_supports_native_choice |
| 508 | aw_rank1_outranks_gold_by_native_key | 25516011 | 5 | 3.574917271697241 | 25.779095057292462 | 13980338 | 55 | 3 | 0.7809438012367963 | 9.140712840613375 | secondary_explanation_supports_native_choice |
| 560 | aw_rank1_outranks_gold_by_native_key | 28015516 | 9 | 1.256130779278532 | 16.474000727205077 | 40096222 | 390 | 5 | 0.5621358451359353 | 7.499827604207393 | secondary_explanation_supports_native_choice |
| 1281 | aw_rank1_outranks_gold_by_native_key | 29214508 | 3 | 2.228312659306519 | 32.291318254314035 | 4387784 | 3964 | 0 | 0.01364178427020811 | 0.19244104899138487 | secondary_explanation_does_not_support_native_choice |
| 830 | aw_rank1_outranks_gold_by_native_key | 52873726 | 10 | 2.6517063790847817 | 35.57637432002039 | 1897324 | 642 | 4 | 1.231589724039946 | 14.779076688479352 | secondary_explanation_supports_native_choice |
| 1110 | aw_rank1_outranks_gold_by_native_key | 756887 | 4 | 2.514508535963073 | 34.84205232282941 | 13770184 | 2705 | 1 | 0.08291567414938497 | 1.9847871846265341 | secondary_explanation_unclear |

## Guardrails

- No backend formula change.
- No anchorization change.
- No stop-word or regex change.
- No report-side formula treated as native AW weight.
- No hardcoded wins or hand-labeled outcomes.
- Native decision derives from the exposed topK sort key fields.
