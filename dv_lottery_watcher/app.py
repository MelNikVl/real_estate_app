import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

import requests

DV_URL = "https://dvprogram.state.gov/"
CHECK_INTERVAL_SECONDS = 12 * 60 * 60  # 2 раза в сутки
STATE_FILE = os.environ.get("DV_STATE_FILE", "state.json")

TELEGRAM_BOT_TOKEN = os.environ.get("DV_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("DV_TELEGRAM_CHAT_ID", "")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {
            "last_hash": None,
            "last_checked_at": None,
            "last_change_at": None,
            "last_open_detected_at": None,
            "last_status_code": None,
            "last_error": None,
            "already_notified": False,
        }

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def normalize_text(html: str) -> str:
    return re.sub(r"\s+", " ", html).strip()


def detect_dv_2027_open(text: str) -> bool:
    lowered = text.lower()
    has_target = ("dv-2027" in lowered) or ("diversity visa 2027" in lowered)

    open_signals = [
        "entry period",
        "entries for the dv",
        "registration period",
        "submit an entry",
        "is now open",
        "will begin",
    ]
    has_open_signal = any(signal in lowered for signal in open_signals)
    return has_target and has_open_signal


def send_telegram(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] Telegram не настроен (DV_TELEGRAM_BOT_TOKEN / DV_TELEGRAM_CHAT_ID).")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=20)
    response.raise_for_status()


def run_check() -> None:
    state = load_state()
    now = utc_now_iso()

    try:
        response = requests.get(DV_URL, timeout=30)
        response.raise_for_status()

        text = normalize_text(response.text)
        current_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        has_changed = state["last_hash"] is not None and state["last_hash"] != current_hash
        open_detected = detect_dv_2027_open(text)

        state["last_checked_at"] = now
        state["last_status_code"] = response.status_code
        state["last_error"] = None

        if has_changed:
            state["last_change_at"] = now
            print(f"[INFO] Изменение страницы обнаружено ({now}).")

        if open_detected and not state.get("already_notified", False):
            send_telegram(
                "🚨 Похоже, регистрация DV-2027 началась или опубликована. "
                "Проверь https://dvprogram.state.gov/ прямо сейчас."
            )
            state["already_notified"] = True
            state["last_open_detected_at"] = now
            print(f"[INFO] Отправлено уведомление в Telegram ({now}).")

        state["last_hash"] = current_hash
        save_state(state)
        print(f"[OK] Проверка завершена ({now}), status={response.status_code}.")

    except Exception as exc:
        state["last_checked_at"] = now
        state["last_error"] = str(exc)
        save_state(state)
        print(f"[ERROR] Проверка не удалась ({now}): {exc}")


def main() -> None:
    run_once = os.environ.get("DV_RUN_ONCE", "false").lower() == "true"

    if run_once:
        run_check()
        return

    while True:
        run_check()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
