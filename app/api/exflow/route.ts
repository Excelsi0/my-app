import { NextResponse } from "next/server";
import {
  calculateTotalRevenue,
  type ExchangeRates,
  type SourceOne,
  type SourceTwo,
} from "@/lib/revenue";

export const dynamic = "force-dynamic";

const requestJson = async <T>(url: string, init?: RequestInit): Promise<T> => {
  let response: Response;

  try {
    response = await fetch(url, {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
  } catch (error) {
    if (error instanceof Error && error.name === "TimeoutError") {
      throw new Error("Сервер не ответил за 15 секунд. Попробуйте ещё раз.");
    }
    throw new Error(
      "Не удалось подключиться к серверу. Проверьте интернет-соединение.",
    );
  }

  if (!response.ok) {
    throw new Error(`Сервис временно недоступен (код ${response.status}).`);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new Error("Сервер вернул данные в неизвестном формате.");
  }
};

export async function GET() {
  const financeApiKey = process.env.EXFLOW_FINANCE_API_KEY;
  const ratesApiKey = process.env.EXFLOW_RATES_API_KEY;

  if (!financeApiKey || !ratesApiKey) {
    return NextResponse.json(
      {
        error:
          "Для live-режима не настроены серверные ключи EXFLOW_FINANCE_API_KEY и EXFLOW_RATES_API_KEY.",
      },
      { status: 503 },
    );
  }

  try {
    const headers = { "x-api-key": financeApiKey };
    const [dataOne, dataTwo, ratesData] = await Promise.all([
      requestJson<SourceOne>(
        "https://cpa-server-vtel.onrender.com/api/finance1",
        { headers },
      ),
      requestJson<SourceTwo>(
        "https://cpa-server-vtel.onrender.com/api/finance2",
        { headers },
      ),
      requestJson<{ rates?: ExchangeRates }>(
        `https://api.currencyfreaks.com/v2.0/rates/latest?apikey=${encodeURIComponent(ratesApiKey)}`,
      ),
    ]);

    if (!ratesData.rates) {
      throw new Error(
        "Сервис курсов валют не вернул актуальные котировки.",
      );
    }

    return NextResponse.json(
      calculateTotalRevenue(dataOne, dataTwo, ratesData.rates),
      {
        headers: { "Cache-Control": "no-store" },
      },
    );
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Неизвестная ошибка. Попробуйте повторить запрос.";

    return NextResponse.json({ error: message }, { status: 502 });
  }
}
