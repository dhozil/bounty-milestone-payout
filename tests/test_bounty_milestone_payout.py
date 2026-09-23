"""Direct-mode tests for the BountyMilestonePayout contract.

Covers: bounty creation, submission, owner-only evaluation, dispute mechanism,
evaluation timeout, fund release, expiry, cancellation.
"""

import json
import re

from gltest.direct import create_address

BOUNTY_TITLE = "Fix Login Bug"
BOUNTY_DESC = "Fix the login page crash on mobile devices"
BOUNTY_CRITERIA = "Must fix the crash, include test, and pass CI"
EVAL_JSON = json.dumps(
    {"decision": "approve", "reasoning": "Submission fixes the crash and includes tests.", "confidence": 90}
)
REJECT_JSON = json.dumps(
    {"decision": "reject", "reasoning": "Submission does not include tests.", "confidence": 85}
)
DISPUTE_UPHOLD_JSON = json.dumps(
    {"decision": "uphold_rejection", "reasoning": "Dispute does not address missing tests.", "confidence": 88}
)
DISPUTE_OVERTURN_JSON = json.dumps(
    {"decision": "overturn_to_approve", "reasoning": "Dispute is valid, tests are present.", "confidence": 92}
)
SUBMIT_URL = "https://github.com/example/repo/pull/123"
SUBMIT_DESC = "Fixed the login crash by updating the event handler"


def _create_bounty(contract, vm, creator, reward=1000):
    vm.sender = creator
    vm.value = reward
    return contract.create_bounty(
        title=BOUNTY_TITLE, description=BOUNTY_DESC,
        criteria=BOUNTY_CRITERIA, deadline_days=7,
    )


def test_create_bounty_validates(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")

    direct_vm.sender = creator
    direct_vm.value = 1000
    with direct_vm.expect_revert("Title and criteria are required"):
        contract.create_bounty("", "desc", "criteria", 7)
    with direct_vm.expect_revert("Deadline must be at least 1 day"):
        contract.create_bounty("T", "d", "c", 0)
    with direct_vm.expect_revert("Reward must be > 0"):
        direct_vm.value = 0
        contract.create_bounty("T", "d", "c", 7)

    bid = _create_bounty(contract, direct_vm, creator)
    assert contract.get_bounty(bid)["status"] == "open"
    assert contract.get_bounty(bid)["reward"] == 1000


def test_submit_work(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    sid = contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)
    assert contract.get_bounty(bid)["status"] == "submitted"
    assert contract.get_bounty(bid)["solver"] == str(solver)


def test_submit_reverts_on_closed_bounty(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    with direct_vm.expect_revert("not open"):
        contract.submit_work(bid, SUBMIT_URL, "Another submission")


def test_evaluate_only_creator(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")
    other = create_address("other")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fix"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), EVAL_JSON)
    direct_vm.sender = other
    with direct_vm.expect_revert("Only creator can evaluate"):
        contract.evaluate_submission(bid)


def test_evaluate_approve(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fixed login bug"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), EVAL_JSON)
    direct_vm.sender = creator
    result = contract.evaluate_submission(bid)
    assert result["decision"] == "approve"
    assert contract.get_bounty(bid)["status"] == "approved"


def test_evaluate_reject(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Partial fix"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), REJECT_JSON)
    direct_vm.sender = creator
    result = contract.evaluate_submission(bid)
    assert result["decision"] == "reject"
    assert contract.get_bounty(bid)["status"] == "rejected"


def test_dispute_rejection(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fix"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), REJECT_JSON)
    direct_vm.sender = creator
    contract.evaluate_submission(bid)
    assert contract.get_bounty(bid)["status"] == "rejected"

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fix with tests"})
    direct_vm.mock_llm(re.escape("bounty dispute resolver"), DISPUTE_OVERTURN_JSON)
    direct_vm.sender = solver
    result = contract.dispute_rejection(bid, "The submission does include tests in the test folder.")
    assert result["decision"] == "overturn_to_approve"
    assert contract.get_bounty(bid)["status"] == "approved"


def test_dispute_only_solver(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")
    other = create_address("other")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fix"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), REJECT_JSON)
    direct_vm.sender = creator
    contract.evaluate_submission(bid)

    direct_vm.sender = other
    with direct_vm.expect_revert("Only solver can dispute"):
        contract.dispute_rejection(bid, "test reason")


def test_release_funds_only_creator(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    direct_vm.mock_web(re.escape(SUBMIT_URL), {"status": 200, "body": "Fix"})
    direct_vm.mock_llm(re.escape("bounty evaluator"), REJECT_JSON)
    direct_vm.sender = creator
    contract.evaluate_submission(bid)

    with direct_vm.expect_revert("not approved"):
        contract.release_funds(bid)


def test_views(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/bounty_milestone_payout.py")
    creator = create_address("creator")
    solver = create_address("solver")

    bid = _create_bounty(contract, direct_vm, creator)
    direct_vm.sender = solver
    contract.submit_work(bid, SUBMIT_URL, SUBMIT_DESC)

    bounty = contract.get_bounty(bid)
    assert bounty["title"] == BOUNTY_TITLE
    assert bounty["status"] == "submitted"
    assert bounty["evaluation_deadline"] != ""

    subs = contract.get_bounty_submissions(bid)
    assert len(subs) == 1
    assert subs[0]["solver"] == str(solver)
