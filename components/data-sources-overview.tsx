import Link from "next/link";

type DataSource = {
  id: string;
  number: string;
  category: string;
  name: string;
  provider: string;
  endpoint: string;
  description: string;
  format: string;
  authentication: string;
  fields: string[];
  accent: "cyan" | "violet" | "fuchsia";
};

const dataSources: DataSource[] = [
  {
    id: "finance-one",
    number: "01",
    category: "Финансовые операции",
    name: "Transactions API",
    provider: "Finance source 1",
    endpoint: "GET /api/finance1",
    description:
      "Передаёт транзакции с типом операции, числовой суммой и кодом валюты. В расчёт попадают только оплаченные операции.",
    format: "JSON object · transactions[]",
    authentication: "Серверный x-api-key",
    fields: ["type: paid", "amount: number", "currency: ISO 4217"],
    accent: "cyan",
  },
  {
    id: "finance-two",
    number: "02",
    category: "Финансовые выплаты",
    name: "Payouts API",
    provider: "Finance source 2",
    endpoint: "GET /api/finance2",
    description:
      "Возвращает выплаты в компактном строковом формате. ExFlow проверяет каждую запись и отделяет сумму от трёхбуквенного кода валюты.",
    format: "JSON array · string[]",
    authentication: "Серверный x-api-key",
    fields: ["680 USD", "368 EUR", "12000 RUB"],
    accent: "violet",
  },
  {
    id: "rates",
    number: "03",
    category: "Валютные котировки",
    name: "Exchange Rates API",
    provider: "CurrencyFreaks",
    endpoint: "GET /v2.0/rates/latest",
    description:
      "Предоставляет курсы с базой USD. Они используются для приведения сумм из разных валют к единому долларовому результату.",
    format: "JSON object · rates{}",
    authentication: "Серверный API key",
    fields: ["USD: base", "EUR: rate", "RUB: rate"],
    accent: "fuchsia",
  },
];

const accentClasses: Record<DataSource["accent"], string> = {
  cyan: "border-cyan-300/15 bg-cyan-300/[0.06] text-cyan-200",
  violet: "border-violet-300/15 bg-violet-300/[0.06] text-violet-200",
  fuchsia: "border-fuchsia-300/15 bg-fuchsia-300/[0.06] text-fuchsia-200",
};

const dotClasses: Record<DataSource["accent"], string> = {
  cyan: "bg-cyan-300 shadow-[0_0_12px_#67e8f9]",
  violet: "bg-violet-300 shadow-[0_0_12px_#c4b5fd]",
  fuchsia: "bg-fuchsia-300 shadow-[0_0_12px_#f0abfc]",
};

export function DataSourcesOverview() {
  return (
    <>
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >
        <div className="ambient ambient-a" />
        <div className="ambient ambient-b" />
        <div className="ambient ambient-c" />
        <div className="noise" />
      </div>

      <div className="app-shell relative mx-auto min-h-screen w-full max-w-[1380px] px-3 pb-8 pt-3 sm:px-6 sm:pb-12 sm:pt-5 xl:px-10">
        <header className="glass topbar flex h-16 items-center justify-between rounded-[22px] px-3.5 sm:px-5">
          <Link
            href="/"
            className="group flex items-center gap-3"
            aria-label="ExFlow — вернуться к финансовому радару"
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
          </Link>

          <Link href="/" className="small-button" aria-label="На главную">
            <span aria-hidden="true">←</span>
            <span className="hidden min-[380px]:inline">К радару</span>
          </Link>
        </header>

        <main id="content" className="mt-3 space-y-3 sm:mt-4 sm:space-y-4">
          <section className="glass hero-card relative overflow-hidden rounded-[28px] px-5 py-10 sm:rounded-[32px] sm:px-8 sm:py-14 lg:px-12 lg:py-16">
            <div className="hero-spectral" aria-hidden="true" />
            <div className="relative z-10 max-w-4xl">
              <div className="flex flex-wrap items-center gap-2">
                <span className="eyebrow">
                  <span className="signal-dot" /> Архитектура расчёта
                </span>
                <span className="eyebrow text-white/40">
                  3 источника · server-side
                </span>
              </div>

              <h1 className="mt-7 max-w-3xl text-4xl font-semibold leading-[1.02] tracking-[-0.055em] text-white/95 sm:mt-9 sm:text-6xl lg:text-7xl">
                Источники данных
                <span className="mt-2 block bg-gradient-to-r from-cyan-200 via-indigo-200 to-fuchsia-200 bg-clip-text text-transparent">
                  для расчёта выручки
                </span>
              </h1>

              <p className="mt-6 max-w-2xl text-sm leading-7 text-white/45 sm:text-base">
                ExFlow объединяет два независимых финансовых потока и актуальные
                валютные котировки. Все запросы выполняются на сервере, а в
                браузер возвращается только безопасный агрегированный результат.
              </p>

              <div className="mt-8 flex flex-wrap gap-2">
                <span className="data-chip">2 финансовых API</span>
                <span className="data-chip">1 сервис курсов</span>
                <span className="data-chip">Параллельная загрузка</span>
                <span className="data-chip">Без кеширования</span>
              </div>
            </div>
          </section>

          <section
            className="grid gap-3 lg:grid-cols-3 lg:gap-4"
            aria-labelledby="source-list-title"
          >
            <h2 id="source-list-title" className="sr-only">
              Список источников данных
            </h2>
            {dataSources.map((source) => (
              <article
                key={source.id}
                className="glass glass-card flex min-h-[430px] flex-col rounded-[26px] p-5 sm:rounded-[28px] sm:p-6"
              >
                <div className="flex items-start justify-between gap-4">
                  <span
                    className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl border font-mono text-xs font-semibold ${accentClasses[source.accent]}`}
                  >
                    {source.number}
                  </span>
                  <span className="data-chip">
                    <span
                      className={`mr-2 h-1.5 w-1.5 rounded-full ${dotClasses[source.accent]}`}
                    />
                    Server only
                  </span>
                </div>

                <div className="mt-7">
                  <p className="section-label">{source.category}</p>
                  <h3 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-white/90">
                    {source.name}
                  </h3>
                  <p className="mt-1 text-xs font-medium text-white/30">
                    {source.provider}
                  </p>
                </div>

                <p className="mt-5 text-sm leading-6 text-white/45">
                  {source.description}
                </p>

                <dl className="mt-6 space-y-3 border-t border-white/[0.07] pt-5 text-xs">
                  <div className="flex items-start justify-between gap-4">
                    <dt className="text-white/25">Endpoint</dt>
                    <dd className="max-w-[70%] text-right font-mono text-[10px] text-white/60">
                      {source.endpoint}
                    </dd>
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <dt className="text-white/25">Формат</dt>
                    <dd className="text-right text-white/55">{source.format}</dd>
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <dt className="text-white/25">Доступ</dt>
                    <dd className="text-right text-white/55">
                      {source.authentication}
                    </dd>
                  </div>
                </dl>

                <div className="mt-auto flex flex-wrap gap-2 pt-6">
                  {source.fields.map((field) => (
                    <span key={field} className="data-chip font-mono">
                      {field}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </section>

          <section className="glass glass-card rounded-[26px] p-5 sm:rounded-[28px] sm:p-7 lg:p-8">
            <div className="grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:items-center">
              <div>
                <p className="section-label">Единый поток</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-white/90 sm:text-3xl">
                  От данных к результату
                </h2>
                <p className="mt-4 max-w-lg text-sm leading-6 text-white/40">
                  Сервер получает ответы одновременно, проверяет структуру каждой
                  записи, конвертирует поддерживаемые валюты и формирует единый
                  результат в USD.
                </p>
              </div>

              <ol className="grid gap-2 sm:grid-cols-4" aria-label="Этапы расчёта">
                {[
                  ["01", "Запрос", "Три API параллельно"],
                  ["02", "Проверка", "Формат и тип операции"],
                  ["03", "Конвертация", "Курсы с базой USD"],
                  ["04", "Итог", "Сумма и качество данных"],
                ].map(([number, title, caption]) => (
                  <li
                    key={number}
                    className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4"
                  >
                    <span className="font-mono text-[10px] text-cyan-200/55">
                      {number}
                    </span>
                    <strong className="mt-4 block text-sm font-semibold text-white/75">
                      {title}
                    </strong>
                    <span className="mt-1 block text-[11px] leading-5 text-white/30">
                      {caption}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          </section>

          <footer className="flex flex-wrap items-center justify-between gap-3 px-2 py-4 text-[10px] uppercase tracking-[0.14em] text-white/20">
            <span>ExFlow · Data lineage</span>
            <span>Ключи API остаются на сервере</span>
          </footer>
        </main>
      </div>
    </>
  );
}
