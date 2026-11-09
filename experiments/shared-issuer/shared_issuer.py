"""Shared-issuer experiment: which configuration admits another Governance Tenant's agent.

The IdP's issuer is multi-tenant, with tenants acme and beta; the RAS
trusts the issuer's tenant acme for acme-data.

Runs the conformance suite's reference IdP, RAS and API in process, sets
each cell's configuration through test control, and records the outcome.
Exits with status 1 if any outcome differs from the expectation below.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "conformance"))

import jws  # noqa: E402
import run as conformance  # noqa: E402
import suite  # noqa: E402

OTHER_AGENT = "agent-77"   # an agent of beta, on the same issuer


def minted(ctx, agent, tenant):
    """An ID-JAG for agent whose tenant claim names tenant."""
    cfg = ctx.cfg
    return ctx.adapter.mint_grant(suite.grant_claims(
        ctx, act={"iss": cfg.expect["agent_iss"], "sub": agent}, tenant=tenant))


def outcome(resp):
    body = resp.json()
    if resp.status == 200 and ("access_token" in body):
        return "admitted"
    return body.get("error") or f"HTTP {resp.status}"


def cell_idp(user_tenant, pair_authorized):
    """The agent in beta, the user in user_tenant, and (beta, acme-data) as given."""
    def run(ctx):
        ctx.adapter.set("idp", "agent_governance_tenant", "beta")
        ctx.adapter.set("idp", "user_tenant", user_tenant)
        ctx.adapter.set("idp", "tenant_pair", ["beta", "acme-data", pair_authorized])
        resp = ctx.client.exchange(ctx.id_token())
        if resp.status != 200:
            return outcome(resp)
        return f"issued, tenant {jws.decode(resp.json()['access_token'])[1].get('tenant')}"
    return run


def cell_ras(jit, gate_rule, correlated, tenant="beta"):
    def run(ctx):
        if jit:
            ctx.adapter.set("ras", "jit", True)
        if gate_rule:
            ctx.adapter.set("ras", "actor_gate_rule", True)
        if correlated:
            ctx.adapter.set("ras", "correlate_agent", OTHER_AGENT)
        return outcome(ctx.client.redeem(minted(ctx, OTHER_AGENT, tenant)))
    return run


def cell_tenant_claim(ctx):
    """Grants for acme's agent-42 and beta's agent-77 differ in tenant."""
    ours = jws.decode(minted(ctx, ctx.cfg.expect["agent"], "acme"))[1]
    theirs = jws.decode(minted(ctx, OTHER_AGENT, "beta"))[1]
    suite.check(sorted(ours) == sorted(theirs), "claim sets differ")
    return f"tenant {ours['tenant']} and {theirs['tenant']}"


CELLS = [
    ("IdP", "agent in beta, user in acme; (beta, acme-data) authorized",
     cell_idp("acme", True), "actor_unauthorized"),
    ("IdP", "agent and user in beta; (beta, acme-data) not authorized",
     cell_idp("beta", False), "actor_unauthorized"),
    ("IdP", "agent and user in beta; (beta, acme-data) authorized",
     cell_idp("beta", True), "issued, tenant beta"),
    ("RAS", "JIT off, per-agent actor gate", cell_ras(False, False, False), "invalid_grant"),
    ("RAS", "JIT on, per-agent actor gate", cell_ras(True, False, False), "invalid_grant"),
    ("RAS", "JIT on, issuer-wide actor-gate rule", cell_ras(True, True, False), "invalid_grant"),
    ("RAS", "agent-77 correlated and admitted by an explicit gate entry",
     cell_ras(False, False, True), "invalid_grant"),
    ("RAS", "beta's agent, grant naming acme; JIT on, issuer-wide rule",
     cell_ras(True, True, False, tenant="acme"), "admitted"),
    ("RAS", "grants for acme's and beta's agents", cell_tenant_claim, "tenant acme and beta"),
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
