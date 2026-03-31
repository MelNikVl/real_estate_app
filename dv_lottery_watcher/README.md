# DV Lottery Watcher (отдельное приложение)

Это отдельное приложение, которое проверяет `https://dvprogram.state.gov/` **2 раза в сутки** и отправляет уведомление в Telegram, когда находит признаки начала/публикации DV-2027.

## Запуск

```bash
cd dv_lottery_watcher
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируй .env
set -a && source .env && set +a
python app.py
```

## Полезно

- Для одноразовой проверки:

```bash
DV_RUN_ONCE=true python app.py
```

- Состояние хранится в `state.json` (хэш страницы, время последней проверки, ошибки, флаг уже отправленного уведомления).
