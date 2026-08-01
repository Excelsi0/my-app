# Клиентское поведение и интерфейс

## Существующее поведение

Dashboard поддерживает:

- live API и локальный demo-расчёт;
- состояния ready, loading, success и error;
- последние шесть расчётов в `localStorage` по ключу `exflow-history`;
- fallback миграции со старого ключа `finora-history`;
- журнал процесса, toast-уведомления, clipboard и экспорт CSV;
- отключение декоративного движения при `prefers-reduced-motion` и проверку pointer capability.

Не обращайся к browser globals вне Client Component или callback/effect, выполняемого в браузере. Содержимое localStorage считай недоверенным и разбирай защитно. Не меняй storage key и колонки CSV без явной миграции.

## React-компоненты

- Держи client boundary минимальной.
- Отделяй orchestration состояния от простых presentational sections.
- Не дублируй финансовую логику внутри JSX или effects; используй чистую функцию из `app/lib/revenue.ts`.
- Очищай timers, animation frames и event listeners.
- Сохраняй корректные disabled/loading/error состояния и предотвращай повторные действия во время загрузки.

## Визуальная система

Сохраняй текущий тёмный glassmorphism: cyan/violet акценты, полупрозрачные поверхности, сдержанное движение, компактную финансовую типографику и отдельные responsive layouts для desktop/mobile.

- Сначала переиспользуй существующие Tailwind utilities и component classes.
- Общие токены и переиспользуемые визуальные правила храни в `app/globals.css`.
- Не добавляй UI- или icon-зависимость для визуалов, уже реализуемых CSS.
- Поддерживай viewport от 320px и проверяй мобильный и desktop режимы.
- Декоративные слои должны оставаться неинтерактивными и скрытыми от assistive technology.

## Доступность и тексты

- Сохраняй семантические элементы, keyboard focus, labels, `role="alert"`, `aria-live` и reduced-motion.
- Проверяй доступность интерактивных элементов с клавиатуры.
- Пользовательский текст пиши по-русски и в существующем тоне продукта.
- Не заменяй понятное сообщение техническим текстом исключения.
