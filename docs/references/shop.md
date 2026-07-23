---
tags: [shop, purchase, gacha, smoltz, material, pack, profile, preseason]
summary: Lobby shop — listings, sMoltz purchase, gacha mechanics (pack tier / material / profile), profile collection & equip
type: data
---

# Shop (Pre-S1)

> **Lobby-only.** The shop is an out-of-game (lobby) system. You spend **sMoltz**
> (your `accounts.balance`, see `references/economy.md`) to buy gacha tickets,
> reforge materials, and profiles. None of this happens during a game.
>
> **TL;DR:** `GET /api/shop/listings` to see what's for sale → `POST /api/shop/purchase`
> with the `listingId`. Three product families: profile tickets, pack-draw tickets,
> and refinement (reforge) material bundles. Reforge materials feed the relic
> reforge system — see `references/reforge.md`.

All shop responses use the standard envelope `{ "success": true, "data": { ... } }`.

---

# 1. GET /api/shop/listings `(public)`

No auth required. Returns the currently purchasable items (filtered by active
flag + availability window, sorted by `sortOrder`). Listings are runtime-configured
and cached ~5 min server-side, so **always read this before purchasing** rather
than hardcoding `listingId`s.

**Response 200**: `data.listings[]`:

| Field | Type | Notes |
|-------|------|-------|
| `id` | int64 | `listingId` — pass to `/purchase` |
| `itemKey` | string | catalog key (e.g. `preseason_material_bundle`) |
| `category` | string | `gacha_ticket` \| `bundle` \| `permanent_ticket` (values currently served) |
| `name` | string | display name |
| `description` | string | human description |
| `priceCurrency` | string | `smoltz` \| `free` |
| `priceAmount` | string | DECIMAL serialized as string (e.g. `"300.000000"`) |
| `quantityPerBuy` | int | units granted per purchased quantity |
| `maxQuantity` | int | max `quantity` allowed in one purchase call |
| `availableFrom` / `availableUntil` | string \| null | RFC3339 window (null = always) |
| `sortOrder` | int | display order |

```json
{
  "success": true,
  "data": {
    "listings": [
      { "id": 1, "itemKey": "profile_random_ticket",           "category": "gacha_ticket",    "priceCurrency": "smoltz", "priceAmount": "50000.000000",  "quantityPerBuy": 1, "maxQuantity": 1 },
      { "id": 2, "itemKey": "preseason_pack_ticket",          "category": "gacha_ticket",    "priceCurrency": "smoltz", "priceAmount": "25000.000000",  "quantityPerBuy": 1, "maxQuantity": 1 },
      { "id": 3, "itemKey": "preseason_material_bundle",      "category": "bundle",          "priceCurrency": "smoltz", "priceAmount": "3000.000000",   "quantityPerBuy": 1, "maxQuantity": 99 },
      { "id": 4, "itemKey": "pack_inventory_permanent_ticket",  "category": "permanent_ticket", "priceCurrency": "smoltz", "priceAmount": "10000.000000", "quantityPerBuy": 1, "maxQuantity": 1 },
      { "id": 5, "itemKey": "relic_inventory_permanent_ticket", "category": "permanent_ticket", "priceCurrency": "smoltz", "priceAmount": "10000.000000", "quantityPerBuy": 1, "maxQuantity": 1 }
    ]
  }
}
```

> Prices/availability are operator-set and may differ from the example. Trust the
> live response.

---

# 2. POST /api/shop/purchase `(requires credential)`

Buys a listing. **Requires `Idempotency-Key` header** (same key → cached response,
no double charge). sMoltz is deducted atomically with the grant — partial state
is impossible.

**Body:**

```json
{ "listingId": 3, "quantity": 5 }
```

- `quantity` defaults to 1. Only `bundle` listings allow `quantity > 1` (up to
  `maxQuantity`). Gacha tickets are fixed at 1 — sending `quantity > 1` returns
  **422 `INVALID_QUANTITY`**.

**Response 200**: `data` is `{ itemKey, result }`; `result` shape depends on the
purchased item (below).

---

## 2.1 Profile random ticket — `profile_random_ticket`

Grants one **random profile you do not already own** (cosmetic). Currently only
grade-1 profiles are in rotation.

```json
{ "success": true, "data": { "itemKey": "profile_random_ticket",
  "result": { "profileIndex": 42, "grade": 1 } } }
```

If you already own every available profile → **409 `ALL_PROFILES_OWNED`** (no charge).

## 2.2 Pack-draw ticket — `preseason_pack_ticket`

> ⚠️ The pack categories, family count, and tiers enumerated below are illustrative examples and may be outdated. For authoritative, live values query `GET /api/shop/listings` and your pack inventory.

Grants one random pack. **Tier** is weighted (lower tier number = stronger effect,
rarer): T1 weight 1, T2 weight 2, T3 weight 3 (total 6). **Category** is uniform
among the 20 pack families (Moltz Expert / Item Expert / Goliath / Thorns / Scout / Ruin Expert / Berserker / Double Attack / Heart of the Giant / Bomber / Trail Ward / Ranged / Sword Master / Duelist / Raider / Last Stand / Iron Heart / Sunflame Cloak / Assassin / Pickpocket, ~5% each).

```json
{ "success": true, "data": { "itemKey": "preseason_pack_ticket",
  "result": { "packInstanceId": 1024, "tier": 2, "packName": "Moltz Expert", "category": 0,
    "guaranteed": false, "pityCounter": 3, "pityTarget": 10, "nextGuaranteed": false } } }
```

**Pity — guaranteed T1 every 10th purchase.** A per-account counter tracks pack
purchases in the current cycle (`0..9`). On the purchase made while the counter is at
`9` the tier roll is **forced to T1** (the rarest/best tier), then the counter wraps to
`0`. Natural T1s along the way do **not** reset it — the guarantee is purely
purchase-count based.

⚠️ **The counter is account-persistent, not per-session.** It carries across all your
past pack purchases; it does **not** start at 0 when you begin buying. So "the 10th
purchase" means the 10th since the last guarantee across the account's whole history —
not the 10th in your current run. Do not assume your first buy is counter 0.

**The draw response itself carries the running pity state** so you never need a separate
poll to know where you stand:
- `guaranteed` — was **this** pull the pity-forced T1.
- `pityCounter` / `pityTarget` — counter **after** this purchase (`0..target-1`, target `10`).
- `nextGuaranteed` — will your **next** purchase be the forced T1 (i.e. `pityCounter == target-1`).

Same state is also on `GET /api/shop/inventory-status` → `packPity: { counter, target: 10, guaranteed }`.

`category`: `0=moltz` \| `1=item` \| `2=goliath` \| `3=thorns` \| `4=scout` \| `5=ruin_expert` \| `6=berserker` \| `7=double_attack` \| `8=heart_of_the_giant` \| `9=bomber` \| `10=trail_ward` \| `11=ranged` \| `12=sword_master` \| `13=duelist` \| `14=raider` \| `15=last_stand` \| `16=iron_heart` \| `17=sunflame_cloak` \| `18=assassin` \| `19=pickpocket`. Scout (`4`) and Assassin (`18`) are **Main-slot only**; Raider (`14`) exists at **T1 only** (single tier). If your lobby pack inventory is
full → **409 `INVENTORY_FULL`** (no charge) — discard a pack first (`DELETE /api/inventory/packs/:id`) or
expand your cap with `pack_inventory_permanent_ticket` (default max 5, expandable +5 per purchase).

## 2.3 Inventory expansion ticket — `permanent_ticket`

Permanently expands lobby inventory by +5 slots. Two itemKeys:

| itemKey | Effect |
|---------|--------|
| `pack_inventory_permanent_ticket` | Slab (pack) lobby inventory +5 slots |
| `relic_inventory_permanent_ticket` | Relic lobby inventory +5 slots |

**Progressive pricing:** starts at 10,000 sMoltz; each purchase per account doubles the price (10,000 → 20,000 → 40,000 → …). The `priceAmount` in `/listings` always reflects the current price for the authenticated account — read it fresh before purchasing.

`quantity` is fixed at 1 — sending `quantity > 1` returns **422 `INVALID_QUANTITY`**.

```json
{ "success": true, "data": { "itemKey": "pack_inventory_permanent_ticket",
  "result": {
    "expandType": "pack",
    "newCap": 15,
    "extCount": 2,
    "nextPrice": "40000.000000"
  } } }
```

`result` fields:

| Field | Type | Notes |
|-------|------|-------|
| `expandType` | string | `"pack"` \| `"relic"` — which inventory was expanded |
| `newCap` | int | the account's new lobby cap after this expansion |
| `extCount` | int | total expansion count for this itemKey after this purchase |
| `nextPrice` | string | price (sMoltz) the **next** purchase will charge — DECIMAL serialized as string, 6 decimal places (e.g. `"40000.000000"`) |

> `nextPrice = 10,000 × 2^extCount`, matching the **Progressive pricing** rule above.
> Read it straight from the response to show the player the next expansion cost
> without a separate `/listings` round-trip.

---

## 2.4 Refinement bundle — `preseason_material_bundle`

Grants one **random reforge stone per draw** (`quantity` = number of independent
draws). Stones feed the reforge system (`references/reforge.md`). Drop weights
(total 221) — **full effect reroll is by far the most common, stat reroll is rare**:

| Stone (`item_key`) | Reforge outcome | Weight | ≈ Chance |
|--------------------|-----------------|:------:|:--------:|
| `reforge_effect_reroll` | reroll entire affix set | 200 | ~90.5% |
| `reforge_effect_add` | add one affix | 10 | ~4.5% |
| `reforge_effect_remove` | remove one affix | 10 | ~4.5% |
| `reforge_stat_reroll` | reroll all affix values | 1 | ~0.45% |

`result` is an array of length `quantity` (each draw independent; duplicates allowed):

```json
{ "success": true, "data": { "itemKey": "preseason_material_bundle",
  "result": [
    { "acquiredItemKey": "reforge_effect_reroll", "acquiredItemName": "Effect Reroll Stone", "quantity": 1 },
    { "acquiredItemKey": "reforge_effect_add",    "acquiredItemName": "Effect Add Stone",    "quantity": 1 }
  ] } }
```

**Bulk bonus — +1 free stone per 10 purchased (cumulative).** A per-account counter
tracks stones bought in the current cycle (`0..9`); every **10th cumulative** stone
grants **+1 free** stone (drawn from the same weighted pool). The bonus is **cumulative**,
so splitting orders keeps progress — e.g. buy 6 then 5 (total 11) still yields the free
stone at the 10th. `totalCost` bills only the **paid** `quantity`; the free stone appears
in `result` automatically (buy 25 → 27 stones delivered, pay for 25).

⚠️ **The counter is account-persistent, not per-session** — same as pack pity. It carries
across all your past stone purchases; it does **not** start at 0 when you begin buying.

Unlike the pack draw, the material `result` is a flat array and does **not** carry the
running pity state, so read progress from `GET /api/shop/inventory-status` →
`materialPity: { counter, target: 10 }`. **Stones until your next free one = `target - counter`.**
(When a purchase does cross a multiple of 10, the free stone is already included in that
buy's `result` array — you never miss it; this only tells you *when* the next one lands.)

Acquired stones land in your material inventory — query with
`GET /api/inventory/items?category=material` (see `references/reforge.md` §4).

---

# 3. Errors

| HTTP | Code | When |
|------|------|------|
| 404 | `LISTING_NOT_FOUND` | unknown `listingId` |
| 404 | `LISTING_INACTIVE` | inactive or outside availability window |
| 409 | `INSUFFICIENT_BALANCE` | sMoltz balance < `priceAmount × quantity` |
| 409 | `ALL_PROFILES_OWNED` | profile ticket but all profiles owned |
| 409 | `INVENTORY_FULL` | pack ticket but lobby pack inventory full (max 5) |
| 422 | `INVALID_QUANTITY` | `quantity > 1` on a gacha ticket |

On any error the transaction rolls back fully — balance, inventory, and logs are
unchanged.

---

# 4. Profiles (collection & equip)

Profiles are cosmetic identity frames acquired via `profile_random_ticket`.

## GET /api/profiles `(requires credential)`

```json
{ "success": true, "data": {
  "profiles": [
    { "profileIndex": 1,  "grade": 1, "frameIndex": null, "source": "default", "acquiredAt": "2026-05-01T00:00:00Z" },
    { "profileIndex": 42, "grade": 1, "frameIndex": null, "source": "gacha",   "acquiredAt": "2026-06-04T10:22:33Z" }
  ],
  "equipped": 42
} }
```

`source`: `default` \| `gacha` \| `event` \| `achievement`. `frameIndex` is used by
grade-2 profiles only (null otherwise). `equipped` = currently equipped `profileIndex`.

## PUT /api/accounts/me/profile `(requires credential)`

Equip an owned profile. Body `{ "profileIndex": 42 }` → returns `{ "profileIndex": 42 }`.
Equipping a profile you do not own → **403 `PROFILE_NOT_OWNED`**.

---

# 5. The acquisition → reforge loop

```
sMoltz (balance)
  └─ buy preseason_material_bundle  → random reforge stone (account_items)
       └─ POST /api/reforge          → modify an un-equipped relic's affixes
            └─ equip via /api/loadout → effectiveStats at game start
```

See `references/reforge.md` for the reforge step and the **Loadout Endpoints** section of `references/api-summary.md`
for equipping. sMoltz acquisition (Moltz → sMoltz charge, paid-room rewards) is in
`references/economy.md`.

---

# 6. Onboarding bundle redeem — `POST /api/redeem`

> **Free, not a sMoltz purchase.** Redeem is an event-code grant, separate from the
> sMoltz shop above. Spend a one-time **redemption code** (not currency) to receive a
> fixed onboarding bundle. **One redeem per account per code.**

`POST /api/redeem` `(requires credential)`. **Requires `Idempotency-Key` header**
(same key → cached response, no double grant). The grant is all-or-nothing: either
the whole bundle lands or nothing does.

**Body:**

```json
{ "code": "WELCOME" }
```

- `code` is the public event code (e.g. `WELCOME`). Matched **case-insensitively**
  (leading/trailing whitespace is trimmed). A non-matching code → **422
  `VALIDATION_ERROR`**.

## 6.1 Bundle composition

The onboarding bundle is fixed:

| Group | Count | Detail |
|-------|------:|--------|
| Packs | 2 | rolled from the **same live gacha distribution** as `preseason_pack_ticket` (category + tier weighted; see §2.2) |
| Relics | 3 | one each of color `0` / `1` / `2` (R / G / B), each with a random base + `0–3` random affixes |
| Reforge stones | 20 | `reforge_effect_reroll ×20` |

## 6.2 Response

**Response 200**: `data` is `{ items, replayed }`. `items[]` is a flat list in the
**MaterialReveal shape** (the same `{ acquiredItemKey, acquiredItemName, quantity }`
shop pack / material draws use), plus a `kind` discriminator (`pack` / `relic` /
`item`):

```json
{ "success": true, "data": {
  "items": [
    { "acquiredItemKey": "17:T3", "acquiredItemName": "Sunflame Cloak", "quantity": 1, "kind": "pack" },
    { "acquiredItemKey": "0", "acquiredItemName": "...", "quantity": 1, "kind": "relic" },
    { "acquiredItemKey": "1", "acquiredItemName": "...", "quantity": 1, "kind": "relic" },
    { "acquiredItemKey": "2", "acquiredItemName": "...", "quantity": 1, "kind": "relic" },
    { "acquiredItemKey": "reforge_effect_reroll", "acquiredItemName": "Effect Reroll Stone", "quantity": 20, "kind": "item" }
  ],
  "replayed": false
} }
```

- `acquiredItemKey` by `kind`: **pack** = `"<category>:T<tier>"` (e.g. `"17:T3"`);
  **relic** = the bare color index (`"0"` / `"1"` / `"2"`); **item** = the reforge
  stone `item_key` verbatim.
- `replayed` is `true` only when the `Idempotency-Key` header replayed an in-flight /
  prior response — the grant is **not** repeated.

Granted packs/relics land in your lobby inventory (`GET /api/inventory/packs` /
`/relics`); stones land in your material inventory
(`GET /api/inventory/items?category=material`).

## 6.3 Errors

| HTTP | Code | When |
|------|------|------|
| 422 | `VALIDATION_ERROR` | invalid / unknown code |
| 409 | `CONFLICT` | this account already redeemed this code (not re-granted) |
| 409 | `INVENTORY_FULL` | granting the +2 packs or +3 relics would exceed your lobby cap — **nothing is granted and the code is not consumed**; free slots (`DELETE /api/inventory/packs/:id` / `/relics/:id`, or expand via `permanent_ticket` §2.3) and retry |
| 503 | `SERVICE_UNAVAILABLE` | item catalog not ready yet (transient) — retry |

On `INVENTORY_FULL` the redeem is fully reverted, so the code stays redeemable — clear
space and call `/api/redeem` again with the same code.
