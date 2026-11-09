# Shared-Issuer Experiment

This experiment records which configuration lets a grant for another
Governance Tenant's agent through, when Governance Tenants share one IdP
issuer. It tests the reference implementation's behavior under explicit
IdP authorization and RAS trust configuration, not conformance; the
[conformance suite](../../conformance/README.md) tests the requirements
involved (N33, N34, N41 and N42).

The first run, before any fix, found that neither grant carried the
agent's Governance Tenant, so a RAS that admitted agents issuer-wide
could not keep another tenant's agents out. The core now treats a
Governance Tenant as a tenant of the issuer in the sense of Section 6.1
of ID-JAG (core: Canonical Identity and Tenant Boundaries), and this run
records the outcomes under that rule.

## Running it

```sh
python3 experiments/shared-issuer/shared_issuer.py
```

It needs the conformance suite's requirements
(`conformance/requirements.txt`). The script prints the table below and
exits with status 1 if any outcome differs from the expectation recorded
in `shared_issuer.py`. It is run by hand; CI does not run it.

Three of the test controls it uses are reference-only and not part of
the suite's adapter contract: `user_tenant` at the IdP, and
`actor_gate_rule` and `correlate_agent` at the RAS. No suite case needs
them.

## Setup

The reference IdP's issuer `https://idp.example/` is multi-tenant, with
tenants `acme` and `beta`. Each tenant is a Governance Tenant, and an
agent identifier is unique across them, as core Canonical Identity and
Tenant Boundaries requires. Alice and `agent-42` are in `acme`, and
every grant names the user's tenant in `tenant`. Policy at the IdP
authorizes (Governance Tenant, Target Tenant) pairs for issuance; by
default only (`acme`, `acme-data`). The RAS governs `acme-data`, trusts
the issuer's tenant `acme` for it, and resolves Alice as `user-108`.

The RAS cells redeem a grant naming `agent-77`, an agent of `beta` that
the RAS has never seen. The suite mints it through the IdP's test
control, naming `beta` in `tenant` as a conforming IdP would, except in
the cell that names `acme`.

## Results

| Role | Configuration | Outcome |
|---|---|---|
| IdP | Agent in `beta`, user in `acme`; (`beta`, `acme-data`) authorized | Refused, `actor_unauthorized` (the agent is not in the user's tenant) |
| IdP | Agent and user in `beta`; (`beta`, `acme-data`) not authorized | Refused, `actor_unauthorized` |
| IdP | Agent and user in `beta`; (`beta`, `acme-data`) authorized | Issued, `tenant` `beta` |
| RAS | Just-in-time correlation off, per-agent actor gate | `invalid_grant` (tenant not trusted) |
| RAS | Just-in-time correlation on, per-agent actor gate | `invalid_grant` |
| RAS | Just-in-time correlation on, an actor-gate rule admitting every agent the issuer asserts for users in `acme-data` | `invalid_grant` |
| RAS | `agent-77` correlated and admitted by an explicit gate entry | `invalid_grant` |
| RAS | `beta`'s agent in a grant naming `acme`; just-in-time correlation on, issuer-wide rule | Admitted |
| RAS | Grants for `acme`'s `agent-42` and `beta`'s `agent-77` | `tenant` `acme` and `beta` |

## Finding

The RAS learns the agent's Governance Tenant from `tenant`, and trusts
the issuer one tenant at a time, so every RAS configuration refuses
`beta`'s grants for `acme-data`, issuer-wide admission included. The IdP
issues `beta`'s agent a delegated grant only for a user in `beta`, and
only where policy authorizes (`beta`, `acme-data`).

What remains is the reliance on the IdP that every grant carries: a
grant naming `acme` for `beta`'s agent is admitted (the eighth row), as
a grant naming any other agent the IdP chose would be. A conforming IdP
does not issue it (the first row).
