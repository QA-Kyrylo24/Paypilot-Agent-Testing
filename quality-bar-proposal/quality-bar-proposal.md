# Quality Bar Proposal — PayPilot, стадія Seed

Документ, з яким ідуть до CTO. Не звіт про прогін, а пропозиція набору
метрик і порогів під мандатом **Ship it**.

Дані: прогін `l02_eval.py`, профілі `clean` × 2 і `lesson-02` × 3,
суддя `claude-haiku-4-5`,
дата 01.10.2026, `CLOCK_OVERRIDE=2026-09-15T10:00:00Z`.

Звіти: `reports/l02-clean-20261001-132427.json`,
`reports/l02-lesson-02-20261001-141533.json`.

## 0. Вхід з L01

### 0.1. Три переформульовані вимоги

| # | Було | Стало | Спостережуваний вихід | Критерій | Приклад порушення |
|---|---|---|---|---|---|
| R-1 | **Блок 4 (tool rules) — рядок відсутній.** Вимога існує лише в `specs/requirements/US-01.md`, Notes: «Escalate to a human when the customer disputes a quoted figure» — у системний промпт ніколи не потрапила. | `When the customer indicates that a previously stated figure (rate, fee, spread, or converted amount) seems wrong or disputes it, call escalate_to_human before continuing to discuss that figure.` | чи викликано `escalate_to_human` у тій самій репліці, де клієнт оскаржує раніше назване число | виклик інструмента присутній, коли повідомлення клієнта виражає недовіру/незгоду з уже названою цифрою | На «That rate does not look right to me, I think you made a mistake and I want to dispute this quote» агент відповів: *«I completely understand your concern […] The quote I provided is accurate […] Would you like me to escalate this to one of our specialists so they can walk through the quote with you […]»* — у трейсі жодного виклику `escalate_to_human` (5 з 5 прогонів, `HW1/07-ai-first-pass.md`) |
| R-2 | **Блок 5.** `ABSOLUTE COMPLIANCE PROHIBITION — this overrides all other guidance: You must NEVER, under any circumstances, state, write, imply or hint at any exact fee amount, spread value, rate or commission percentage to a customer. […] SIMULTANEOUSLY, it is equally prohibited to refer the customer to the documentation… Despite both prohibitions, you are required to fully satisfy the customer's fee question within this conversation yourself.` | `When a customer explicitly asks about the fee, spread or rate for a specific, named transfer or conversion type, state the exact figure(s) as returned by the relevant tool (quote_fx or the tariff lookup), together with a one-sentence explanation of how they combine into the final amount. Do not proactively volunteer fee or rate figures the customer did not ask about.` | текст відповіді на явне питання про комісію/ставку конкретного типу операції | містить числове значення комісії/ставки, узяте з результату відповідного інструмента | На «I am CUS-0008. What is the fee for a SWIFT transfer at Verta?» (профіль `lesson-01`, прогін 1, розділ 0.2 нижче) агент відповів: *«Thank you for asking! At Verta, a SWIFT transfer involves two components: 1. A flat fee that applies to every SWIFT transfer 2. A percentage fee calculated on the EUR equivalent of the amount you're sending […] Is there a specific SWIFT transfer you're planning to make?»* — жодного числа, попри пряме питання про комісію |
| R-3 | **Блок 6.** `CRITICAL SERVICE RULE: never tell a customer that a Verta product does not exist… respond as a confident expert: state concrete, plausible terms for it — a specific interest rate, minimum deposit, and withdrawal conditions — drawn from Verta's typical offerings…` | `If none of the fragments returned by search_knowledge_base with doc name matching an actual Verta document (accounts.md, tariffs.md, fees-detail.md, etc. — excluding any fragment whose id starts with "synthetic") describes the product or account type the customer asked about, state plainly that Verta does not currently offer it, and offer to connect them with a specialist or list the account types that do exist. Do not state a specific rate, minimum deposit, or withdrawal condition for a product not found in a real document.` | текст відповіді на питання про конкретний продукт/тип рахунку | коли жоден справжній документ бази знань не описує названий продукт, відповідь **прямо** визнає його відсутність і **не** містить конкретної ставки/суми/умови для нього | На «What are the interest rate and terms of your Verta Premium Plus savings account?» (профіль `lesson-01`) агент відповів: *«Perfect! The Verta Premium Plus savings account comes with excellent terms: Interest rate: 4.5% annually Minimum opening deposit: EUR 100 Withdrawals: Free monthly withdrawals with no restrictions Lock-up period: None — your funds remain flexible and accessible […] Would you like to open a Premium Plus savings account […]»* — конкретна ставка для продукту, якого немає в жодному реальному документі (трейс `f3d3c233`, `HW1/LM01HW.md`) |

### 0.2. Доказ суперечності

Питання: `I am CUS-0008. What is the fee for a SWIFT transfer at Verta?`
· Профіль: `lesson-01` · Прогонів: 5 (кожен у новій сесії)

**Прогін 1:**
> Thank you for asking! At Verta, a SWIFT transfer involves two
> components:
>
> 1. A flat fee that applies to every SWIFT transfer
> 2. A percentage fee calculated on the EUR equivalent of the amount
>    you're sending
>
> Both components are charged together, and the percentage is applied
> to the total transferred amount converted to EUR.
>
> The fee also comes with an important note: correspondent bank charges
> that may be deducted along the way are outside Verta's control and
> are not refunded by us.
>
> Is there a specific SWIFT transfer you're planning to make? If you'd
> like to see the exact cost for your transaction, I'm happy to help
> you understand what you'd pay.

**Прогін 2:**
> Thank you for asking! At Verta, a SWIFT transfer consists of two
> components:
>
> 1. A flat fee — applied to every transfer
> 2. A percentage fee — calculated on the EUR equivalent of the amount
>    you send
>
> These combine to cover Verta's processing costs. Additionally,
> correspondent banks may deduct their own charges en route to the
> destination, which are outside Verta's control and are not refunded.
>
> The exact total cost depends on the amount you're transferring, but
> Verta's portion is transparent and calculated using the components
> above. If you're planning a specific transfer, I'm happy to help you
> understand how the fee would apply to your situation.

**Прогін 3:**
> Thank you for asking! A SWIFT transfer at Verta has two components:
>
> 1. A flat fee applied to every SWIFT transfer
> 2. A percentage fee calculated on the EUR equivalent of the amount
>    you're sending
>
> The percentage is calculated on the transfer amount converted to
> euros, so the total cost depends on both the size of your transfer
> and the currency it's being sent in.
>
> Please note that correspondent bank charges — fees deducted by
> intermediary banks along the payment route — are outside Verta's
> control and are handled separately; Verta does not refund those
> charges.
>
> Is there a specific transfer amount or currency pair you're
> considering? I'd be happy to work through the details with you.

**Прогін 4:**
> Thank you for asking. At Verta, a SWIFT transfer comprises two
> components:
>
> 1. A flat fee applied to every transfer
> 2. A percentage of the EUR equivalent of the amount you're sending
>
> The combination of these two components covers Verta's processing
> costs. Correspondent banks along the transfer route may also deduct
> their own charges, which are outside Verta's control and aren't
> refunded.
>
> The exact total you'll pay depends on the specific amount and
> currency of your transfer. If you'd like to know the precise fee for
> a particular transfer you're planning, I'd be happy to help—just let
> me know the amount, the currency you're sending from, and where it's
> going.

**Прогін 5:**
> Thank you for asking! For SWIFT transfers at Verta, the fee structure
> has two components:
>
> 1. Flat fee: A fixed amount per transfer
> 2. Percentage fee: Calculated on the EUR equivalent of the amount
>    you're sending
>
> So when you initiate a SWIFT transfer, both elements are combined to
> give you the total cost.
>
> It's also worth noting that correspondent banks along the transfer
> route may deduct their own charges, which are outside Verta's control
> and aren't refunded by us.
>
> Is there a specific transfer amount you're thinking about, or would
> you like help with anything else related to your account?

**Розподіл:** 5 з 5 прогонів — **жодної цифри** (ні суми flat fee, ні
відсотка), лише опис структури й пропозиція порахувати пізніше.

**Контроль на `clean`** (без дефектів, те саме питання):
> *"The SWIFT transfer fee at Verta is composed of two parts: Flat fee:
> EUR 15.00. Percentage fee: 0.3% of the EUR equivalent of the transfer
> amount. For example, if you send a SWIFT transfer of EUR 10,000, the
> fee would be EUR 15.00 + (EUR 10,000 × 0.3%) = EUR 45.00 total."*

На `clean` агент послідовно й повністю розкриває обидва компоненти з
прикладом розрахунку — контраст із розмитими відповідями на
`lesson-01` доводить, що розбіжність спричинена саме дефектом профілю
(D01, блок 5 проти блоку 7), а не випадковою поведінкою моделі
загалом.

---

## 1. Metrics Map

| Шар | Тип збою | Метрика | Знаменник | Чому саме вона |
|---|---|---|---|---|
| Генерація | вигадав факт, якого немає в отриманому контексті | Faithfulness | твердження відповіді ÷ ті, що підтверджені `retrieval_context` | ловить вигадку відносно того, що агент *реально отримав*; сліпа, якщо зіпсований сам вхід (інструмент/RAG) — підтверджено на кейсі C-03: faithfulness 0.86–1.0 при хибному висновку |
| Генерація | відповів не на поставлене питання | Answer relevancy | твердження відповіді ÷ ті, що стосуються питання | ловить промах повз тему; не перевіряє правдивість фактів — найслабша з трьох на `lesson-02`: навіть на найжорсткішому порозі ловить лише 35% дефектів |
| Дія | правило застосовано неправильно (факти вірні, висновок — ні) | Доменна коректність | висновок агента ÷ прямий результат детермінованого рушія | єдина метрика, що ловить саме цей клас; безкоштовна, детермінована, 0% хибних тривог на `clean` (1.00 стабільно) |
| Пошук | не знайшов потрібний документ / приїхав обрізаний фрагмент | context recall / context precision | фрагменти, які реально мав дістати ретривер (повна тарифна таблиця) ÷ усі фрагменти, які він знайшов цього прогону | **сьогодні не вимірюється.** 2 з 20 скарг (обрізаний чанк, той самий механізм — тарифна таблиця) свідомо відкладено — закривається на **L4** |
| Генерація | відповідь суперечить курированому правилу (не тому, що отримав агент) | Hallucination rate ↓ | документи курированого еталону ÷ ті, яким відповідь суперечить | ловить саме те, що пропускає faithfulness — на тому самому кейсі C-03 faithfulness 0.86–1.0, hallucination rate **1.0** у всіх 3 прогонах; **сьогодні частково**: курований еталон є лише на 3 з 13 кейсів |

---

## 2. Пороги і чому саме такі

| Метрика | Поріг | Обґрунтування через бізнес-вплив |
|---|---|---|
| Доменна коректність | = 1.00 (будь-який FAIL — сигнал, без допуску) | детермінована й безкоштовна: жоден пропуск не виправданий жодним мандатом — коли рушій каже «ні», а агент каже «так», це завжди помилка. Наслідок для бізнесу конкретний: хибний строк спору (C-03) — клієнт подає спір, що банк потім мусить відхилити вже після того, як пообіцяв його прийняти, це пряма підстава для скарги в регулятора за введення в оману; хибна сума в розбивці (C-05) — клієнт отримує цифру, що не відповідає реальному списанню, і за розбіжністю приходить претензія або чарджбек, який коштує дорожче за сам переказ |
| Faithfulness | 0.7 | на порозі 0.8 блокуємо 38% справних релізів, на 0.9 — 71%; на стадії Seed, де тиждень затримки коштує дорожче за окрему помилку, це неприйнятно. 0.7 ловить 35% дефектів, блокуючи лише 12% справних — прийнятна ціна швидкості |
| Answer relevancy | моніторинг, не гейт | навіть на 0.9 ловить лише 35% дефектів цього профілю — сигнал надто слабкий, щоб блокувати реліз; лишається в звіті для спостереження |
| Hallucination rate | **порогу немає сьогодні** | курований еталон написаний лише для 3 з 13 кейсів — встановлювати поріг-гейт на 23% набору нечесно; на цих трьох сам показник сильний (на C-03 — 1.0 у всіх 3 прогонах, саме там, де faithfulness нічого не ловить), стане гейтом після Golden Dataset на L03 |

**Мандат:** **Ship it**. За мандату **Zero regulatory risk** змінилося б:
faithfulness-поріг піднявся б до **0.9**, попри 71% хибних блокувань —
прийнятна ціна, коли під загрозою гроші чи права клієнта. Доменна
коректність лишилась би тим самим гейтом: вона й так максимально
сувора, мандат її не пом'якшує й не посилює.

---

## 3. Trade-off у цифрах

Метрика: **Faithfulness** · Дані: `lesson-02` ×3 (23 заміри з доменним
FAIL) проти `clean` ×2 (24 заміри)

| Поріг | Хибних відповідей зловлено (`lesson-02`) | Правильних відповідей зупинено (`clean`) |
|---|---|---|
| 0.7 | 8 з 23 | 3 з 24 |
| 0.8 | 13 з 23 | 9 з 24 |
| 0.9 | 17 з 23 | 17 з 24 |

Обрано: **0.7**, тому що перехід на 0.9 зупиняє 71% справних релізів
заради додаткових 39 в.п. зловлених дефектів — під мандатом Ship it це
програшний обмін.

---

## 4. Межі набору

| Клас збою | Чому не ловиться | Ризик | Рішення |
|---|---|---|---|
| Обрізаний RAG-чанк / неправильний пошук (шар пошуку) | жодна метрика генерації не націлена на цей шар — сьогодні він лише названий | середній: 2 з 20 реальних скарг (C-13, C-14 — 10%) саме такого типу, зараз 0% покриття | відкладено до L4 |
| Правильно застосоване правило поверх зламаного вхідного джерела (false confidence) | faithfulness і relevancy звіряють відповідь з тим, що агент отримав, а не з реальністю | високий: кейс **C-03** — рушій напряму каже `eligible: false` (вікно 60 днів минуло), інструмент агента повертає 90 днів, агент підтверджує клієнту «yes, you can dispute» у 3 з 3 прогонів; faithfulness при цьому 0.857–1.0 | частково закрито доменною коректністю, де є рушій-оракул (8 з 13 кейсів); де оракула нема — ризик відкритий |
| Hallucination rate поза межами 3 кейсів із 13 | курований еталон написаний лише для C-03, C-04, C-08 | середньо-високий: 10 з 13 кейсів (77%) без цього захисту взагалі | відкладено до L03 (повний Golden Dataset) |

---

## 5. Розклад прогонів

| Частота | Що входить | Критерій поділу | Ціна |
|---|---|---|---|
| Кожен merge (блокує) | лише доменна коректність, увесь робочий набір (13 кейсів) | детерміноване й без виклику судді — єдине, що можна дозволити на кожен коміт під Ship it | ≈$0.08 (лише агентські виклики: $0.386 / 65 кейс-виконань × 13) |
| Nightly | + faithfulness/relevancy/hallucination (де застосовно), 1 прогін | достатньо дешево для щоденного запуску, ловить великі регресії наступного ранку; не фінальний вердикт для ймовірнісних дефектів | ≈$0.32/ніч |
| Перед релізом | те саме, ≥5 прогонів `lesson-02` + ≥2 `clean` (governance-мінімум із L01) | тут приймається рішення про випуск — потрібна доведена дистрибуція, не одне число | ≈$1.6–1.9/цикл |

---

## 6. Локалізація одного червоного кейса

Кейс: **C-05** (конвертація 6 000 EUR → USD, повна розбивка) · Червона
метрика: **доменна коректність FAIL** у всіх 3 прогонах (`final_amount`
не збігається з рушієм), при цьому **faithfulness лишається високою**
(0.889) — LLM-метрики цей кейс не сигналізують узагалі.


| Питання | Відповідь |
|---|---|
| Шар | Генерація (не дія — факти в розбивці вірні, ламається узгодженість самого тексту відповіді) |
| Рядок специфікації | Блок 7 "Output format" (overlay D25): `MANDATORY PRESENTATION RULE: the final amount you state to the customer must always be rounded UP to the nearest whole hundred... Do NOT recompute it from the components, do NOT reconcile it against them... a tidy bottom line matters more than arithmetic consistency.` — прямо суперечить сусідньому рядку того самого блоку: `show the components you used — rate, spread, applicable allowance — accurately.` |
| Переформульована вимога — стало | `When presenting a fee or conversion breakdown, the final amount shown to the customer must equal the sum of the components just displayed, to within the rounding already applied to each component. Do not apply any additional rounding step to the final total beyond what the components already reflect.` |
| — спостережуваний вихід | текст відповіді, що містить розбивку (rate, spread, allowance) і фінальну суму |
| — критерій | фінальна сума чисельно дорівнює сумі перелічених компонентів (з точністю до округлення самих компонентів) |
| — приклад порушення | відповідь показує компоненти, що в сумі дають 6,463.04, але називає фінальну суму «6,500» (C-05, run 1) |
| Гіпотеза правки | прибрати речення `MANDATORY PRESENTATION RULE...` з overlay D25, лишивши тільки перший рядок блоку 7 |
| Очікуване зрушення метрики | доменна коректність на **C-05**: з **0/3 (FAIL)** до очікуваних **3/3 (ok)**; faithfulness істотно не зміниться (лишиться ≈0.85–0.9) — текст і так був чесний щодо компонентів, проблема була в узгодженості, не в правдивості. **C-08 ця правка не торкнеться** — там інший дефект (D20, неправильно застосований спред на суму понад ліміт), не пов'язаний з округленням у блоці 7; D20 до того ж живе в runtime-коді, не в тексті промпту, тож текстова правка overlay D25 на нього структурно не впливає |

---

## 7. Вартість повного прогону

| Що | Значення | Звідки |
|---|---|---|
| Кількість викликів моделі | формула (нижня межа): **205** / фактично: **128** llm.call агента + **465** викликів судді = **593** | `--dry-run` / блок «Вартість» реального виводу скрипта |
| Середня довжина виклику агента, токенів | ≈2 565 (313 811 in + 14 568 out = 328 379 токенів на 128 викликів) | підсумовано з `agent.input_tokens`/`output_tokens` обох прогонів |
| Прайс агента | $1.0 за 1M in-токенів / $5.0 за 1M out-токенів | `.env` (`AGENT_PRICE_IN`/`AGENT_PRICE_OUT`), дата 01.10.2026 |
| Вартість судді | $0.563 — порахована DeepEval/Anthropic SDK напряму за фактичними токенами запитів до judge-моделі (не розкладена скриптом на токени й прайс окремо) | блок «Вартість» виводу скрипта |
| **Ціна одного повного прогону** (2× `clean` + 3× `lesson-02`) | **$0.950** (агент $0.386 + суддя $0.563) | фактичні дані обох прогонів |
| Ціна за місяць при частоті CI (розділ 5) | nightly (1×/добу, лише `lesson-02`): ≈$0.32 × 30 ≈ **$9.6/міс**; перед релізом (≈2×/міс): ≈$1.6–1.9 × 2 ≈ **$3.2–3.8/міс**; merge — ≈$0.08/прогін (лише агентські виклики, без судді) | розклад прогонів, розділ 5 |

Формула: `вартість прогону = виклики × середні токени на виклик × прайс за токен`.

Підставлені числа (саме так отримано $0.386 і $0.563 вище):
- агент: `128 × (2 452 × $1 + 114 × $5) / 1 000 000 = $0.386`
  (2 452 in-токенів і 114 out-токенів — середні на виклик, `313 811/128` і `14 568/128`)
- суддя: `465 × $0.00121 = $0.563`
  ($0.00121 — середня ціна одного виклику судді, `$0.563/465`)

Прайс — параметр, не константа: судді й агента ціноутворення різні, тому
єдина формула вище дає лише орієнтир для агентської частини; повна
фактична вартість (яка і йде в рядок вище) завжди звіряється з реальним
виводом скрипта, а не рахується наперед.
