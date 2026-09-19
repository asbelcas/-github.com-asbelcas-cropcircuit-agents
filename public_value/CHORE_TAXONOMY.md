# CropCircuit Open Farm Chore Taxonomy

Farm labor logs become much more useful when "move fence," "move temp fence," and "portable fencing" can be recognized as the same kind of work.

This taxonomy provides a small controlled vocabulary for normalizing repeated farm tasks.

## Goals

- simple enough for a small farm to use
- human-readable codes
- stable enough for benchmark tooling
- broad enough to cover mixed farms
- extensible when real usage shows a missing task
- neutral about whether a task is "good" or "bad"

## Example codes

```text
livestock.feed
livestock.move_rotate
crops.weeding
crops.harvest
washpack.pack
fencing.move
water.system_check
maintenance.equipment
sales.market_selling
admin.recordkeeping
general.travel_internal
```

## What the taxonomy does not do

It does not prescribe how work should be performed.

It does not encode:

- productivity targets
- animal-care standards
- agronomic rates
- wage assumptions
- "efficient" task times
- equipment recommendations

It is a naming layer.

## Versioning

Current version: **0.1.0**

Codes should remain stable inside a major version. New codes can be added as real farms expose missing concepts.

Deprecated codes should be mapped to a replacement rather than silently changing meaning.

## Machine-readable files

- `farm_chore_taxonomy.json`
- `farm_chore_taxonomy.schema.json`
- `validate_chore_taxonomy.mjs`

## Mapper

`chore_taxonomy_mapper.html` imports a CropCircuit labor-log CSV, groups distinct free-text task names, lets the operator assign canonical codes, and exports an enriched CSV.

Nothing is uploaded.

## License

The CropCircuit-authored taxonomy structure and labels are dedicated under CC0 1.0 to the extent CropCircuit holds rights in them. The goal is interoperability, not lock-in.
