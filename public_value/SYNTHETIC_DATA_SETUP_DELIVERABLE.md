# Synthetic Assisted Data Setup — Example Deliverable

> **Demonstration only.** Every farm name, record, amount, part number, and operational detail below is fictional.

## Client

**Demo Farm:** Haven Field Farm  
**Source package received:** 3 files  
**Rows received:** 13  
**Workspace target:** CropCircuit Workspace 1.2

## 1. Source inventory

| Source | Rows | Intended destination | Result |
| --- | ---: | --- | --- |
| `demo_time_log.csv` | 6 | labor | mapped |
| `demo_operations.xlsx` | 5 | chores + maintenance + parts | mapped with one note |
| `demo_market_sales.csv` | 2 | direct-market sales | mapped |

No customer personal data, banking data, payroll data, credentials, or payment-card data were included.

## 2. Mapping summary

### Labor

Mapped:

- date → `date`
- work category → `category`
- activity → `task`
- minutes → `minutes`
- crew count → `workers`

Derived:

```text
worker_hours = minutes / 60 × workers
```

The original free-text activity is preserved.

### Chores

The source used `weekly` in lowercase.

It was normalized to:

```text
WEEKLY
```

No recurrence interval was invented; the supplied interval of 1 was preserved.

### Equipment maintenance

The source contained an oil-service interval supplied by the fictional operator.

CropCircuit stored the supplied interval; it did not replace it with a generic recommendation.

### Parts

One alternate filter number was present in the source.

It was preserved as an operator-entered cross reference. No compatibility claim was added.

### Sales

Gross amount, card fee, refund/discount, and entered direct cost were preserved as separate fields.

CropCircuit did not classify any value for tax/accounting purposes.

## 3. Ambiguity / quality notes

One equipment row said only:

```text
tractor filter
```

and did not identify whether it was the engine-oil, hydraulic, fuel, or air filter.

That row was **not** converted into a specific maintenance item.

It remains in the unresolved-items note for the operator to clarify.

## 4. Canonical outputs

Delivered:

- `labor.csv`
- `chore_schedule.csv`
- `equipment_maintenance.csv`
- `parts_inventory.csv`
- `sales.csv`
- `cropcircuit_workspace_1_2.json`

All canonical outputs use the published CropCircuit data contracts.

## 5. Coarse operations snapshot

Synthetic 7-day summary:

- labor entries: 6
- worker-hours: 11.47
- recurring chore templates: 3
- equipment-maintenance items: 2
- parts tracked: 2
- parts at/below operator-entered threshold: 1
- harvest entries: 0
- sales records: 2

Sales-dollar totals are intentionally omitted from the shareable snapshot in this example.

## 6. What changed

The setup changed **format**, not farm facts.

It:

- normalized column names;
- normalized supported recurrence values;
- calculated worker-hours where minutes and worker count were supplied;
- separated sales fields that were already present;
- collected compatible records into Workspace 1.2;
- documented one unresolved equipment description.

It did not:

- invent missing measurements;
- create accounting categories;
- recommend a machine service interval;
- assert substitute-part compatibility;
- infer harvest from sales;
- convert demo data into benchmark/customer evidence.

## 7. Suggested next use

The fictional operator could now:

1. open the Workspace Backup tool and restore the file;
2. inspect the Weekly Farm Operations Brief;
3. use the Labor Opportunity Analyzer on the cleaned labor records;
4. update equipment/parts records locally as work happens;
5. export a new Workspace backup periodically.

## Delivery check

- [x] inputs accounted for
- [x] ambiguous field documented
- [x] canonical files created
- [x] Workspace created
- [x] snapshot created
- [x] no private/financial credentials present
- [x] no hidden domain assumptions added
- [x] synthetic data clearly labeled
