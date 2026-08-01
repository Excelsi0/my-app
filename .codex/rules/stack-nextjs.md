# Стек, Bun и Next.js

## Версии и инструменты

- Next.js `16.2.12`, App Router.
- React и React DOM `19.2.4`.
- TypeScript 5, `strict: true`, alias `@/*`.
- Tailwind CSS 4 через `@tailwindcss/postcss`.
- ESLint 9 с пресетами Next.js Core Web Vitals и TypeScript.
- Bun `1.2.15` — объявленный package manager.

Используй Bun для зависимостей и скриптов. Не создавай lock-файлы npm, pnpm или Yarn.

```bash
bun install --frozen-lockfile
bun run dev
bun run lint
bun run build
bun run start
```

## Правила Next.js 16

Next.js 16 может отличаться от знакомых старых версий. Перед применением или изменением framework API получи актуальную документацию через Context7 и прочитай подходящий локальный guide в `node_modules/next/dist/docs/`. Учитывай предупреждения об устаревании.

- Pages и layouts в App Router являются Server Components по умолчанию.
- Добавляй `"use client"` только на минимальной границе, которой нужны состояние, эффекты, обработчики, `window`, `localStorage`, clipboard или другие browser API.
- Не переноси секреты и авторизованные внешние запросы в Client Components.
- Route Handlers размещай в `app/**/route.ts`; используй Web Request/Response API или `NextResponse`.
- Не полагайся на старые значения кеширования по умолчанию. Для routes и `fetch` задавай требуемое поведение осознанно.
- В динамических маршрутах Next.js 16 параметры `params` у pages и Route Handlers являются promises.

## Зависимости и конфигурация

- Перед добавлением пакета проверь, нельзя ли решить задачу текущим стеком.
- При реальном изменении зависимостей синхронизируй `package.json` и `bun.lock`.
- Не ослабляй `strict` TypeScript и правила ESLint ради обхода ошибки.
- Сохраняй существующий alias `@/` и bundler module resolution.
- Изменения `next.config.ts`, `tsconfig.json`, PostCSS и ESLint должны быть минимальными и иметь конкретную причину.
