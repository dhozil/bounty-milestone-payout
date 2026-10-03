<div align="center">

# Bounty & Milestone Payout

**Trustless bounties for open work — submissions evaluated and payouts released by GenLayer validator consensus.**

![GenLayer](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-6a4cff)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Status](https://img.shields.io/badge/status-live%20on%20studionet-2ea44f)
![Tests](https://img.shields.io/badge/tests-18%20passed-2ea44f)

[Live Contract](https://explorer-studio.genlayer.com/address/0x935397C69F318331D4cb73EF2dc0ee7aA1a18b13) ·
[GenLayer Docs](https://docs.genlayer.com)

</div>

---

## Why

Bug bounties, grants and milestone payouts today depend on a trusted middleman to judge *"does this submission satisfy the bounty?"* BountyMilestonePayout removes the middleman: anyone can fund a bounty, anyone can submit work, and GenLayer validators reach consensus on whether the work meets the criteria — then funds move automatically.

## Live Deployment

| | |
|---|---|
| **Contract** | [BountyMilestonePayout](https://explorer-studio.genlayer.com/address/0x935397C69F318331D4cb73EF2dc0ee7aA1a18b13) |
| **Address** | `0x935397C69F318331D4cb73EF2dc0ee7aA1a18b13` |
| **Network** | GenLayer studionet (chain `61999`) |
| **Status** | ✅ deployed + audited on-chain |

## Highlights

- 🎯 **LLM evaluation** — validators independently fetch the submission URL and agree on `approve` / `reject`
- ⚖️ **Solver disputes** — rejected solvers can dispute once within the dispute window; validators re-evaluate and uphold or overturn
- 💸 **Atomic payout** — every status has exactly one payout/refund transition, executed at most once (`paid` / `cancelled` / `refunded` are terminal)
- 🧑‍💻 **Solver claim** — an approved solver collects the reward themselves; no creator call required
- ⏱️ **Bounded everywhere** — evaluation window (7d) → solver timeout claim; dispute window (3d) → creator refund; no funds can be locked or double-paid
- 🧱 **Reusable primitive** — bug bounties, grants, hackathon prizes, milestone-based gig work

## How It Works

```
create_bounty (creator funds reward + criteria)
      │
      ▼
submit_work (solver) ── evaluation window 7d ──► claim_evaluation_timeout → paid (SOLVER)
      │                                (creator can no longer evaluate after the window)
      ▼
evaluate_submission (creator, within window — LLM consensus)
      │                             │
      ├── approved ───────────────► release_funds (creator) ─┐
      │                        └──► claim_reward  (solver) ──┴──► paid (SOLVER)
      │
      └── rejected ── dispute window 3d ──► dispute_rejection (solver, once)
                 │                          ├─ overturn ──► approved (pays solver)
                 │                          └─ uphold ────► rejected (disputed once)
                 │
                 └─ window passed / dispute upheld ──► finalize_rejection (creator) → refunded (CREATOR)

open ──► cancel_bounty (creator) ─────────────► cancelled (CREATOR refund)
open ── deadline passed ──► reclaim_expired ──► expired ──► cancel_bounty → cancelled
```

### Every reachable status has exactly one payout/refund transition

| From | Payout / refund transition | Authorized by | Bound |
|---|---|---|---|
| `open` | `cancel_bounty` → `cancelled` (refund creator) | creator | — |
| `open` (past deadline) | `reclaim_expired` → `expired` *(marks only, no money)* → `cancel_bounty` | creator | bounty deadline |
| `submitted` | `evaluate_submission` → `approved` / `rejected` *(decision only)* | creator | evaluation deadline (7d) |
| `submitted` (window passed) | `claim_evaluation_timeout` → `paid` **(pays solver)** | solver | evaluation deadline |
| `approved` | `release_funds` (creator) or `claim_reward` (solver) → `paid` **(pays solver)** | creator or solver | — |
| `rejected` | `finalize_rejection` → `refunded` (refund creator) | creator | after 3d dispute window, or immediately once a dispute is upheld |
| `rejected` (dispute path) | `dispute_rejection` → `approved` / `rejected` *(decision only, once)* | solver | dispute deadline (3d) |
| `paid`, `cancelled`, `refunded`, `expired→cancelled` | terminal — no further transitions | — | — |

Replay safety: every transition flips `status` first; replays and mis-role calls revert (`expect_revert`-covered in tests, verified on-chain).

## Methods

| Role | Method | Guard |
|---|---|---|
| Creator | `create_bounty` *(payable)*, `evaluate_submission`, `release_funds`, `finalize_rejection`, `cancel_bounty`, `reclaim_expired` | creator-only; status + deadline/window checks |
| Solver | `submit_work`, `dispute_rejection`, `claim_reward`, `claim_evaluation_timeout` | solver-only; status + window checks |
| Any | `get_bounty`, `get_all_bounties`, `get_submission`, `get_bounty_submissions` | read-only |

## Security Model

- Ownership enforced on every mutation (`evaluate_submission` / `release_funds` / `finalize_rejection` creator-only, `dispute_rejection` / `claim_reward` / `claim_evaluation_timeout` solver-only)
- **Evidence is evaluated, not just linked**: the contract fetches the submission URL on-chain (`gl.nondet.web.get`, non-200 reverts) and feeds the fetched content into the evaluation/dispute consensus
- Validators independently re-fetch + re-evaluate and must agree on the exact stored decision
- **Exactly one payout/refund transition per status, each once-only** via `emit_transfer` after a status flip; money only ever moves *into* `paid`, `cancelled`, or `refunded` — `expired` is a bookkeeping state whose only money transition is `cancel_bounty` (a reclaimed bounty cannot be refunded twice)
- **Bounded dispute**: at most one dispute per rejection (`dispute_reason` set), only inside the 3-day dispute window
- **Bounded evaluation**: the creator must evaluate inside the 7-day window; after it, only the solver's timeout claim can resolve the bounty — the solver's remedy, never a creator-only refund
- Full input validation (title, lengths, deadline, URL, dispute reason)

## Deploy

```bash
genlayer deploy --contract contracts/bounty_milestone_payout.py
```

## Test

```bash
pip install -r requirements.txt
pytest tests/
```
