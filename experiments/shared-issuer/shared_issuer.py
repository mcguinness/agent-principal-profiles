"""Shared-issuer experiment: which configuration admits another Governance Tenant's agent.

Runs the conformance suite's reference IdP, RAS and API in process, sets
each cell's configuration through test control, and records the outcome.
Exits with status 1 if any outcome differs from the expectation below.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "conformance"))

import jws  # noqa: E402
import run as conformance  # noqa: E402
import suite  # noqa: E402

OTHER_AGENT = "agent-77"   # an agent of beta-gov, on the same issuer


def claim_names(token):
    return sorted(jws.decode(token)[1])


def minted(ctx, agent):
    """The ID-JAG an IdP that authorized (beta-gov, acme-data) would issue for agent."""
    cfg = ctx.cfg
    return ctx.adapter.mint_grant(suite.grant_claims(
        ctx, act={"iss": cfg.expect["agent_iss"], "sub": agent}))


def outcome(resp):
    body = resp.json()
    if resp.status == 200 and ("access_token" in body):
        return "admitted"
    return body.get("error") or f"HTTP {resp.status}"


def cell_idp_unauthorized(ctx):
    ctx.adapter.set("idp", "agent_governance_tenant", "beta-gov")
    return outcome(ctx.client.exchange(ctx.id_token()))


def cell_idp_authorized(ctx):
    ctx.adapter.set("idp", "agent_governance_tenant", "beta-gov")
    ctx.adapter.set("idp", "tenant_pair", ["beta-gov", "acme-data", True])
    resp = ctx.client.exchange(ctx.id_token())
    if resp.status != 200:
        return outcome(resp)
    grant = resp.json()["access_token"]
    # The grant names no Governance Tenant: nothing in it says beta-gov.
    suite.check("beta-gov" not in json.dumps(jws.decode(grant)[1]),
                "the grant carries the Governance Tenant")
    return "issued, no Governance Tenant in the grant"


def cell_ras(jit, gate_rule, correlated):
    def run(ctx):
        if jit:
            ctx.adapter.set("ras", "jit", True)
        if gate_rule:
            ctx.adapter.set("ras", "actor_gate_rule", True)
        if correlated:
            ctx.adapter.set("ras", "correlate_agent", OTHER_AGENT)
        return outcome(ctx.client.redeem(minted(ctx, OTHER_AGENT)))
    return run


def cell_same_shape(ctx):
    """A grant for acme-gov's agent-42 and one for beta-gov's agent-77 have the same claims."""
    ours = minted(ctx, ctx.cfg.expect["agent"])
    theirs = minted(ctx, OTHER_AGENT)
    suite.check(claim_names(ours) == claim_names(theirs), "claim sets differ")
    return "same claim names; only act.sub differs"


CELLS = [
    ("IdP", "beta-gov not authorized for acme-data", cell_idp_unauthorized,
     "actor_unauthorized"),
    ("IdP", "beta-gov authorized for acme-data", cell_idp_authorized,
     "issued, no Governance Tenant in the grant"),
    ("RAS", "JIT off, per-agent actor gate", cell_ras(False, False, False), "invalid_grant"),
    ("RAS", "JIT on, per-agent actor gate", cell_ras(True, False, False), "actor_unauthorized"),
    ("RAS", "JIT on, issuer-wide actor-gate rule", cell_ras(True, True, False), "admitted"),
    ("RAS", "agent-77 correlated and admitted by an explicit gate entry",
     cell_ras(False, False, True), "admitted"),
    ("RAS", "grants for acme-gov's and beta-gov's agents", cell_same_shape,
     "same claim names; only act.sub differs"),
]


def main():
    cfg, adapter, servers = conformance.reference_config()
    suite.wait_ready(cfg)
    mismatches = 0
    print(f"{'Role':4}  {'Configuration':58}  Outcome")
    for role, label, fn, expected in CELLS:
        adapter.reset()
        ctx = suite.Context(cfg, adapter)
        try:
            got = fn(ctx)
        except AssertionError as err:
            got = f"check failed: {err}"
        mark = "" if got == expected else f"   (expected {expected})"
        mismatches += got != expected
        print(f"{role:4}  {label:58}  {got}{mark}")
    for server in servers:
        server.shutdown()
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
