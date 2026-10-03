# Submission: Bounty & Milestone Payout

## Category
Intelligent Contracts

## Contract Name
Bounty & Milestone Payout

## Summary
A reusable GenLayer primitive for trustless bounties and milestone-based payouts. Creators fund bounties with natural-language acceptance criteria, solvers submit work via URL, and GenLayer validators reach consensus on whether the submission satisfies the criteria — releasing funds automatically on approval.

## What Makes This Unique
- **Consensus-based evaluation**: LLM validators decide "does this meet the bounty?" instead of a trusted judge
- **Solver dispute path**: rejected solvers can dispute once within a bounded window; validators re-evaluate and uphold or overturn
- **Exactly-one payout machine**: every reachable status has exactly one authorized, replay-safe payout or refund transition — money only moves into `paid`, `cancelled`, or `refunded`, never twice
- **Solver remedies**: an approved solver claims the reward without any creator call; an evaluation-timeout claim pays the solver (not only the creator)
- **No locked funds**: creator cancel, rejection finalize (after the dispute window), and expiry reclaim cover every reachable state in bounded time
- **Reusable primitive**: foundation for bug bounties, grants, hackathons, milestone gig work

## Terminal-Path Completeness (steward request)
| Requirement | Mechanism |
|---|---|
| Approved solver receives reward without a voluntary creator call | `claim_reward` (solver-only): `approved → paid`, pays the solver; `release_funds` remains as the creator's optional path into the same single transition |
| Rejection (incl. upheld dispute) has a bounded finalization/refund | `finalize_rejection` (creator-only): `rejected → refunded`, allowed once the 3-day dispute window passes **or** immediately after a dispute is upheld; disputes are limited to one (`dispute_reason` set on first dispute) |
| Evaluation-timeout gives a coherent solver remedy | `claim_evaluation_timeout` now pays the **solver**: `submitted → paid` after the 7-day evaluation window; the creator can no longer evaluate past the window, so there is no race and no creator-only refund path |
| Every reachable status: exactly one authorized, replay-safe payout/refund transition | Status-flip guards make each transition once-only; `reclaim_expired` no longer moves money (it only marks `expired`), removing the old double-refund via `cancel_bounty` from `expired`; unreachable `disputed` status removed |

All of the above verified on-chain at the live deployment (creator/solver role checks, replay attempts, dispute-window block, uphold→finalize→refunded) and covered by 18 direct-mode unit tests (including time-warped window tests).

## How Consensus Is Used
The contract uses `gl.vm.run_nondet_unsafe()` with a custom validator function. Each validator independently fetches the submission URL on-chain (`gl.nondet.web.get`, non-200 reverts) and the **contract-fetched content is embedded directly into the prompt** (`--- BEGIN FETCHED CONTENT ---`), so evaluation and dispute both judge the exact bytes the contract retrieved — not a URL the LLM would re-fetch on its own. Consensus is reached when validators agree on the exact decision (`approve`/`reject`, `uphold_rejection`/`overturn_to_approve`).

The dispute path performs a **fresh evaluation** of the fetched content against the criteria; the original decision's free-form reasoning is deliberately not carried into the dispute prompt, so no unverified text can influence the final outcome.

## Technical Details
- Python-based GenLayer Intelligent Contract
- Uses `gl.nondet.exec_prompt()` for LLM evaluation and dispute resolution
- Uses `gl.nondet.web.get()` for contract-side submission acquisition (non-200 reverts)
- Custom validators require exact decision agreement
- TreeMap for scalable bounty and submission storage
- Payouts via `emit_transfer`; integer-only value domain

## Use Case
Bug bounty platforms, grant programs, hackathon prizes, milestone-based freelance work — any scenario where payment depends on judging submitted work against stated criteria.

## Live Deployment
Deployed on GenLayer studionet (chain `61999`):
[`0x935397C69F318331D4cb73EF2dc0ee7aA1a18b13`](https://explorer-studio.genlayer.com/address/0x935397C69F318331D4cb73EF2dc0ee7aA1a18b13)

## Source Code
See `contracts/bounty_milestone_payout.py`
