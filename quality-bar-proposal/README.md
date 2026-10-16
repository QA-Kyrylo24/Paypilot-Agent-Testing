# Quality Bar Proposal — PayPilot (L02 homework)

Документ: [`quality-bar-proposal.md`](./quality-bar-proposal.md).
Усі числа в ньому отримані прогоном `l02_eval.py` з цього репозиторію
проти локального стенду `paypilot-stand`, профілі `clean` і
`lesson-02`.

## Судді й профілі

- Суддя: `claude-haiku-4-5` (Anthropic), `temperature=0`.
- Профілі: `clean` × 2 прогони (baseline), `lesson-02` × 3 прогони.
- Час стенду зафіксовано: `CLOCK_OVERRIDE=2026-09-15T10:00:00Z`.

## Як відтворити прогін

Інструментарій (Dockerfile, docker-compose.yml, `.env.example`) —
з публічного репозиторію
[`paypilot-l02-eval`](https://github.com/sergeytkachenko/paypilot-l02-eval),
без змін. Тут лежать лише три файли, на яких реально зроблено цей
прогін (`cases.json`, `l02_eval.py`, `requirements.txt`) — щоб
замінити ними відповідні файли в своєму клоні `paypilot-l02-eval`,
якщо потрібна точна відповідність.

Передумова: локально піднятий `paypilot-stand` (`docker compose up -d
--build` у його каталозі) з `CLOCK_OVERRIDE=2026-09-15T10:00:00Z` у
його `.env`, і `paypilot-l02-eval` склонований поруч з ним.

```bash
cp .env.example .env   # вписати ANTHROPIC_API_KEY — той самий, що в .env стенду
docker compose build

# варіант з умови завдання — обидва профілі одним викликом:
docker compose run --rm eval --runs 3 --baseline-runs 2

# варіант, яким реально отримано числа цього документа —
# два окремі виклики (економія: без повторного clean):
docker compose run --rm eval --profiles clean --baseline-runs 2
docker compose run --rm eval --profiles lesson-02 --runs 3
```

Сирі JSON-звіти цих двох запусків — `reports/l02-clean-20261001-
132427.json` і `reports/l02-lesson-02-20261001-141533.json`. Таблиці
дельт і порогів у `quality-bar-proposal.md`, розраховані вручну з цих
двох файлів (оскільки прогони розведені по окремих викликах, скрипт
не друкує їх автоматично) — методика підрахунку описана в самому
документі (розділи 1, 3).

## Файли в цьому репозиторії

- `quality-bar-proposal.md` — сам документ (ДЗ).
- `cases.json`, `l02_eval.py`, `requirements.txt` — точні версії,
  на яких зроблено прогін.
- `reports/*.json` — сирі дані обох прогонів.
