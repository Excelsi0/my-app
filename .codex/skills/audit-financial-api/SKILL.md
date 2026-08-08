---
name: audit-financial-api
description: Проверяет текущие live-ответы или локальные JSON-снимки финансовых API ExFlow, выявляет schema drift, разный регистр статусов и валют, несуществующие или неподдерживаемые валюты, невалидные суммы и курсы, подозрительные дубликаты, HTTP-ошибки и проблемы доступности. Использовать для диагностики источников finance1, finance2 и CurrencyFreaks, проверки качества backend-данных и подготовки русского Markdown-отчёта для backend-разработчиков; при запросе также создавать и визуально проверять PDF.
---

# Аудит финансовых API

## Порядок работы

1. Прочитать `references/contracts.md` перед интерпретацией результатов.
2. Проверить наличие `.env.local`, не выводя значения ключей.
3. Выбрать режим:
   - live — для проверки текущего состояния внешних API;
   - snapshot — если пользователь передал JSON-файлы или сеть/credentials недоступны.
4. Запустить `scripts/audit_financial_api.py` из корня проекта.
5. Прочитать созданный Markdown целиком. Отделить подтверждённые нарушения контракта от эвристических предупреждений.
6. Если нужен PDF, запустить renderer, отрисовать все страницы в PNG и визуально проверить их до передачи пользователю.
7. Сообщить пути к отчётам, время проверки, реально проверенные endpoints и ограничения. Не утверждать, что live API проверены, если использовались snapshots.

## Live-аудит

```bash
python3 .codex/skills/audit-financial-api/scripts/audit_financial_api.py \
  --env-file .env.local \
  --output-dir reports/api-audit
```

Скрипт читает `EXFLOW_FINANCE_API_KEY` и `EXFLOW_RATES_API_KEY` сначала из окружения, затем из указанного env-файла. Значения не выводятся и не записываются в отчёт.

Не использовать `set -x`, `env`, `printenv`, URL с открытым `apikey` или команды, печатающие `.env.local`.

## Аудит снимков

Передать все три файла одновременно:

```bash
python3 .codex/skills/audit-financial-api/scripts/audit_financial_api.py \
  --source-one-file /path/finance1.json \
  --source-two-file /path/finance2.json \
  --rates-file /path/rates.json \
  --output-dir reports/api-audit
```

Не копировать исходные финансовые payload в репозиторий без прямого разрешения пользователя. Для временных снимков использовать безопасный временный каталог.

## PDF

Установить ReportLab только если PDF действительно требуется:

```bash
python3 -m pip install reportlab
python3 .codex/skills/audit-financial-api/scripts/render_report_pdf.py \
  reports/api-audit/<report>.md \
  output/pdf/<report>.pdf
```

После генерации:

```bash
mkdir -p tmp/pdfs/<report>
pdftoppm -png output/pdf/<report>.pdf tmp/pdfs/<report>/page
```

Просмотреть каждую PNG-страницу. Проверить кириллицу, переносы таблиц, заголовки, номера страниц, отсутствие обрезанного и наложенного текста. Если `reportlab` или Poppler недоступны, не заявлять об успешной PDF-проверке; передать Markdown и назвать недостающую зависимость.

Если Poppler недоступен, но установлен PyMuPDF, использовать безопасный fallback:

```bash
python3 .codex/skills/audit-financial-api/scripts/render_pdf_pages.py \
  output/pdf/<report>.pdf \
  tmp/pdfs/<report>
```

При отсутствии и Poppler, и PyMuPDF не заявлять об успешной визуальной проверке PDF.

## Интерпретация

- `CRITICAL` — endpoint или обязательная структура недоступны, аудит данных невозможен.
- `HIGH` — запись будет пропущена приложением, валюта невалидна/не имеет курса или нарушен основной контракт.
- `MEDIUM` — данные могут интерпретироваться неоднозначно либо формат нестабилен.
- `LOW` — подозрительная аномалия или рекомендация по унификации.
- `INFO` — наблюдение без доказанного влияния.

Не называть потенциальный дубликат подтверждённым дублем без стабильного transaction ID. Не считать любой non-`paid` статус ошибкой: приложение намеренно учитывает только `paid`. Не включать полные payload, персональные данные, заголовки авторизации или секреты.

## Выходные артефакты

Аудитор создаёт:

- `<name>.md` — основной текстовый отчёт для backend-команды;
- `<name>.json` — машинно-читаемые metadata и findings без полных payload;
- `<name>.pdf` — только при отдельном запуске renderer.

Использовать стабильный каталог `reports/api-audit/` для Markdown/JSON и `output/pdf/` для финального PDF. Не коммитить отчёты с реальными финансовыми наблюдениями без явного запроса пользователя.
