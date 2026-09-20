# Synthetic delivery note — Assisted Farm Data Setup

> Demonstration only. All records and identifiers in this case study are fictional.

## Source inventory

| Source | Rows | Target |
| --- | ---: | --- |
| source_labor_messy.csv | 5 | labor |
| source_sales_messy.csv | 2 | sales |
| source_equipment_messy.csv | 3 | maintenance + parts |

## Transformations

- normalized dates into YYYY-MM-DD;
- renamed source columns into CropCircuit canonical fields;
- calculated worker-hours from supplied minutes × worker count;
- attached canonical chore codes to the five unambiguous labor tasks;
- stripped currency symbols/commas from numeric sales fields;
- split maintenance and parts records from the equipment sheet;
- preserved the alternate part number exactly as supplied;
- created Workspace 1.2;
- generated a coarse Operations Snapshot with sales dollars excluded.

## Unresolved item

One source row said only:

```text
Demo Tractor,tractor filter
```

The source did not identify whether that meant engine-oil, hydraulic, fuel, air, transmission, or another filter.

That row was omitted rather than guessed.

## Outputs

- labor.csv
- sales.csv
- equipment_maintenance.csv
- parts_inventory.csv
- workspace.json
- operations_snapshot.json

## Domain boundaries

No service interval was invented.  
No substitute-part compatibility was asserted.  
No accounting/tax category was inferred.  
No harvest quantity was inferred from sales.  
No customer data or payment-card data was included.
