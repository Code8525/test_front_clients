#!/usr/bin/env python3
"""
Тесты валидации и бизнес-ошибок API клиентов.
- Валидация: ИНН не более 12 символов (422, errorName=VALIDATION_ERROR).
- Бизнес: дубликат имени/ИНН, клиент не найден, родитель не найден (409/404, errorName).

Ответы API в camelCase: errorName, clientId, errors[].field, message.
Запуск: python scripts/test_validation_errors.py
Сервер: http://127.0.0.1:8000
"""
import json
import uuid
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def request(method: str, path: str, body: dict | None = None) -> tuple[int, dict | None]:
    """Выполнить HTTP-запрос, вернуть (status_code, json_body или None)."""
    url = f"{BASE}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if not raw:
                return resp.status, None
            return resp.status, json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            body_res = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:
            body_res = None
        return e.code, body_res
    except urllib.error.URLError as e:
        print(f"Ошибка соединения: {e}")
        raise


def get_first_region_id() -> str | None:
    """Получить id первого региона."""
    status, data = request("GET", "/api/regions")
    if status != 200 or not data:
        return None
    items = data.get("items") or []
    if not items:
        return None
    return items[0]["id"]


def main() -> None:
    print("=== Тесты валидации и бизнес-ошибок на", BASE, "===\n")

    region_id = get_first_region_id()
    if not region_id:
        print("Пропуск: нет регионов в БД")
        return

    failed = 0

    # --- Валидация: ИНН не более 12 символов ---
    print("1. Валидация: ИНН > 12 символов (POST)")
    status, data = request(
        "POST",
        "/api/clients",
        {
            "name": f"Тест ИНН длинный {uuid.uuid4().hex[:6]}",
            "full_name": "ООО Тест",
            "party_type": "legal",
            "inn": "1234567890123",  # 13 символов
            "region_id": region_id,
        },
    )
    if status != 422:
        print("   ОШИБКА: ожидался 422, получен", status, data)
        failed += 1
    elif not data or data.get("errorName") != "VALIDATION_ERROR":
        print("   ОШИБКА: ожидался errorName=VALIDATION_ERROR, получено", data)
        failed += 1
    else:
        inn_errors = [e for e in (data.get("errors") or []) if "inn" in e.get("field", "").lower()]
        if not inn_errors:
            print("   ОШИБКА: в details нет ошибки по полю inn", data.get("errors"))
            failed += 1
        else:
            print("   OK: 422, VALIDATION_ERROR, ошибка по полю inn")

    print("2. Валидация: ИНН > 12 символов (PATCH)")
    # Сначала создаём клиента с валидным уникальным ИНН
    unique_name = f"Тест PATCH ИНН {uuid.uuid4().hex[:8]}"
    inn_patch_ok = "77" + str(uuid.uuid4().int % 10**8).zfill(8)
    status, created = request(
        "POST",
        "/api/clients",
        {
            "name": unique_name,
            "full_name": "ООО Тест PATCH",
            "party_type": "legal",
            "inn": inn_patch_ok,
            "region_id": region_id,
        },
    )
    if status != 201:
        print("   ОШИБКА: не удалось создать клиента для PATCH", status, created)
        failed += 1
    else:
        client_id = created["clientId"]
        status, data = request(
            "PATCH",
            f"/api/clients/{client_id}",
            {"inn": "1234567890123"},
        )
        request("DELETE", f"/api/clients/{client_id}")
        if status != 422:
            print("   ОШИБКА: ожидался 422, получен", status, data)
            failed += 1
        elif not data or data.get("errorName") != "VALIDATION_ERROR":
            print("   ОШИБКА: ожидался errorName=VALIDATION_ERROR, получено", data)
            failed += 1
        else:
            print("   OK: 422, VALIDATION_ERROR при PATCH с длинным ИНН")

    # --- Валидация: ИНН ровно 12 символов — допустимо ---
    print("3. Валидация: ИНН ровно 12 символов — допустимо")
    inn_12 = str(uuid.uuid4().int % 10**12).zfill(12)
    status, created = request(
        "POST",
        "/api/clients",
        {
            "name": f"Тест ИНН 12 символов {uuid.uuid4().hex[:6]}",
            "full_name": "ООО Тест 12",
            "party_type": "legal",
            "inn": inn_12,
            "region_id": region_id,
        },
    )
    if status != 201:
        print("   ОШИБКА: ИНН из 12 символов должен быть принят", status, created)
        failed += 1
    else:
        request("DELETE", f"/api/clients/{created['clientId']}")
        print("   OK: 201, клиент создан и удалён")

    # --- Бизнес-ошибки: дубликат имени ---
    print("4. Бизнес: дубликат имени (ClientAlreadyExists)")
    name_unique = f"Уникальное имя {uuid.uuid4().hex[:8]}"
    inn_first = "77" + str(uuid.uuid4().int % 10**8).zfill(8)
    status, c1 = request(
        "POST",
        "/api/clients",
        {
            "name": name_unique,
            "full_name": "ООО Первый",
            "party_type": "legal",
            "inn": inn_first,
            "region_id": region_id,
        },
    )
    if status != 201:
        print("   ОШИБКА: не удалось создать первого клиента", status, c1)
        failed += 1
    else:
        status, data = request(
            "POST",
            "/api/clients",
            {
                "name": name_unique,
                "full_name": "ООО Второй",
                "party_type": "legal",
                "inn": "77" + str(uuid.uuid4().int % 10**8).zfill(8),
                "region_id": region_id,
            },
        )
        request("DELETE", f"/api/clients/{c1['clientId']}")
        if status != 409:
            print("   ОШИБКА: ожидался 409, получен", status, data)
            failed += 1
        elif not data or data.get("errorName") != "CLIENT_ALREADY_EXISTS":
            print("   ОШИБКА: ожидался errorName=CLIENT_ALREADY_EXISTS, получено", data)
            failed += 1
        else:
            print("   OK: 409, CLIENT_ALREADY_EXISTS")

    # --- Бизнес-ошибки: дубликат ИНН ---
    print("5. Бизнес: дубликат ИНН (ClientAlreadyExistsByInn)")
    inn_unique = "77" + str(uuid.uuid4().int % 10**8).zfill(8)
    status, c1 = request(
        "POST",
        "/api/clients",
        {
            "name": f"Клиент А {uuid.uuid4().hex[:6]}",
            "full_name": "ООО А",
            "party_type": "legal",
            "inn": inn_unique,
            "region_id": region_id,
        },
    )
    if status != 201:
        print("   ОШИБКА: не удалось создать клиента с ИНН", status, c1)
        failed += 1
    else:
        status, data = request(
            "POST",
            "/api/clients",
            {
                "name": f"Клиент Б {uuid.uuid4().hex[:6]}",
                "full_name": "ООО Б",
                "party_type": "legal",
                "inn": inn_unique,
                "region_id": region_id,
            },
        )
        request("DELETE", f"/api/clients/{c1['clientId']}")
        if status != 409:
            print("   ОШИБКА: ожидался 409, получен", status, data)
            failed += 1
        elif not data or data.get("errorName") != "CLIENT_ALREADY_EXISTS_BY_INN":
            print("   ОШИБКА: ожидался errorName=CLIENT_ALREADY_EXISTS_BY_INN, получено", data)
            failed += 1
        else:
            print("   OK: 409, CLIENT_ALREADY_EXISTS_BY_INN")

    # --- Бизнес-ошибки: клиент не найден ---
    print("6. Бизнес: клиент не найден (ClientNotFound)")
    fake_id = str(uuid.uuid4())
    status, data = request("GET", f"/api/clients/{fake_id}")
    if status != 404:
        print("   ОШИБКА: ожидался 404, получен", status, data)
        failed += 1
    elif not data or data.get("errorName") != "CLIENT_NOT_FOUND":
        print("   ОШИБКА: ожидался errorName=CLIENT_NOT_FOUND, получено", data)
        failed += 1
    else:
        print("   OK: 404, CLIENT_NOT_FOUND")

    # --- Бизнес-ошибки: родительский клиент не найден ---
    print("7. Бизнес: родительский клиент не найден при создании (ParentClientNotFound)")
    fake_parent_id = str(uuid.uuid4())
    inn_child = "77" + str(uuid.uuid4().int % 10**8).zfill(8)
    status, data = request(
        "POST",
        "/api/clients",
        {
            "name": f"Дочерний {uuid.uuid4().hex[:6]}",
            "full_name": "ООО Дочерний",
            "party_type": "legal",
            "inn": inn_child,
            "region_id": region_id,
            "parent_id": fake_parent_id,
        },
    )
    if status != 404:
        print("   ОШИБКА: ожидался 404, получен", status, data)
        failed += 1
    elif not data or data.get("errorName") != "PARENT_CLIENT_NOT_FOUND":
        print("   ОШИБКА: ожидался errorName=PARENT_CLIENT_NOT_FOUND, получено", data)
        failed += 1
    else:
        print("   OK: 404, PARENT_CLIENT_NOT_FOUND")

    # --- Бизнес-ошибки: родитель не найден при PATCH ---
    print("8. Бизнес: родительский клиент не найден при обновлении")
    inn_patch_parent = "77" + str(uuid.uuid4().int % 10**8).zfill(8)
    status, created = request(
        "POST",
        "/api/clients",
        {
            "name": f"Для PATCH parent {uuid.uuid4().hex[:6]}",
            "full_name": "ООО Тест",
            "party_type": "legal",
            "inn": inn_patch_parent,
            "region_id": region_id,
        },
    )
    if status != 201:
        print("   ОШИБКА: не удалось создать клиента", status, created)
        failed += 1
    else:
        status, data = request(
            "PATCH",
            f"/api/clients/{created['clientId']}",
            {"parent_id": str(uuid.uuid4())},
        )
        request("DELETE", f"/api/clients/{created['clientId']}")
        if status != 404:
            print("   ОШИБКА: ожидался 404, получен", status, data)
            failed += 1
        elif not data or data.get("errorName") != "PARENT_CLIENT_NOT_FOUND":
            print("   ОШИБКА: ожидался errorName=PARENT_CLIENT_NOT_FOUND, получено", data)
            failed += 1
        else:
            print("   OK: 404, PARENT_CLIENT_NOT_FOUND при PATCH")

    if failed:
        print(f"\n=== Провалено проверок: {failed} ===")
        raise SystemExit(1)
    print("\n=== Все проверки пройдены ===")


if __name__ == "__main__":
    main()
