export interface LaborRecord {
  date: string;
  category: string;
  task: string;
  chore_code?: string;
  minutes: number | string;
  workers: number | string;
  worker_hours?: number | string | null;
  notes?: string;
  [key: string]: unknown;
}

export interface ScheduleItem {
  task?: string;
  chore_code?: string;
  category?: string;
  first_date?: string;
  date?: string;
  frequency?: "ONCE" | "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY" | string;
  freq?: "ONCE" | "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY" | string;
  interval?: number | string;
  estimated_minutes?: number | string;
  minutes?: number | string;
  [key: string]: unknown;
}

export function annualTaskCost(args: {
  minutes: number;
  occurrencesPerWeek: number;
  weeksPerYear?: number;
  workers?: number;
  hourlyCost: number;
}): {
  annualHours: number;
  annualLaborCost: number;
};

export function simplePayback(args: {
  upfrontCost: number;
  annualSavings: number;
  annualAddedCost?: number;
  salvageValue?: number;
}): {
  netAnnualSavings: number;
  netCapitalAtRisk: number;
  paybackMonths: number | null;
};

export function fenceEstimate(args: {
  acres: number;
  installedCostPerFoot: number;
  shapeFactor?: number;
  internalFenceFeet?: number;
  gateCost?: number;
}): {
  squareSideFeet: number;
  baselinePerimeterFeet: number;
  outerFenceFeet: number;
  totalFenceFeet: number;
  estimatedCost: number;
};

export function waterStorage(args: {
  animals: number;
  gallonsPerAnimalPerDay: number;
  autonomyDays: number;
  reservePercent?: number;
}): {
  dailyDemandGallons: number;
  baseStorageGallons: number;
  recommendedStorageGallons: number;
};

export function breakEvenTransactions(args: {
  fixedCosts: number;
  averageSale: number;
  variableCostPerTransaction?: number;
}): {
  contributionPerTransaction: number;
  breakEvenTransactions: number | null;
  breakEvenGrossRevenue: number | null;
};

export function rectangleAcres(args: {
  lengthFeet: number;
  widthFeet: number;
}): {
  squareFeet: number;
  acres: number;
};

export function median(values: number[]): number | null;

export function summarizeSample(workerHoursPerOccurrence: number[]): {
  n: number;
  medianWorkerHours: number | null;
  meanWorkerHours: number | null;
  totalWorkerHours: number;
};

export function compareSamples(args: {
  baseline: number[];
  after: number[];
}): {
  baseline: ReturnType<typeof summarizeSample>;
  after: ReturnType<typeof summarizeSample>;
  medianChangeWorkerHours: number | null;
  medianChangePercent: number | null;
  direction: "less-labor" | "more-labor" | "no-change" | "insufficient-data";
};

export function annualizeObservedChange(args: {
  baselineMedianWorkerHours: number;
  afterMedianWorkerHours: number;
  occurrencesPerWeek: number;
  weeksPerYear?: number;
  hourlyCost: number;
  interventionCost?: number;
}): {
  hoursSavedPerOccurrence: number;
  annualHoursSaved: number;
  annualLaborValue: number;
  paybackMonths: number | null;
};

export function workerHours(args: {
  minutes: number | string;
  workers: number | string;
}): number | null;

export function normalizeLaborIdentity(record: Partial<LaborRecord>): {
  key: string;
  method: "chore_code" | "task_text" | "none";
  chore_code: string;
};

export function normalizeDate(value: unknown): string;

export function normalizeLaborRecord(
  input: Partial<LaborRecord>,
  options?: { calculateWorkerHours?: boolean }
): {
  date: string;
  category: string;
  task: string;
  chore_code: string;
  minutes: number | null;
  workers: number | null;
  worker_hours: number | null;
  notes: string;
};

export function validateLaborRecord(
  record: Partial<LaborRecord>,
  options?: {
    knownChoreCodes?: Set<string> | null;
    workerHourTolerance?: number;
  }
): string[];

export function expandScheduleItem(
  item: ScheduleItem,
  options: {
    startDate: string;
    endDate: string;
    maxOccurrences?: number;
  }
): string[];

export function buildDailyLoad(
  items: ScheduleItem[],
  options: {
    startDate: string;
    endDate: string;
  }
): Array<{
  date: string;
  total_estimated_minutes: number;
  tasks: Array<{
    task: string;
    chore_code: string;
    category: string;
    estimated_minutes: number;
  }>;
}>;

export const WORKSPACE_VERSION: "1.2";
export const SUPPORTED_WORKSPACE_VERSIONS: readonly ["1.0","1.1","1.2"];

export const WORKSPACE_KEYS: Readonly<{
  laborEntries: string;
  laborSettings: string;
  choreSchedule: string;
  equipmentMaintenance: string;
  harvestEntries: string;
  salesEntries: string;
  partsInventory: string;
}>;

export interface CropCircuitWorkspace {
  schema_version: "1.0" | "1.1" | "1.2";
  exported_at?: string;
  labor_entries: Array<Record<string, unknown>>;
  labor_settings: Record<string, unknown>;
  chore_schedule: Array<Record<string, unknown>>;
  equipment_maintenance?: Array<Record<string, unknown>>;
  harvest_entries?: Array<Record<string, unknown>>;
  sales_entries?: Array<Record<string, unknown>>;
  parts_inventory?: Array<Record<string, unknown>>;
}

export function readWorkspace(storage: Storage): CropCircuitWorkspace;
export function validateWorkspace(workspace: unknown): string[];
export function writeWorkspace(
  storage: Storage,
  workspace: CropCircuitWorkspace,
  options?: { mode?: "replace" | "merge" }
): {
  ok: boolean;
  errors: string[];
  labor_entries?: number;
  chore_schedule?: number;
  equipment_maintenance?: number;
  harvest_entries?: number;
  sales_entries?: number;
  parts_inventory?: number;
};

export function marketDayEconomics(args: {
  boothFee?: number;
  roundTripMiles?: number;
  vehicleCostPerMile?: number;
  travelHours?: number;
  setupHours?: number;
  sellingHours?: number;
  teardownHours?: number;
  workers?: number;
  hourlyLaborCost?: number;
  otherFixedCosts?: number;
  averageSale: number;
  variableCostPerSale?: number;
  cardFeePercent?: number;
  expectedTransactions?: number | null;
}): {
  totalWorkerHours: number;
  vehicleCost: number;
  laborCost: number;
  fixedDayCost: number;
  cardFeePerSale: number;
  contributionPerSale: number;
  breakEvenTransactions: number | null;
  breakEvenGrossRevenue: number | null;
  forecast: {
    transactions: number;
    grossRevenue: number;
    estimatedDayMargin: number;
  } | null;
};

export function csaEconomics(args: {
  plannedShares: number;
  pricePerShare: number;
  fixedSeasonCosts?: number;
  seasonLaborHours?: number;
  hourlyLaborCost?: number;
  variableCostPerShare?: number;
  paymentFeePercent?: number;
  targetSeasonSurplus?: number;
}): {
  laborCost: number;
  seasonFixedCost: number;
  contributionPerShare: number;
  breakEvenShares: number | null;
  targetShares: number | null;
  grossRevenue: number;
  paymentFees: number;
  variableCosts: number;
  modeledSeasonSurplus: number;
  requiredPricePerShare: number | null;
};

export function hourServiceStatus(args: {
  currentHours: number | string;
  lastServiceHours: number | string;
  intervalHours: number | string;
}): {
  configured: boolean;
  nextDueHours: number | null;
  hoursRemaining: number | null;
  status: "overdue" | "due" | "not-due" | "not-configured";
};

export function dateServiceStatus(args: {
  lastServiceDate: string;
  intervalDays: number | string;
  asOfDate: string;
}): {
  configured: boolean;
  nextDueDate: string | null;
  daysRemaining: number | null;
  status: "overdue" | "due" | "not-due" | "not-configured";
};

export function combinedServiceStatus(args: {
  currentHours?: number | string;
  lastServiceHours?: number | string;
  intervalHours?: number | string;
  lastServiceDate?: string;
  intervalDays?: number | string;
  asOfDate?: string;
}): {
  overall: "overdue" | "due" | "not-due" | "not-configured";
  hours: ReturnType<typeof hourServiceStatus>;
  date: ReturnType<typeof dateServiceStatus>;
};

export function summarizeHarvest(
  records: Array<{
    date?: string;
    item?: string;
    crop?: string;
    quantity?: number | string;
    unit?: string;
    [key: string]: unknown;
  }>,
  options?: { startDate?: string; endDate?: string }
): Array<{
  item: string;
  unit: string;
  entries: number;
  quantity: number;
}>;

export function compareHarvest(
  records: Array<{
    date?: string;
    item?: string;
    crop?: string;
    quantity?: number | string;
    unit?: string;
    [key: string]: unknown;
  }>,
  options: {
    periodA: { startDate: string; endDate: string };
    periodB: { startDate: string; endDate: string };
  }
): Array<{
  item: string;
  unit: string;
  quantityA: number;
  quantityB: number;
  change: number;
  changePercent: number | null;
}>;

export function salesRecordEconomics(record: {
  gross_amount?: number | string;
  payment_fees?: number | string;
  refunds_discounts?: number | string;
  direct_costs?: number | string;
}): {
  grossAmount: number;
  paymentFees: number;
  refundsDiscounts: number;
  directCosts: number;
  netReceipts: number;
  contributionAfterDirectCosts: number;
};

export function summarizeSales(
  records: Array<Record<string, unknown>>,
  options?: {
    startDate?: string | null;
    endDate?: string | null;
    groupBy?: string;
  }
): Array<{
  group: string;
  transactions: number;
  grossAmount: number;
  paymentFees: number;
  refundsDiscounts: number;
  directCosts: number;
  netReceipts: number;
  contributionAfterDirectCosts: number;
}>;

export function partStockStatus(args: {
  quantityOnHand: number | string;
  reorderThreshold: number | string;
  preferredOrderQuantity?: number | string | null;
}): {
  configured: boolean;
  status: "reorder" | "ok" | "not-configured";
  quantityOnHand: number | null;
  reorderThreshold: number | null;
  suggestedOrderQuantity: number | null;
};

export function summarizePartInventory(
  parts: Array<{
    quantity_on_hand?: number | string;
    reorder_threshold?: number | string;
    preferred_order_quantity?: number | string | null;
    [key: string]: unknown;
  }>
): {
  totalParts: number;
  configuredParts: number;
  reorderParts: number;
  okParts: number;
};

export function buildOperationsSnapshot(
  workspace: Record<string, unknown>,
  options?: {
    startDate?: string | null;
    endDate?: string | null;
    includeSalesDollars?: boolean;
  }
): Record<string, unknown>;
