"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import {
  calculateTotalRevenue,
  type RevenueResult,
} from "@/app/lib/revenue";
import {
  HistoryCard,
  LogsCard,
  QualityCard,
  SourcesCard,
  type HistoryEntry,
  type LogEntry,
} from "@/app/components/exflow-sections";

type Mode = "live" | "demo";
type LogTone = LogEntry["tone"];

const HISTORY_KEY = "exflow-history";
const HISTORY_EVENT = "exflow-history-change";
const EMPTY_HISTORY = "[]";

const DEMO_RATES = { EUR: "0.92", RUB: "90.00" };
const DEMO_SOURCE_ONE = {
  transactions: [
    { type: "paid", amount: 1250, currency: "USD" },
    { type: "paid", amount: 920, currency: "EUR" },
    { type: "paid", amount: 45000, currency: "RUB" },
    { type: "pending", amount: 190, currency: "USD" },
  ],
};
const DEMO_SOURCE_TWO = ["680 USD", "368 eur", "12000 RUB", "400 XYZ"];

export const moneyFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const subscribeToHistory = (callback: () => void) => {
  window.addEventListener("storage", callback);
  window.addEventListener(HISTORY_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(HISTORY_EVENT, callback);
  };
};

const getHistorySnapshot = () =>
  localStorage.getItem(HISTORY_KEY) ??
  localStorage.getItem("finora-history") ??
  EMPTY_HISTORY;

const parseHistory = (snapshot: string): HistoryEntry[] => {
  try {
    const value: unknown = JSON.parse(snapshot);
    return Array.isArray(value) ? (value as HistoryEntry[]).slice(0, 6) : [];
  } catch {
    return [];
  }
};

const saveHistory = (entries: HistoryEntry[]) => {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
  window.dispatchEvent(new Event(HISTORY_EVENT));
};

const currentTime = () =>
  new Date().toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

const isRevenueResult = (value: unknown): value is RevenueResult => {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<RevenueResult>;
  return (
    typeof candidate.total === "number" &&
    candidate.currency === "USD" &&
    typeof candidate.processed === "number" &&
    typeof candidate.skipped === "number" &&
    Array.isArray(candidate.sources) &&
    Array.isArray(candidate.currencies) &&
    Array.isArray(candidate.warnings)
  );
};

const getApiError = (value: unknown, fallback: string) => {
  if (
    value &&
    typeof value === "object" &&
    "error" in value &&
    typeof value.error === "string"
  ) {
    return value.error;
  }
  return fallback;
};

export function ExflowDashboard() {
  const historySnapshot = useSyncExternalStore(
    subscribeToHistory,
    getHistorySnapshot,
    () => EMPTY_HISTORY,
  );
  const history = useMemo(
    () => parseHistory(historySnapshot),
    [historySnapshot],
  );
  const [result, setResult] = useState<RevenueResult | null>(null);
  const [mode, setMode] = useState<Mode | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("Готов к синхронизации");
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: "initial",
      time: "00:00",
      message: "Система готова к работе",
      tone: "default",
    },
  ]);
  const [toast, setToast] = useState("");
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const consoleRef = useRef<HTMLDivElement>(null);
  const cursorGlowRef = useRef<HTMLDivElement>(null);

  const addLog = useCallback((message: string, tone: LogTone = "default") => {
    setLogs((items) => [
      ...items,
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        time: currentTime(),
        message,
        tone,
      },
    ]);
  }, []);

  useEffect(() => {
    consoleRef.current?.scrollTo({
      top: consoleRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [logs]);

  useEffect(() => {
    const glow = cursorGlowRef.current;
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (!glow || !finePointer || reducedMotion) return;

    const position = {
      currentX: window.innerWidth / 2,
      currentY: window.innerHeight / 3,
      targetX: window.innerWidth / 2,
      targetY: window.innerHeight / 3,
    };
    let animationFrame = 0;

    const followPointer = () => {
      position.currentX += (position.targetX - position.currentX) * 0.075;
      position.currentY += (position.targetY - position.currentY) * 0.075;
      glow.style.setProperty("--glow-x", `${position.currentX}px`);
      glow.style.setProperty("--glow-y", `${position.currentY}px`);
      animationFrame = window.requestAnimationFrame(followPointer);
    };
    const handlePointerMove = (event: PointerEvent) => {
      position.targetX = event.clientX;
      position.targetY = event.clientY;
      glow.classList.add("is-active");
    };
    const handlePointerLeave = () => glow.classList.remove("is-active");

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    document.documentElement.addEventListener("mouseleave", handlePointerLeave);
    animationFrame = window.requestAnimationFrame(followPointer);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("pointermove", handlePointerMove);
      document.documentElement.removeEventListener(
        "mouseleave",
        handlePointerLeave,
      );
    };
  }, []);

  useEffect(
    () => () => {
      if (toastTimer.current) clearTimeout(toastTimer.current);
    },
    [],
  );

  const showToast = (message: string) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(message);
    toastTimer.current = setTimeout(() => setToast(""), 2200);
  };

  const commitResult = (nextResult: RevenueResult, nextMode: Mode) => {
    setResult(nextResult);
    setMode(nextMode);
    setError(null);
    setUpdatedAt(currentTime());
    nextResult.warnings.forEach((warning) =>
      addLog(`${warning} — операция пропущена`, "warning"),
    );
    addLog(
      `Готово: ${moneyFormatter.format(nextResult.total)} ${nextResult.currency}`,
      "success",
    );

    const entry: HistoryEntry = {
      id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
      mode: nextMode,
      total: nextResult.total,
      currency: nextResult.currency,
      processed: nextResult.processed,
      skipped: nextResult.skipped,
      timestamp: Date.now(),
    };
    saveHistory([entry, ...history].slice(0, 6));
  };

  const runLive = async () => {
    setError(null);
    setLoading(true);
    setLoadingLabel("Получаем данные…");
    addLog("Запрашиваем транзакции и актуальные курсы");

    try {
      const response = await fetch("/api/exflow", { cache: "no-store" });
      const data: unknown = await response.json();

      if (!response.ok || !isRevenueResult(data)) {
        throw new Error(
          getApiError(
            data,
            `Сервис временно недоступен (код ${response.status}).`,
          ),
        );
      }

      addLog("Оба источника ответили успешно", "success");
      commitResult(data, "live");
      setLoadingLabel("Синхронизация завершена");
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Неизвестная ошибка. Попробуйте повторить запрос.";
      setError(message);
      setLoadingLabel("Ошибка подключения");
      addLog(message, "error");
    } finally {
      setLoading(false);
    }
  };

  const runDemo = () => {
    setError(null);
    setLoading(true);
    setLoadingLabel("Запускаем демо…");
    addLog("Загружен демонстрационный набор из двух источников");

    window.setTimeout(() => {
      const demoResult = calculateTotalRevenue(
        DEMO_SOURCE_ONE,
        DEMO_SOURCE_TWO,
        DEMO_RATES,
      );
      commitResult(demoResult, "demo");
      setLoading(false);
      setLoadingLabel("Демонстрация завершена");
    }, 550);
  };

  const copyResult = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(
        `ExFlow: ${moneyFormatter.format(result.total)} ${result.currency} · ${result.processed} операций`,
      );
      showToast("Результат скопирован");
    } catch {
      showToast("Браузер запретил доступ к буферу");
    }
  };

  const exportHistory = () => {
    if (!history.length) return;
    const rows = [
      ["mode", "total", "currency", "processed", "skipped", "timestamp"],
      ...history.map((item) => [
        item.mode,
        item.total,
        item.currency,
        item.processed,
        item.skipped,
        new Date(item.timestamp).toISOString(),
      ]),
    ];
    const csv = rows.map((row) => row.join(",")).join("\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = `exflow-history-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    showToast("CSV-файл сохранён");
  };

  const connectionState = error
    ? "error"
    : loading
      ? "loading"
      : result
        ? "done"
        : "ready";

  return (
    <>
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >
        <div className="ambient ambient-a" />
        <div className="ambient ambient-b" />
        <div className="ambient ambient-c" />
        <div ref={cursorGlowRef} className="cursor-glow" />
        <div className="noise" />
      </div>

      <div className="app-shell relative mx-auto min-h-screen w-full max-w-[1500px] px-3 pb-8 pt-3 sm:px-6 sm:pb-10 sm:pt-5 xl:px-10">
        <header className="glass topbar flex h-16 items-center justify-between rounded-[22px] px-3.5 sm:px-5">
          <a
            href="#content"
            className="group flex items-center gap-3"
            aria-label="ExFlow — к финансовому радару"
          >
            <span className="logo-mark" aria-hidden="true">
              <i className="logo-ribbon logo-ribbon-a" />
              <i className="logo-ribbon logo-ribbon-b" />
              <b className="logo-core" />
            </span>
            <span>
              <span className="brand-name block text-[16px] font-semibold tracking-[-0.04em]">
                <span>Ex</span>Flow
              </span>
              <span className="hidden text-[10px] font-medium uppercase tracking-[0.16em] text-white/35 sm:block">
                Revenue intelligence
              </span>
            </span>
          </a>
          <ConnectionStatus state={connectionState} label={loadingLabel} />
        </header>

        <main
          id="content"
          className="mt-3 grid gap-3 sm:mt-4 sm:gap-4 lg:grid-cols-[minmax(0,1.48fr)_minmax(340px,0.72fr)]"
        >
          <section className="glass hero-card relative min-h-[520px] overflow-hidden rounded-[28px] p-5 sm:min-h-[540px] sm:rounded-[32px] sm:p-8 lg:p-10">
            <div className="hero-spectral" aria-hidden="true" />
            <div className="relative z-10 flex h-full min-h-[480px] flex-col sm:min-h-[476px]">
              <div className="flex flex-wrap items-center gap-2">
                <span className="eyebrow">
                  <span className="signal-dot" /> Финансовый радар
                </span>
                <span className="eyebrow text-white/40">
                  {mode === "live"
                    ? "API · актуальные данные"
                    : mode === "demo"
                      ? "Демо · тестовые данные"
                      : "Выберите режим"}
                </span>
              </div>

              <div className="mt-9 max-w-3xl sm:mt-12">
                <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.22em] text-white/35 sm:text-xs">
                  Совокупная выручка
                </p>
                <div className="metric-row flex flex-wrap items-end gap-x-3 gap-y-3 sm:gap-x-4">
                  <span
                    key={`${mode}-${result?.total ?? 0}`}
                    className={`metric-value ${result ? "result-pop" : ""}`}
                    data-compact={
                      moneyFormatter.format(result?.total ?? 0).length > 10
                    }
                  >
                    {moneyFormatter.format(result?.total ?? 0)}
                  </span>
                  <span className="currency-badge mb-1.5 px-3 py-1.5 text-xs font-semibold sm:mb-3 sm:text-sm">
                    {result?.currency ?? "USD"}
                  </span>
                </div>
                <div className="mt-4 flex min-h-6 flex-wrap items-center gap-x-3 gap-y-2 text-xs">
                  <span className="inline-flex items-center gap-2 font-medium text-white/45">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        error
                          ? "bg-rose-300 shadow-[0_0_8px_#fda4af]"
                          : result
                            ? "bg-emerald-300 shadow-[0_0_8px_#6ee7b7]"
                            : "bg-white/30"
                      }`}
                    />
                    {error
                      ? "Обновление не выполнено"
                      : result
                        ? "Расчёт успешно завершён"
                        : "Данные ещё не рассчитаны"}
                  </span>
                  {updatedAt && (
                    <span className="text-white/25">· {updatedAt}</span>
                  )}
                </div>
              </div>

              {error && (
                <div className="error-panel mt-6 rounded-2xl p-4" role="alert">
                  <div className="error-layout flex gap-3">
                    <span
                      className="error-icon mt-0.5 shrink-0"
                      aria-hidden="true"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-rose-100">
                        Не удалось обновить данные
                      </p>
                      <p className="mt-1 text-xs leading-5 text-rose-100/55">
                        {error}
                      </p>
                    </div>
                    <div className="error-actions flex shrink-0 flex-col items-end gap-2">
                      <button
                        className="retry-button"
                        type="button"
                        onClick={runLive}
                        disabled={loading}
                      >
                        Повторить API
                      </button>
                      <button
                        className="error-demo-button"
                        type="button"
                        onClick={runDemo}
                        disabled={loading}
                      >
                        Открыть пример
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-auto pt-8">
                <button
                  className={`primary-button group ${loading ? "is-loading" : ""}`}
                  type="button"
                  onClick={runLive}
                  disabled={loading}
                >
                  <span className="button-icon">
                    <span className="ui-icon icon-refresh" />
                  </span>
                  <span>Рассчитать данные API</span>
                  <span className="ui-icon icon-arrow ml-auto text-white/45 transition group-hover:translate-x-0.5" />
                </button>

                <ModeGuide loading={loading} onDemo={runDemo} />

                <div className="calculation-note mt-2.5 flex items-start gap-2.5">
                  <span className="calculation-icon" aria-hidden="true">
                    <i />
                    <i />
                    <i />
                  </span>
                  <p className="text-[10px] leading-4 text-white/28">
                    <strong className="font-semibold text-white/45">
                      Как считается:
                    </strong>{" "}
                    ExFlow берёт только оплаченные операции, переводит валюты в
                    USD и складывает результаты двух источников.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <aside className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <SourcesCard result={result} />
            <QualityCard result={result} />
          </aside>
        </main>

        <section className="mt-3 grid gap-3 sm:mt-4 sm:gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.52fr)]">
          <HistoryCard
            history={history}
            canCopy={Boolean(result)}
            onCopy={copyResult}
            onExport={exportHistory}
          />
          <LogsCard
            logs={logs}
            consoleRef={consoleRef}
            onClear={() => {
              setLogs([]);
              addLog("Журнал очищен");
            }}
          />
        </section>

        <footer className="flex flex-col items-center justify-between gap-2 px-2 pt-6 text-center text-[9px] uppercase tracking-[0.15em] text-white/20 min-[390px]:text-[10px] sm:flex-row sm:text-left">
          <span>ExFlow · Finance data normalized</span>
          <span>Next.js · React · TypeScript</span>
        </footer>
      </div>

      <div
        className={`toast ${toast ? "is-visible" : ""}`}
        role="status"
        aria-live="polite"
      >
        {toast}
      </div>
    </>
  );
}

function ConnectionStatus({
  state,
  label,
}: {
  state: "ready" | "loading" | "done" | "error";
  label: string;
}) {
  const dotClasses = {
    ready: "bg-emerald-400 shadow-[0_0_10px_#34d399]",
    loading: "animate-pulse bg-cyan-300 shadow-[0_0_10px_#67e8f9]",
    done: "bg-emerald-400 shadow-[0_0_10px_#34d399]",
    error: "bg-rose-400 shadow-[0_0_10px_#fb7185]",
  };
  const mobileLabel = {
    ready: "Ready",
    loading: "Sync",
    done: "Done",
    error: "Error",
  };

  return (
    <div className="status-capsule flex items-center gap-2 rounded-full px-2.5 py-2 sm:px-3">
      <span
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClasses[state]}`}
      />
      <span className="hidden text-[11px] font-medium text-white/55 min-[380px]:inline">
        {label}
      </span>
      <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-white/35 min-[380px]:hidden">
        {mobileLabel[state]}
      </span>
    </div>
  );
}

function ModeGuide({
  loading,
  onDemo,
}: {
  loading: boolean;
  onDemo: () => void;
}) {
  return (
    <div className="mode-guide mt-4 grid gap-2 sm:grid-cols-2">
      <article className="mode-guide-card mode-guide-live">
        <div className="flex items-center gap-2.5">
          <span className="guide-icon guide-icon-live" aria-hidden="true">
            <i />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <strong className="text-[11px] font-semibold text-white/75">
                Данные подключённых API
              </strong>
              <span className="guide-badge guide-badge-live">Live</span>
            </div>
            <p className="mt-1 text-[10px] leading-4 text-white/30">
              Операции с серверов и актуальные курсы. Это данные API, а не
              подтверждённая банковская выписка.
            </p>
          </div>
        </div>
      </article>

      <article className="mode-guide-card mode-guide-demo">
        <div className="flex items-center gap-2.5">
          <span className="guide-icon guide-icon-demo" aria-hidden="true" />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <strong className="text-[11px] font-semibold text-white/75">
                Тестовый пример
              </strong>
              <span className="guide-badge guide-badge-demo">Demo</span>
            </div>
            <p className="mt-1 text-[10px] leading-4 text-white/30">
              Готовый набор для знакомства с интерфейсом. Показанные суммы не
              являются реальными деньгами.
            </p>
            <button
              className="demo-link mt-2"
              type="button"
              onClick={onDemo}
              disabled={loading}
            >
              <span className="ui-icon icon-play" />
              Посмотреть пример
              <span className="ui-icon icon-arrow" />
            </button>
          </div>
        </div>
      </article>
    </div>
  );
}
