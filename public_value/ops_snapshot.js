/**
 * CropCircuit operations snapshot helpers.
 * Produces coarse, shareable summaries from Workspace 1.2 data.
 * Free-text notes and raw transaction/task rows are deliberately excluded.
 */

function round(value, places = 2) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

function inRange(date, startDate, endDate) {
  const d = String(date ?? "");
  if (startDate && d < startDate) return false;
  if (endDate && d > endDate) return false;
  return true;
}

function laborHours(row) {
  const direct = Number(row?.worker_hours);
  if (Number.isFinite(direct) && direct >= 0) return direct;
  const minutes = Number(row?.minutes);
  const workers = Number(row?.workers);
  if (!Number.isFinite(minutes) || !Number.isFinite(workers) || minutes < 0 || workers < 0) return 0;
  return minutes / 60 * workers;
}

export function buildOperationsSnapshot(workspace, {
  startDate = null,
  endDate = null,
  includeSalesDollars = false,
} = {}) {
  const labor = (workspace?.labor_entries ?? []).filter(r => inRange(r.date,startDate,endDate));
  const harvest = (workspace?.harvest_entries ?? []).filter(r => inRange(r.date,startDate,endDate));
  const sales = (workspace?.sales_entries ?? []).filter(r => inRange(r.date,startDate,endDate));
  const maintenance = Array.isArray(workspace?.equipment_maintenance) ? workspace.equipment_maintenance : [];
  const parts = Array.isArray(workspace?.parts_inventory) ? workspace.parts_inventory : [];
  const chores = Array.isArray(workspace?.chore_schedule) ? workspace.chore_schedule : [];

  const laborByCategory = new Map();
  let totalWorkerHours = 0;

  for (const row of labor) {
    const category = String(row?.category ?? "Other").trim() || "Other";
    const hours = laborHours(row);
    totalWorkerHours += hours;
    const bucket = laborByCategory.get(category) ?? { entries:0, worker_hours:0 };
    bucket.entries += 1;
    bucket.worker_hours += hours;
    laborByCategory.set(category,bucket);
  }

  const laborCategories = [...laborByCategory.entries()]
    .map(([category,v]) => ({
      category,
      entries:v.entries,
      worker_hours:round(v.worker_hours,2),
      share_percent: totalWorkerHours > 0 ? round(v.worker_hours/totalWorkerHours*100,1) : 0,
    }))
    .sort((a,b)=>b.worker_hours-a.worker_hours);

  const harvestByItemUnit = new Map();
  for (const row of harvest) {
    const item=String(row?.item ?? row?.crop ?? "").trim();
    const unit=String(row?.unit ?? "").trim();
    const quantity=Number(row?.quantity);
    if(!item||!unit||!Number.isFinite(quantity)||quantity<0) continue;
    const key=item.toLowerCase()+"\u0000"+unit.toLowerCase();
    const bucket=harvestByItemUnit.get(key)??{item,unit,entries:0,quantity:0};
    bucket.entries+=1;bucket.quantity+=quantity;harvestByItemUnit.set(key,bucket);
  }

  const harvestSummary=[...harvestByItemUnit.values()]
    .map(x=>({...x,quantity:round(x.quantity,3)}))
    .sort((a,b)=>a.item.localeCompare(b.item)||a.unit.localeCompare(b.unit));

  const salesByChannel = new Map();
  for (const row of sales) {
    const channel=String(row?.channel??"Unspecified").trim()||"Unspecified";
    const gross=Math.max(Number(row?.gross_amount)||0,0);
    const fees=Math.max(Number(row?.payment_fees)||0,0);
    const refunds=Math.max(Number(row?.refunds_discounts)||0,0);
    const direct=Math.max(Number(row?.direct_costs)||0,0);
    const bucket=salesByChannel.get(channel)??{channel,records:0,gross:0,net:0,direct:0};
    bucket.records+=1;
    bucket.gross+=gross;
    bucket.net+=gross-fees-refunds;
    bucket.direct+=direct;
    salesByChannel.set(channel,bucket);
  }

  const salesChannels=[...salesByChannel.values()]
    .map(x=>includeSalesDollars?{
      channel:x.channel,
      records:x.records,
      gross_amount:round(x.gross),
      net_receipts:round(x.net),
      direct_costs_entered:round(x.direct),
    }:{
      channel:x.channel,
      records:x.records,
    })
    .sort((a,b)=>b.records-a.records);

  const maintenanceConfigured=maintenance.filter(x=>
    Number.isFinite(Number(x?.interval_hours)) ||
    Number.isFinite(Number(x?.interval_days))
  ).length;

  const partsConfigured=parts.filter(x=>
    String(x?.quantity_on_hand??"").trim()!=="" &&
    String(x?.reorder_threshold??"").trim()!==""
  );
  const partsAtOrBelowThreshold=partsConfigured.filter(x=>
    Number(x.quantity_on_hand) <= Number(x.reorder_threshold)
  ).length;

  return {
    schema_version:"1.0",
    generated_at:new Date().toISOString(),
    period:{start_date:startDate,end_date:endDate},
    privacy:{
      raw_rows_included:false,
      free_text_notes_included:false,
      exact_dates_included:false,
      sales_dollars_included:Boolean(includeSalesDollars),
    },
    labor:{
      entries:labor.length,
      worker_hours:round(totalWorkerHours,2),
      categories:laborCategories,
    },
    chores:{
      recurring_templates:chores.length,
    },
    equipment:{
      maintenance_items:maintenance.length,
      maintenance_items_with_interval:maintenanceConfigured,
      parts_tracked:parts.length,
      parts_with_threshold:partsConfigured.length,
      parts_at_or_below_threshold:partsAtOrBelowThreshold,
    },
    harvest:{
      entries:harvest.length,
      totals_by_item_unit:harvestSummary,
    },
    sales:{
      records:sales.length,
      channels:salesChannels,
    },
  };
}
