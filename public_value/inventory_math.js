/**
 * CropCircuit equipment-parts inventory math.
 * Reorder logic uses only user-supplied on-hand and threshold values.
 */

function finiteOrNull(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function nonnegative(value) {
  const n = finiteOrNull(value);
  return n === null ? null : Math.max(n, 0);
}

export function partStockStatus({
  quantityOnHand,
  reorderThreshold,
  preferredOrderQuantity = null,
}) {
  const onHand = nonnegative(quantityOnHand);
  const threshold = nonnegative(reorderThreshold);
  const orderQty = preferredOrderQuantity === null || preferredOrderQuantity === undefined || preferredOrderQuantity === ""
    ? null
    : nonnegative(preferredOrderQuantity);

  if (onHand === null || threshold === null) {
    return {
      configured: false,
      status: "not-configured",
      quantityOnHand: onHand,
      reorderThreshold: threshold,
      suggestedOrderQuantity: null,
    };
  }

  const needsReorder = onHand <= threshold;
  const minimumToExceedThreshold = needsReorder
    ? Math.max(threshold + 1 - onHand, 0)
    : 0;

  return {
    configured: true,
    status: needsReorder ? "reorder" : "ok",
    quantityOnHand: onHand,
    reorderThreshold: threshold,
    suggestedOrderQuantity: needsReorder
      ? Math.max(orderQty ?? minimumToExceedThreshold, minimumToExceedThreshold)
      : 0,
  };
}

export function summarizePartInventory(parts) {
  let total = 0;
  let configured = 0;
  let reorder = 0;
  let ok = 0;

  for (const part of parts ?? []) {
    total += 1;
    const status = partStockStatus({
      quantityOnHand: part.quantity_on_hand,
      reorderThreshold: part.reorder_threshold,
      preferredOrderQuantity: part.preferred_order_quantity,
    });
    if (!status.configured) continue;
    configured += 1;
    if (status.status === "reorder") reorder += 1;
    else ok += 1;
  }

  return {
    totalParts: total,
    configuredParts: configured,
    reorderParts: reorder,
    okParts: ok,
  };
}
