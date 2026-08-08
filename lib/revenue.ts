// Pure domain types and calculations shared by live and demo flows.
export type SourceOne = {
  transactions?: Array<{
    type?: unknown;
    amount?: unknown;
    currency?: unknown;
  }>;
};

export type SourceTwo = unknown[];
export type ExchangeRates = Record<string, string | number>;

export type RevenueSource = {
  id: "finance1" | "finance2";
  name: string;
  total: number;
};

export type RevenueResult = {
  total: number;
  currency: "USD";
  processed: number;
  skipped: number;
  currencies: string[];
  warnings: string[];
  sources: RevenueSource[];
};

const paidType = /^paid$/i;
const amountWithCurrency = /^(\d+(?:\.\d+)?)\s+([a-z]{3})$/i;

const roundMoney = (value: number) =>
  Math.round((value + Number.EPSILON) * 100) / 100;

export function calculateTotalRevenue(
  sourceOne: SourceOne,
  sourceTwo: SourceTwo,
  rates: ExchangeRates,
): RevenueResult {
  let processed = 0;
  let skipped = 0;
  const currencies = new Set<string>();
  const warnings = new Set<string>();

  const convertToUsd = (amount: number, code: string) => {
    const currencyCode = code.toUpperCase();
    currencies.add(currencyCode);

    if (currencyCode === "USD") return amount;

    const rate = Number(rates[currencyCode]);
    if (!Number.isFinite(rate) || rate <= 0) {
      skipped += 1;
      warnings.add(`Нет курса для ${currencyCode}`);
      return null;
    }

    return amount / rate;
  };

  let sourceOneTotal = 0;
  const transactions = Array.isArray(sourceOne.transactions)
    ? sourceOne.transactions
    : [];

  for (const transaction of transactions) {
    const type =
      typeof transaction?.type === "string" ? transaction.type : "";
    const code =
      typeof transaction?.currency === "string" ? transaction.currency : "";
    const amount = transaction?.amount;

    if (
      !paidType.test(type) ||
      typeof amount !== "number" ||
      !Number.isFinite(amount) ||
      !code
    ) {
      skipped += 1;
      continue;
    }

    const converted = convertToUsd(amount, code);
    if (converted === null) continue;

    processed += 1;
    sourceOneTotal += converted;
  }

  let sourceTwoTotal = 0;
  for (const entry of Array.isArray(sourceTwo) ? sourceTwo : []) {
    const match =
      typeof entry === "string" ? entry.match(amountWithCurrency) : null;

    if (!match) {
      skipped += 1;
      continue;
    }

    const converted = convertToUsd(Number(match[1]), match[2]);
    if (converted === null) continue;

    processed += 1;
    sourceTwoTotal += converted;
  }

  sourceOneTotal = roundMoney(sourceOneTotal);
  sourceTwoTotal = roundMoney(sourceTwoTotal);

  return {
    total: roundMoney(sourceOneTotal + sourceTwoTotal),
    currency: "USD",
    processed,
    skipped,
    currencies: [...currencies].sort(),
    warnings: [...warnings],
    sources: [
      {
        id: "finance1",
        name: "Transactions API",
        total: sourceOneTotal,
      },
      { id: "finance2", name: "Payouts API", total: sourceTwoTotal },
    ],
  };
}
