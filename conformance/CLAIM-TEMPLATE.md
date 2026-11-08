# Conformance Claim Template

A form for stating what an implementation of the governed agent profiles
claims. It adds no requirement: each line points to the draft text that
defines the claim. The core's Conformance Claims section requires a
claim to identify the profile by its URI, the realization, the role,
the supported inputs, and any claim of generic shared-client
interoperability (Part 1). The rest records optional capabilities,
companion claims, the configuration a peer must agree on, and the
evidence offered.

Copy it, fill in each line, and delete the guidance in italics.

## Part 1. What the core requires a claim to state

| Item | Value | Draft text |
|---|---|---|
| Implementation and version | | |
| Role | IdP / RAS / API / client | core: Conformance Claims |
| Realization | Delegated (ID-JAG) / self-acting (WAG) / both | core: Conformance Claims |
| Profile URIs | `urn:ietf:params:oauth:grant-profile:id-jag-governed-agent`, `...:id-jag-agent-federation`, `...:wag-governed-agent`, `...:wag-agent-federation` (list each) | core: Authorization Server and Client Metadata |
| Supported inputs | Dedicated client with `private_key_jwt` (mandatory for the IdP and client); existing platform JWT; SAML subjects; IdP refresh-token subjects; inputs of the input profiles companion (name each) | core: Conformance Claims; Agent Resolution |
| Generic shared-client interoperability | Claimed / not claimed. *A claim requires the existing platform JWT input: an IdP accepts it, a client presents it. For an IdP, the suite's P11, P12 and N36 to N39 test the claim when `Config.shared_client` is set.* | core: Conformance Claims; Existing Platform JWT |

## Part 2. Optional capabilities

*Mark each supported, not supported, or not applicable to the role.*

| Capability | Status | Draft text |
|---|---|---|
| Bearer access tokens for resources configured to permit them | | core: Access-Token Protection |
| Mutual-TLS-bound access tokens | | core: Access-Token Protection |
| Re-redemption of a bound grant under explicit policy | | core: Common Grant Validation |
| Just-in-time correlation | | core: Optional Just-in-Time Correlation |
| RAS refresh tokens | | core: Optional RAS Refresh Tokens |
| Opaque access tokens and introspection | | core: Optional Opaque Access Tokens and Introspection |
| Policy services | | core: Optional Policy Services |
| DPoP nonces demanded (RFC 9449 Sections 8 and 9) | | RFC 9449 |

## Part 3. Companion claims

| Companion | Claims made | Draft text |
|---|---|---|
| Agent resolution input profiles | Each input claimed | inputs: Conformance |
| Identity continuation | Delegated / self-acting continuation per role; grant-anchored continuation (IdP) | continuation: Conformance Claims |
| Human oversight | Deferred governed issuance; deferred continuation; supervised issuance per target; deferred redemption; per-action oversight (each with its role) | oversight: Conformance |
| Lifecycle | Provisioning, signals, grant-derived revocation | lifecycle: Conformance and Configuration |
| SCIM management | Resources and operations supported | SCIM agent federation: Conformance and Administrative Trust |

## Part 4. Configuration a peer must agree on

*The implementer's guide lists what each pair of implementations
exchanges ("Configuration exchanged between implementations"). Record
the values this deployment uses, or how a peer obtains them.*

| Value | This deployment |
|---|---|
| Minimum adoption profile, per client, issuer and resource | |
| Grant lifetime (the core recommends at most 300 s) | |
| Freshness limit on cached policy data at the IdP | |
| Access-token lifetime, and refresh-authorization lifetime where issued | |
| Absolute authorization expiration | |
| Maximum disablement delay, including propagation and cache freshness | |
| Where the Target Tenant is carried | |
| Client registration association at each RAS | |
| How the actor gate is set (per agent, per tenant, consent, other rule) | |
| Clock skew allowed on time claims and DPoP proofs | |

## Part 5. Evidence

| Item | Value |
|---|---|
| Suite revision run (repository commit) | |
| Mode | Full / RAS-only (`suite.SigningAdapter`) |
| Cases passed | |
| Cases failed, with reasons | |
| Cases not run, with reasons (IdP cases in RAS-only mode; missing test-control capability) | |
| Notes reported (SHOULD-level departures) | |
| Interoperability tested with (implementation, version, roles) | |

Passing the suite is evidence for the cases it runs, not a conformance
claim ([README](README.md)).
