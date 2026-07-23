---
tags: [reforge, relic, affix, pack, rolled_params, material, smelting, preseason]
summary: Reforge (POST /api/reforge) — relic affix reroll/add/remove via reforge stones, plus pack rolled_params reroll (packInstanceId); outcomes, request contract, material inventory query
type: data
---

# Reforge (Pre-S1)

> **Lobby-only optimization via `POST /api/reforge`.** Reforge rerolls an item's
> randomized stats to chase a better roll before you equip it — it never happens
> in-game. The one endpoint targets **either a relic or a pack** (the two targets
> are **mutually exclusive** — never send both ids in one call):
> - **Relic** (`relicInstanceId`) — consume **one reforge stone** to reroll / add /
>   remove the relic's **affixes** (§1–§5 below).
> - **Pack** (`packInstanceId`) — reroll the pack's **`rolled_params`** (§6). This
>   shifts the pack's in-combat effect magnitude — notably its damage multiplier.
>
> Either target is **random**: the server rolls the new values. You cannot choose
> the affix, the param, or the resulting number.
>
> **TL;DR (relic):** acquire stones from the shop (`preseason_material_bundle`, see
> `references/shop.md` §2.4) → un-equip the target relic from its loadout slot →
> `POST /api/reforge` with the relic id + the stone's `itemKey`. Each call consumes
> exactly one stone and is idempotent on `idempotencyKey`.

Relic affixes are rolled from 6 stat types (atk, def, explore, item_atk,
max_hp, max_ep); each relic carries 0–3 affixes. See the **Relics** section of
`game-guide.md`. Reforge operates on those affixes.

---

# 1. Stones ↔ outcomes

Each stone `item_key` maps to one fixed outcome:

| Stone `item_key` | Outcome | Effect on the relic |
|------------------|---------|---------------------|
| `reforge_effect_reroll` | `effect_reroll` | Reroll the **entire affix set**: new affix types **and** values (count may change) |
| `reforge_stat_reroll` | `stat_reroll` | Reroll **all affix values**, keeping the existing affix types |
| `reforge_effect_add` | `effect_add` | Add **one** new random affix (only if the relic has < 3 affixes) |
| `reforge_effect_remove` | `effect_remove` | Remove **one random** affix (the server picks — not caller-chosen) |

A relic holds 0–3 affixes. `effect_add` at 3 affixes, `effect_remove`/`stat_reroll`
on a 0-affix relic, etc. are rejected as not-applicable (see §3) **without
consuming the stone**.

---

# 2. POST /api/reforge `(requires credential)`

**Body:**

```json
{
  "relicInstanceId": 1234,
  "itemKey": "reforge_effect_remove",
  "idempotencyKey": "reforge-1234-a1b2c3"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `relicInstanceId` | int64 | the relic to reforge (must be owned + **un-equipped**) |
| `itemKey` | string | the stone to consume (table above) — determines the outcome |
| `targetAffixIndex` | omit | **Do not send.** No outcome is caller-targeted (`effect_remove` removes a random affix); sending it → 400 `REFORGE_TARGET_INVALID` |
| `idempotencyKey` | string (≤64) | de-dup key. **Same key → the original result is replayed (200), no second consumption.** Reuse the same key when retrying a timeout/503 |

> Idempotency is carried in the **body** (`idempotencyKey`), not an `Idempotency-Key`
> header. Generate one key per intended reforge; reuse it verbatim on retry.

**Response 200**: `data`:

```json
{ "success": true, "data": {
  "outcome": "effect_remove",
  "relicInstanceId": 1234,
  "beforeAffixes": [
    { "affixDefId": 5,  "rolledValue": 12, "statType": "atk",    "displayName": "Ferocious" },
    { "affixDefId": 9,  "rolledValue": 3,  "statType": "def",    "displayName": "Unyielding" }
  ],
  "afterAffixes": [
    { "affixDefId": 5,  "rolledValue": 12, "statType": "atk",    "displayName": "Ferocious" }
  ],
  "remainingQty": 4
} }
```

- `beforeAffixes` / `afterAffixes` — the relic's affixes before and after. Each is
  `{ affixDefId, rolledValue, statType?, displayName?, description? }` (the
  `statType`/`displayName`/`description` enrich from the catalog).
- `remainingQty` — your remaining count of this stone after the consume
  (informational; on an idempotent replay it is the current value, not a snapshot).
- The relic must be **un-equipped first**: unequip via
  `DELETE /api/loadout/slot/:typeIndex` (see the **Loadout Endpoints** section of `references/api-summary.md`).

---

# 3. Errors

| HTTP | Code | When | Action |
|------|------|------|--------|
| 400 | `REFORGE_TARGET_INVALID` | `targetAffixIndex` was sent — no outcome accepts it (`effect_remove` is random) | drop `targetAffixIndex` |
| 400 | `VALIDATION_ERROR` | `idempotencyKey` missing | add the key |
| 404 | `RELIC_NOT_FOUND` | relic not owned / wrong id | — |
| 409 | `NO_MATERIAL` | you hold 0 of that stone | buy more (`references/shop.md`) |
| 409 | `RELIC_EQUIPPED` | relic is currently equipped in a loadout slot | unequip first |
| 409 | `IDEMPOTENCY_CONFLICT` | same `idempotencyKey` reused with **different** params | use a fresh key |
| 422 | `REFORGE_NOT_APPLICABLE` | add@3-affixes / remove@0-affixes / reroll@empty / unsupported `item_key` | pick a different stone/relic — **no stone consumed** |
| 503 | `SERVICE_UNAVAILABLE` / `REFORGE_TIMEOUT` | transient deadlock / time-budget exceeded | **retry with the same `idempotencyKey`** |

Not-applicable (422) and all error paths are **non-consuming**: only a 200
consumes a stone.

---

# 4. GET /api/inventory/items?category=material `(requires credential)`

Lists the reforge stones (and any other consumables of the given category) you
currently hold, `quantity > 0` only. Use it before reforging to see which stones
are available.

**Query:** `category` (required) — `material` for reforge stones.

**Response 200:**

```json
{ "success": true, "data": [
  { "itemKey": "reforge_stat_reroll", "quantity": 12 },
  { "itemKey": "reforge_effect_add",  "quantity": 3 }
] }
```

Empty inventory returns `{ "success": true, "data": [] }`.

---

# 5. Workflow

```
1. GET /api/inventory/items?category=material   → which stones do I have?
2. GET /api/inventory/relics                     → pick a relic to improve
3. (if equipped) DELETE /api/loadout/slot/:idx   → un-equip it
4. POST /api/reforge { relicInstanceId, itemKey, idempotencyKey }
5. inspect afterAffixes; repeat or re-equip via PUT /api/loadout/slot/:idx
```

---

# 6. Pack reforge — reroll `rolled_params` (`packInstanceId`)

The **same** endpoint, `POST /api/reforge`, also reforges a **pack**: instead of a
relic's affixes it rerolls the pack instance's **`rolled_params`**. No reforge stone
is involved — you target the pack directly by id.

**What `rolled_params` are.** Every pack **instance** carries its own deterministic
`rolled_params`: when the pack is granted, each rollable ("ranged") effect field is
rolled once **within that tier's `min`/`max` band** (the bands live in the
`pack-catalog` tier `ranges`, dotted-path keyed). These rolled values set the pack's
**in-combat effect magnitude** — notably a **damage-output multiplier** (surfaced in
battle logs as the `dmg_mult` variant → `dmg ×N` for Scout / Steel Heart / Thorns /
Sun Cloak). So two instances of the *same* family/tier can hit for different damage.

**Reforging a pack rerolls those params** — **random, server-rolled, not
chooseable**, the same random principle as relic reforge (§1): you cannot pick the
resulting values. The response returns the params **before** and **after** the reroll.

**Body** — send `packInstanceId` (never `relicInstanceId`; the two targets are
**mutually exclusive**, do not send both):

```json
{
  "packInstanceId": 66,
  "idempotencyKey": "reforge-pack-66-a1b2c3"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `packInstanceId` | int64 | the pack to reforge (must be owned; a pack currently listed on the marketplace must be un-listed first). **Mutually exclusive with `relicInstanceId`** — sending both is invalid |
| `idempotencyKey` | string (≤64) | de-dup key, same replay semantics as the relic path (§2) |

**Response 200** returns `beforeParams` / `afterParams` — the pack's `rolled_params`
before and after the reroll (dotted-path keyed; the keys/bands below are
**illustrative** — the authoritative key set comes from the `pack-catalog` tier
`ranges` / `/openapi.yaml`):

```json
{ "success": true, "data": {
  "packInstanceId": 66,
  "beforeParams": { "effect.dmg_mult": 1.4 },
  "afterParams":  { "effect.dmg_mult": 1.7 }
} }
```

Because a reroll **shifts the multiplier**, it changes the damage that pack
contributes in battle — so evaluate an **instance's** `rolled_params`, not just its
family/tier, when choosing and reforging packs for a loadout.

> A listed pack is escrowed and **cannot be reforged until the listing is cancelled**
> (see `references/marketplace.md`). The authoritative field list, error codes, and
> the exact `rolled_params` keys are in `/openapi.yaml`.
