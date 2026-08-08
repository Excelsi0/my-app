# Отчёт об аудите финансовых API ExFlow

## Резюме

- Время проверки (UTC): `2026-08-08T20:00:46.861471Z`
- Режим: `live API`
- Итог: **Критическое состояние: часть API или обязательных структур недоступна**
- Findings: CRITICAL `3`, HIGH `0`, MEDIUM `0`, LOW `0`, INFO `0`
- Проверено записей: finance1 `0`, finance2 `0`

> Полные API payload, заголовки авторизации и секреты намеренно не включены. Примеры сокращены и очищены.

## Состояние endpoints

| Endpoint | Источник | HTTP | Content-Type | Latency | Размер |
| --- | --- | ---: | --- | ---: | ---: |
| finance1 | https://cpa-server-vtel.onrender.com/api/finance1 | нет | нет | 1 ms | 0 B |
| finance2 | https://cpa-server-vtel.onrender.com/api/finance2 | нет | нет | 0 ms | 0 B |
| rates | https://api.currencyfreaks.com/v2.0/rates/latest?apikey=REDACTED | нет | нет | 0 ms | 0 B |

## Найденные проблемы

| № | Severity | Code | Endpoint | Location | Проблема |
| ---: | --- | --- | --- | --- | --- |
| 1 | CRITICAL | ENDPOINT_UNAVAILABLE | finance1 | $ | Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: cpa-server-vtel.onrender.com |
| 2 | CRITICAL | ENDPOINT_UNAVAILABLE | finance2 | $ | Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: cpa-server-vtel.onrender.com |
| 3 | CRITICAL | ENDPOINT_UNAVAILABLE | rates | $ | Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: api.currencyfreaks.com |

## Детали findings

### 1. [CRITICAL] ENDPOINT_UNAVAILABLE

- Endpoint: `finance1`
- Location: `$`
- Классификация: `нарушение/риск контракта`
- Проблема: Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: cpa-server-vtel.onrender.com
- Ожидание: HTTP 2xx и корректный JSON.
- Рекомендация: Проверить доступность, авторизацию, status code и JSON-сериализацию ответа.

### 2. [CRITICAL] ENDPOINT_UNAVAILABLE

- Endpoint: `finance2`
- Location: `$`
- Классификация: `нарушение/риск контракта`
- Проблема: Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: cpa-server-vtel.onrender.com
- Ожидание: HTTP 2xx и корректный JSON.
- Рекомендация: Проверить доступность, авторизацию, status code и JSON-сериализацию ответа.

### 3. [CRITICAL] ENDPOINT_UNAVAILABLE

- Endpoint: `rates`
- Location: `$`
- Классификация: `нарушение/риск контракта`
- Проблема: Ответ невозможно проверить: curl 6: curl: (6) Could not resolve host: api.currencyfreaks.com
- Ожидание: HTTP 2xx и корректный JSON.
- Рекомендация: Проверить доступность, авторизацию, status code и JSON-сериализацию ответа.

## Рекомендуемый порядок исправления

1. Проверить доступность, авторизацию, status code и JSON-сериализацию ответа.

## Наблюдаемое покрытие валют

- Finance 1: `нет данных`
- Finance 2: `нет данных`
- Всего в источниках: `нет данных`

## Методика и ограничения

- Проверка является снимком состояния на указанное время и не доказывает стабильность API за другой период.
- Потенциальные дубликаты определяются без transaction ID и требуют проверки backend-командой.
- ISO 4217 allowlist встроен в аудитор; нестандартные instrument codes требуют отдельной документации.
- Non-`paid` статусы не считаются ошибкой сами по себе.
- Отчёт оценивает контракт и качество данных, но не заменяет server logs, tracing и бизнес-сверку.

## Критерий повторной проверки

После исправлений повторить live-аудит и ожидать отсутствия CRITICAL/HIGH, единого регистра статусов и валют, валидных курсов для всех non-USD операций и стабильной JSON-схемы.
