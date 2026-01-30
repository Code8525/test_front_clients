#!/usr/bin/env python3
"""
Проверка CRUD клиентов на развёрнутом сервере http://127.0.0.1:8000
Запуск: python scripts/test_client_crud.py
"""
import json
import urllib.error
import urllib.request
import uuid

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
            body = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:
            body = None
        return e.code, body
    except urllib.error.URLError as e:
        print(f"Ошибка соединения: {e}")
        raise


def get_first_region_id() -> str | None:
    """Получить id первого региона для создания клиента."""
    status, data = request("GET", "/api/regions")
    if status != 200 or not data:
        print("Не удалось получить список регионов")
        return None
    items = data.get("items") or []
    if not items:
        return None
    return items[0]["id"]


def main() -> None:
    print("=== Проверка CRUD клиентов на", BASE, "===\n")

    # 1) Регион для клиента
    region_id = get_first_region_id()
    if not region_id:
        print("Пропуск: нет регионов в БД")
        return
    print("1. Регион для клиента:", region_id)

    # 2) Создание клиента (уникальные name/inn для повторных запусков)
    suffix = uuid.uuid4().hex[:8]
    create_body = {
        "name": f"Тест CRUD {suffix}",
        "full_name": "ООО Тест CRUD",
        "party_type": "legal",
        "inn": "77" + str(uuid.uuid4().int % 10**8).zfill(8),
        "region_id": region_id,
    }
    status, created = request("POST", "/api/clients", create_body)
    if status != 201:
        print("2. Создание клиента: ОШИБКА", status, created)
        return
    client_id = created["clientId"]
    print("2. Создание клиента: OK, client_id =", client_id)

    # 3) Редактирование клиента
    update_body = {"name": f"Тест CRUD (обновлён {suffix})", "inn": "77" + str(uuid.uuid4().int % 10**8).zfill(8)}
    status, updated = request("PATCH", f"/api/clients/{client_id}", update_body)
    if status != 200:
        print("3. Редактирование клиента: ОШИБКА", status, updated)
        return
    if updated["name"] != update_body["name"] or updated["inn"] != update_body["inn"]:
        print("3. Редактирование клиента: данные не совпадают", updated)
        return
    print("3. Редактирование клиента: OK, name =", updated["name"], ", inn =", updated["inn"])

    # 4) Удаление клиента
    status, _ = request("DELETE", f"/api/clients/{client_id}")
    if status != 204:
        print("4. Удаление клиента: ОШИБКА", status)
        return
    print("4. Удаление клиента: OK")

    # 5) Проверка, что клиент удалён (GET 404)
    status, _ = request("GET", f"/api/clients/{client_id}")
    if status != 404:
        print("5. Проверка 404 после удаления: ОШИБКА, ожидался 404, получен", status)
        return
    print("5. После удаления GET возвращает 404: OK")

    print("\n=== Все проверки пройдены ===")


if __name__ == "__main__":
    main()
