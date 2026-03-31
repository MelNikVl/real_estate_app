# real_estate_app

## Отдельное приложение для мониторинга DV-лотереи

По запросу добавлено **отдельное** приложение (не встроенное в backend API):

- `dv_lottery_watcher/` — проверяет `https://dvprogram.state.gov/` 2 раза в сутки;
- отправляет уведомления в Telegram при обнаружении признаков начала DV-2027;
- инструкция по запуску: `dv_lottery_watcher/README.md`.
