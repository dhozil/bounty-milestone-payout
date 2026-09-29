# Submission: Bounty & Milestone Payout

## Category
Intelligent Contracts

## Contract Name
Bounty & Milestone Payout

## Summary
A reusable GenLayer primitive for trustless bounties and milestone-based payouts. Creators fund bounties with natural-language acceptance criteria, solvers submit work via URL, and GenLayer validators reach consensus on whether the submission satisfies the criteria — releasing funds automatically on approval.

## What Makes This Unique
- **Consensus-based evaluation**: LLM validators decide "does this meet the bounty?" instead of a trusted judge
- **Solver dispute path**: rejected solvers can dispute; validators re-evaluate and uphold or overturn
- **Atomic payout**: approved bounties pay exactly once, no double release
- **No locked funds**: cancel, evaluation-timeout reclaim, and expiry reclaim cover every stuck state
- **Reusable primitive**: foundation for bug bounties, grants, hackathons, milestone gig work

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
[`0xD6644fc00207A7B0846A14D099be122Ae6040190`](https://explorer-studio.genlayer.com/address/0xD6644fc00207A7B0846A14D099be122Ae6040190)

## Source Code
See `contracts/bounty_milestone_payout.py`
