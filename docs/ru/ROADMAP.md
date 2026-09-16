# Roadmap

### Этап 0. Подготовка окружения (20–30 мин)

- [x] Репозиторий по структуре из [ARCHITECTURE.md](ARCHITECTURE.md)
- [x] `.env` с `LLM_PROVIDER` (`openrouter` для тестов на бесплатной модели / `anthropic` позже), `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`
- [x] Python 3.11+, Node 18+, FastAPI, React + TypeScript (Vite)
- [x] Положить в `knowledge/` три документа под тематику ШПД-провайдера: `tariffs.md`, `router-setup.md`, `troubleshooting.md`
- [x] `.env.example` и смонтированный Docker volume для кэша HuggingFace (`HF_HOME`), чтобы модель не скачивалась заново при каждом рестарте

**Готово, когда:** оба проекта запускаются локально пустыми.

---

### Этап 1. Backend-скелет (30–40 мин)

- [x] `POST /api/chat` — принимает `{message, session_id}`, пока заглушка
- [x] `POST /api/upload` — принимает файл, сохраняет в `knowledge/`
- [x] Структура папок как в ARCHITECTURE.md (`api/`, `agent/`, `rag/`, `models/`)
- [x] `agent/llm.py` — фабрика `get_llm()`: по `settings.llm_provider` возвращает `ChatOpenAI(base_url="https://openrouter.ai/api/v1")` (OpenRouter, бесплатная модель с поддержкой tool calling, напр. `deepseek/deepseek-chat`) или `ChatAnthropic` — переключение только через `.env`, без правок кода в `agent/`
- [x] CORS

**Готово, когда:** curl/Postman к обоим эндпоинтам возвращают корректный JSON.

---

### Этап 2. RAG-слой (40–60 мин)

- [x] `rag/embeddings.py` — обёртка над моделью эмбеддингов (`multilingual-e5-small` для русскоязычного корпуса)
- [x] `rag/ingest.py` — chunking (500–800 токенов, overlap 50–100) + запись в Chroma
- [x] `rag/retriever.py` — `retrieve(query, k=4)`, возвращает чанки вместе с метаданными: имя документа, номер чанка, score
- [x] Триггер ingest явно зафиксирован: `python -m rag.ingest` запускается один раз при старте backend и обрабатывает всё, что лежит в `knowledge/` (не на каждый запрос — иначе время старта сервера растёт). `POST /api/upload` (Этап 1) после сохранения файла должен вызывать ту же ingest-функцию для нового файла, а не только класть его в папку — иначе он не попадёт в поиск

> Метаданные из этого шага понадобятся на Этапе 4 для поля `sources` в ответе — не пропускать их уже здесь.

**Готово, когда:** тестовый вопрос возвращает релевантный чанк с корректными метаданными источника.

---

### Этап 3. Явный agent workflow (60–90 мин)

Вместо `AgentExecutor`/ReAct — router с явными ветками.

- [x] `agent/router.py`: LLM-классификатор intent — `rag_search` / `tool_call` / `direct_answer` / `combined`
- [x] `agent/tools.py`: `check_order_status(order_id)`, `create_ticket(topic)` — заглушки с фиктивными данными (сами данные вынесены в `data/orders.py`, `data/tickets.py` — см. правило dependency direction в CLAUDE.md)
- [x] Ветка `rag_search` → вызов `retriever.retrieve()`
- [x] Ветка `tool_call` → вызов нужного tool по имени и аргументам, извлечённым классификатором
- [x] Ветка `combined` → ручной ReAct-цикл (не `AgentExecutor`): максимум 2–3 итерации `think → act → observe` в Python-цикле (`for` с верхней границей — эквивалент `while` с тем же гарантированным завершением) — модель на каждом шаге решает, каких данных не хватает (RAG или tool), вызывает нужное действие, получает результат и решает, достаточно ли информации для финального ответа
- [x] Жёсткий лимит итераций (`MAX_REACT_ITERATIONS = 3`) — защита от зацикливания
- [x] Финальный синтез ответа — через общую фабрику `get_llm()` (Этап 1), тот же провайдер, что и для классификации/ReAct-шагов: переключение только через `.env`, без спец-случаев в `agent/`. Для провайдера `anthropic` модель берётся из `settings.anthropic_model` (например, `claude-sonnet-5`), без хардкода строки
- [x] Память диалога по `session_id` (in-memory dict — простое хранилище, обнуляется при рестарте, это осознанный компромисс для pet-проекта)
- [x] Если RAG не находит релевантного контекста — агент честно говорит об этом, не выдумывает
- [x] Логирование ключевых шагов через встроенный `logging` (JSON-формат, без отдельных библиотек вроде structlog) — `session_id`, выбранный intent, тайминги (`llm_ms`, `retrieval_ms`) для каждого шага (классификация, retrieval, tool call, react-шаги, synthesis)

**Готово, когда:** на все три сценария (RAG / tool / комбинированный) роутер выбирает корректную ветку и генерирует адекватный ответ.

---

### Этап 4. Структурированный ответ с источниками (20–30 мин)

- [ ] `/api/chat` возвращает строго:
```json
{
  "reply": "...",
  "tool_calls": [
    { "name": "check_order_status", "args": { "order_id": "12345" } }
  ],
  "sources": [
    { "document": "tariffs.md", "chunk": 3, "score": 0.87 }
  ]
}
```
- [ ] `sources` заполняется из метаданных, которые уже возвращает `retriever.retrieve()` (Этап 2)
- [ ] Поля `tool_calls` и `sources` присутствуют всегда, даже если пустые списки

**Готово, когда:** структура ответа не меняется в зависимости от сценария — фронтенду не нужно ветвление на разные форматы.

---

### Этап 5. Фронтенд на React (50–70 мин)

- [ ] Чат: список сообщений, инпут, отправка, индикатор загрузки
- [ ] Явные состояния `idle | loading | error`, блокировка кнопки отправки (`isSubmitting`), таймаут запроса через `AbortController`
- [ ] `session_id` в localStorage
- [ ] Блок «Agent activity» (только факт оркестрации, без внутренних рассуждений модели):
```
Agent activity
✓ Retrieved 4 relevant documents
✓ Called check_order_status
✓ Generated response
```
- [ ] Блок источников под ответом:
```
Ответ основан на:
— Tariffs & Plans — section 3
— Router Setup — section 2
```

**Готово, когда:** видно и что агент сделал (оркестрация), и на чём основан ответ (источники) — без утечки внутреннего reasoning модели.

---

### Этап 6. Evaluation-слой (40–60 мин)

Отдельный, самый недооценённый шаг — то, что реально отличает «поиграл с RAG» от «проверил, что RAG работает».

- [ ] `evaluation/questions.json`:
```json
[
  { "question": "Как сменить тариф?", "expected_source": "tariffs.md" },
  { "question": "Что делать при отсутствии сигнала?", "expected_source": "troubleshooting.md" },
  { "question": "Как настроить VLAN на MikroTik?", "expected_source": "router-setup.md" }
]
```
- [ ] `evaluation/run.py` — прогоняет вопросы через `retriever.retrieve()`, сравнивает топ-1 источник с `expected_source`, считает accuracy
- [ ] `temperature=0` в скрипте прогона для детерминированности результатов
- [ ] Негативные тесты в `questions.json` (out-of-domain вопросы) — проверка, что агент не выдумывает источник вместо честного «не нашёл»
- [ ] Вывод скрипта:
```
Questions: 10
Correct source retrieved: 9/10
Retrieval accuracy: 90%
```

**Готово, когда:** есть количественное подтверждение качества retrieval — конкретное число accuracy, а не «вроде работает».

---

### Этап 7. Докеризация и деплой (30–60 мин)

- [ ] Dockerfile для backend и frontend, docker-compose.yml
- [ ] Проверка полного запуска через `docker compose up`
- [ ] Минимальный CI (GitHub Actions): один workflow — lint + прогон `evaluation/run.py` при пуше в main

> Облачный деплой (Render/Railway) — факультативно: PyTorch-эмбеддинги легко выходят за 512 MB RAM бесплатных тарифов. Достаточно видео/gif + `docker compose up` вживую при необходимости.

---

### Этап 8. Документация (30–40 мин)

- [ ] README со схемой из ARCHITECTURE.md, стеком, инструкцией запуска
- [ ] Явно указать retrieval accuracy из Этапа 6 (конкретное число)
- [ ] Упоминание использования AI-ассистентов в разработке

---

## Что сознательно не делаем

Список того, что увеличивает объём, но почти не увеличивает ценность демонстрации:

- аутентификация
- Kubernetes
- Redis / PostgreSQL для session memory
- Celery, Kafka
- Terraform
- CI/CD на 5 стадий
- observability-стек (Prometheus/Grafana и т.п.)
- сложный, «продуктовый» фронтенд
- streaming token-by-token
- multi-agent архитектура
- 10+ инструментов

Если в процессе появляется желание «раз уж делаю AI-проект, добавлю ещё...» — это сигнал остановиться.

---

## Оценка времени (три уровня)

| Уровень | Время | Что получаешь |
|---|---|---|
| **MVP** | 4–7 часов | FastAPI, React, RAG, Claude, tools, память, Docker, рабочее демо |
| **Interview-ready** (рекомендуется) | 8–12 часов | + sources/citations, evaluation-слой, аккуратные Pydantic-схемы, README со схемой, error handling |
| **Избыточно — не стоит** | 15–20+ часов | Начинается scope creep из раздела «Что сознательно не делаем» |

Целевой уровень — **Interview-ready**: MVP уже достаточен для демо, но sources + evaluation — это то, что отличает «собрал чатик» от «построил и проверил AI-систему».
