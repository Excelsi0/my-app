# ExFlow

Next.js-приложение для агрегации финансовых данных из двух источников и
пересчёта выручки в USD.

## Локальный запуск

Требуется Bun 1.2.15 или новее.

```bash
bun install --frozen-lockfile
bun run dev
```

Приложение будет доступно по адресу `http://localhost:3000`.

## Переменные окружения

Создайте `.env.local` на основе `.env.example`:

```env
EXFLOW_FINANCE_API_KEY=your_finance_api_key
EXFLOW_RATES_API_KEY=your_currencyfreaks_api_key
```

Переменные не имеют префикса `NEXT_PUBLIC_`, поэтому используются только
серверным маршрутом `/api/exflow` и не попадают в браузерный JavaScript.

## Развёртывание с Bun

Хостинг должен поддерживать серверные Next.js-приложения и исходящие
HTTPS-запросы. Статический файловый хостинг не подойдёт.

Настройки сборки:

```text
Install command: bun install --frozen-lockfile
Build command:   bun run build
Start command:   bun run start
```

В панели хостинга добавьте:

```env
NODE_ENV=production
EXFLOW_FINANCE_API_KEY=production_finance_api_key
EXFLOW_RATES_API_KEY=production_currencyfreaks_api_key
```

Хостинг обычно передаёт порт через переменную `PORT`; команда `next start`
использует её автоматически.

Загружайте исходники проекта целиком. Не загружайте `.env.local`,
`node_modules`, `.next` и `.git`.
