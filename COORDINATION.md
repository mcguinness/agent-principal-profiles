# Coordination Notes for OAuth 2.0 Profile for Agent Principal Federation

This file keeps the full coordination notes that the draft's
"Differences, Dependencies, and Excluded Compositions" appendix
summarizes. They list what the profile needs from the specifications it
depends on, and the compositions it defers, in more detail than the
draft carries before working-group adoption. Backquoted names refer to
anchors and references
in `draft-mcguinness-oauth-governed-agent-federation.md`, except where a
note names the input profiles companion
(`draft-mcguinness-oauth-governed-agent-inputs.md`, `INPUTS`) or the
implementer's guide (`IMPLEMENTERS-GUIDE.md`).

## Dependencies and Deferred Work

These notes record dependencies and deferred work.
Revisions read in full against the family's use: WAG-02, ID-JAG-06,
and JWT DPoP Grant-02 (2026-11-04); DTR-01, SPIFFE OAuth-03, WIT-03,
ATTEST-12, CIMD-03, Client Instance Identifiers-01, and Client Attester
Endorsement-01 (2026-11-07); and, earlier, ICA-02, Actor Profile-01,
CIMD-02, and WISE draft 03. For RFC 10070, published from RFC 7523bis-11
with the cited section unchanged, and AIMS-01, only the cited sections
were assessed.

The drafts pin every Internet-Draft they cite: to its assessed revision,
or, for a draft cited without section numbers, to the revision current
on 2026-11-06 (Identity Chaining-17, Entity Profiles-02, Oversight
Acts-00, SCIM Agent Resource-00). CIMD is pinned at -03 with its
Section 6 an open item (`Client Authentication Drafts`, below). In CI, `tools/check_citations.py`
checks that every cited section of a pinned RFC or draft still has the
heading recorded in `tools/cited-sections.json`. Moving a pin means
reading the cited sections in the new revision and then recording their
headings (`--fetch`, `--update`).

RFC 8725 has a successor in the OAuth WG
(`draft-ietf-oauth-rfc8725bis-10`, a BCP). When it is published, the
core's citations of Sections 3.8 and 3.12 of RFC 8725 move to it once
those sections are read in it. Its Section 3.11 states that a `typ` of
`JWT` "does not constitute effective explicit typing", which the core's
credential-class rule for platform JWTs (`imported-jwt-input`) already
applies.

### Downward References

Three normative references are to documents of lower status than the
Standards Track drafts that cite them, and none is in the IETF Downref
Registry, so each needs a call-out in its Last Call (BCP 97):

* The SCIM OAuth client management profile cites RFC 7592
  (Experimental). Its requirements for a server that also offers the
  RFC 7592 interface depend on it, so the reference stays normative, as
  a reference needed to implement an optional feature is normative
  (the IESG statement on normative and informative references, Note 1;
  the same reasoning that made ICA and the continuation companion
  normative in the oversight companion).
* The lifecycle profile and the SCIM agent management profile cite the
  SCIM Agent Resource draft (`draft-wzdk-scim-agent-resource-00`,
  Informational). Both extend its Agent resource, so the reference
  cannot become informative while they do. If that draft moves to the
  Standards Track, the downref goes away.

The core cites WAG (Informational) informatively, for the reason under
WAG below.

### Upstream Dependencies

| Specification | What this profile needs | Consequence until resolved |
|---|---|---|
| WAG | Alignment on protection (`wag-gaps`) | Generic WAG support does not imply the governed composition (`wag-flow`) |
| ID-JAG and JWT DPoP Grant | One error for a bound grant redeemed without a proof (below) | Both errors are permitted |
| Actor Profile | A reusable principal-resolution extension point separating credential validation, identity mapping, and actor construction | The mapping is defined locally in `actor-construction` |
| AuthZEN OAuth mapping profile (planned; openid/authzen issue 788) | Governed-profile requirements for the represented subject, the issuer-qualified agent, the client, and the path, all taken from the validated token; COAZ-MCP, the token issuance and exchange profiles, and ARAP are to build on it (below) | Governed enforcement points supply these themselves (`policy-services`); this profile defines no AuthZEN mapping |
| COAZ-MCP error transport | Which HTTP status accompanies each JSON-RPC error on Streamable HTTP, whether a JSON-RPC error body on a non-2xx response satisfies Section 10, when the enforcement point decides, and how an actor denial is identified (below) | The implementer's guide gives a proposed interpretation: the core's status, with COAZ-MCP's error in the body. How the core's denial responses compose with COAZ-MCP is open |
| Deferred Token Response | A statement that the token returned after a deferral carries the identities the authorization server resolved from the originating request | The oversight profile requires this for governed issuance and for deferred redemption at the RAS |
| AuthZEN profiles (ARAP and its Actor Delegation Profile, AROP, Token Issuance, Token Exchange) | The mapping profile's identity model; the resolved agent as a mandatory issuance-decision input; an approval bound to the governed request and its resolved identities; an approval deadline that bounds only what the approving server issues (below) | Each enforcement point maps each profile into the governed model; the oversight profile profiles AROP at the RAS, without continuation, and AROP at the IdP stays an excluded composition |

#### WAG

In WAG-02 a Workload Identity Provider, the Platform's issuing
component, issues the grant (Section 2 of WAG). `wag-issuance` defines
issuance by an IdP acting as that Workload Identity Provider, with the
token exchange that Section 5 of WAG anticipates.

Resolved in WAG-02: Section 5.1 of WAG defines the JWT type
`oauth-wag+jwt`, which an authorization server must check (Section 6.1);
Section 5 names the token type `urn:ietf:params:oauth:token-type:wag`
for token exchange issuance; Section 8 advertises
`urn:ietf:params:oauth:grant-profile:wag` in
`authorization_grant_profiles_supported`; and Section 11 registers all
three. The core uses them (`wag-claims`, `wag-redemption`,
`server-metadata`).

Reference class: the core cites WAG informatively because it restates
every WAG requirement on the path it defines. Checked line by line
against WAG-02 Sections 5, 5.1 and 6.1 to 6.3: the grant type, the
access token's audience, `typ`, the claim set, the refresh-token
prohibition, issuer and key binding, and `sub` and `jti` scoped to the
issuer are restated (`wag-claims`, `wag-redemption`,
`redemption-common`, `time-validation`). WAG's access-token lifetime
SHOULD restates Section 4.1 of RFC 7521, which reaches the core's grants
without WAG, through RFC 7523 and JWT DPoP Grant (Renewal, below). The
rest are recorded differences that need no change to WAG (below):
issuance details, client authentication, per-agent registration, unseen
agents accepted only where policy permits, `resource` required, and
`tenant` as the shared-issuer claim. The core uses the token type, media type and grant
profile values that Section 11 of WAG registers; if WAG does not
publish, those values are unregistered.

Coordination is needed on protection: WAG-02 is a bearer grant, and
Section 9 of WAG lists proof of possession as open. This document
proposes DPoP binding at issuance and redemption under
`grant-protection`.

Open in this family, with no change to WAG: `AGENT-MANAGEMENT`
administers Client Associations for delegated issuance only, so
self-acting permission needs a flow dimension there; and
`AGENT-LIFECYCLE` defines no WAG wire composition, so revoking one WAG
is deployment-specific (`wag-gaps`).

Recorded differences, which need no change to WAG:

* **Issuance:** Section 5 of WAG names the token type for an issuer that
  uses token exchange and leaves how an Agent obtains a grant otherwise
  out of scope. Two details of the core's issuance follow from its own
  composition, not from WAG. The IdP advertises the WAG token type in
  `identity_chaining_requested_token_types_supported` (Section 7.1 of
  ID-JAG), a use that neither WAG nor ID-JAG defines
  (`server-metadata`). Because RFC 8693 requires `subject_token`, a
  client authenticated with a JWT repeats that JWT as the subject token
  (`wag-request`); a client authenticated by X.509-SVID has no
  self-acting path and can authenticate with a JWT-SVID instead. A token
  exchange that named the authenticated client as the subject would be
  an RFC 8693 extension, not a WAG change.
* **Shared issuers:** Section 6.3 of WAG, present since -01, tells
  Workload Identity Providers that share one issuer apart by a claim
  registered for each, and recommends dedicated issuers or the ID-JAG
  `tenant` claim, leaving the claim's name to each registration. The
  core takes the second recommendation (`canonical-identity`): a
  Governance Tenant is a tenant of the issuer in the sense of Section
  6.1 of ID-JAG, so at a multi-tenant issuer an ID-JAG's `tenant` names
  the agent's Governance Tenant as well as the user's (the core refuses
  delegation across tenants there), every WAG carries `tenant`, and the
  RAS trusts the issuer one tenant at a time, applying Section 4.4.1 of
  ID-JAG's tenant rule to a WAG too. The two-tenant experiment
  (`experiments/shared-issuer`) records the outcomes: every RAS
  configuration refuses another tenant's grants. WAG need not change,
  though it could name `tenant` as the claim for an issuer that several
  tenants share. An
  unauthorized (Governance Tenant, Target Tenant) pair is refused with
  `actor_unauthorized` (delegated) or `invalid_target` (self-acting).
* **Linking:** WAG accepts previously unseen agents on their first
  assertion (Section 3 of WAG), notes that each new agent creates state
  at the authorization server and that the server can cap new agents
  (Section 10), and leaves permissions to local policy (Section 6.2).
  Governed agents need an authorized local correlation before issuance
  (`wag-redemption`), provisioned in advance or created just in time
  where resource policy permits (`jit-correlation`). With just-in-time
  correlation enabled, a RAS accepts an unseen agent's first WAG as WAG
  describes; the core makes that a policy choice, off by default, keys
  the record by the exact pair, and keeps creating it separate from
  authorization. The reference tests it for a WAG (N47).
* **Renewal:** This document adopts WAG's prohibition on refresh tokens;
  continuing self-acting access re-issues the grant. Section 5 of WAG-02
  adds that access tokens SHOULD NOT outlive the assertion by a
  significant period, citing Section 4.1 of RFC 7521. RFC 7521 states
  that recommendation as an access token's lifetime relative to the
  assertion's validity period, and it applies to both grants'
  redemption: RFC 7523 (`jwt-bearer`) and JWT DPoP Grant (`jwt-dpop`)
  both use RFC 7521's access token request. `authorization-lifetime`
  points to it unchanged. Neither document defines "significant". In
  the oversight profile's deferred redemption, approval can come after
  the grant's `exp`; the token then issued is subject to RAS lifetime
  policy and to the approval expiry, any enforcement deadline, and the
  absolute authorization expiration.
* **Client registration:** Section 5 of WAG-02 says an authorization
  server MUST NOT require a client registration per Agent. This
  document does not adopt that prohibition. Client registration is
  required for the redeeming client. Shared clients can redeem grants
  for multiple agents, and several dedicated clients can map to one
  registration (`flow-configuration`), but a RAS can still give each
  agent's client its own. CIMD can avoid pre-registration where the RAS
  supports onboarding from the client's metadata document; Section 9.2
  of CIMD-03 also permits pre-registered Client Identifier URLs. The
  core's composition table states this difference (`base-differences`).
  The agent record that the RAS requires for each agent is a separate
  difference (Linking, above).

#### ID-JAG Bound Grants

Section 4.4 of ID-JAG-06 redeems a DPoP-bound ID-JAG with `jwt-dpop`,
and Section 5.2 of JWT DPoP Grant -02 forbids a server that supports
`jwt-dpop` from accepting a DPoP-bound assertion with `jwt-bearer`. The
core now redeems every grant containing `cnf` with `jwt-dpop`
(`redemption-request`), and the continuation profile follows Section
5.5.5 of ICA. One difference remains: for a bound grant redeemed
without a proof, Section 9.11.1.2.2 of ID-JAG returns `invalid_grant`
and Section 5 of JWT DPoP Grant returns `invalid_dpop_proof`. The core
permits either (`grant-protection`).

#### ID-JAG Error Codes

Section 4.4.3 of ID-JAG-06 profiles `invalid_grant` for an ID-JAG that
fails validation and `access_denied` for a valid ID-JAG whose user or
client is not authorized, and permits any other code. Section 4.4.4
tells a client that gets `invalid_grant` on re-submission to request
one new ID-JAG. Section 4.4.1 adds two MUSTs: `access_denied` when none
of the grant's resources is acceptable, and `invalid_grant` when the
recipient tenant cannot be determined or a resource is not governed
for it. The core follows both (`redemption-errors`, `errors`) and keeps
`actor_unauthorized` for an actor-gate refusal. It also keeps
`invalid_grant` for an unresolved or disabled user and an uncorrelated
or disabled agent (#59), where Section 4.4.3 profiles `access_denied`;
a generic ID-JAG client therefore requests one more ID-JAG before it
stops. At the IdP the core follows Section 4.3.4.3 of ID-JAG-06 for an
invalid subject or agent-resolution credential (`invalid_request`). It
keeps `invalid_grant` for a valid credential that resolves no user,
binding, agent, or tenant, and `actor_unauthorized`, not
`access_denied`, for a missing Delegation Authorization
(`issuance-errors`); Section 4.3.4.3 permits any code.

#### Authorization Details Errors

`draft-ietf-oauth-rar-metadata-remediation-00` (OAuth WG, Standards
Track, August 2026) defines the `insufficient_authorization` error code
and an `authorization_remediation` parameter. Its Section 4 says
resource servers "SHOULD return insufficient_authorization when access
is denied due to missing or insufficient authorization details"; its
examples use HTTP 401. The core's `resource-errors` row 5 returns HTTP
403 with `insufficient_scope` when "The operation needs scope or
authorization details that the token does not carry", so an API that
follows the core does not follow that SHOULD for authorization details.
The core keeps row 5 while the draft is at -00. When the draft is
revised or reaches Working Group Last Call, row 5 can split:
`insufficient_scope` for scope, and the draft's code and remediation for
authorization details. Which status accompanies that code joins the
open question of how the core's denial responses compose with other
denial formats (`AuthZEN and COAZ-MCP`, below).

#### Grant Replay and Re-redemption

Section 4.4.4 of ID-JAG lets a client re-submit an unexpired ID-JAG for
a new access token, and lets the RAS instead accept each ID-JAG only
once by tracking its `jti`. Section 9 of WAG leaves replay open. This
profile decides by the grant's own binding (`redemption-common`): an
unbound grant is single-use, and the RAS may accept a bound grant again
under explicit policy with a fresh proof matching its `cnf.jkt`.

Resolved in Actor Profile-01
(https://github.com/mcguinness/draft-mcguinness-oauth-actor-profile/issues/5):
Section 4.2 of ACTOR-PROFILE now makes a grant without an enforced
grant-level sender constraint single-use, and a proof used only for
client authentication or to bind the issued token is not such a
constraint. The two rules agree.

#### Client Instance Identifiers

This document composes `INSTANCE` as evidence beside the governed agent:
an instance identifier selects the Agent Principal only through an
exact, approved managed-installation binding, and the RAS conveys instance context only for an instance it validated. Two items
for the `INSTANCE` draft:

* **Appendix A.3 example:** it names the issuing authorization server as
  `act.iss`. Under governed actor preservation, the RAS keeps the IdP's
  issuer in `act.iss`, so the example should use an IdP issuer distinct
  from the token issuer.
* **Grant-carried context:** if a deployment needs the instance that
  obtained the grant, not only the one that redeemed it, this document
  would become a consuming profile under Section 7.4 of `INSTANCE` and
  define provenance and association for context in the ID-JAG or WAG.

#### Client Authentication Drafts

Two differences found in assessing the 2026-11-07 revisions:

* Not yet filed: ATTEST-12 makes `iat` REQUIRED in a Client Attestation, and its
  Section 13 lets a profile deviate only on `typ`, `sub`, and refresh
  binding. SPIFFE OAuth-03 Section 3.4.1 makes the WIT-SVID such a
  profile but validates it under WIT-03, which does not require `iat`.
  A generic ATTEST-12 server therefore rejects a WIT-SVID without `iat`
  that SPIFFE OAuth-03 accepts. `INPUTS` lists no WIT-SVID claims and
  takes no side.
* Filed as oauth-wg/draft-ietf-oauth-client-id-metadata-document#131:
  CIMD-03 Section 6 rejects a request with `invalid_client` when the
  `response_types` that a document declares and the server supports do
  not intersect. Read literally, a server with no authorization
  endpoint, such as a RAS without one, rejects every token request from
  a CIMD client, and every server rejects a document whose
  `response_types` is empty. The drafts pin CIMD-03 anyway (ruling R5,
  2026-11-10) for its Section 5, where a client lists its methods in
  `token_endpoint_auth_methods_supported`, so one document can serve an
  IdP and a RAS that accept different methods. The core makes no
  exception to Section 6: its Upstream Dependencies table states the
  consequence, a separate registration at such a server. Open until the
  issue is resolved.
* Not filed: CIMD-03 Section 5 says that "When using JWT-based client
  authentication methods such as private_key_jwt", the document "MUST
  include either jwks or jwks_uri". Read literally, that covers
  `spiffe_jwt` (SPIFFE OAuth-03) and the attestation methods of
  ATTEST-12, whose keys come from a SPIFFE bundle or an attester, so a
  document listing only such methods carries a JWK Set that no server
  uses or is rejected. The core requires `jwks` or `jwks_uri` only with
  a listed `private_key_jwt`, and `INPUTS` takes no side.
* Not filed: the same section says that when a document declares
  `private_key_jwt` "and the authorization server supports this method",
  the server "MUST require client authentication according to Section
  2.2 of [RFC7523]". The core has every IdP advertise `private_key_jwt`,
  so read literally, an IdP must demand it from a SPIFFE client that
  lists it for the RAS. The one-document deployment of the core's Client
  Metadata relies on reading "supports" per client, through the same
  section's "MAY restrict the supported methods of client authentication
  based on its own policies". The core's Client Metadata states both
  points beside the one-document case.

#### Shared Signals: WISE and CAEP

The family uses WISE (OpenID Shared Signals WG, draft 03) for workload
facts and CAEP for sessions and IdP risk:

* **Platform to IdP:** WISE credential and posture events about
  platform-hosted agents, with an RFC 9493 `aliases` subject carrying
  both the WISE `uri` workload identifier and `iss_sub` for the governed
  Agent Principal (`platform-signals` in the lifecycle draft). WISE names only the `uri`
  format; coordination is needed so that an `aliases` subject including
  `iss_sub` is a recognized WISE subject for governed agents.
* **Credential authority to IdP:** WISE credential and trust events stop
  resolution through the affected credentials and trust material
  (`time-validation`), within what configuration trusts the sending
  authority for. WISE Section 2.6.6 asks a receiver to reject every
  credential of a trust domain named in `trust-domain-federation-revoked`;
  the core does not let one authority's event end trust the IdP places
  in that domain directly.
* **Lifecycle state:** WISE `workload-enabled` carries state. This
  family keeps the notice-then-retrieve asymmetry, so enabled events
  only trigger retrieval (`scim-events` in the lifecycle draft).
* **Agent principal:** CAEP `risk-level-change` requires a `principal`,
  and neither CAEP nor SSF defines one for an agent; stream
  configuration fixes it today. A registered agent principal value in
  CAEP or SSF would remove that configuration.
* **Reference:** draft 03 is cited at its working-group editor's copy;
  move the reference to openid.net once a revision is published there.

#### Resolution from Authentication Context

This document explicitly defines delegated issuance from validated
authentication context and an approved Identity Binding, without
`actor_token`: dedicated-client identity under `client-assertion-input`
or the SPIFFE and Client Attestation identities defined in
`INPUTS`.
ID-JAG makes that parameter optional and leaves actor processing to
extensions (Section 9.10 of ID-JAG); its omission alone does not establish
this composition.

Appendix A.1 of `RFC8693` describes a subject-only request as
impersonation. Section 6.4.1.2 of ACTOR-PROFILE permits authentication-context
reuse only when the same client assertion is also present as
`actor_token`, and requires the client subject as `act.sub`.
Neither defines these mapped authentication-context inputs.

Coordination with Actor Profile and ID-JAG is needed on this explicit
extension: trusted configuration selects the resolution input,
separate mapping and authorization checks establish the governed actor,
and the issued ID-JAG contains `act`. Generic Token Exchange or Actor
Profile support does not advertise support for this composition.

#### AuthZEN and COAZ-MCP

`policy-services` lets an API delegate evaluation to a policy decision
service, names AuthZEN as one optional interface, and defines no
mapping. The service must keep the user, the issuer-qualified Agent
Principal, and the OAuth client distinct; the API takes them from the
validated access token, or an authenticated introspection response,
and trusted configuration, never from request attributes; and the
client identifier must not stand in for the actor
(`actor-authorization`).

AuthZEN Authorization API 1.0 defines a subject with `type`, `id`, and
`properties`, and no member for an actor acting on behalf of a subject.
COAZ-MCP Draft 1 (February 2026) takes the subject from the token's
`sub` (Section 3.1) and, in its default `tools/call` mapping (Section
7.1), puts the agent in `context.agent`, "typically `$token.?client_id`".
It does not read `act` or mention token exchange. For a governed
delegated token, that default names the platform's shared client, or
in a further domain the continuing gateway, as the agent for every agent
behind it.

Changing the mapping's source to `act` is not enough on its own.
COAZ-MCP treats every attribute a server-declared mapping produces,
other than the verified `subject.id`, as untrusted input (Section 11.4),
and it verifies only `subject.id` against the token (Section 8). A
declared mapping could therefore supply another agent's identity in
`context.agent` and obtain an actor-gate decision for that agent.

The OpenID AuthZEN working group decided this question on 2026-10-08,
in its [closing comment on issue
612](https://github.com/openid/authzen/issues/612#issuecomment-6068842002);
pull request 667, which proposed a trusted `context.agent`, closed with
it. COAZ-MCP will not define a trust-anchored `context.agent`. The
validated token's claims, such as `client_id` and `act`, are the
authoritative source; policies that need the actor reason over them;
and deployment-specific `context` values "carry no trust semantics from
the binding". That is the rule `policy-services` states, so the change
these notes suggested for COAZ-MCP is answered and was not filed.

The decision moves the mapping of "the represented subject, the client
as principal, the current delegated actor, and actor chains" into a
separate OAuth mapping profile, on which COAZ-MCP, the token issuance
and exchange profiles, and ARAP are to build ([issue
788](https://github.com/openid/authzen/issues/788)). A reusable
vocabulary for these members belongs there, not in these profiles,
whose examples are illustrations only. The implementer's guide
("Authorization decisions with AuthZEN") shows the enforcement point's
inputs and COAZ-MCP's default mapping as a counter-example.

**Error transport.** COAZ-MCP reports each failure as a JSON-RPC error
(Section 10) and names no HTTP status:
- mapping errors as `-32602`;
- denials as `-32001`, or as an `isError` result;
- PDP communication errors as `-32603`.

The COAZ Framework leaves error transport to each binding. The core
fixes the HTTP response (`resource-errors`). The implementer's guide
("Failures at an MCP enforcement point") proposes a deployment
interpretation: the core's status, with COAZ-MCP's error in the body.
It applies where the enforcement point controls the HTTP status and
decides before the response is committed.

That interpretation needs COAZ-MCP to settle:
* whether a JSON-RPC error body on a non-2xx response satisfies
  Section 10, and which HTTP status accompanies each category on
  Streamable HTTP;
* that the enforcement point decides before the response is committed,
  or what happens once a stream has opened;
* a way to tell an actor denial, which the core reports as
  `actor_unauthorized`, from any other denial;
* the HTTP status of a mapping failure. The guide's interpretation is
  400 when the request violates its declared contract, and 503, under
  the core's precedence, when the mapping is defective.

The core ranks the 400 only when the operation, its target, and its
tenant are identified without the invalid argument. The core's Error
Disclosure recommends validating the access token, its proof, and the
token's applicability before an error that reveals whether a route,
target, or tenant exists. The precedence of a request whose operation,
target, or tenant cannot be identified, against the core's error table,
stays unspecified. That includes a token validation that cannot complete
(503 against 404 or 400), and a mapping failure on an argument that
names the target.

A separate question remains open: how the core's denial responses
(HTTP 403 with its challenge) compose with COAZ-MCP's denials, and with
denials that MCP reports inside a result (SEP-2643, a draft).

The MCP TypeScript SDK 2.4.0 has two gaps for this interpretation
([experiment](experiments/mcp-transport/README.md)):
- for a 503, or a 403 without `insufficient_scope`, the error a client
  receives carries the status and the body as text, but not
  `Retry-After` or the challenge;
- a pre-dispatch authorization hook has no supported way to return an
  explicit unavailable response.

None of these is filed.

#### Convergence across AuthZEN profiles

COAZ-MCP is one of several AuthZEN profiles that take identity from an
OAuth token, and each places the agent differently:
- ARAP, with the Actor Delegation Profile, in `client.actor`;
- AROP Draft 1 in `subject.properties.act`, with `context.client_id`;
- Token Issuance Draft 1 in no member, because the authorization server
  builds `act`;
- the Mission-Bound Runtime Enforcement AuthZEN profile in
  `context.actor`.

The implementer's guide compares them with the governed model ("One
identity model across AuthZEN profiles"). A shared field is not enough
on its own. The OAuth mapping profile (issue 788) is where these
profiles are to converge. That issue covers the representation of
security tokens in AuthZEN requests generally, and its mapping and
trust model are still open, so the items below are requirements of the
governed profiles, stated without member names, not rules for every
OAuth deployment. These profiles need the same identity model:

* **One actor identifier.** Each profile identifies the agent by the
  (`iss`, `sub`) pair of Actor Profile, as the Actor Delegation Profile
  already does, and keeps the client identifier as a separate
  attribute.
* **Supplied by the enforcement point.** The agent comes from the
  validated token or a verified chain, never from a declared mapping or
  request input. The Actor Delegation Profile already requires this for
  `client.actor`, and the working group's COAZ-MCP decision reaches the
  same rule (above).
* **A self-acting agent is the subject.** For a token established
  through trusted context as governed self-acting access, the subject
  represents the agent. The absence of `act` alone does not establish
  that interpretation. COAZ-MCP's default names the client as the agent
  instead. The Mission profile already keeps the workload principal in
  `subject` and the client in `context.actor`; it calls that client the
  immediate actor, so policy written for it needs to take the agent
  from `subject` for these tokens.
* **Gateways are not actors.** Governed continuation keeps one actor
  and lists continuing clients in `continuation_via`. A profile that
  needs the path reads that claim, or an introspection equivalent;
  it does not expect gateways in `act`.
* **Issuance decides on the resolved agent.** Token Issuance's rule
  that a decision "may narrow what is issued; it may not broaden it,
  re-subject it, or re-target it" matches `issuance-authorization`. A
  governed IdP decides on the Agent Principal resolved through an
  Identity Binding. For a dedicated client, that agent is not the
  requesting client. Token Issuance requires every input on which the
  decision depends to be in its five mandatory fields, and treats
  `properties` and `context` as advisory input that a conforming policy
  decision point need not read. Its Token Exchange binding adds a
  requesting-party gate, but the requesting party is the party of the
  `actor_token`, or the authenticated client when there is none, so it
  need not identify the resolved agent. A new member alone is therefore
  not enough: a governed issuance binding needs the resolved agent as an
  explicit, mandatory decision input, separate from the represented
  subject and the authenticated client.
* **Cite the working-group DTR.** AROP still cites
  `draft-gerber-oauth-deferred-token-response`, which
  `draft-ietf-oauth-deferred-token-response` replaced.
* **Approval keeps the resolved identities.** AROP completes an
  approved request as an access token, and its Deferred Token Response
  binding rides on any originating grant, including redemption of an
  ID-JAG at the RAS. It does not say which identities the completed
  token carries. For a governed grant these are not the grant's literal
  claims: redemption resolves the grant's subject to the RAS's local
  user (`alice-ras` becomes `user-108` in the core's walkthrough) and
  keeps a delegated `act` unchanged, and redeeming a WAG yields the
  local agent principal as subject with no `act`. A composition needs
  the authorization server to resolve these before it requests
  approval, bind the pending request to them, and issue the token for
  them, so that neither the approval nor an account-link change while
  the request is pending substitutes another principal. Under
  `external-approval`, approval satisfies a condition and never
  replaces identity resolution, the Client Association, or the
  delegation. AROP should state this; naming the JWT grant types
  (RFC 7523 and JWT DPoP Grant) as originating grants would make the
  mapping explicit. The oversight companion already requires it for
  deferred redemption at the RAS (`redemption-deferring`).
* **Approval binds the governed request.** ARAP binds an approval to
  the Subject, Resource, Action, and authorization-relevant Context of
  the denied evaluation, but its default comparison excludes
  `subject.properties.act`, and its default completion re-evaluates
  access with the approval. Carrying the actor in a request therefore
  does not bind the approval to it. ARAP pull request 756, open and
  pending the working group's decision, would keep the actor in the
  Subject and compare it. Even then, a composition with governed
  issuance needs an approval-binding contract that ties the approval to
  the pending governed request; to the represented subject and the
  issuer-qualified agent; to the OAuth client and, for a continuation,
  the continuing client; and to the tenant, target, authority, and
  proof key. Its tests substitute another agent, client, target, or
  pending request. Until the mapping profile defines the members, such
  a contract is deployment-specific.
* **An approval deadline bounds what the approving server issues.**
  ARAP requires a PEP that issues credentials on an approval to bound
  their lifetime by `approved_until`. At a governed IdP those
  credentials are the grant; the deadline does not reach the tokens the
  RAS issues when it redeems the grant. Three cases differ: an IdP
  approval bounds grant issuance and redemption; a separate approval at
  the RAS bounds the authority the RAS issues; and carrying one
  approval from the IdP to the RAS needs an authenticated association
  between that approval and the redeemed grant, which nothing defines.
  ARAP should say that its bound applies to the credentials the PEP
  itself issues.
* **The approval deadline and exchange.** AROP bounds every token
  "obtained by exchange" by `approved_until`, without saying where the
  exchange happens. Continuation exchanges an access token at the CAI,
  then the resulting assertion at the IdP, which authorizes the onward
  grant on its own. AROP should say that `approved_until` bounds the
  credentials the deferring server itself issues, and whether an
  onward grant authorized independently derives from the approval.
  Until it does, the oversight companion makes an authorization from a
  deferred redemption ineligible for continuation
  (`redemption-refresh`), and AROP at the IdP stays excluded.

The identity items are governed-profile requirements for the OAuth
mapping profile; the rest are requests to the OpenID AuthZEN working
group and, for the Mission profile, to its editors. Not yet filed.

### Deferred Compositions

#### Grant Key Transition

A control plane obtaining a bound grant for redemption by a different
worker needs an authorized proof-key transition. This document defines
no such transition: the holder of the issuance key also redeems the
grant (the implementer's guide, "Distributed platforms and key use"). A future composition would need to bind
the new key without weakening the applicable grant protection.

#### Portable Authorization Deadlines

A portable IdP-imposed deadline on downstream access needs an
authenticated claim or reference, its association with the delegation,
and enforcement rules for access tokens and refresh authorization.
That composition is outside the scope of this document. ID-JAG `exp`
remains the redemption limit; it cannot communicate a deadline for
subsequent access (`authorization-lifetime`).

#### User Access Tokens as Subjects

Deployed on-behalf-of (OBO) flows, including `AWS-AGENTCORE-OBO`, use a user
access
token as input. This document accepts ID-JAG's ID Token, SAML, and
refresh-token subjects; it defines no access-token subject composition.
Such a composition needs rules for token eligibility and audience,
user/client/actor resolution, sender constraints, and the authority to
request downstream access. Coordinate those rules with ID-JAG;
changing only `subject_token_type` does not establish them.

#### Excluded Compositions

The following compositions are not defined in this document. Their
exclusion does not prevent the independently supported uses listed here.

| Composition | Boundary in this document |
|---|---|
| Approval before issuance or redemption | Defined for governed issuance, including continuation, and for governed redemption at the RAS, in the oversight companion (`OVERSIGHT`, below) |
| Asynchronous approval with `AROP` | At the RAS, defined for deferred redemption in the oversight companion, without continuation from the resulting authorization; at the IdP, external approval remains subject to `external-approval` and the lifetime limits in `authorization-lifetime` |
| Continuation with `ICA` | Defined for governed grants in the continuation companion (`CONTINUATION`, below); renewal without continuation follows `continuing-access` |
| General WIMSE WIT/WIC inputs | WIT-SVID and X.509-SVID resolution is defined in `spiffe-input` of `INPUTS`; non-SPIFFE credentials need an explicit OAuth presentation and proof composition |
| Instance context carried in an ID-JAG or WAG, or preserved across domains, under `INSTANCE` | The RAS conveys only an instance it validated (`access-token-response`); instances resolve the agent only through a managed-installation binding (`agent-evidence` of `INPUTS`). Preservation would need this profile to define provenance and association under Section 7.4 of `INSTANCE` |
| Mutual-TLS-bound ID-JAG | Bound grants use DPoP. Mutual TLS remains available for access-token protection under `access-token-protection`, except after a deferred redemption, which the oversight companion requires to be DPoP-bound |
| Rich Authorization Requests without scope | This profile requires meaningful scope alongside any authorization details; it does not define the scope-free mode permitted by `RFC9396` |
| Public or unattested native agents | Both grant paths authenticate the client (`scope`); a client that uses `none` and presents no attestation from a configured attester (`INPUTS`) has no governed grant path, and enrolling a key is out of scope (`overview`) |

### Operational Dependencies

Provisioning, account linking, and lifecycle propagation are deployment
choices. The implementer's guide ("Provisioning and linking") lists
useful controls. SCIM `RFC7644` and Agent resources `SCIM-AGENT` provide
building blocks, not a lifecycle propagation contract.

#### Provisioning and Disablement

Consistent correlation and disablement across IdP and RAS need an agreed
provisioning and enforcement contract. `AGENT-LIFECYCLE` profiles SCIM,
optional Shared Signals, and the effects of applied changes on authorization.
It distinguishes current administrative state from revocation history and
states the limits of missed-event recovery and token enforcement. Stronger
guarantees across unobserved transitions require an additional composition.
One is deferred rather than prohibited: it would carry an authenticated
authorization generation in the grant, agreed with ID-JAG, and define the
comparison the RAS applies.
The companion is not required for conformance to this federation profile;
`agent-correlation` and `status-changes` state this document's guarantees.

#### SCIM Interoperability Profile

`draft-zollner-scim-interop-profile-02` (individual, Standards Track)
profiles SCIM clients and Service Providers. A Service Provider opts in
by listing it in `conformsTo`; it then applies "to every resource type
that a Service Provider implements, including resource types defined
outside [RFC7643]", which includes the Agent and OAuthClient resources
here. A Service Provider can conform to it and to these profiles
together. A client cannot:

* Section 6.7: clients "MUST NOT include HTTP headers related to
  conditional requests or entity tags (ETags), such as If-Match". Here,
  changing an inactive resource to active MUST use `If-Match` with a
  resource-version ETag, and other writes SHOULD use it (Common
  Provisioning Conventions in the SCIM OAuth client management profile,
  which the lifecycle and SCIM agent management profiles follow). The
  activation condition keeps an activation based on stale state from
  overtaking a later disablement; the interoperability profile accepts
  lost updates instead. A client that follows it cannot reactivate an
  inactive Agent or OAuthClient here.
* Sections 6.3 and 6.5: clients use only the `eq` and `and` filter
  operators and "SHALL NOT use the PUT operation". These do not
  conflict. Service Providers here support PUT, and `gt` and `ge` on
  `meta.lastModified`, but no client is required to use them: a
  connector can write with PATCH alone and reconcile with equality
  filters and complete listings.

Only conditional activation conflicts. A comment to the authors could
ask that activation be exempt from Section 6.7, or that a use-case
profile be able to require conditional writes; nothing is filed.

### Related Work

#### Credential Broker for Agents (CB4A)

`draft-hartman-credential-broker-4-agents-00` (Informational, March 2026,
now expired) describes a credential broker that keeps long-lived
credentials away from agents. No draft in this family cites it. The
implementer's guide ("Credential brokers") gives the deployment
patterns. This note compares CB4A element by element; a counterpart is
the nearest mechanism here, not an equivalent.

| CB4A element | Nearest counterpart here | Difference |
|---|---|---|
| Policy decision point before credential issuance | IdP issuance authorization (Delegation or Agent Authorization), optionally through an AuthZEN PDP | None in role; CB4A also scores behavior against baselines |
| Human and MFA approval tiers | An additional issuance condition (`external-approval`), or approval before issuance under the oversight profile | Approval completes as a governed grant through Deferred Token Response, or, at the RAS, as an access token through deferred redemption, which AROP can realize; AROP at the IdP is an excluded composition (`excluded-compositions`) |
| Credential delivery point minting, for a target that accepts governed grants | The IdP grant, redeemed at the target's RAS for an access token | No vaulted credential; the target sees the agent |
| Proxy gateway, for a target that accepts governed grants | Continuation through a gateway | No credential injection; the onward grant names the same agent |
| Envelope target: service, action, resource, scope | Token exchange `audience`, `resource`, `scope`, `authorization_details` | None |
| Envelope justification and task reference | Mission-Bound Authorization; Transaction Tokens within one trust domain | Outside this family |
| Native token (Section 4.11), validated directly by the target service | For self-acting access, the access token a target RAS issues after redeeming a governed WAG | Two steps instead of one: the WAG is addressed to the RAS. The access token's issuer is the target's RAS, not a broker; its subject is the RAS's local principal correlated with the Agent Principal, not a session SPIFFE ID; it carries no envelope provenance |
| Lease revocation on an anomaly signal | Grant-derived revocation for an ID-JAG (lifecycle, optional); applied disablement or Local Suspension for the agent | No selective revocation of WAG-derived access is defined; it is deployment-specific |
| Targets that accept only API keys or their own minting | None | Outside OAuth interoperability |

Points for its author, not yet raised:

* For a target with its own authorization server, WAG issuance followed
  by RAS redemption is an alternative architecture to the native token
  of Section 4.11 for self-acting access. The target then needs no
  CB4A-specific validation, and the IdP it already trusts names the
  agent.
* The SPIFFE ID of Section 4.1 combines agent, user, and session. A
  stable agent identifier, with the user and session conveyed
  separately, would let a CB4A broker federate through these profiles:
  `identity-binding` requires an exact identity and forbids an
  execution identifier from selecting the Agent Principal.
* Its approval tiers would compose with governed issuance as approval
  before issuance under the oversight profile.
* Its `envelope_hash` provenance claim has no counterpart here, and the
  question stays open. Within one trust domain, Transaction Tokens
  (draft-ietf-oauth-transaction-tokens-11, Section 9.2.3) carry
  transaction context.

#### Agentic Identity Reference Architecture (The Identity Underground)

Sean O'Dell's post ["You Already Have the Pieces. Now Build
It."](https://www.theidentityunderground.com/post/you-already-have-the-pieces-now-build-it)
(June 4, 2026) argues that agent identity is "an assembly gap" and
proposes a reference architecture. It has five parts: a SPIFFE identity
whose namespace encodes operating bounds, an agentic gateway as the
single enforcement point, a trust broker that mints tokens and never
hands credentials to the agent, Transaction Tokens for call-chain
integrity, and Shared Signals for continuous risk. Each counterpart
below is the nearest mechanism here, not an equivalent.

| The post | Nearest counterpart here | Difference |
|---|---|---|
| A SPIFFE ID whose namespace encodes domain, intent, and trust realm | An Identity Binding to a stable Agent Principal, with authority in separate authorizations | A change of scope does not rename the agent |
| An agentic gateway as the single enforcement point | A gateway as API and continuing client, with per-action decisions through AuthZEN | The gateway does not become an actor or mint access for other domains |
| A trust broker that mints tokens for downstream tools | The IdP issues grants, and each RAS issues its own access tokens | No broker mints access across domains |
| A Transaction Token with the user as `sub` and the agent's SPIFFE ID in `act` | An ID-JAG across domains (user as `sub`, Agent Principal in `act`); inside one domain, a Transaction Token carrying the governed context in `tctx` | Transaction Tokens are bound to one trust domain, and draft-ietf-oauth-transaction-tokens-11 defines no `act` claim |
| The user's identity carried in a claim of the agent's JWT-SVID | The user's own ID Token as the subject token | The agent's credential never carries the user |
| `act_chain` for agent-to-agent delegation | Out of scope (multi-agent delegation) | Gateways forward without becoming actors (`continuation_via`) |
| Shared Signals for continuous risk | Lifecycle signals: SCIM events, CAEP grant-derived revocation, platform signals | Response to risk remains local policy |
| No sender constraint named | DPoP-bound grants in the bound profile; separately configured access-token protection | |

The post lists five unresolved questions:

* **Gateway-broker relationship (inline per request or a session):**
  answered. Grants are per resource, clients reuse tokens within the
  same authorized context (`client-token-reuse`), and a continuing
  gateway reuses downstream tokens within the same context and source
  hop.
* **Client metadata ownership (the tool endpoint registry):** answered
  in part. The IdP holds Agent Principals and their relationships, and
  resource domains hold local principals; a tool endpoint registry is
  outside these profiles.
* **Multi-hop token chaining:** answered for gateways. Continuation
  holds the chain at the IdP and needs one exchange per source hop and
  target. It ends on governance events and discloses the path.
  Agent-to-agent delegation stays out of scope. ID-JAG itself profiles
  the identity-chaining work the post cites.
* **SPIFFE namespace governance:** avoided. Identifiers carry no
  authority, so no namespace schema has to encode it.
* **Shared Signals receiver response policy:** answered in part. The
  lifecycle profile defines receiver actions for provisioning events and
  grant-derived revocation; the response to risk remains local policy.

#### Workload Identity Metadata

`draft-heigh-wimse-workload-identity-metadata-00` (Standards Track,
individual submission to WIMSE, October 16, 2026) separates a
workload's identifier from its attributes. It profiles the registered
`groups`, `roles`, and `entitlements` claims for Workload Identity
Credentials. It defines an authenticated metadata endpoint
(`/.well-known/workload-metadata?sub=`), and a `metadata_uri` claim and
an X.509 extension that locate it. It also forbids an identifier shared
by workloads that need distinct identities, and treats an AI agent as a
workload (Section 5). No draft in this family cites it. The principles
largely agree with this family's; the wire formats barely overlap. Each
counterpart below is the nearest mechanism here, not an equivalent.

| The draft | Nearest counterpart here | Difference |
|---|---|---|
| Attributes are not encoded in identifiers (Section 3) | Exact resolution through an Identity Binding (`identity-binding`); in the lifecycle profile, names, owners, and groups do not select the governed identity or grant delegation | None in principle |
| The Workload Identifier is the agent's identity (Sections 3.2 and 5) | The Agent Principal, which the IdP governs and an Identity Binding resolves from a workload identity (`model`) | A workload identifier is an input here. An agent can move between workloads through approved Identity Bindings (`governance-boundary`), and grants carry the Agent Principal, not the platform identity |
| Workloads that need separate authorization or attribution need distinct identifiers; replicas need not (Sections 4.4 and 5) | Separate Agent Principals for actors that need independent authorization, attribution, or disablement, even on a shared runtime or credential; executions alone do not need them (`governance-boundary`) | None in principle |
| An issuer distinguishes workloads on a shared execution credential by a means the workload does not control (Sections 4.4 and 11.2) | A shared IAM role needs distinct credential identities or additional trusted selectors; a caller-controlled claim distinguishes agents only under trusted issuance policy (`imported-jwt-input`, `aws-example`) | The draft constrains a credential issuer; here the IdP, like the exchanging issuer of Section 9, determines the agent but issues a grant naming the Agent Principal, not a Workload Identity Credential. Section 11.2 permits platform-assigned properties as selectors, as `imported-jwt-input` does |
| An owner or operator association confers no authority to act for that principal (Section 4.2) | `owners` on the Agent resource (`SCIM-AGENT`); the lifecycle profile states that owners provide accountability and are not automatically user delegators | The draft leaves the association's representation open (Open Issue 1); here it is a provisioned attribute, not a credential claim |
| Per-request delegation belongs in the authorization context (Sections 4.2 and 5) | The ID-JAG, with the user as subject and the Agent Principal as actor (`act`) | Section 5 cites Section 10.3 of AIMS-00, which puts the agent in an access token's `client_id` and the user in `sub`; AIMS-01 Section 10.3 says the same. Here the grant carries the agent in `act`, and each RAS issues its own access token |
| Credentials carry coarse attributes, not grants; a relying party takes authorization from its own policy (Section 4.3) | Workload evidence identifies the agent; authority comes from IdP authorizations and RAS policy | None in principle |
| An exchanging issuer's metadata is its own assertion (Section 9) | Grants carry the IdP-qualified Agent Principal (`model`) | The IdP's output is a grant, not a Workload Identity Credential |
| `groups`, `roles`, and `entitlements` claims, the metadata endpoint, and `metadata_uri` | None in grants or access tokens. SCIM carries agent attributes from platform to IdP (the SCIM agent management profile) and from IdP to resource domain (`AGENT-LIFECYCLE`) | A different interface, caller, and trust model. The draft's endpoint serves metadata by Workload Identifier to a relying party it authorizes. The lifecycle profile's Receiver serves the Agent by `externalId`, set to the exact Agent Principal identifier, to an authenticated connector within its Provisioning Domain, which supplies the issuer context (`scim` in the lifecycle draft) |

Points for its authors, not yet raised:

* Open Issue 1 asks whether a durable principal association belongs in
  Workload Metadata. This family gives one worked answer: owners are a
  provisioned attribute of the governed agent, accountable without
  delegating; an Identity Binding, not an owner, associates a workload
  with the agent; and delegation travels in the grant.
* A Workload Identifier can denote a logical workload rather than an
  execution, and the Issuer that assigns it need not be the credential
  issuer (Section 2). The draft does not define how execution
  identities bind to a separately governed agent identity, as an
  Identity Binding does here. Section 5 could say how the two compose,
  and whether metadata then describes the workload or the governed
  agent.
* Section 4.4's remedy is to issue a Workload Identity Credential
  asserting the distinguished identifier, and Section 9 extends the
  issuer's obligations to an exchange. An IdP that resolves a shared
  platform JWT to an Agent Principal makes the same determination but
  issues an authorization grant. Sections 4.4 and 9 could say whether
  they cover an exchange whose output is a grant.

## Identity Continuation Companion

`draft-mcguinness-oauth-governed-agent-continuation.md` (`CONTINUATION`)
profiles ICA-02 for governed chains, with gateways as the primary
deployment. Its "Relationship to Other Specifications" appendix lists
the changes these notes discuss. Backquoted anchors in this section
refer to that draft.

### ICA

The companion replaces or extends these ICA-02 rules for governed chains
(`relationship-to-ica`). Each is either a candidate change to ICA or a
rule that stays local to the profile:

* **Onward actor:** Section 5.5.5 of ICA places the current actor atop
  IdP-derived lineage in the onward `act`. Governed chains keep the
  Agent Principal as the only actor (ID-JAG) or as the subject (WAG),
  and the continuing client is `client_id` (`identity-preservation`).
  The core requires one `act` with no nesting at the RAS and API, and a
  WAG carries no `act`, so the ICA form cannot reach a governed target.
  The companion now defines `continuation_via`, which discloses
  continuing clients as intermediaries rather than actors, and proposes
  it for ICA with an acting or forwarding mode per hop (ICA issue #138).
  If ICA adopts it, the companion uses ICA's claim instead. Precedents
  record forwarding services apart from the principal: in the terms of
  [WS-Trust 1.4](http://docs.oasis-open.org/ws-sx/ws-trust/v1.4/os/ws-trust-1.4-spec-os.html),
  the gateway requests access on behalf of the agent rather than acting
  as it; the Kerberos privilege attribute certificate lists the services
  that a delegated ticket passed through
  ([MS-PAC](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-pac/));
  and AWS lists the services that made a request on a principal's
  behalf ([AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html)).
* **Non-user anchors:** Section 6.1 of ICA puts non-user-rooted
  authority out of scope. Self-acting chains anchor to an agent
  session: IdP state refreshed only by the agent's own authentication
  through one Identity Binding, ended by an idle timeout or an
  absolute expiration (`self-acting-root`). ICA could generalize
  anchors to any principal's session, or leave non-user roots to
  profiles. A durable anchor for scheduled self-acting work, like the
  refresh-token grant for users, is open (open item 5 of the
  companion).
* **WAG chains:** ICA issues only ID-JAGs. The companion issues onward
  WAGs and registers `governed-agent-continuation`, one grant-profile
  value for handle binding of governed ID-JAGs and WAGs, because its
  access-token protection and redemption differ from what
  `id-jag-continuation` advertises.
* **Tenant at the RAS:** Section 5.2 of ICA binds "the tenant where
  the deployment conveys one" and leaves how the RAS learns it
  deployment-specific. The governed grants now convey it: at a
  multi-tenant issuer, `tenant` names the chain's Governance Tenant
  (core `canonical-identity`), and the companion's root redemption says
  so. A gateway serving several Governance Tenants selects its
  registration by configuration, usually a Target Tenant per issuer
  tenant (`implementation-client`); the companion defines no carrier.
* **Redemption grant type:** resolved by ID-JAG-06. Section 5.5.5 of
  ICA redeems onward ID-JAGs with `jwt-dpop` (citing Section 9.8.1.2.1
  of ID-JAG-04, now 9.11.1.2.1), and Section 4.4 of ID-JAG-06 names
  `jwt-dpop` for a DPoP-bound ID-JAG. The core redeems every grant
  containing `cnf` with `jwt-dpop`, so the companion follows ICA here,
  and the core's metadata rule meets the `jwt-dpop` advertisement that
  Section 7.2 of ICA requires.
* **Access-token protection and bearer ingress:** Step 3 of Section 5.2
  of ICA requires a DPoP-bound access token for a continuation-capable
  grant carrying `cnf`; ICA tracks bearer ingress as issue #110. The
  companion keeps the core's protection selection (DPoP, mutual TLS, or
  configured bearer) and instead records no continuation eligibility
  for a bearer access token without explicit policy
  (`root-redemption`). Bearer-only MCP clients therefore need that
  policy to start a chain.
* **Retry fingerprint:** Section 5.5.7.1 of ICA fingerprints a retry
  without the requested token type, because ICA issues only ID-JAGs.
  With two grant types the companion adds `requested_token_type`.
* **Errors:** The companion uses the codes of Section 5.5.6 of ICA for
  both chain types, placing each governed check in one of ICA's
  validation rules (`continuation-errors`). It does not use the core's
  `actor_unauthorized` or `invalid_grant` for continuation failures.
* **Temporary refusals:** The companion answers HTTP 503 when the IdP
  cannot confirm shared state that a continuation depends on, such as
  an agent session or a replay reservation, and does not treat an
  agent session as ended on that basis (`continuation-errors`). ICA
  could adopt the same response, and define an OAuth error code for
  policy that blocks a chain only temporarily (open item 6 of the
  companion).
* **Root `actor_token`:** Section 5.1.1 of ICA leaves `actor_token`
  processing on the root exchange out of scope. The governed root uses
  the core's presented-evidence mode (`delegated-root`).
* **Request narrowing:** Exactly one `resource` and a required `scope`,
  from the core. Local to the profile; no ICA change needed.
* **Continuation window:** ICA bounds no hop by how long after issuance
  a CAI can obtain continuations from it, and a compromised RAS acting
  as CAI can attest any hop it accepted (Section 9.5 of ICA). The
  companion requires a finite, configured window per hop, checked when
  a request is received; lengthening the window does not extend a
  deadline already set (`governed-chain-authorization`). The window
  bounds continuation from one hop, not the chain, which ICA's finite
  hop-count limit bounds (Section 6.3 of ICA). ICA could adopt the
  window for all chains.
* **Restriction meaning:** Section 5.1.4 of ICA leaves the
  representation of a chain authorization's restrictions
  implementation-specific, so two IdPs can enforce different bounds
  from the same configuration. The companion defines their meaning
  (`restrictions`): an absent member restricts nothing, as Section 9.2
  of ICA describes for targets; a present one is a fixed ceiling; an
  empty one permits nothing; values match exactly; and an entry with
  authorization details is not met by a request without them. ICA
  could adopt that meaning for all chains. A representation that
  another product can read waits on the [authority inventory
  exercise](exercises/authority-inventory/README.md).
* **Per-hop narrowing:** A continuing client cannot ask that the hops
  it creates receive less than it holds, for example a gateway asking
  in advance for `files.read` only at the file service, in that
  service's own vocabulary. That needs restrictions carried in ICA's
  hop records, an authenticated way for a continuing client or CAI to
  request narrowing, and rules for what a child hop inherits from its
  parent. Deferred until a deployment needs it.

### WAG

* A WAG that carries `identity_continuation_handle`, and a WAG issued by
  an IdP on a continuation exchange rather than at the agent's own
  request to its Workload Identity Provider (Section 3 of WAG).
* Advertising `governed-agent-continuation` for WAGs in
  `authorization_grant_profiles_supported`, the parameter that
  Section 8 of WAG uses for `urn:ietf:params:oauth:grant-profile:wag`.

### Management

`AGENT-MANAGEMENT` administers Client Associations only. Continuation
Associations (`continuation-association`) need a resource or an
association dimension there before SCIM can administer them, and a
Delegation or Agent Authorization needs a way to record its permission
to continue (`chain-establishment`).

### Open items local to the companion

Two of the companion's open items need nothing from another
specification: whether the IdP advertises support for self-acting
continuation in metadata (open item 2), and whether the companion
recommends default idle and absolute limits for agent sessions and
conveys a session's expiration to the gateway (open item 3).

### Mission

How Mission-Bound Authorization composes with governed continuation is
unresolved. Mission stays optional, as the candidate layer for task
authorization. The "Identity Continuation Transport" of
`draft-mcguinness-oauth-mission-continuation` uses ICA and bounds each
onward ID-JAG's authorization details by the Mission's Authority Set,
but "the actor is rebound per hop", where the companion keeps the Agent
Principal as the actor and lists continuing clients in
`continuation_via` (`identity-preservation`). Aligning that sentence
alone would not complete the composition. Also open:

* how a Mission is authoritatively associated with a governed chain;
* how Mission authority maps to each target's scopes and authorization
  details (`restrictions`);
* whether narrowing a Mission narrows a chain whose chain authorization
  recorded a wider ceiling;
* how Mission state, expiry, and ancestor checks sit beside the governed
  chain-ending events (`chain-ending`); and
* which error takes precedence, and how a client retries, when a Mission
  denial and a governed failure such as `invalid_continuation` both
  apply.

A deadline for a whole task, which the per-hop continuation window does
not provide, belongs to this composition.

`draft-mcguinness-oauth-mission-child-delegation` makes a child an
OAuth client of the Child Mission ("Child Client Identity"), not an
Agent Principal with an Identity Binding, a Client Association, or a
governed authorization. The companion's "One agent" condition
(`scope-boundaries`) stands without Mission: a child agent that needs
its own governance is an Agent Principal of its own and obtains its own
governed grants and chains, and its acting for the parent agent remains
multi-agent delegation, which the core excludes. A Child Mission can
optionally supply its task lineage.

### References

The companion references the core and ICA normatively. The core
references the companion informatively, from its "Continuation with
ICA" row of Excluded Compositions, because the core does not depend on
it. No publication cluster forms.

## Human Oversight Companion

These notes apply to the oversight companion
(`draft-mcguinness-oauth-governed-agent-oversight.md`), whose anchors
the backquoted names below refer to.

### Deferred Token Response

The companion profiles `draft-ietf-oauth-deferred-token-response-01`
for governed token exchange. It narrows DTR in two places. A deferred
governed request always carries a DPoP proof (`opt-in`), where DTR
Section 11.1 lets a confidential client using `private_key_jwt` omit
one. Every governed check runs before deferral and again at resolution
(`deferring`, `resolution`), where DTR Section 11.7 re-checks consent
and client authorization only.

DTR says nothing about which identities the token returned after a
deferral carries; the companion requires the grant to keep the
request's Agent Principal, acting relationship, user, and client
(`resolution`).

The companion also profiles DTR for the redemption of an ID-JAG or a
WAG at the RAS (`deferred-redemption`), which DTR's introduction and
Section 9.3 anticipate for ID-JAG. There it narrows DTR further. A
deferred grant is accepted once, so the parallel request without
`completion_mode` that Section 9.3 suggests fails
(`redemption-deferring`). The RAS does not defer where configuration
selects mutual-TLS access tokens, since Section 11.1 requires the
issued token to be DPoP-bound to the request's key
(`redemption-opt-in`). A lost deferred response is recovered with the
same grant and key (`redemption-recovery`).

DTR-01 adds `interaction_uri`, and its Appendix A.6 describes a deferred
ID-JAG redemption in which the agent sends the user's browser to that
URI. The companion names it as one approval channel (`approval`), with
limits. The approver still authenticates to the channel at the strength
policy requires. Reaching the URI is not that authentication. Neither is
a session in a browser the agent operates (`security-self`). The
companion accepts every pending code of DTR Section 6.6 in polls.

Five questions for DTR, not yet filed:

* whether a grant profile's replay rules can forbid the parallel
  request of Section 9.3, as the companion does;
* whether the originating-grant preconditions that Section 11.7
  re-evaluates include the grant's own expiration when the client does
  not present the grant again. The companion checks the grant's `exp`
  on receipt (`redemption-deferring`) and records the question as an
  open item;
* whether an approval that the authorization server starts out of band,
  such as a CIBA request to the approver, is "external interaction", so
  that `authorization_pending` is no longer the code for it once the
  server observes the interaction began;
* which opt-in rule governs `deferred_interactive`. Section 5.1 implies
  that a `completion_mode` of `deferred_interactive` alone opts in;
  Section 5.3 forbids deferral unless `completion_mode` includes
  `deferred`; and Appendices A.6 to A.8 send only `deferred`. The
  companion follows Section 5.3, and a client able to present an
  `interaction_uri` sends both values (`approval`); and
* which error a deferred response carries. Section 6.4 says
  `authorization_pending`, then returns `interaction_required` with a
  deferral code for a response waiting on external interaction, in its
  own example. The companion accepts both in the deferred response
  (`deferring`, `redemption-deferring`).

### AROP

The companion profiles AROP's token issuance completion at the RAS and
not at the IdP. At the IdP, the core keeps asynchronous approval with
AROP among its excluded compositions. AROP bounds every
token issued under an approval by `approved_until`, including refresh
tokens and tokens obtained by exchange, and requires a refresh or
exchange after that time to fail. When the IdP defers governed
issuance, the RAS issues those tokens and has no portable way to learn
the deadline. The core forbids treating a shorter grant lifetime as
enforcing a downstream condition (the core's `issuance-authorization`),
so a composition at the IdP cannot meet AROP's bound.

AROP's Deferred Token Response binding already names deferral by the
RAS when an agent redeems an ID-JAG. The RAS issues the tokens AROP
bounds, so the companion composes AROP there (`deferred-redemption`).
The approval is the RAS's own: it bounds the authority the RAS issues
and carries nothing from an approval at the IdP. The companion adopts
AROP's re-evaluation at issuance and at every refresh, its bound on
every token the RAS issues, and its single redemption of the deferral
code. It narrows AROP in five places:

* the identities are resolved at receipt and bound to the pending
  redemption ("Approval keeps the resolved identities" above);
* each approval is bound to one pending redemption and kept unchanged,
  and AROP's idempotent submission, which compares the client and the
  requested authority but not the agent, is replaced by recovery with
  the same grant and key (`redemption-approval`,
  `redemption-recovery`);
* the grant is accepted once, and its replay record is kept until the
  grant's acceptance window has passed, not only until the request
  ends;
* a DPoP proof is required, so the deferral code has a sender
  constraint when the grant has no `cnf`; and
* the agent is the issuer-qualified `act` for an ID-JAG, or the
  subject for a WAG, never `context.client_id`.

The companion makes the resulting authorization ineligible for
continuation, since AROP's bound reaches tokens obtained by exchange
("The approval deadline and exchange" above).

AROP still cites `draft-gerber-oauth-deferred-token-response`; the
"Convergence across AuthZEN profiles" note above records the requests.

### ARAP

The companion names ARAP as one way to route an approval and defines
no composition with it. Using ARAP for a governed pending request at the
IdP needs the approval-binding contract described in "Convergence
across AuthZEN profiles" above. At the RAS, the companion binds each
approval to the one pending redemption it was requested for and keeps
ARAP's `approval` object unchanged (`redemption-approval`), so deferred
redemption does not depend on ARAP's comparison. ARAP's default completion re-evaluates access with
the approval; at a governed IdP, that decision would be one more check
at resolution, not a replacement for the re-checks `resolution`
requires.

### ICA

A deferred continuation holds ICA's replay reservation while a person
decides (`deferred-continuation`). Where the IdP offers idempotent
retry, ICA Section 5.5.7.1 makes an unissued reservation FAILED at the
assertion's `exp` plus skew; the companion keeps it RESERVED until the
pending request ends and excludes recovery of a grant issued at
resolution. A later ICA revision could define this deferred state
itself. The companion also counts ICA's Section 6.3 limits when the
onward grant issues, which follows from ICA counting issued
continuations.

### MCP

The companion's MCP section is informative and relies only on merged
MCP features: tasks, URL-mode elicitation, and scope step-up in
revision 2026-07-28. SEP-2848 (asynchronous approval for tool calls)
and SEP-2643 (structured authorization denials) are cited as
proposals. If SEP-2848 is accepted, its task held in `working` is the
per-action realization the companion describes.

### References

The companion references the core, DTR, the continuation companion and
ICA normatively. Deferred continuation (`deferred-continuation`) is
optional, but an IdP that claims it applies the continuation exchange
and ICA's replay reservation, and Note 1 of the IESG statement on
normative and informative references classifies such dependencies as
normative even for an optional feature. The core and the continuation
companion reference this companion informatively, so no publication
cluster forms.

### Open Items

The companion's open items (`open-items`) are AROP at the IdP and
continuation from a deferred redemption, an attribute for the
oversight mode in the SCIM management profile, a Shared Signals event
for supervised-issuance notices, duplicate pending requests at the
IdP, DTR's originating-grant preconditions, and whether policy may
lower a continuation's oversight mode on account of the continuing
client (the continuation mode floor, which awaits a negative test).
Mode policy already takes the chain's root client as a continuation's
client, so a continuation meets the mode of the same request made
directly.

## Family Structure

### Publication Cluster with the Input Profiles Companion

The core references the input profiles companion (`INPUTS`) normatively.
Its client-authentication rule (`algorithms`) requires an implementation
that uses JWT-SVID client authentication to claim the companion's
JWT-SVID input and follow its rules. Those rules supply validation and
algorithm requirements that the core does not contain, and Note 1 of the
IESG statement on normative and informative references classifies such
a dependency as normative even for an optional feature. The companion
references the core normatively, so the two drafts form a publication
cluster: neither can be published as an RFC without the other.

The cluster can be broken with a small behavior change:

* The core keeps only "JWT-SVID client authentication is not a
  dedicated-client method." Agent resolution from a JWT-SVID remains the
  companion's input, through the core's input-profile extension point.
* JWT-SVID client authentication at the RAS follows `SPIFFE-OAUTH`
  without this profile's narrowings: configured-bundle precedence and
  the limits on bundles from client metadata, the rule that an optional
  `iss` does not select another trust domain, and `RS256` and `ES256` as
  mandatory to implement.
* `INPUTS` becomes an informative reference.

Breaking the cluster alone does not let the core advance ahead of early
dependencies. The core also references Client Instance Identifiers
(`INSTANCE`) normatively, for the client instance rule in
`identity-binding` and the instance context of `access-token-response`
and `api-validation`.

Decide this at working-group adoption, if the core should be adopted or
published separately from the SPIFFE and Client Attestation inputs.
Do not revisit the family structure before the human comprehension
check of the core's opening.
