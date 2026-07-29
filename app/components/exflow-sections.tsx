import type { RefObject } from "react";
import type { RevenueResult } from "@/app/lib/revenue";

export type HistoryEntry = {
  id: string;
  mode: "live" | "demo";
  total: number;
  currency: string;
  processed: number;
  skipped: number;
  timestamp: number;
};

export type LogEntry = {
  id: string;
  time: string;
  message: string;
  tone: "default" | "success" | "warning" | "error";
};

const moneyFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function SourcesCard({ result }: { result: RevenueResult | null }) {
  return (
    <section className="glass glass-card rounded-[26px] p-5 sm:rounded-[28px] sm:p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="section-label">Поток данных</p>
          <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">
            Структура выручки
          </h2>
        </div>
        <span className="data-chip">
          <span className="chip-spark" />2 источника
        </span>
      </div>
      <div className="mt-6 space-y-5">
        {!result ? (
          <>
            <div className="empty-line" />
            <div className="empty-line w-4/5" />
          </>
        ) : (
          result.sources.map((source, index) => {
            const percent =
              result.total > 0
                ? Math.round((source.total / result.total) * 100)
                : 0;
            return (
              <div key={source.id}>
                <div className="mb-2.5 flex items-center justify-between gap-4">
                  <div className="flex min-w-0 items-center gap-2.5">
                    <span
                      className={`h-2 w-2 shrink-0 rounded-full ${
                        index === 0
                          ? "bg-cyan-300 shadow-[0_0_9px_#67e8f9]"
                          : "bg-violet-400 shadow-[0_0_9px_#a78bfa]"
                      }`}
                    />
                    <span className="truncate text-xs font-medium text-white/60">
                      {source.name}
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-white/80">
                    ${moneyFormatter.format(source.total)}
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={`source-bar h-full rounded-full ${
                      index === 0
                        ? "bg-gradient-to-r from-cyan-400 to-blue-500"
                        : "bg-gradient-to-r from-violet-500 to-fuchsia-400"
                    }`}
                    style={{ width: `${percent}%` }}
                  />
                </div>
                <p className="mt-2 text-right text-[10px] text-white/25">
                  {percent}% от итога
                </p>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

export function QualityCard({ result }: { result: RevenueResult | null }) {
  return (
    <section className="glass glass-card rounded-[26px] p-5 sm:rounded-[28px] sm:p-6">
      <p className="section-label">Качество расчёта</p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <article className="mini-card">
          <span className="mini-icon mini-icon-cyan text-cyan-200">
            <span className="ui-icon icon-check" />
          </span>
          <strong className="mt-5 block text-2xl font-semibold tracking-tight">
            {result?.processed ?? 0}
          </strong>
          <span className="mt-1 block text-[11px] text-white/35">
            Учтено операций
          </span>
        </article>
        <article className="mini-card">
          <span className="mini-icon mini-icon-violet text-violet-200">
            <span className="ui-icon icon-filter" />
          </span>
          <strong className="mt-5 block text-2xl font-semibold tracking-tight">
            {result?.skipped ?? 0}
          </strong>
          <span className="mt-1 block text-[11px] text-white/35">
            Пропущено
          </span>
        </article>
      </div>
      <div className="mt-5 border-t border-white/[0.07] pt-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/25">
          Обнаруженные валюты
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {result?.currencies.length ? (
            result.currencies.map((code) => (
              <span key={code} className="data-chip">
                {code}
              </span>
            ))
          ) : (
            <span className="data-chip text-white/25">Нет данных</span>
          )}
        </div>
      </div>
    </section>
  );
}

export function HistoryCard({
  history,
  canCopy,
  onCopy,
  onExport,
}: {
  history: HistoryEntry[];
  canCopy: boolean;
  onCopy: () => void;
  onExport: () => void;
}) {
  return (
    <article className="glass glass-card rounded-[26px] p-5 sm:rounded-[28px] sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="section-label">История</p>
          <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">
            Последние расчёты
          </h2>
        </div>
        <div className="flex gap-2">
          <button
            className="small-button"
            type="button"
            disabled={!canCopy}
            onClick={onCopy}
          >
            <span className="ui-icon icon-copy" />
            <span className="hidden min-[390px]:inline">Копировать</span>
          </button>
          <button
            className="small-button"
            type="button"
            disabled={!history.length}
            onClick={onExport}
          >
            <span className="ui-icon icon-download" />
            <span className="hidden min-[390px]:inline">Экспорт CSV</span>
          </button>
        </div>
      </div>

      {history.length ? (
        <>
          <div className="mt-5 hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[560px] text-left">
              <thead className="text-[10px] uppercase tracking-[0.14em] text-white/25">
                <tr>
                  <th className="pb-3 font-medium">Режим</th>
                  <th className="pb-3 font-medium">Результат</th>
                  <th className="pb-3 font-medium">Операции</th>
                  <th className="pb-3 text-right font-medium">Время</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-xs">
                {history.map((entry) => (
                  <HistoryRow key={entry.id} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-5 grid gap-2 sm:hidden">
            {history.map((entry) => (
              <HistoryMobileCard key={entry.id} entry={entry} />
            ))}
          </div>
        </>
      ) : (
        <p className="py-8 text-center text-xs text-white/25">
          Здесь появятся результаты ваших запусков
        </p>
      )}
    </article>
  );
}

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const time = new Date(entry.timestamp);
  const label = entry.mode === "live" ? "Live API" : "Демо · тест";
  return (
    <tr>
      <td className="py-3.5">
        <span className="inline-flex items-center gap-2 text-white/55">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              entry.mode === "live" ? "bg-emerald-300" : "bg-violet-300"
            }`}
          />
          {label}
        </span>
      </td>
      <td className="py-3.5 font-semibold text-white/80">
        {moneyFormatter.format(entry.total)} {entry.currency}
      </td>
      <td className="py-3.5 text-white/35">
        {entry.processed} учтено · {entry.skipped} мимо
      </td>
      <td className="py-3.5 text-right text-white/30">
        {formatHistoryTime(time)}
      </td>
    </tr>
  );
}

function HistoryMobileCard({ entry }: { entry: HistoryEntry }) {
  const label = entry.mode === "live" ? "Live API" : "Демо · тест";
  return (
    <article className="history-mobile-card">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-[11px] font-medium text-white/55">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              entry.mode === "live"
                ? "bg-emerald-300 shadow-[0_0_8px_#6ee7b7]"
                : "bg-violet-300 shadow-[0_0_8px_#c4b5fd]"
            }`}
          />
          {label}
        </span>
        <span className="text-[10px] text-white/25">
          {formatHistoryTime(new Date(entry.timestamp))}
        </span>
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <strong className="text-base font-semibold tracking-[-0.02em] text-white/85">
          {moneyFormatter.format(entry.total)}{" "}
          <span className="text-[10px] text-white/35">{entry.currency}</span>
        </strong>
        <span className="text-[10px] text-white/30">
          {entry.processed} учтено · {entry.skipped} мимо
        </span>
      </div>
    </article>
  );
}

export function LogsCard({
  logs,
  consoleRef,
  onClear,
}: {
  logs: LogEntry[];
  consoleRef: RefObject<HTMLDivElement | null>;
  onClear: () => void;
}) {
  const toneClasses: Record<LogEntry["tone"], string> = {
    default: "text-white/45",
    success: "text-emerald-200/80",
    warning: "text-amber-200/80",
    error: "text-rose-200/80",
  };

  return (
    <article className="glass glass-card rounded-[26px] p-5 sm:rounded-[28px] sm:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="section-label">Live console</p>
          <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">
            Журнал процесса
          </h2>
        </div>
        <button className="small-button" type="button" onClick={onClear}>
          <span className="ui-icon icon-trash" />
          <span className="hidden min-[390px]:inline">Очистить</span>
        </button>
      </div>
      <div
        ref={consoleRef}
        className="console-scroll console-panel mt-5 h-[164px] space-y-2 overflow-y-auto rounded-2xl p-4 font-mono text-[11px] leading-5"
        aria-live="polite"
      >
        {logs.map((log) => (
          <p key={log.id} className={toneClasses[log.tone]}>
            <span className="mr-2 text-cyan-300/50">{log.time}</span>
            {log.message}
          </p>
        ))}
      </div>
    </article>
  );
}

function formatHistoryTime(date: Date) {
  return `${date.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
  })}, ${date.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}
