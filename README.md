<div align="center">

# Bounty & Milestone Payout

**Trustless bounties for open work — submissions evaluated and payouts released by GenLayer validator consensus.**

![GenLayer](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-6a4cff)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Status](https://img.shields.io/badge/status-live%20on%20studionet-2ea44f)
![Tests](https://img.shields.io/badge/tests-10%20passed-2ea44f)

[Live Contract](https://explorer-studio.genlayer.com/address/0xd5187391b8531e4C09E20Ef544Fbb312279be797) ·
[GenLayer Docs](https://docs.genlayer.com)

</div>

---

## Why

Bug bounties, grants and milestone payouts today depend on a trusted middleman to judge *"does this submission satisfy the bounty?"* BountyMilestonePayout removes the middleman: anyone can fund a bounty, anyone can submit work, and GenLayer validators reach consensus on whether the work meets the criteria — then funds move automatically.

## Live Deployment

| | |
|---|---|
| **Contract** | [BountyMilestonePayout](https://explorer-studio.genlayer.com/address/0xd5187391b8531e4C09E20Ef544Fbb312279be797) |
| **Address** | `0xd5187391b8531e4C09E20Ef544Fbb312279be797` |
| **Network** | GenLayer studionet (chain `61999`) |
| **Status** | ✅ deployed + audited on-chain |

## Highlights

- 🎯 **LLM evaluation** — validators independently fetch the submission URL and agree on `approve` / `reject`
- ⚖️ **Solver disputes** — rejected solvers can dispute; validators re-evaluate and uphold or overturn
- 💸 **Atomic payout** — approved bounties pay the solver exactly once; no double release
- 🔓 **No fund locks** — creator can cancel open bounties; solver can reclaim if evaluation times out (7 days); expired bounties are reclaimable
- 🧱 **Reusable primitive** — bug bounties, grants, hackathon prizes, milestone-based gig work

## How It Works

```
create_bounty (creator funds reward + criteria)
      │
      ▼
submit_work (solver, with submission URL)
      │
      ▼
evaluate_submission (creator only — LLM consensus)
      │                             │
      ├── approved ───────────────► release_funds → solver paid
      └── rejected ───────────────► dispute_rejection (solver) → uphold / overturn_to_approve
```

Stuck states always have an exit: `cancel_bounty`, `claim_evaluation_timeout`, `reclaim_expired`.

## Methods

| Role | Method | Guard |
|---|---|---|
| Creator | `create_bounty` *(payable)*, `evaluate_submission`, `release_funds`, `cancel_bounty`, `reclaim_expired` | creator-only; status + deadline checks |
| Solver | `submit_work`, `dispute_rejection`, `claim_evaluation_timeout` | solver-only; open/submitted/rejected states |
| Any | `get_bounty`, `get_all_bounties`, `get_submission`, `get_bounty_submissions` | read-only |

## Security Model

- Ownership enforced on every mutation (`evaluate_submission` / `release_funds` creator-only, `dispute_rejection` solver-only)
- **Evidence is evaluated, not just linked**: the contract fetches the submission URL on-chain (`gl.nondet.web.get`, non-200 reverts) and feeds the fetched content into the evaluation/dispute consensus
- Validators independently re-fetch + re-evaluate and must agree on the exact stored decision
- **Atomic, once-only payout** via `emit_transfer`; terminal states (`paid`, `cancelled`, `refunded`, `expired`) can't transition further
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
