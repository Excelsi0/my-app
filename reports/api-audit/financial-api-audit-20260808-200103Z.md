# Отчёт об аудите финансовых API ExFlow

## Резюме

- Время проверки (UTC): `2026-08-08T20:01:03.121885Z`
- Режим: `live API`
- Итог: **Нужна унификация: найдены значимые проблемы консистентности**
- Findings: CRITICAL `0`, HIGH `0`, MEDIUM `9`, LOW `0`, INFO `1`
- Проверено записей: finance1 `8`, finance2 `9`

> Полные API payload, заголовки авторизации и секреты намеренно не включены. Примеры сокращены и очищены.

## Состояние endpoints

| Endpoint | Источник | HTTP | Content-Type | Latency | Размер |
| --- | --- | ---: | --- | ---: | ---: |
| finance1 | https://cpa-server-vtel.onrender.com/api/finance1 | 200 | application/json; charset=utf-8 | 1244 ms | 465 B |
| finance2 | https://cpa-server-vtel.onrender.com/api/finance2 | 200 | application/json; charset=utf-8 | 1184 ms | 91 B |
| rates | https://api.currencyfreaks.com/v2.0/rates/latest?apikey=REDACTED | 200 | application/json | 1713 ms | 26251 B |

## Найденные проблемы

| № | Severity | Code | Endpoint | Location | Проблема |
| ---: | --- | --- | --- | --- | --- |
| 1 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[0] | Формат неканонический: неверхний регистр валюты. |
| 2 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[1] | Формат неканонический: неверхний регистр валюты. |
| 3 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[2] | Формат неканонический: неверхний регистр валюты. |
| 4 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[3] | Формат неканонический: неверхний регистр валюты. |
| 5 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[4] | Формат неканонический: неверхний регистр валюты. |
| 6 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[5] | Формат неканонический: неверхний регистр валюты. |
| 7 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[6] | Формат неканонический: неверхний регистр валюты. |
| 8 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[7] | Формат неканонический: неверхний регистр валюты. |
| 9 | MEDIUM | FINANCE2_NON_CANONICAL | finance2 | $[8] | Формат неканонический: неверхний регистр валюты. |
| 10 | INFO | RATE_NON_ISO_INSTRUMENTS_PRESENT | rates | $.rates | Rates provider содержит 863 non-ISO instrument/crypto codes; они исключены из валютной проверки. |

## Детали findings

### 1. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[0]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `300 usd`

### 2. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[1]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `200 eur`

### 3. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[2]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `150 usd`

### 4. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[3]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `200 usd`

### 5. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[4]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `450 eur`

### 6. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[5]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `400 usd`

### 7. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[6]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `670 usd`

### 8. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[7]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `190 usd`

### 9. [MEDIUM] FINANCE2_NON_CANONICAL

- Endpoint: `finance2`
- Location: `$[8]`
- Классификация: `нарушение/риск контракта`
- Проблема: Формат неканонический: неверхний регистр валюты.
- Ожидание: Один пробел, decimal point, положительная сумма, uppercase ISO code.
- Рекомендация: Нормализовать сериализацию или заменить строку на object schema.
- Сокращённый пример: `500 eur`

### 10. [INFO] RATE_NON_ISO_INSTRUMENTS_PRESENT

- Endpoint: `rates`
- Location: `$.rates`
- Классификация: `информационное наблюдение`
- Проблема: Rates provider содержит 863 non-ISO instrument/crypto codes; они исключены из валютной проверки.
- Ожидание: Это допустимо для универсального rates provider; финансовые источники должны использовать ISO 4217.
- Рекомендация: Не считать эти keys ошибкой. Проверять только валюты, фактически встречающиеся в finance1/finance2.
- Сокращённый пример: `["$MICHI", "00", "0X0"]`

## Рекомендуемый порядок исправления

1. Нормализовать сериализацию или заменить строку на object schema.

## Наблюдаемое покрытие валют

- Finance 1: `EUR, USD`
- Finance 2: `EUR, USD`
- Всего в источниках: `EUR, USD`

## Методика и ограничения

- Проверка является снимком состояния на указанное время и не доказывает стабильность API за другой период.
- Потенциальные дубликаты определяются без transaction ID и требуют проверки backend-командой.
- ISO 4217 allowlist встроен в аудитор; нестандартные instrument codes требуют отдельной документации.
- Non-`paid` статусы не считаются ошибкой сами по себе.
- Отчёт оценивает контракт и качество данных, но не заменяет server logs, tracing и бизнес-сверку.

## Критерий повторной проверки

После исправлений повторить live-аудит и ожидать отсутствия CRITICAL/HIGH, единого регистра статусов и валют, валидных курсов для всех non-USD операций и стабильной JSON-схемы.
