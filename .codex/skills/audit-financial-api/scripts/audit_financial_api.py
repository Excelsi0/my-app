#!/usr/bin/env python3
"""Audit ExFlow financial API payloads and produce redacted Markdown/JSON reports."""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SOURCE_ONE_URL = "https://cpa-server-vtel.onrender.com/api/finance1"
DEFAULT_SOURCE_TWO_URL = "https://cpa-server-vtel.onrender.com/api/finance2"
DEFAULT_RATES_URL = "https://api.currencyfreaks.com/v2.0/rates/latest"

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}

ISO_4217_CODES = set(
    """
    AED AFN ALL AMD AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND
    BOB BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNY COP
    COU CRC CUC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP
    GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK
    JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL
    LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD
    NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB
    RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD SSP STN SVC SYP SZL
    THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD USN UYI UYU UYW UZS
    VED VES VND VUV WST XAF XAG XAU XBA XBB XBC XBD XCD XCG XDR XOF
    XPD XPF XPT XSU XTS XUA XXX YER ZAR ZMW ZWL
    """.split()
)

SECRET_KEY_PATTERN = re.compile(
    r"(?:api.?key|token|secret|authorization|password|cookie)", re.IGNORECASE
)
SOURCE_TWO_LOOSE_PATTERN = re.compile(
    r"^\s*([+-]?\d+(?:[.,]\d+)?)\s+([A-Za-z]{3})\s*$"
)
SOURCE_TWO_CANONICAL_PATTERN = re.compile(r"^(\d+(?:\.\d+)?) ([A-Z]{3})$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


@dataclasses.dataclass
class EndpointResult:
    name: str
    display_url: str
    status: int | None
    content_type: str
    latency_ms: int
    payload_bytes: int
    payload: Any = None
    error: str | None = None
    mode: str = "live"


@dataclasses.dataclass
class Finding:
    severity: str
    code: str
    endpoint: str
    location: str
    problem: str
    expected: str
    recommendation: str
    sample: str = ""
    heuristic: bool = False


class Auditor:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.source_currencies: dict[str, set[str]] = {
            "finance1": set(),
            "finance2": set(),
        }

    def add(
        self,
        severity: str,
        code: str,
        endpoint: str,
        location: str,
        problem: str,
        expected: str,
        recommendation: str,
        sample: Any = "",
        *,
        heuristic: bool = False,
    ) -> None:
        self.findings.append(
            Finding(
                severity=severity,
                code=code,
                endpoint=endpoint,
                location=location,
                problem=problem,
                expected=expected,
                recommendation=recommendation,
                sample=safe_sample(sample),
                heuristic=heuristic,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Проверить live API ExFlow или три локальных JSON-снимка."
    )
    parser.add_argument("--env-file", default=".env.local")
    parser.add_argument("--output-dir", default="reports/api-audit")
    parser.add_argument("--report-name")
    parser.add_argument("--source-one-url", default=DEFAULT_SOURCE_ONE_URL)
    parser.add_argument("--source-two-url", default=DEFAULT_SOURCE_TWO_URL)
    parser.add_argument("--rates-url", default=DEFAULT_RATES_URL)
    parser.add_argument("--source-one-file", type=Path)
    parser.add_argument("--source-two-file", type=Path)
    parser.add_argument("--rates-file", type=Path)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--fail-on",
        choices=["none", "critical", "high", "medium", "low"],
        default="none",
        help="Вернуть exit code 1 при finding выбранной или большей серьёзности.",
    )
    return parser.parse_args()


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def get_secret(name: str, env_file_values: dict[str, str]) -> str:
    return os.environ.get(name, "").strip() or env_file_values.get(name, "").strip()


def safe_display_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = [
        (key, "REDACTED" if SECRET_KEY_PATTERN.search(key) else value)
        for key, value in query
    ]
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(redacted), "")
    )


def safe_sample(value: Any, limit: int = 160) -> str:
    def redact(item: Any) -> Any:
        if isinstance(item, dict):
            safe: dict[str, Any] = {}
            for key, nested in item.items():
                safe[str(key)] = (
                    "<redacted>" if SECRET_KEY_PATTERN.search(str(key)) else redact(nested)
                )
            return safe
        if isinstance(item, list):
            return [redact(nested) for nested in item[:3]]
        return item

    if value == "":
        return ""
    if isinstance(value, str):
        rendered = value
    else:
        try:
            rendered = json.dumps(redact(value), ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            rendered = repr(value)
    rendered = rendered.replace("\n", " ").replace("\r", " ")
    return rendered if len(rendered) <= limit else rendered[: limit - 1] + "…"


def read_snapshot(name: str, path: Path) -> EndpointResult:
    started = time.perf_counter()
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        return EndpointResult(
            name=name,
            display_url=str(path),
            status=200,
            content_type="application/json (local snapshot)",
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=len(raw),
            payload=payload,
            mode="snapshot",
        )
    except Exception as error:  # report operational snapshot errors uniformly
        return EndpointResult(
            name=name,
            display_url=str(path),
            status=None,
            content_type="",
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=0,
            error=f"{type(error).__name__}: {error}",
            mode="snapshot",
        )


def fetch_json(
    name: str,
    url: str,
    headers: dict[str, str],
    timeout: float,
) -> EndpointResult:
    if shutil.which("curl"):
        return fetch_json_with_curl(name, url, headers, timeout)

    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "ExFlow-API-Audit/1.0", **headers},
        method="GET",
    )
    status: int | None = None
    content_type = ""
    raw = b""
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(5_000_001)
    except urllib.error.HTTPError as error:
        status = error.code
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        raw = error.read(64_000)
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=status,
            content_type=content_type,
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=len(raw),
            error=f"HTTP {status}",
        )
    except Exception as error:
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=None,
            content_type=content_type,
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=len(raw),
            error=f"{type(error).__name__}: {error}",
        )

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as error:
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=status,
            content_type=content_type,
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=len(raw),
            error=f"Некорректный JSON: {type(error).__name__}",
        )

    return EndpointResult(
        name=name,
        display_url=safe_display_url(url),
        status=status,
        content_type=content_type,
        latency_ms=round((time.perf_counter() - started) * 1000),
        payload_bytes=len(raw),
        payload=payload,
    )


def curl_config_quote(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Переводы строк запрещены в URL и HTTP headers.")
    return value.replace("\\", "\\\\").replace('"', '\\"')


def sanitize_transport_error(text: str, url: str, headers: dict[str, str]) -> str:
    sanitized = text
    for value in headers.values():
        if value:
            sanitized = sanitized.replace(value, "<redacted>")
    for key, value in urllib.parse.parse_qsl(
        urllib.parse.urlsplit(url).query, keep_blank_values=True
    ):
        if value and SECRET_KEY_PATTERN.search(key):
            sanitized = sanitized.replace(value, "<redacted>")
    return sanitized.strip()


def fetch_json_with_curl(
    name: str,
    url: str,
    headers: dict[str, str],
    timeout: float,
) -> EndpointResult:
    started = time.perf_counter()
    marker = b"\n__EXFLOW_AUDIT_META__\t"
    config_lines = [
        f'url = "{curl_config_quote(url)}"',
        'header = "Accept: application/json"',
        'user-agent = "ExFlow-API-Audit/1.0"',
    ]
    for key, value in headers.items():
        config_lines.append(
            f'header = "{curl_config_quote(key)}: {curl_config_quote(value)}"'
        )
    config = ("\n".join(config_lines) + "\n").encode("utf-8")
    command = [
        "curl",
        "--config",
        "-",
        "--silent",
        "--show-error",
        "--location",
        "--max-time",
        str(timeout),
        "--max-filesize",
        "5000001",
        "--output",
        "-",
        "--write-out",
        "\\n__EXFLOW_AUDIT_META__\\t%{http_code}\\t%{content_type}\\t%{time_total}",
    ]
    try:
        completed = subprocess.run(
            command,
            input=config,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout + 3,
        )
    except Exception as error:
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=None,
            content_type="",
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=0,
            error=f"curl execution failed: {type(error).__name__}",
        )

    stdout = completed.stdout
    if marker not in stdout:
        error_text = sanitize_transport_error(
            completed.stderr.decode("utf-8", errors="replace"), url, headers
        )
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=None,
            content_type="",
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=0,
            error=f"curl {completed.returncode}: {error_text or 'response metadata missing'}",
        )

    raw, meta = stdout.rsplit(marker, 1)
    meta_parts = meta.decode("utf-8", errors="replace").split("\t")
    try:
        status = int(meta_parts[0])
        content_type = meta_parts[1]
        latency_ms = round(float(meta_parts[2]) * 1000)
    except (IndexError, TypeError, ValueError):
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=None,
            content_type="",
            latency_ms=round((time.perf_counter() - started) * 1000),
            payload_bytes=len(raw),
            error="curl response metadata malformed",
        )

    if completed.returncode != 0:
        error_text = sanitize_transport_error(
            completed.stderr.decode("utf-8", errors="replace"), url, headers
        )
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=status or None,
            content_type=content_type,
            latency_ms=latency_ms,
            payload_bytes=len(raw),
            error=f"curl {completed.returncode}: {error_text or 'request failed'}",
        )
    if not 200 <= status < 300:
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=status,
            content_type=content_type,
            latency_ms=latency_ms,
            payload_bytes=len(raw),
            error=f"HTTP {status}",
        )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as error:
        return EndpointResult(
            name=name,
            display_url=safe_display_url(url),
            status=status,
            content_type=content_type,
            latency_ms=latency_ms,
            payload_bytes=len(raw),
            error=f"Некорректный JSON: {type(error).__name__}",
        )
    return EndpointResult(
        name=name,
        display_url=safe_display_url(url),
        status=status,
        content_type=content_type,
        latency_ms=latency_ms,
        payload_bytes=len(raw),
        payload=payload,
    )


def audit_transport(auditor: Auditor, result: EndpointResult) -> None:
    if result.error:
        auditor.add(
            "CRITICAL",
            "ENDPOINT_UNAVAILABLE",
            result.name,
            "$",
            f"Ответ невозможно проверить: {result.error}",
            "HTTP 2xx и корректный JSON.",
            "Проверить доступность, авторизацию, status code и JSON-сериализацию ответа.",
        )
        return
    if result.status is None or not 200 <= result.status < 300:
        auditor.add(
            "CRITICAL",
            "UNEXPECTED_HTTP_STATUS",
            result.name,
            "$",
            f"Получен HTTP status {result.status}.",
            "HTTP 2xx.",
            "Исправить status code или причину серверной ошибки.",
        )
    if "json" not in result.content_type.lower() and result.mode == "live":
        auditor.add(
            "MEDIUM",
            "NON_JSON_CONTENT_TYPE",
            result.name,
            "$",
            f"Content-Type не обозначает JSON: {result.content_type or '<empty>'}.",
            "Content-Type: application/json.",
            "Установить корректный Content-Type для JSON-ответа.",
        )
    if result.latency_ms > 12_000:
        severity = "HIGH"
    elif result.latency_ms > 5_000:
        severity = "MEDIUM"
    else:
        severity = ""
    if severity:
        auditor.add(
            severity,
            "HIGH_LATENCY",
            result.name,
            "$",
            f"Ответ получен за {result.latency_ms} мс.",
            "Стабильный ответ быстрее 5000 мс.",
            "Проверить cold start, внешние зависимости, индексы и server timing.",
            heuristic=True,
        )
    if result.payload_bytes > 5_000_000:
        auditor.add(
            "MEDIUM",
            "OVERSIZED_PAYLOAD",
            result.name,
            "$",
            f"Размер ответа превышает 5 MB ({result.payload_bytes} bytes).",
            "Ограниченный и предсказуемый размер ответа.",
            "Добавить pagination, фильтрацию или лимит периода.",
            heuristic=True,
        )


def normalized_rate_codes(auditor: Auditor, result: EndpointResult) -> set[str]:
    if result.error:
        return set()
    payload = result.payload
    if not isinstance(payload, dict):
        auditor.add(
            "CRITICAL",
            "RATES_ROOT_TYPE",
            "rates",
            "$",
            f"Корень ответа имеет тип {type(payload).__name__}.",
            "JSON object с полем rates.",
            "Вернуть объект согласованной схемы.",
            payload,
        )
        return set()
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        auditor.add(
            "CRITICAL",
            "RATES_FIELD_TYPE",
            "rates",
            "$.rates",
            "Поле rates отсутствует или не является object.",
            "Object: currency code -> positive numeric value.",
            "Вернуть обязательное поле rates правильного типа.",
            rates,
        )
        return set()

    valid: set[str] = set()
    variants: dict[str, set[str]] = collections.defaultdict(set)
    non_iso_codes: list[str] = []
    for raw_code, raw_rate in rates.items():
        code = str(raw_code).strip().upper()
        variants[code].add(str(raw_code))
        location = f"$.rates.{raw_code}"
        is_iso = bool(CURRENCY_PATTERN.fullmatch(code) and code in ISO_4217_CODES)
        if not is_iso:
            non_iso_codes.append(code or "<empty>")
            continue
        if str(raw_code) != code:
            auditor.add(
                "MEDIUM",
                "RATE_CURRENCY_CASE",
                "rates",
                location,
                "Код валюты содержит пробелы или записан не в верхнем регистре.",
                "Трёхбуквенный uppercase ISO 4217 code.",
                "Нормализовать ключи rates на стороне API.",
                raw_code,
            )
        if isinstance(raw_rate, bool):
            numeric_rate = math.nan
        else:
            try:
                numeric_rate = float(raw_rate)
            except (TypeError, ValueError):
                numeric_rate = math.nan
        if not math.isfinite(numeric_rate) or numeric_rate <= 0:
            auditor.add(
                "HIGH",
                "RATE_INVALID_VALUE",
                "rates",
                location,
                "Курс не преобразуется в конечное положительное число.",
                "Number или numeric string больше нуля.",
                "Исправить источник курса и серверную валидацию перед ответом.",
                raw_rate,
            )
            continue
        valid.add(code)

    for code, raw_variants in variants.items():
        if len(raw_variants) > 1:
            auditor.add(
                "HIGH",
                "RATE_DUPLICATE_CURRENCY_KEYS",
                "rates",
                "$.rates",
                f"Одна валюта {code} представлена несколькими вариантами ключа.",
                "Один канонический uppercase key на валюту.",
                "Дедуплицировать ключи после нормализации регистра.",
                sorted(raw_variants),
            )
    if non_iso_codes:
        auditor.add(
            "INFO",
            "RATE_NON_ISO_INSTRUMENTS_PRESENT",
            "rates",
            "$.rates",
            f"Rates provider содержит {len(non_iso_codes)} non-ISO instrument/crypto codes; они исключены из валютной проверки.",
            "Это допустимо для универсального rates provider; финансовые источники должны использовать ISO 4217.",
            "Не считать эти keys ошибкой. Проверять только валюты, фактически встречающиеся в finance1/finance2.",
            sorted(non_iso_codes)[:10],
        )
    return valid


def audit_currency(
    auditor: Auditor,
    endpoint: str,
    location: str,
    raw_currency: Any,
    valid_rate_codes: set[str],
    *,
    report_noncanonical: bool = True,
) -> str | None:
    if not isinstance(raw_currency, str) or not raw_currency:
        auditor.add(
            "HIGH",
            "CURRENCY_TYPE",
            endpoint,
            location,
            "Код валюты отсутствует или не является строкой.",
            "Трёхбуквенный uppercase ISO 4217 code.",
            "Валидировать и сериализовать currency как строку.",
            raw_currency,
        )
        return None
    code = raw_currency.strip().upper()
    if raw_currency != code and report_noncanonical:
        auditor.add(
            "MEDIUM",
            "CURRENCY_NON_CANONICAL",
            endpoint,
            location,
            "Код валюты содержит пробелы или записан не в верхнем регистре.",
            "Трёхбуквенный uppercase ISO 4217 code без пробелов.",
            "Нормализовать currency до отправки ответа.",
            raw_currency,
        )
    if not CURRENCY_PATTERN.fullmatch(code) or code not in ISO_4217_CODES:
        auditor.add(
            "HIGH",
            "UNKNOWN_CURRENCY",
            endpoint,
            location,
            f"Код {code or '<empty>'} не распознан как ISO 4217.",
            "Действующий трёхбуквенный ISO 4217 code.",
            "Исправить mapping валют и добавить server-side allowlist.",
            raw_currency,
        )
        return code
    if code != "USD" and code not in valid_rate_codes:
        auditor.add(
            "HIGH",
            "MISSING_EXCHANGE_RATE",
            endpoint,
            location,
            f"Для валюты {code} нет валидного курса в текущем rates payload.",
            "Каждая non-USD валюта источника присутствует в rates с валидным курсом.",
            "Синхронизировать набор валют или не отдавать операцию до появления курса.",
            raw_currency,
        )
    return code


def audit_source_one(
    auditor: Auditor,
    result: EndpointResult,
    valid_rate_codes: set[str],
) -> int:
    if result.error:
        return 0
    payload = result.payload
    if not isinstance(payload, dict):
        auditor.add(
            "CRITICAL",
            "FINANCE1_ROOT_TYPE",
            "finance1",
            "$",
            f"Корень ответа имеет тип {type(payload).__name__}.",
            "Object с массивом transactions.",
            "Вернуть согласованный корневой объект.",
            payload,
        )
        return 0
    transactions = payload.get("transactions")
    if not isinstance(transactions, list):
        auditor.add(
            "CRITICAL",
            "TRANSACTIONS_FIELD_TYPE",
            "finance1",
            "$.transactions",
            "Поле transactions отсутствует или не является array.",
            "Array объектов транзакций.",
            "Вернуть обязательный массив transactions.",
            transactions,
        )
        return 0

    status_variants: dict[str, set[str]] = collections.defaultdict(set)
    fingerprints: collections.Counter[tuple[Any, Any, Any]] = collections.Counter()
    unexpected_keys: set[str] = set()

    for index, transaction in enumerate(transactions):
        base = f"$.transactions[{index}]"
        if not isinstance(transaction, dict):
            auditor.add(
                "HIGH",
                "TRANSACTION_TYPE",
                "finance1",
                base,
                "Элемент transactions не является object.",
                "Object с type, amount и currency.",
                "Исправить сериализацию списка транзакций.",
                transaction,
            )
            continue
        unexpected_keys.update(set(map(str, transaction)) - {"type", "amount", "currency"})
        raw_type = transaction.get("type")
        raw_amount = transaction.get("amount")
        raw_currency = transaction.get("currency")
        fingerprints[(safe_sample(raw_type), safe_sample(raw_amount), safe_sample(raw_currency))] += 1

        if not isinstance(raw_type, str) or not raw_type:
            auditor.add(
                "HIGH",
                "STATUS_TYPE",
                "finance1",
                f"{base}.type",
                "type отсутствует или не является непустой строкой.",
                "Непустой строковый status; для оплаты канонически paid.",
                "Исправить тип и обязательность поля type.",
                raw_type,
            )
        else:
            normalized_type = raw_type.strip().casefold()
            status_variants[normalized_type].add(raw_type)
            if raw_type != raw_type.strip():
                auditor.add(
                    "HIGH",
                    "STATUS_WHITESPACE",
                    "finance1",
                    f"{base}.type",
                    "Status содержит пробелы по краям и не будет распознан текущим фильтром.",
                    "Строка без leading/trailing whitespace.",
                    "Обрезать пробелы до сериализации.",
                    raw_type,
                )

        if isinstance(raw_amount, bool) or not isinstance(raw_amount, (int, float)):
            auditor.add(
                "HIGH",
                "AMOUNT_TYPE",
                "finance1",
                f"{base}.amount",
                "amount отсутствует или не является JSON number.",
                "Конечное JSON number.",
                "Сериализовать amount числом, не numeric string.",
                raw_amount,
            )
        elif not math.isfinite(float(raw_amount)):
            auditor.add(
                "HIGH",
                "AMOUNT_NON_FINITE",
                "finance1",
                f"{base}.amount",
                "amount не является конечным числом.",
                "Конечное JSON number.",
                "Отклонять NaN и infinity на сервере.",
                raw_amount,
            )
        else:
            amount = float(raw_amount)
            if amount <= 0:
                auditor.add(
                    "MEDIUM",
                    "AMOUNT_NON_POSITIVE",
                    "finance1",
                    f"{base}.amount",
                    f"Обнаружена неположительная сумма {amount}.",
                    "Положительная сумма либо документированная корректировка/refund.",
                    "Уточнить бизнес-семантику и использовать отдельный type для корректировок.",
                    raw_amount,
                    heuristic=True,
                )
            decimals = str(raw_amount).partition(".")[2].rstrip("0")
            if len(decimals) > 2:
                auditor.add(
                    "LOW",
                    "AMOUNT_PRECISION",
                    "finance1",
                    f"{base}.amount",
                    "Сумма содержит более двух значащих десятичных знаков.",
                    "Денежная precision, согласованная контрактом.",
                    "Документировать precision или округлять на стороне источника.",
                    raw_amount,
                    heuristic=True,
                )

        code = audit_currency(
            auditor,
            "finance1",
            f"{base}.currency",
            raw_currency,
            valid_rate_codes,
        )
        if code:
            auditor.source_currencies["finance1"].add(code)

    for normalized, variants in status_variants.items():
        if len(variants) > 1 or (normalized == "paid" and variants != {"paid"}):
            auditor.add(
                "MEDIUM",
                "STATUS_CASE_VARIANTS",
                "finance1",
                "$.transactions[*].type",
                f"Один status представлен разными вариантами: {', '.join(sorted(variants))}.",
                f"Один канонический вариант: {normalized}.",
                "Нормализовать status на стороне API и закрепить enum в контракте.",
                sorted(variants),
            )
    for fingerprint, count in fingerprints.items():
        if count > 1:
            auditor.add(
                "LOW",
                "POTENTIAL_DUPLICATE",
                "finance1",
                "$.transactions",
                f"Идентичное сочетание type/amount/currency встречается {count} раз.",
                "Уникальные операции либо стабильный transaction ID для дедупликации.",
                "Проверить источник; добавить transaction ID, если повторы допустимы.",
                fingerprint,
                heuristic=True,
            )
    if unexpected_keys:
        auditor.add(
            "INFO",
            "ADDITIONAL_FIELDS",
            "finance1",
            "$.transactions[*]",
            "Обнаружены поля вне минимального контракта.",
            "Документированная схема и versioning при её расширении.",
            "Задокументировать дополнительные поля; не удалять их только из-за этого finding.",
            sorted(unexpected_keys),
        )
    return len(transactions)


def audit_source_two(
    auditor: Auditor,
    result: EndpointResult,
    valid_rate_codes: set[str],
) -> int:
    if result.error:
        return 0
    payload = result.payload
    if not isinstance(payload, list):
        auditor.add(
            "CRITICAL",
            "FINANCE2_ROOT_TYPE",
            "finance2",
            "$",
            f"Корень ответа имеет тип {type(payload).__name__}.",
            "Array строк '<amount> <CURRENCY>'.",
            "Вернуть согласованный корневой массив.",
            payload,
        )
        return 0

    fingerprints: collections.Counter[str] = collections.Counter()
    for index, entry in enumerate(payload):
        location = f"$[{index}]"
        if not isinstance(entry, str):
            auditor.add(
                "HIGH",
                "FINANCE2_ENTRY_TYPE",
                "finance2",
                location,
                "Элемент не является строкой.",
                "Строка '<positive amount> <uppercase ISO code>'.",
                "Сериализовать все элементы единообразно или перейти на object schema.",
                entry,
            )
            continue
        fingerprints[entry] += 1
        loose = SOURCE_TWO_LOOSE_PATTERN.fullmatch(entry)
        canonical = SOURCE_TWO_CANONICAL_PATTERN.fullmatch(entry)
        if not loose:
            auditor.add(
                "HIGH",
                "FINANCE2_FORMAT",
                "finance2",
                location,
                "Строка не соответствует распознаваемому формату amount + currency.",
                "Например: '120.50 EUR'.",
                "Лучше вернуть структурированный object; минимум — исправить формат строки.",
                entry,
            )
            continue
        raw_amount, raw_currency = loose.groups()
        if not canonical:
            reasons: list[str] = []
            if entry != entry.strip() or re.search(r"\s{2,}", entry):
                reasons.append("лишние пробелы")
            if "," in raw_amount:
                reasons.append("запятая как decimal separator")
            if raw_currency != raw_currency.upper():
                reasons.append("неверхний регистр валюты")
            if raw_amount.startswith(('+', '-')):
                reasons.append("явный знак суммы")
            auditor.add(
                "HIGH" if "," in raw_amount or raw_amount.startswith(('+', '-')) else "MEDIUM",
                "FINANCE2_NON_CANONICAL",
                "finance2",
                location,
                "Формат неканонический" + (f": {', '.join(reasons)}." if reasons else "."),
                "Один пробел, decimal point, положительная сумма, uppercase ISO code.",
                "Нормализовать сериализацию или заменить строку на object schema.",
                entry,
            )
        amount = float(raw_amount.replace(",", "."))
        if amount <= 0:
            auditor.add(
                "MEDIUM",
                "FINANCE2_NON_POSITIVE",
                "finance2",
                location,
                f"Обнаружена неположительная сумма {amount}.",
                "Положительная сумма либо отдельный документированный тип корректировки.",
                "Уточнить бизнес-семантику и не кодировать refund знаком в строке.",
                entry,
                heuristic=True,
            )
        code = audit_currency(
            auditor,
            "finance2",
            location,
            raw_currency,
            valid_rate_codes,
            report_noncanonical=False,
        )
        if code:
            auditor.source_currencies["finance2"].add(code)

    for entry, count in fingerprints.items():
        if count > 1:
            auditor.add(
                "LOW",
                "POTENTIAL_DUPLICATE",
                "finance2",
                "$",
                f"Идентичная строка встречается {count} раз.",
                "Уникальные операции либо стабильный transaction ID.",
                "Проверить источник; перейти на object schema с ID.",
                entry,
                heuristic=True,
            )
    return len(payload)


def severity_counts(findings: Iterable[Finding]) -> dict[str, int]:
    counter = collections.Counter(finding.severity for finding in findings)
    return {severity: counter.get(severity, 0) for severity in SEVERITY_ORDER}


def overall_status(counts: dict[str, int]) -> str:
    if counts["CRITICAL"]:
        return "Критическое состояние: часть API или обязательных структур недоступна"
    if counts["HIGH"]:
        return "Требуется исправление: найдены данные, нарушающие основной контракт"
    if counts["MEDIUM"]:
        return "Нужна унификация: найдены значимые проблемы консистентности"
    if counts["LOW"]:
        return "Основной контракт соблюдён, есть некритичные наблюдения"
    return "Проблем по проверяемым правилам не обнаружено"


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_markdown(
    generated_at: dt.datetime,
    mode: str,
    endpoints: list[EndpointResult],
    auditor: Auditor,
    record_counts: dict[str, int],
) -> str:
    findings = sorted(
        auditor.findings,
        key=lambda item: (SEVERITY_ORDER[item.severity], item.endpoint, item.location, item.code),
    )
    counts = severity_counts(findings)
    lines = [
        "# Отчёт об аудите финансовых API ExFlow",
        "",
        "## Резюме",
        "",
        f"- Время проверки (UTC): `{generated_at.isoformat().replace('+00:00', 'Z')}`",
        f"- Режим: `{'live API' if mode == 'live' else 'локальные JSON-снимки'}`",
        f"- Итог: **{overall_status(counts)}**",
        f"- Findings: CRITICAL `{counts['CRITICAL']}`, HIGH `{counts['HIGH']}`, MEDIUM `{counts['MEDIUM']}`, LOW `{counts['LOW']}`, INFO `{counts['INFO']}`",
        f"- Проверено записей: finance1 `{record_counts.get('finance1', 0)}`, finance2 `{record_counts.get('finance2', 0)}`",
        "",
        "> Полные API payload, заголовки авторизации и секреты намеренно не включены. Примеры сокращены и очищены.",
        "",
        "## Состояние endpoints",
        "",
        "| Endpoint | Источник | HTTP | Content-Type | Latency | Размер |",
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for endpoint in endpoints:
        lines.append(
            "| "
            + " | ".join(
                [
                    endpoint.name,
                    markdown_escape(endpoint.display_url),
                    str(endpoint.status) if endpoint.status is not None else "нет",
                    markdown_escape(endpoint.content_type or "нет"),
                    f"{endpoint.latency_ms} ms",
                    f"{endpoint.payload_bytes} B",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Найденные проблемы", ""])
    if not findings:
        lines.append("По текущим правилам проблемы не обнаружены.")
    else:
        lines.extend(
            [
                "| № | Severity | Code | Endpoint | Location | Проблема |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for number, finding in enumerate(findings, 1):
            marker = " (эвристика)" if finding.heuristic else ""
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(number),
                        finding.severity,
                        finding.code,
                        finding.endpoint,
                        markdown_escape(finding.location),
                        markdown_escape(finding.problem + marker),
                    ]
                )
                + " |"
            )
        lines.extend(["", "## Детали findings", ""])
        for number, finding in enumerate(findings, 1):
            if finding.severity == "INFO":
                classification = "информационное наблюдение"
            elif finding.heuristic:
                classification = "эвристическое наблюдение"
            else:
                classification = "нарушение/риск контракта"
            lines.extend(
                [
                    f"### {number}. [{finding.severity}] {finding.code}",
                    "",
                    f"- Endpoint: `{finding.endpoint}`",
                    f"- Location: `{finding.location}`",
                    f"- Классификация: `{classification}`",
                    f"- Проблема: {finding.problem}",
                    f"- Ожидание: {finding.expected}",
                    f"- Рекомендация: {finding.recommendation}",
                ]
            )
            if finding.sample:
                lines.append(f"- Сокращённый пример: `{finding.sample.replace('`', "'")}`")
            lines.append("")

    actionable = [finding for finding in findings if finding.severity in {"CRITICAL", "HIGH", "MEDIUM"}]
    lines.extend(["## Рекомендуемый порядок исправления", ""])
    if actionable:
        unique_actions: list[str] = []
        for finding in actionable:
            action = finding.recommendation.rstrip(".") + "."
            if action not in unique_actions:
                unique_actions.append(action)
        for number, action in enumerate(unique_actions, 1):
            lines.append(f"{number}. {action}")
    else:
        lines.append("1. Критичных действий не требуется; рассмотреть LOW/INFO наблюдения при следующем обновлении контракта.")

    all_currencies = sorted(set().union(*auditor.source_currencies.values()))
    lines.extend(
        [
            "",
            "## Наблюдаемое покрытие валют",
            "",
            f"- Finance 1: `{', '.join(sorted(auditor.source_currencies['finance1'])) or 'нет данных'}`",
            f"- Finance 2: `{', '.join(sorted(auditor.source_currencies['finance2'])) or 'нет данных'}`",
            f"- Всего в источниках: `{', '.join(all_currencies) or 'нет данных'}`",
            "",
            "## Методика и ограничения",
            "",
            "- Проверка является снимком состояния на указанное время и не доказывает стабильность API за другой период.",
            "- Потенциальные дубликаты определяются без transaction ID и требуют проверки backend-командой.",
            "- ISO 4217 allowlist встроен в аудитор; нестандартные instrument codes требуют отдельной документации.",
            "- Non-`paid` статусы не считаются ошибкой сами по себе.",
            "- Отчёт оценивает контракт и качество данных, но не заменяет server logs, tracing и бизнес-сверку.",
            "",
            "## Критерий повторной проверки",
            "",
            "После исправлений повторить live-аудит и ожидать отсутствия CRITICAL/HIGH, единого регистра статусов и валют, валидных курсов для всех non-USD операций и стабильной JSON-схемы.",
            "",
        ]
    )
    return "\n".join(lines)


def finding_to_dict(finding: Finding) -> dict[str, Any]:
    return dataclasses.asdict(finding)


def endpoint_to_dict(endpoint: EndpointResult) -> dict[str, Any]:
    return {
        "name": endpoint.name,
        "url": endpoint.display_url,
        "status": endpoint.status,
        "content_type": endpoint.content_type,
        "latency_ms": endpoint.latency_ms,
        "payload_bytes": endpoint.payload_bytes,
        "error": endpoint.error,
        "mode": endpoint.mode,
    }


def threshold_failed(findings: list[Finding], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    threshold = SEVERITY_ORDER[fail_on.upper()]
    return any(SEVERITY_ORDER[finding.severity] <= threshold for finding in findings)


def main() -> int:
    args = parse_args()
    snapshot_paths = [args.source_one_file, args.source_two_file, args.rates_file]
    if any(snapshot_paths) and not all(snapshot_paths):
        raise SystemExit(
            "Для snapshot-режима одновременно укажите --source-one-file, --source-two-file и --rates-file."
        )

    generated_at = dt.datetime.now(dt.timezone.utc)
    mode = "snapshot" if all(snapshot_paths) else "live"

    if mode == "snapshot":
        endpoints = [
            read_snapshot("finance1", args.source_one_file),
            read_snapshot("finance2", args.source_two_file),
            read_snapshot("rates", args.rates_file),
        ]
    else:
        env_values = load_env_file(Path(args.env_file))
        finance_key = get_secret("EXFLOW_FINANCE_API_KEY", env_values)
        rates_key = get_secret("EXFLOW_RATES_API_KEY", env_values)
        auditor = Auditor()
        if not finance_key:
            auditor.add(
                "CRITICAL",
                "MISSING_FINANCE_API_KEY",
                "configuration",
                "EXFLOW_FINANCE_API_KEY",
                "Finance API key отсутствует.",
                "Серверная переменная с непустым значением.",
                "Настроить ключ в окружении или .env.local, не раскрывая его.",
            )
        if not rates_key:
            auditor.add(
                "CRITICAL",
                "MISSING_RATES_API_KEY",
                "configuration",
                "EXFLOW_RATES_API_KEY",
                "Rates API key отсутствует.",
                "Серверная переменная с непустым значением.",
                "Настроить ключ в окружении или .env.local, не раскрывая его.",
            )
        if not finance_key or not rates_key:
            endpoints = []
            record_counts = {"finance1": 0, "finance2": 0}
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            report_name = args.report_name or f"financial-api-audit-{generated_at:%Y%m%d-%H%M%SZ}"
            markdown = build_markdown(generated_at, mode, endpoints, auditor, record_counts)
            md_path = output_dir / f"{report_name}.md"
            json_path = output_dir / f"{report_name}.json"
            md_path.write_text(markdown, encoding="utf-8")
            json_path.write_text(
                json.dumps(
                    {
                        "generated_at": generated_at.isoformat(),
                        "mode": mode,
                        "summary": severity_counts(auditor.findings),
                        "endpoints": [],
                        "findings": [finding_to_dict(item) for item in auditor.findings],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print(md_path)
            print(json_path)
            return 1

        rates_query = urllib.parse.urlencode({"apikey": rates_key})
        rates_url = args.rates_url + ("&" if "?" in args.rates_url else "?") + rates_query
        endpoints = [
            fetch_json("finance1", args.source_one_url, {"x-api-key": finance_key}, args.timeout),
            fetch_json("finance2", args.source_two_url, {"x-api-key": finance_key}, args.timeout),
            fetch_json("rates", rates_url, {}, args.timeout),
        ]

    auditor = locals().get("auditor") or Auditor()
    for endpoint in endpoints:
        audit_transport(auditor, endpoint)
    endpoint_map = {endpoint.name: endpoint for endpoint in endpoints}
    rates_codes = normalized_rate_codes(auditor, endpoint_map["rates"])
    record_counts = {
        "finance1": audit_source_one(auditor, endpoint_map["finance1"], rates_codes),
        "finance2": audit_source_two(auditor, endpoint_map["finance2"], rates_codes),
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_name = args.report_name or f"financial-api-audit-{generated_at:%Y%m%d-%H%M%SZ}"
    md_path = output_dir / f"{report_name}.md"
    json_path = output_dir / f"{report_name}.json"
    md_path.write_text(
        build_markdown(generated_at, mode, endpoints, auditor, record_counts),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "generated_at": generated_at.isoformat(),
                "mode": mode,
                "record_counts": record_counts,
                "summary": severity_counts(auditor.findings),
                "source_currencies": {
                    key: sorted(value) for key, value in auditor.source_currencies.items()
                },
                "endpoints": [endpoint_to_dict(item) for item in endpoints],
                "findings": [finding_to_dict(item) for item in auditor.findings],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(md_path)
    print(json_path)
    return 1 if threshold_failed(auditor.findings, args.fail_on) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Аудит прерван пользователем.", file=sys.stderr)
        raise SystemExit(130)
