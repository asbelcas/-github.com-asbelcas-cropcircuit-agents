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

export const WORKSPACE_VERSION: "1.0";

export const WORKSPACE_KEYS: Readonly<{
  laborEntries: string;
  laborSettings: string;
  choreSchedule: string;
}>;

export interface CropCircuitWorkspace {
  schema_version: "1.0";
  exported_at?: string;
  labor_entries: Array<Record<string, unknown>>;
  labor_settings: Record<string, unknown>;
  chore_schedule: Array<Record<string, unknown>>;
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
};
