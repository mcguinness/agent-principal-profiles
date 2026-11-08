# Shared-Issuer Experiment

This experiment records which configuration lets a grant for another
Governance Tenant's agent through, when Governance Tenants share one IdP
issuer. It tests the reference implementation's behavior under explicit
IdP authorization and RAS trust configuration, not conformance; the
[conformance suite](../../conformance/README.md) tests the two
requirements involved (N33 and N34). The experiment comes before any
fix: COORDINATION's WAG notes record the gap it examines.

## Running it

```sh
python3 experiments/shared-issuer/shared_issuer.py
```

It needs the conformance suite's requirements
(`conformance/requirements.txt`). The script prints the table below and
exits with status 1 if any outcome differs from the expectation recorded
in `shared_issuer.py`. It is run by hand; CI does not run it.

Three of the test controls it uses are reference-only and not part of
the suite's adapter contract: `tenant_pair` at the IdP, and
`actor_gate_rule` and `correlate_agent` at the RAS. No suite case needs
them.

## Setup

The reference IdP's issuer `https://idp.example/` serves two Governance
Tenants, `acme` and `beta`. An agent identifier is unique across
them, as core Canonical Identity and Tenant Boundaries requires. Policy
at the IdP authorizes (Governance Tenant, Target Tenant) pairs for
issuance; by default only (`acme`, `acme-data`). The RAS governs
`acme-data`, trusts the IdP's issuer for users and agents, and resolves
Alice as `user-108`.

The RAS cells redeem a grant naming `agent-77`, an agent of `beta`
that the RAS has never seen. The suite mints it through the IdP's test
control. It stands for the grant an IdP that authorized (`beta`,
`acme-data`) would issue: the IdP cells show that the IdP issues such a
grant only when that pair is authorized, and that the grant it then
issues names no Governance Tenant.

## Results

| Role | Configuration | Outcome |
|---|---|---|
| IdP | `beta` not authorized for `acme-data` | Refused, `actor_unauthorized` |
| IdP | `beta` authorized for `acme-data` | Issued; no claim names the Governance Tenant |
| RAS | Just-in-time correlation off, per-agent actor gate | `invalid_grant` (no correlation) |
| RAS | Just-in-time correlation on, per-agent actor gate | `actor_unauthorized` (correlation is not authorization) |
| RAS | Just-in-time correlation on, an actor-gate rule admitting every agent the issuer asserts for users in `acme-data` | Admitted |
| RAS | `agent-77` correlated and admitted by an explicit gate entry | Admitted |
| RAS | Grants for `acme`'s `agent-42` and `beta`'s `agent-77` | Same claim names; only `act.sub` differs |

The admitting rule in the fifth row conforms. The actor-gate
requirement leaves the decision to the RAS: it "MUST independently
decide whether to accept that delegation under its local user, actor,
client, tenant, and resource policy" (core: Delegated Actor
Authorization). The RAS and API implementation considerations
illustrate this: the gate "can be implemented through an agent
registration, tenant assignment, consent policy, or another explicit
rule". The API's own actor gate is not exercised here; the experiment
stops at the RAS.

## Finding

The RAS cannot learn the agent's Governance Tenant from the grant,
because neither grant carries it. Per-agent admission remains an
independent control: a RAS that correlates and admits each agent
explicitly refuses the other tenant's agent (the first two RAS rows).
With issuer-wide admission, and no governance-partition information
provisioned to the RAS by other means, the RAS relies on the IdP's
(Governance Tenant, Target Tenant) authorization to keep one tenant's
agents out of another tenant's resources.

## Fix candidates

None is chosen here.

1. **Dedicated issuers.** One issuer per Governance Tenant, which
   Section 6.3 of WAG RECOMMENDED. RAS trust and actor-gate rules keyed
   by issuer then mean one tenant. No grant changes.
2. **A Governance Tenant claim in both grants**, with RAS trust and
   just-in-time correlation keyed by (issuer, Governance Tenant), as
   Section 6.3 of WAG does with a registered claim. ID-JAG's `tenant`
   claim carries the user's tenant at a multi-tenant issuer (Section 3.1
   of ID-JAG), and the core does not require the agent's Governance
   Tenant to be the user's tenant. Whether the two can differ in a
   delegated grant has to be settled before choosing this candidate,
   since one claim cannot carry both if they can.
3. **A security consideration only:** say that an issuer-wide actor-gate
   rule at a shared issuer admits every Governance Tenant's agents, and
   that a RAS relying on such a rule depends on the IdP's tenant-pair
   authorization.
