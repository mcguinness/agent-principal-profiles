# Conformance suite

This directory holds executable positive and negative tests for one
interoperable path through the core profile, and a reference
implementation to run them against. The path is the mandatory
interoperability path for delegated access in the core's [Conformance
Claims][core-scope], under the bound profile, as
[EXAMPLES.md](../EXAMPLES.md)'s [first delegated
transaction](../EXAMPLES.md#first-delegated-transaction) traces it:

* a dedicated client authenticating with `private_key_jwt`;
* an ID Token as the subject token;
* bound governed agent access, with DPoP at the IdP and the RAS;
* a DPoP-bound JWT access token, validated at the API.

Beyond that path, it tests self-acting issuance and redemption (P14,
P15, N44 to N49, N51, N52, N54), the existing platform JWT input for a
shared client (P11 to P13, N36 to N39), and just-in-time correlation
(N34, N47 to N49, N54). It also holds tests of the oversight companion's
deferred redemption at the reference RAS ([Deferred redemption at the
RAS](#deferred-redemption-at-the-ras)), and of the core's Optional
Policy Services, error selection order, self-acting access and
introspection at the reference API ([Policy services at the
API](#policy-services-at-the-api)).

The drafts define every requirement. The suite tests a subset of them,
and passing it is evidence for that subset only, not a conformance claim.
[CLAIM-TEMPLATE.md](CLAIM-TEMPLATE.md) is a form for stating a claim:
what the core requires a claim to name, optional capabilities,
companion claims, the configuration a peer must agree on, and the
suite results offered as evidence.

* [Run](#run)
* [Cases](#cases)
* [Deferred redemption at the RAS](#deferred-redemption-at-the-ras)
* [Policy services at the API](#policy-services-at-the-api)
* [What the suite does not cover](#what-the-suite-does-not-cover)
* [Running against another implementation](#running-against-another-implementation)
* [Configuration the reference assumes](#configuration-the-reference-assumes)
* [Draft questions found while implementing](#draft-questions-found-while-implementing)

## Run

The suite needs Python 3 and one package, `cryptography`:

```sh
python3 -m venv .venv-conformance
.venv-conformance/bin/pip install -r conformance/requirements.txt
.venv-conformance/bin/python conformance/run.py --vacuity
```

`run.py` starts the reference IdP, RAS and API on localhost ports, plays
the client, and prints one line per case. `--vacuity` then runs every
case that cites reference checks once for each check, with that check
switched off, prints why the case failed, and fails if it still passes. `--list` prints each case's source and
the test-control capabilities it needs. `--ras-only` runs the suite in
RAS-only mode ([below](#ras-only-mode)). The exit status is non-zero
on any failure.

The reference servers use the example identifiers: `https://idp.example/`,
`https://ras.example/` and `https://api.example` are the issuer and
origin values in tokens, client assertions and DPoP proofs, while the
servers listen on localhost. A reader can lay the output beside
the [first delegated
transaction](../EXAMPLES.md#first-delegated-transaction) in
[EXAMPLES.md](../EXAMPLES.md). The reference runs
`https://idp.example/` as a multi-tenant issuer, so its grants also
carry `tenant` with the value `acme`, which the examples'
single-tenant issuer omits.

## Cases

| Case | Role | Checks that | Source | Test control |
|---|---|---|---|---|
| P1 | IdP | The ID-JAG names the user in the RAS namespace, the agent in `act`, the RAS registration as `client_id`, the grant key in `cnf.jkt`, and, at a multi-tenant issuer, the user's tenant in `tenant`, lives no longer than the configured limit (`max_grant_lifetime`, 300 s by default) or the ID Token, and is noted if it exceeds the recommended 300 s | core: Actor Resolution and Construction; Grant Issuance; Common Grant Claims | None |
| P2 | RAS | The access token is DPoP-bound to the same key, names the local user, and carries `act` unchanged; a refresh token is noted, not failed | core: Actor Preservation; Access Token Issuance and Response | None |
| P3 | API | A read with the access token and a fresh proof succeeds | core: Token Validation; Delegated Access | None |
| P4 | API | An access token typed `application/at+jwt`, with a one-element `aud` array, is accepted | RFC 9068 Sections 2.1 and 4; core: Token Validation | Mint an access token |
| P5 | RAS | With unbound grants and a resource that permits DPoP or bearer, a redemption with no proof gets `token_type` Bearer and an access token without `cnf` | core: Access-Token Protection | Let the IdP issue, and the RAS accept, unbound grants; permit bearer for the resource |
| P6 | API | That bearer token, presented with the `Bearer` scheme, reads the file | core: Access-Token Protection; Token Validation; RFC 6750 | As P5; permit bearer tokens at the API |
| P7 | RAS | With the same configuration, a redemption with a valid proof gets `token_type` DPoP and an access token bound to the proof key | core: Access-Token Protection (DPoP or bearer) | As P5 |
| P8 | IdP | With the IdP requiring DPoP nonces, an exchange whose proof carries a nonce the IdP never provided gets `use_dpop_nonce` and a `DPoP-Nonce`, and the retry that carries that nonce gets the grant | RFC 9449 Sections 4.3 and 8; core: Grant Protection | Require nonces at the IdP |
| P9 | RAS | With the RAS requiring DPoP nonces, a redemption whose proof carries a nonce the RAS never provided gets `use_dpop_nonce`, and the retry with the RAS's nonce gets the access token | RFC 9449 Sections 4.3 and 8; core: Access-Token Protection | Require nonces at the RAS |
| P10 | API | With the API requiring DPoP nonces, a read whose proof carries a nonce the API never provided gets HTTP 401 with `use_dpop_nonce`, and the retry with the API's nonce is served | RFC 9449 Sections 4.3 and 9; core: Token Validation | Require nonces at the API |
| P16 | IdP | For an ID Token that expires in 90 s, the grant expires no later than the ID Token | core: Grant Issuance (the subject credential's expiration) | ID Token with chosen claims |
| P11 | IdP | The shared client `platform-client` presents a platform JWT for `workload-43` as `actor_token`; the grant names `agent-43` in `act` and the shared client's RAS registration, `platform-api`, as `client_id` | core: Conformance Claims (generic shared-client interoperability); Existing Platform JWT | A shared client configured |
| P12 | IdP | With a platform JWT that expires in 90 s, the grant expires no later than that evidence deadline | core: Existing Platform JWT (Validation); Common Grant Claims | A shared client configured |
| P13 | IdP | With `platform-client` mapped to the dedicated client's registration `analysis-api`, grants for `agent-42` and `agent-43` both name `analysis-api` and redeem with its credential; after `agent-42` is disabled at the RAS, its grant fails with `invalid_grant` and `agent-43`'s is still redeemed | core: Issuance Prerequisites (Downstream client); Agent Principal Correlation | A shared client configured; set the client registration association; disable the agent at the RAS |
| P14 | IdP | `analysis-client`'s self-acting exchange, its assertion repeated as the subject token, returns a WAG with `typ` `oauth-wag+jwt` naming `agent-42` as `sub`, with no `act`, the self-acting registration `analysis-agent-client` as `client_id`, `tenant` `acme`, and the grant key in `cnf.jkt` | core: Self-Acting Issuance: WAG; Grant Claims; Issuance Prerequisites | The self-acting registration's key |
| P15 | RAS | Redeemed under `analysis-agent-client`, the WAG yields an access token naming `service-principal-42` as `sub`, with no `act` and no refresh token, and the API serves the read | core: Self-Acting Redemption: WAG; Self-Acting Access | The self-acting registration's key |
| N01 | IdP | A reused client assertion fails with `invalid_client` | core: Dedicated Client Identity (Replay); negative-test row for the nonce retry | None |
| N02 | IdP | A client assertion addressed to the token endpoint URL fails with `invalid_client` | core: Dedicated Client Identity (Audience) | None |
| N03 | IdP | An exchange without a DPoP proof under the bound profile fails with `invalid_request` | core: Grant Protection | None |
| N04 | IdP | Two `resource` parameters fail with `invalid_target` | core: Token Exchange Request | None |
| N05 | IdP | An ID Token issued to another client fails with `invalid_request` | core: Subject Token Validation | ID Token for another audience |
| N06 | IdP | A disabled Identity Binding fails with `invalid_grant` | core: negative-test row | Disable the binding |
| N07 | IdP | A disabled Agent Principal fails with `invalid_grant` | core: Issuance Errors; PLAYBOOK runbook | Disable the agent |
| N08 | IdP | No Client Association fails with `actor_unauthorized` | core: negative-test row | Remove the association |
| N09 | IdP | A withdrawn Delegation Authorization fails with `actor_unauthorized` | core: Delegation Authorization; Issuance Errors; PLAYBOOK recipe | Withdraw the delegation |
| N10 | RAS | A grant without `cnf` under the bound profile fails with `invalid_grant` | core: negative-test row | Let the IdP issue unbound grants |
| N11 | RAS | A bound grant redeemed without a proof fails with `invalid_grant` or `invalid_dpop_proof`, at the DPoP-only resource and again where the resource permits bearer tokens | core: negative-test row; Access-Token Protection | Permit bearer for the resource |
| N12 | RAS | A redemption proven with another key fails with `invalid_grant` | core: Grant Protection | None |
| N13 | RAS | A grant redeemed by a client other than its `client_id` fails with `invalid_grant` | core: Redemption Request; ID-JAG Section 4.4.1 | None; needs a second RAS client |
| N14 | RAS | A `resource` parameter other than the grant's fails with `invalid_target` | core: Common Grant Validation | None |
| N15 | RAS | A grant for an agent disabled at the RAS fails with `invalid_grant` | core: Agent Principal Correlation; Applied Disablement and Revocation; Redemption Errors | Disable the agent at the RAS |
| N16 | RAS | An agent the RAS's policy does not let act for the user fails with `actor_unauthorized` | core: Delegated Actor Authorization; Redemption Errors | Close the actor gate at the RAS |
| N17 | API | An access token used in another tenant, with a fresh proof, fails with 401 `invalid_token` | core: negative-test row | None; needs a second tenant |
| N18 | API | A delegated-population token without `act` fails with 401 `invalid_token` | core: negative-test row; Profile Applicability | Mint an access token |
| N19 | API | A request proven with another key fails with 401 `invalid_token` | core: Token Validation; RFC 9449 Section 7.1 | None |
| N20 | API | A closed actor gate fails with 403 `actor_unauthorized`, not `insufficient_scope` | core: Error Responses | Close the actor gate at the API |
| N21 | IdP | An ID Token whose `iat` is an hour ahead fails with `invalid_request` | core: Time, Replay, and Key Validation | ID Token with chosen claims |
| N22 | IdP | A client assertion whose `nbf` is an hour ahead fails with `invalid_client` | RFC 7523 Section 3; core: Time, Replay, and Key Validation | None |
| N23 | RAS | A grant whose `nbf` is an hour ahead fails with `invalid_grant` | RFC 7523 Section 3; core: Time, Replay, and Key Validation | Mint a grant |
| N24 | API | An access token whose `iat` is an hour ahead fails with 401 `invalid_token` | core: Time, Replay, and Key Validation; RFC 9068 Section 4 | Mint an access token |
| N25 | IdP | A request for `files.write`, when the delegation permits only `files.read`, fails with `invalid_scope` | core: Issuance Authorization; Issuance Errors | Set the delegation's scope |
| N26 | RAS | A grant whose `scope` claim is missing, empty or an array fails with `invalid_grant` | core: Common Grant Validation | Mint a grant |
| N27 | RAS | A grant whose `act` names `agent-99`, which the RAS has no correlation for, fails with `invalid_grant` | core: Agent Principal Correlation; Redemption Errors | Mint a grant |
| N28 | IdP | A request for `files.write`, which the delegation permits but policy categorically prohibits for the agent, fails with `actor_unauthorized` | core: Issuance Authorization; Issuance Errors | Set the delegation's scope; prohibit a scope for the agent |
| N29 | RAS | A bound grant presented with `jwt-bearer` and a valid proof fails with `invalid_grant` | core: Redemption Request; JWT DPoP Grant Section 5.2 | None |
| N30 | RAS | An unbound grant presented with `jwt-dpop` fails with `invalid_grant` | core: Redemption Request; JWT DPoP Grant Section 5 | Let the IdP issue, and the RAS accept, unbound grants |
| N31 | IdP | An ID Token whose `sub` is `null` or the number 123 fails with `invalid_request`, as an invalid subject credential | core: Issuance Errors; RFC 8693 Section 2.2.2 | ID Token with chosen claims |
| N32 | IdP | A valid ID Token whose `sub` is `carol`, a user the IdP has no record of, fails with `invalid_grant`, as a user resolution failure | core: Subject Resolution; Issuance Errors | ID Token with chosen claims |
| N33 | IdP | With policy no longer authorizing the agent's Governance Tenant `acme` for the Target Tenant `acme-data`, the exchange fails with `actor_unauthorized` | core: Issuance Authorization; Issuance Errors | Set a tenant pair |
| N34 | RAS | With just-in-time correlation on, a grant whose `act` names `agent-99`, which the RAS has not seen, fails with `actor_unauthorized` or `invalid_grant`: the created record does not authorize the agent | core: Optional Just-in-Time Correlation; Redemption Errors | Mint a grant; turn on just-in-time correlation |
| N35 | API | Where the API accepts bearer tokens for the resource, a DPoP-bound access token presented with the `Bearer` scheme fails with HTTP 401 | RFC 9449 Section 7.2; core: Access-Token Protection (Enforcement) | Permit bearer tokens at the API |
| N36 | IdP | The shared client's exchange without a platform JWT fails with `invalid_request`, not a fallback to the client's own authentication | core: Agent Resolution Input Validation; Issuance Errors | A shared client configured |
| N37 | IdP | A platform JWT whose `aud` is `https://another-idp.example/` fails with `invalid_request` | core: Existing Platform JWT (Audience); Issuance Errors | A shared client configured |
| N38 | IdP | A valid platform JWT for `workload-43-shadow`, which only begins with the bound `workload-43`, fails with `invalid_grant` | core: Existing Platform JWT (Resolution); Issuance Errors | A shared client configured |
| N39 | IdP | A platform JWT whose `cnf.jkt` names another key than the one the request proves fails with `invalid_request`: the reference supports no platform JWT binding, and an unsupported binding never gets bearer treatment | core: Existing Platform JWT (Proof); Issuance Errors | A shared client configured |
| N40 | RAS | With `agent-42` disabled at the RAS, its first grant through the second RAS client fails with `invalid_grant`, and after it is re-enabled the next such grant succeeds: the restriction follows the agent, not the clients the RAS already knows it through | core: Introduction; Agent Principal Correlation; Applied Disablement and Revocation | Disable and re-enable the agent at the RAS; mint a grant; needs a second RAS client, and a reset that clears which clients the agent arrived through |
| N41 | IdP | At a multi-tenant issuer, with `agent-42` moved to `beta` and (`beta`, `acme-data`) authorized, Alice's exchange fails with `actor_unauthorized`, since the agent is not in the user's tenant | core: Canonical Identity and Tenant Boundaries; Issuance Errors | Set the agent's Governance Tenant and a tenant pair; a multi-tenant issuer |
| N42 | RAS | A grant from the multi-tenant issuer naming `beta`, which the RAS does not trust for `acme-data`, fails with `invalid_grant` even for a `beta` subject linked to the user, and so does a grant naming no tenant | ID-JAG Section 4.4.1; core: Canonical Identity and Tenant Boundaries | Mint a grant; link a user; a multi-tenant issuer |
| N43 | RAS | With the RAS also trusting `beta` for `acme-data` and linking `beta`'s `bob-ras` to `user-108`, a `beta` grant for `bob-ras` redeems, and a `beta` grant for `alice-ras`, `acme`'s subject, fails with `invalid_grant`: a subject is resolved within its issuer tenant | ID-JAG Section 6.3; core: User Resolution and Linking | Set the RAS's tenant trust; link a user; a multi-tenant issuer |
| N44 | IdP | Without the Client Association for self-acting issuance, the self-acting exchange fails with `unauthorized_client` | core: Self-Acting Issuance: WAG; Issuance Errors | Remove the self-acting Client Association |
| N45 | IdP | With policy no longer authorizing (`acme`, `acme-data`), the self-acting exchange fails with `invalid_target` | core: Issuance Authorization; Issuance Errors | Set a tenant pair |
| N46 | RAS | A WAG from the multi-tenant issuer naming `beta`, which the RAS does not trust for `acme-data`, or naming no tenant, fails with `invalid_grant` | core: Canonical Identity and Tenant Boundaries; Self-Acting Redemption: WAG | Mint a WAG; a multi-tenant issuer |
| N47 | RAS | With just-in-time correlation on and created records eligible, a WAG naming `agent-99`, which the RAS has not seen, fails with `invalid_target`: the created record authorizes nothing. With a self-acting rule granting the issuer's agents `files.read` in `acme-data`, the next such WAG redeems for a token whose `sub` is the created record's local principal, as test control reads it back | core: Optional Just-in-Time Correlation; Self-Acting Redemption: WAG; Redemption Errors | Turn on just-in-time correlation; make created records eligible; set a self-acting rule; mint a WAG; read the agent record |
| N48 | RAS | With just-in-time correlation on and created records ineligible, a WAG naming `agent-99` fails with `invalid_grant` and leaves a record for the pair. With a self-acting rule set, the next such WAG still fails with `invalid_grant`: permission does not make the record eligible | core: Optional Just-in-Time Correlation; Redemption Errors | Turn on just-in-time correlation; make created records ineligible; set a self-acting rule; mint a WAG; read the agent record |
| N49 | RAS | With the RAS also trusting `https://partner-idp.example/` and correlating both issuers' agents just in time, a WAG for `agent-99` from the IdP's issuer redeems under a self-acting rule for that issuer, and one from the partner issuer fails with `invalid_target`. With a rule for the partner issuer too, its WAG redeems. Each token's `sub` is its own record's local principal, and the two differ | core: Optional Just-in-Time Correlation; Agent Principal Correlation; Self-Acting Redemption: WAG | Trust a second issuer; turn on just-in-time correlation for both issuers; make created records eligible; set self-acting rules; mint WAGs for both issuers; read the agent records |
| N50 | RAS | With unbound grants, an ID-JAG without `cnf` redeemed once with a proof of K and presented again with a proof of K2 fails with `invalid_grant` | core: Common Grant Validation (Grant replay); Renewal and Negative Tests | Let the IdP issue, and the RAS accept, unbound grants |
| N51 | RAS | With unbound grants, a WAG without `cnf` redeemed once and presented again fails with `invalid_grant` | core: Common Grant Validation (Grant replay); Renewal and Negative Tests | As N50, for the self-acting registration |
| N52 | RAS | With just-in-time correlation on, created records eligible and a self-acting rule set, an ID-JAG-typed grant without `act`, naming the self-acting registration, and a WAG-typed grant carrying `act` both fail with `invalid_grant`: the RAS tells the grants apart by `typ`, so neither becomes the other | core: Grant Validation (Actor); Self-Acting Redemption: WAG, step 1; Credential and Token Confusion | Turn on just-in-time correlation; make created records eligible; set a self-acting rule; mint an ID-JAG and a WAG |
| N53 | API | With the user delegating only `files.write` and the API's actor gate closed, a read with the resulting access token, which lacks `files.read`, fails with 403 `actor_unauthorized`, not `insufficient_scope`: the actor gate is reported first | core: Error Responses (selection order); Delegated Actor Authorization | Set the delegation's scopes at the IdP; close the API's actor gate |
| N54 | RAS | With just-in-time correlation on, created records eligible and a self-acting rule set, a WAG for `agent-99` redeems and creates its record. After the RAS removes that correlation, the next such WAG fails with `invalid_grant`, and the RAS holds no record for the pair: the removal is retained revocation state, which just-in-time correlation does not undo | core: Optional Just-in-Time Correlation; Applied Disablement and Revocation; Redemption Errors | Turn on just-in-time correlation; make created records eligible; set a self-acting rule; remove a correlation; mint WAGs; read the agent record |
| D01 | RAS | Without `completion_mode=deferred`, a redemption that needs approval fails with `access_denied` and carries no deferral code | oversight: Redemption Opt-In; core: Redemption Errors | Require approval |
| D02 | RAS | A deferred redemption stays pending until approved, then issues an access token like P2's, expiring within `approved_until`, that the API accepts; a second poll fails with `invalid_grant` | oversight: Deferring a Redemption; Redemption Resolution | Require approval; approve |
| D03 | RAS | A poll proven with another key fails with `invalid_dpop_proof` | oversight: Deferring a Redemption | Require approval |
| D04 | RAS | With a 24 h maximum pending lifetime and an 8 h absolute expiration, `expires_in` is at most 8 h, and an approval after 9 h finds `expired_token` | oversight: Deferring a Redemption | Require approval; set both lifetimes; approve; advance the clock |
| D05 | RAS | An agent disabled while pending gets `access_denied` at the poll after approval | oversight: Redemption Resolution | Require approval; disable the agent at the RAS; approve |
| D06 | RAS | After a denial, the poll gets `access_denied` and the grant presented again gets `invalid_grant` | oversight: Recovery; Redemption Resolution | Require approval; deny |
| D07 | RAS | While pending, the grant presented without the opt-in fails with `invalid_grant` | oversight: Recovery; Deferring a Redemption | Require approval |
| D08 | RAS | For an unbound grant, a repeated request gets the same deferral code and an `expires_in` no greater than the first; the same request with another key fails with `invalid_grant` | oversight: Recovery | Require approval; let both the IdP and the RAS accept unbound grants |
| D09 | RAS | After approval, a repeated request gets the same deferral code and no token, and the poll then issues | oversight: Recovery | Require approval; approve |
| D10 | RAS | A second agent's grant through the same client, for the same user, resource and scope, gets its own deferral code and access request; approving the first leaves it pending | oversight: Approval Binding | Require approval; mint a grant; approve |
| D11 | RAS | When the Access Request Service answers the second request with the first one's approval, the second stays pending | oversight: Approval Binding | Require approval; mint a grant; approve; substitute |
| D12 | RAS | An approval narrowed from `files.read files.write` to `files.read` yields `scope` `files.read` in the response and the token, in any order | oversight: Redemption Resolution | Require approval; mint a grant; approve |
| D13 | RAS | With an approval expiry 300 s ahead, the access token expires within it, and a refresh after it fails with `invalid_grant` | oversight: Redemption Resolution; Refresh and Continuation | Require approval; permit refresh; approve; advance the clock |
| D14 | RAS | A refresh after the approval is revoked fails with `invalid_grant` | oversight: Refresh and Continuation | Require approval; permit refresh; approve; revoke; advance the clock |
| D15 | RAS | A shorter approval expiry returned at one refresh bounds that token and the next | oversight: Approval Binding; Refresh and Continuation | Require approval; permit refresh; approve; shorten |
| D16 | RAS | Two identical requests sent together, from two threads, get one deferral code, and one access request is opened. The reference serves one request at a time, so against it D16 shows the shared pending redemption but cannot show the absence of a race | oversight: Recovery | Require approval; list tasks |
| D17 | RAS | After the grant's `exp`, a repeated request gets the same deferral code with the remaining `expires_in`, and the approval then issues | oversight: Recovery | Require approval; approve; advance the clock |
| D18 | RAS | A repeated request that reuses the first request's DPoP proof fails with `invalid_dpop_proof` | oversight: Recovery; RFC 9449 Section 11.1 | Require approval |
| D19 | RAS | After a token response redeems the code, a repeated request fails with `invalid_grant` | oversight: Recovery | Require approval; approve |
| D20 | RAS | An agent whose correlation changes to another local principal while pending gets `access_denied` at the poll after approval | oversight: Redemption Resolution; core: Agent Principal Correlation | Require approval; change the agent's local principal at the RAS; approve |
| D21 | RAS | After an unbound grant's deferred redemption, raising the client's minimum to the bound profile makes the next refresh fail with `invalid_grant` | oversight: Refresh and Continuation; core: Optional RAS Refresh Tokens (step 3) | Require approval; permit refresh; set the governed profile; approve |
| D22 | RAS | A refresh with another key is rejected and the next refresh still succeeds; a refresh rejected on re-evaluation ends the authorization, so restoring the actor gate does not revive it | oversight: Refresh and Continuation (ending the refresh authorization) | Require approval; permit refresh; approve; close and reopen the actor gate |
| D23 | RAS | A repeated request that presents the bound grant with `jwt-bearer` fails with `invalid_grant` and carries no deferral code | oversight: Recovery; core: Redemption Request | Require approval |
| D24 | RAS | With `completion_mode=deferred deferred_interactive`, a redemption is deferred, a repeated request gets the same deferral code and any `interaction_uri` again, and the poll after approval issues | oversight: Redemption Opt-In; Recovery; Approval | Require approval; approve |
| D25 | RAS | A redemption deferred while the RAS trusts `acme` for `acme-data` gets `access_denied` at the poll after approval once that trust is withdrawn | oversight: Redemption Resolution; core: Canonical Identity and Tenant Boundaries | Require approval; withdraw the RAS's tenant trust; approve; a multi-tenant issuer |
| D26 | RAS | After a refresh succeeds, withdrawing the RAS's trust in `acme` for `acme-data` makes the next refresh fail with `invalid_grant` | core: Optional RAS Refresh Tokens; oversight: Refresh and Continuation | Require approval; permit refresh tokens; withdraw the RAS's tenant trust; approve; a multi-tenant issuer |
| S01 | API | Through the policy service, the positive path's read succeeds, and the evaluation names the user `user-108` as subject, the agent from `act`, the client `analysis-api`, the tenant `acme-data`, and `files.read` in the token constraints | core: Optional Policy Services; Delegated Access | Turn on the policy service; set its policy; read its evaluations |
| S02 | API | A request attribute naming `agent-77`, which policy permits instead of `agent-42`, fails with 403 `actor_unauthorized`, not `insufficient_scope` | core: Optional Policy Services; negative-test row for a policy service; Error Responses | Turn on the policy service; set its policy |
| S03 | API | When policy permits only `agent-42`, another agent's access token with the same `client_id` fails with 403 `actor_unauthorized`, and `agent-42`'s succeeds | core: Delegated Actor Authorization; negative-test row for the platform JWT variant's policy | Turn on the policy service; set its policy; mint an access token |
| S04 | API | A request attribute naming another user, whom policy permits instead, fails with HTTP 403, a challenge without an `error` attribute, neither `actor_unauthorized` nor `insufficient_scope`, and none of the file's data | core: Optional Policy Services; Error Responses | Turn on the policy service; set its policy |
| S05 | API | A request attribute naming another OAuth client, `other-api`, which policy permits instead, fails as S04 does | core: Optional Policy Services; Error Responses | Turn on the policy service; set its policy |
| S06 | API | With an `acme-data` token on the `acme-data` path, a request attribute naming tenant `beta-data`, which policy permits instead, fails as S04 does | core: Optional Policy Services; Token Validation (Tenant); Error Responses | Turn on the policy service; set its policy |
| S07 | API | With a `files.read` token, a request attribute naming `files.admin`, which policy requires, fails with HTTP 403 `insufficient_scope` and none of the file's data | core: Optional Policy Services; Error Responses | Turn on the policy service; set its policy |
| S08 | API | A self-acting token is served with the API's actor gate closed, and through the policy service, whose evaluation has the local agent principal as subject and names no user | core: Self-Acting Access; Optional Policy Services; Profile Applicability | Mint an access token; close the actor gate at the API; turn on the policy service; set its policy; read its evaluations |
| S09 | API | For a self-acting token, a request attribute naming `service-principal-77`, which policy permits instead, fails as S04 does | core: Optional Policy Services; Self-Acting Access; Error Responses | Mint an access token; turn on the policy service; set its policy |
| S10 | API | An opaque DPoP-bound token is introspected and served, and the evaluation takes the user, the unchanged `act` and the client from the introspection response | core: Optional Opaque Access Tokens and Introspection; Optional Policy Services | Mint an opaque token; turn on the policy service; set its policy; read its evaluations |
| S11 | API | For an opaque token, a request attribute naming `agent-77`, which policy permits instead, fails with 403 `actor_unauthorized` | core: Optional Policy Services; Optional Opaque Access Tokens and Introspection | Mint an opaque token; turn on the policy service; set its policy |
| S12 | API | An introspection response with `active` false fails with 401 `invalid_token` | core: Optional Opaque Access Tokens and Introspection; RFC 7662 Section 2.2 | Mint an opaque token |
| S13 | API | A delegated-population introspection response without `act` fails with 401 `invalid_token` | core: Optional Opaque Access Tokens and Introspection; Profile Applicability | Mint an opaque token; have the RAS leave `act` out of introspection |
| S14 | API | When policy requires `files.admin`, which the token lacks, and categorically prohibits the agent, the request fails with 403 `actor_unauthorized`, not `insufficient_scope` | core: Error Responses; Optional Policy Services | Turn on the policy service; set its policy |
| S15 | API | When the actor gate and the user's permission both deny, the request fails with 403 `actor_unauthorized` | core: Error Responses; Optional Policy Services | Turn on the policy service; set its policy |
| S16 | API | A request proven with another key, which policy would also deny, fails with 401 `invalid_token`, not 403 | core: Error Responses; Token Validation; RFC 9449 Section 7.1 | Turn on the policy service; set its policy |
| S17 | API | When the policy service cannot be reached, the request gets HTTP 503, none of the file's data and no denial code; a missing `Retry-After` is noted | core: Error Responses; Optional Policy Services | Turn on the policy service; set its policy; make it unavailable |
| S18 | API | When the actor gate denies and the evaluation of the user's permissions cannot complete, the request gets HTTP 403 `actor_unauthorized`, since no unfinished check comes earlier | core: Error Responses; Optional Policy Services | Turn on the policy service; set its policy; make the `other` condition unavailable |
| S19 | API | When the actor gate cannot be evaluated and the user's permission denies, the request gets HTTP 503, since the unfinished actor gate could come earlier | core: Error Responses; Optional Policy Services | Turn on the policy service; set its policy; make the `actor` condition unavailable |
| S20 | API | With an opaque token the API has not introspected before, when the introspection endpoint answers HTTP 503, answers 200 with a body that is not a JSON object, or closes the connection before the body it declares, the request gets HTTP 503, none of the file's data and no `invalid_token`; a missing `Retry-After` is noted | core: Optional Opaque Access Tokens and Introspection; Error Responses; RFC 7662 Section 2.3 | Mint an opaque token; make introspection fail |
| S21 | API | When introspection cannot complete and the DPoP proof's `ath` names another token, the request gets HTTP 401 for the proof, not 503, since the unfinished validation is in the same row | core: Error Responses; Token Validation; RFC 9449 Section 4.3 | Mint an opaque token; make introspection fail |
| S22 | API | With `version=abc`, an argument outside the read's declared contract, the request gets the argument's rejection (HTTP 400 `invalid_request`, unless the adapter recognizes another form), none of the file's data and neither denial code, whether the API checks arguments first or last; `version=3` is served | core: Error Responses (row 3) | Set the evaluation order |
| S23 | API | With `version=abc` and a proof made with another key, the request gets HTTP 401 for the proof in both orders | core: Error Responses (rows 1 and 3); Token Validation (Protection) | Set the evaluation order |
| S24 | API | With `version=abc` and a token used in another tenant, the request gets HTTP 401 `invalid_token` in both orders | core: Error Responses (rows 2 and 3); Token Validation (Tenant) | Set the evaluation order |
| S25 | API | With `version=abc`, while the API's own actor gate denies, the request gets the argument's rejection, not `actor_unauthorized`, in both orders | core: Error Responses (rows 3 and 4); Delegated Actor Authorization | Set the evaluation order; close the actor gate at the API |
| S26 | API | With `version=abc`, while a policy evaluation that parses `version` before deciding cannot decide a prohibition that does not depend on it, the request gets the argument's rejection in both orders; with `version=3` the prohibition gives `actor_unauthorized` | core: Error Responses (rows 3 and 4); Optional Policy Services | Set the evaluation order; turn on the policy service; set its policy |
| S27 | API | With `version=abc`, while the actor gate's policy needs `version` to be at least 2, the request gets the argument's rejection in both orders; `version=3` is served and `version=1` gets `actor_unauthorized` | core: Error Responses (rows 3 and 4); Optional Policy Services | Set the evaluation order; turn on the policy service; set its policy |
| S28 | API | With `version=abc` and a token that lacks `files.read`, the request gets the argument's rejection, not `insufficient_scope`, in both orders | core: Error Responses (rows 3 and 5) | Set the evaluation order; mint an access token |
| S29 | API | With `version=abc`, while the user lacks permission, the request gets the argument's rejection, not a 403, in both orders; without the argument, the user's denial is a 403 without a code | core: Error Responses (rows 3 and 6); Optional Policy Services | Set the evaluation order; turn on the policy service; set its policy |
| S30 | API | With `version=abc`, while the policy service cannot be reached, the request gets the argument's rejection, not HTTP 503, in both orders; without the argument, the request gets HTTP 503 | core: Error Responses (row 3; evaluation that cannot complete); Optional Policy Services | Set the evaluation order; turn on the policy service; set its policy; make it unavailable |
| S31 | API | With `version=abc` and an opaque token the API has not introspected before, while introspection cannot complete, the request gets HTTP 503 in both orders | core: Error Responses (rows 1 and 3); Optional Opaque Access Tokens and Introspection | Set the evaluation order; mint an opaque token; make introspection fail |
| S32 | API | An unknown path under the API, with no token, an expired token, or a proof made with another key, gets the same status and error as the read path; with a valid token it is rejected as `Adapter.route_rejection` recognizes (the reference: 404). A difference is noted | core: Error Disclosure (SHOULD); Error Responses | Mint an access token |
| S33 | API | `POST` to the read path with a proof made for `POST` is rejected as `Adapter.route_rejection` recognizes (the reference: 405 with `Allow: GET`) and not as `invalid_dpop_proof`, and `POST` with a proof made for `GET` gets the same answer on the read path and an unknown path. A rejected proof or a difference is noted | core: Error Disclosure (SHOULD); Token Validation (Protection); RFC 9449 Section 4.3 | None |
| S34 | API | While introspection cannot complete, an unknown path gets the same answer as the read path (HTTP 503, S20), each with an opaque token the API has not introspected; a difference is noted | core: Error Disclosure (SHOULD; precedence not specified) | Mint an opaque token; make introspection fail |
| S35 | API | A read of a file that does not exist, while the API's actor gate denies, gets 403 `actor_unauthorized`, not 404 | core: Error Responses; Error Disclosure | Close the actor gate at the API |
| S36 | API | A token whose `act` names `agent-42` under the home issuer is served; the same `sub` under a trusted partner issuer gets 403 `actor_unauthorized` at the API's own actor gate, and under an untrusted issuer 401 `invalid_token` | core: Delegated Access (Identity); Delegated Actor Authorization; Error Responses | Mint access tokens |
| S37 | API | Through the policy service, whose gate permits only the home issuer's `agent-42`, the partner issuer's `agent-42` gets 403 `actor_unauthorized`, and the evaluation names it with the partner's issuer | core: Optional Policy Services; Delegated Actor Authorization | Mint access tokens; turn on the policy service; set its policy; read its evaluations |
| S38 | API | With bearer tokens permitted, a bearer request whose opaque token cannot be introspected gets HTTP 503, not 401 `invalid_token` | core: Optional Opaque Access Tokens and Introspection; Error Responses | Mint opaque tokens; permit bearer tokens; make introspection fail |
| S39 | API | Every challenge to a bearer request uses the `Bearer` scheme: 401 `invalid_token` for an expired token, 400 `invalid_request` for an invalid argument, 403 `insufficient_scope`, 403 `actor_unauthorized`, and a 403 with `realm` and no `error` for any other denial | core: Error Responses (the selected scheme); RFC 6750 Section 3 | Mint access tokens; permit bearer tokens; close the API's actor gate |

The "negative-test row" sources are the rows of the core's "Renewal and
Negative Tests" table. N15 and N27 assert `invalid_grant`, which the
core's Redemption Errors assigns to an ID-JAG whose `act` agent has no
authorized correlation or is disabled. N16 asserts `actor_unauthorized`,
which Redemption Errors assigns when the actor gate refuses a valid
ID-JAG's agent. N25 and N28 send a single scope, so they do not
depend on whether the IdP narrows a request, which Issuance
Authorization permits but does not require. The time cases use an hour,
well beyond the few minutes of skew the core contemplates, so they do
not depend on one implementation's tolerance.

The suite fails a case only for a departure from a requirement. A
departure from a recommendation, such as a grant longer than five
minutes, a 401 challenge without an `error` parameter, or a 503 without
`Retry-After`, is printed as a note. An HTTP 403 is different: under the
core's Error Responses, a 403 challenge without an `error` attribute is
the response for a denial other than the actor gate or token authority.
A case that expects `actor_unauthorized` or `insufficient_scope` at the
API (N20, N53, S02, S03, S07, S11, S14, S15, S18, S35 to S37, S39, and the
setup reads of S25 to S28) therefore requires the code,
in the challenge's `error` attribute or, where the challenge has none,
in the body.

Run against the reference, `run.py` also fails a case that produces a
note, in normal and vacuity runs alike: the reference follows every
recommendation the suite notes, so a note from it is a regression.
Another implementation's notes are reported and fail nothing. S32 to
S34 fail only if a path is served; their other checks are notes, since
validating the token before saying whether a path exists is a SHOULD.

Every negative case but N32, and P2, P7 to P10, P12, P13, P16, D02,
D09 and D24, name the reference checks they exercise (`CHECKS` in
[reference.py](reference.py)). With `--vacuity`, each of these 123
cases runs once for each check it names, with that check switched off;
eight S cases, N40, N47 and N49 name two checks, so there are 134 runs,
and every run fails. Forty-six N cases fail because the server then
accepts the request, and N53 because the API then reports
`insufficient_scope` first. P2 fails because the access token
then carries a rewritten `act`, P7 because it is then a bearer
token, P8 to P10 because the server then accepts a nonce it never
provided, P12 and P16 because the grant then outlives the platform JWT
or the ID Token, and P13 because the disabled agent's grant is then
redeemed. N36
fails because the IdP then falls back to the shared client's own
authentication, which resolves no agent (`invalid_grant`). N11 fails because the RAS's
access-token protection check then
rejects the redemption with `invalid_request`; Access-Token Protection
states that Grant Protection's checks come first, so the case requires
`invalid_grant` or `invalid_dpop_proof`, the two codes Grant Protection
permits, and no longer depends on the reference's own order. Its second
step makes the resource permit bearer tokens, where access-token
protection would issue a bearer token, so only Grant Protection can
refuse the bound grant. N27 fails
because the RAS's actor gate then refuses the uncorrelated agent with
`actor_unauthorized`, the code Redemption Errors
keeps for an actor-gate refusal of a valid ID-JAG's agent. N31 fails
because the IdP then looks the malformed `sub` up as a user and
reports `invalid_grant`, the code for a valid credential that resolves
no user. N32 names no check: the reference resolves users in two
steps, and with both removed the request fails at the Delegation
Authorization with `actor_unauthorized` instead. N48 fails because the
RAS then refuses the ineligible record's agent on policy
(`invalid_target`), and N49 because both issuers' agents then get one
local principal. Without `ras.wag_policy`, N47 and N49 fail because the
RAS then admits a WAG that its policy does not permit.

The D cases fail without their check in these ways:

* the RAS issues a token it must not: D01, D02 (a second token), D05,
  D11, D14, D20, D21, D22 (after the actor gate reopens), D25 and D26;
* it returns or keeps a deferral where an error is required: D03, D06
  (a new deferral after the denial), D08, D18, D19 and D23;
* it returns another error: D07 (`access_denied`);
* it exceeds a bound: D04 and D17 (`expires_in`), D12 (`scope`), D13
  and D15 (the token's `exp`);
* it opens one access request for two redemptions (D10), or two
  pending redemptions for one grant (D16).

D09 and D24 are positive cases that depend on recovery: without
`ras.single_pending`, recovery returns another deferral code. D24 also
fails when the reference's opt-in test is the exact match
`completion_mode=deferred`, or when the suite accepts only
`authorization_pending` in a deferred response.

Without these checks, the S cases fail because the API then serves the
file (HTTP 200):

* S02, S04 to S07, S09 and S11 (`api.policy_source`): the request
  attribute replaces the token's value in the evaluation, and policy
  permits that value;
* S03 (`api.agent_from_token`): the API takes the agent from the client
  registration, so the other agent's token is evaluated as `agent-42`;
* S12 (`api.introspection_active`): the API reads the members of an
  inactive response;
* S13 (`api.introspection_act`): without `act`, the API applies no
  actor gate, as if the token were self-acting;
* S22 (`api.argument_validation`): the API ignores the invalid argument;
* S36 and S37 (`api.issuer_qualified_agent`): the API keys agents by
  `sub` alone, as the home issuer's, so it serves the partner issuer's
  `agent-42`.

Without these, they fail on the response the API selects:

* S04 to S07 and S09 (`api.denial_codes`): the API returns
  `actor_unauthorized` for every denial of a delegated token, and
  `insufficient_scope` for every denial of a self-acting one, so S04 to
  S06 and S09 find an `error` attribute, and S07 finds
  `actor_unauthorized`;
* S14 and S15 (`api.error_order`): the API reports the failing
  conditions in reverse order, so S14 gets `insufficient_scope` and S15
  gets a 403 without a code;
* S16 (`api.key_binding`): the API accepts the proof and reports the
  policy denial, HTTP 403 `actor_unauthorized`;
* S17 (`api.evaluation_unavailable`): the API treats the unreachable
  policy service as a denial, HTTP 403;
* S18 (`api.established_failure`): the API evaluates every condition
  and answers HTTP 503 whenever one cannot complete, even after the
  actor gate has denied;
* S19 (`api.incomplete_outranks`): the API passes over the unfinished
  actor gate and reports the user's denial, HTTP 403 without a code;
* S20 (`api.introspection_unavailable`): the API reads the failed
  introspection call as an invalid token, HTTP 401 `invalid_token`;
* S21 (`api.established_failure`): the API answers HTTP 503 without
  checking the proof it could have rejected;
* S38 (`api.bearer_outage`): the API looks for a DPoP proof on the
  bearer request, finds none, and answers HTTP 401 `invalid_token`;
* S39 (`api.challenge_scheme`): the API answers the bearer request with
  `DPoP` challenges;
* S23, S24 and S31 (`api.argument_rank`), with the arguments checked
  first: the API reports the invalid argument as soon as it finds it,
  HTTP 400, before the proof (S23), the tenant (S24) or the unfinished
  introspection (S31);
* S25 to S30 (`api.argument_rank`), with the arguments checked last: the
  API reports what authorization found, `actor_unauthorized` (S25,
  S27), `insufficient_scope` (S28), a 403 without a code (S29), or HTTP
  503 for the unfinished evaluation (S26, S30);
* S26 and S30 (`api.arguments_outrank_unfinished`): the API answers HTTP
  503 for the unfinished evaluation. Only the run with the arguments
  checked last can fail, since an API that checks them first never
  calls the policy service;
* S32 and S34 (`api.authenticate_before_route`): the API routes before
  it validates the token, so an unknown path gets 404 whatever the
  credentials, where the read path gets 401 or 503. The cases fail
  through the note this produces;
* S33 (`api.proof_method`): the API checks every proof as for `GET`, so
  it rejects the proof made for `POST` as `invalid_dpop_proof`, and
  accepts the one made for `GET`, so that the read path gets 405 and an
  unknown path 404;
* S35 (`api.existence_after_authorization`): the API reports the
  missing file, HTTP 404, before the actor gate's denial;
* S36 (`api.require_act`): the API accepts the untrusted issuer's `act`
  and denies it at the actor gate, HTTP 403 `actor_unauthorized`, not
  401 `invalid_token`.

S01, S08 and S10 are positive cases and name no check.

## Deferred redemption at the RAS

The D cases test the oversight companion's Deferred Redemption at the
reference RAS. In each of them, RAS policy requires approval for the
requested scope. They follow the companion's "Deferred redemption
negative test cases" table, and add a positive flow (D02) and a
recovery after approval (D09). D17 also covers the table's row in which
the grant's `exp` passes while the redemption is pending and the
approval then issues.

**Test-controlled Access Request Service.** The reference RAS opens one
task for each pending redemption in an Access Request Service of its
own, which test control decides. The suite can list the tasks, approve
one until an `approved_until` (optionally narrowing the scope), deny
one, revoke an approval, have the next re-evaluation of an approval
return a shorter `approved_until`, and have the service answer one
task's status with another task's result. The RAS keeps each approval
as the complete object it received (`id`, `approved_until`,
`approved_at`, and any `state`) and keeps a shorter deadline apart from
it, as its enforcement deadline.

**Clock control.** Test control advances each server's clock. The
suite's client advances its own clock with them, so DPoP proofs and
client assertions stay fresh, and no case sleeps. D04 advances nine
hours; D13, D14 and D17 advance some minutes.

**Reference-implementation tests.** A case that approves, denies,
revokes, shortens or substitutes needs control of the implementation's
Access Request Service, and a clock case needs control of its clock. A
third party cannot exercise those through the token endpoint, so these
are tests of the reference implementation, not black-box conformance
cases. Another implementation can run them only through an adapter that
provides the hooks ([Running against another
implementation](#running-against-another-implementation)). D01, D03,
D07 and D18 need only configuration: a RAS that requires approval for
the scope. D08 also needs an IdP and a RAS that accept unbound grants.

Some cases depend on choices made for the reference:

* D10 and D11 need a second agent, `agent-43`, for the same user. Its
  ID-JAG comes from the IdP's `mint_grant` test control, for the same
  RAS client, resource and scope. This stands for a shared client's
  issuance, which the reference IdP does not implement. D12 mints a
  grant for `files.read files.write` the same way, because the
  reference Delegation Authorization covers `files.read` only.
* D13 uses an approval expiry 300 s ahead, shorter than the 600 s
  access-token lifetime, so that the bound changes the token. The
  companion's row uses one hour, which any 600 s token meets. D15 uses a
  shorter expiry 120 s ahead, returned at one re-evaluation only, so the
  second refresh shows that the RAS kept it.
* D08 uses an unbound grant. For a bound grant, a proof of another key
  already fails Grant Protection, so the recovery match would not be
  what refuses it.
* D11 asserts a pending response, as Approval Binding says. A poll may
  get any pending code of DTR-01 Section 6.6 (`authorization_pending`,
  `interaction_pending`, or `interaction_required` with an
  `interaction_uri`) or `slow_down`. A deferred response carries
  `authorization_pending`, or `interaction_required` with an
  `interaction_uri`, as DTR-01 Section 6.4 shows both, and always the
  `interval` DTR-01 requires. The reference returns
  `interaction_required` with an `interaction_uri` when the opt-in
  includes `deferred_interactive` (D24), and `authorization_pending`
  otherwise. It never serves the URI; approval stays with test control.

## Policy services at the API

The S cases test the core's Optional Policy Services at the reference
API: when the API delegates authorization evaluation to a policy
decision service, it takes the user, the Agent Principal, the OAuth
client, the tenant and the token constraints only from the validated
access token or an authenticated introspection response, and trusted
configuration. Attributes derived from the request never supply or
override them. S02 and S03 are the core's negative-test rows for the
API's policy: the request attribute naming `agent-77`, and the platform
JWT variant's two agents with one `client_id`. S04 to S13 cover each
member, self-acting access, and introspection.

The S cases also test the core's Error Responses. When several checks
fail, the API reports the first in this order: the token and proof (HTTP
401), the token context (HTTP 401 `invalid_token`), an invalid argument
(the protocol's rejection; the reference answers HTTP 400
`invalid_request`), the actor gate (HTTP 403 `actor_unauthorized`),
token authority (HTTP 403 `insufficient_scope`), and any other denial
(HTTP 403 with a challenge that carries no `error` attribute). An
evaluation that cannot complete is not a denial: HTTP 503. S04 to S07
and S09 each fail one condition after the actor gate; S14 to S16 fail
two conditions at once; S17 makes the policy service unavailable; S18
and S19 make one condition's evaluation fail beside a denial, so that an
established failure is reported only when no unfinished check comes
earlier. S20 and S21 do the same for token validation: an introspection
call that cannot complete gets 503, unless a proof failure in the same
row is already established. S22 to S31 add an invalid argument: the read
declares `version`, a positive integer. S22 sends `version=abc` alone,
and each other case sends it beside one other condition. Each runs
twice, with the API checking arguments first and then last (test control
`evaluation_order`), and expects the same response: the argument's
rejection over every authorization failure and unfinished policy
evaluation (S25 to S30), and the proof, the tenant and an unfinished
introspection over the argument (S23, S24, S31).

**Test fixtures.** The policy service and the API's introspection
caller are test fixtures under the suite's control. The policy service
runs in the API's process. When test control turns it on, it replaces
the API's own user-permission and actor-gate evaluation; token
validation, DPoP, applicability and the tenant check still run first,
and the API still requires the token's scope for the read, so a permit
never overrides the token's constraints. Test control sets its policy,
makes it unavailable, and reads the evaluation requests it received.
The API's `evaluation_order` control chooses when it checks the read's
arguments; a conforming API reports the same failure either way.
The S cases are reference-implementation tests, not black-box
conformance cases, and passing them claims nothing about a real policy
decision point integration.

**Policy and decisions.** The policy is a document whose members each
list what policy permits: the actor gate's (user, agent, tenant)
entries, categorical prohibitions of an agent for an action, the scope
each action requires, the user's own permissions, a self-acting agent's
own permissions, and the allowed clients and tenants. The service
evaluates three conditions in the order the API asks for and returns
the first that fails as the decision's reason: the actor gate (delegated
access only), then the required scope, then the rest. The API merges
that reason with its own scope check, reports the first in the order,
and maps it to `actor_unauthorized`, to `insufficient_scope` with the
required scope, or to a DPoP challenge without an `error` attribute and
an empty JSON body. A decision it cannot interpret, or an unreachable
service, gets HTTP 503 with `Retry-After`. The API's own evaluation,
without the service, uses the same order. Two members serve S26 and
S27: `parse_arguments` makes the evaluation parse request attributes
before deciding anything, and an actor-gate entry with `min_version`
also needs the request's `version` to be at least that.

**Evaluation requests.** The API's request follows the implementer's
guide's [illustrative AuthZEN
requests](../IMPLEMENTERS-GUIDE.md#illustrative-requests): `subject`,
`action` and `resource`, with `agent`, `client`, `tenant` and
`constraints` (`scope` and `aud`) in `context`. For self-acting access
the subject is the local agent principal and there is no `agent`
member. The drafts define no AuthZEN mapping; this shape is the
reference's own.

**Request attributes.** The API accepts the query parameters `agent`,
`user`, `client_id`, `tenant`, `scope` and `version` on a file read.
They stand in for a tool call's arguments; the drafts define no such
parameters. The read declares one argument contract: `version`, where
present, is one positive integer, and any other value is rejected with
HTTP 400 `invalid_request`. The
API passes every query parameter to the policy service unchanged, in
`context.request` and nowhere else.

**Self-acting tokens.** The API configures a separate client
registration, `analysis-agent-client`, as the self-acting population for
the `acme-data` resource, as Profile Applicability permits. Its tokens
name the local agent principal `service-principal-42` as `sub` and carry
no `act`. The IdP's client registration association names that
registration for `analysis-client`'s WAGs, and the RAS redeems a WAG
under it for such a token (P14, P15); the S cases mint them through
test control. The reference does not defer a WAG.

**Introspection.** The RAS answers RFC 7662 introspection at
`/introspect` to a caller that authenticates with HTTP Basic, and
rejects any other caller with 401 `invalid_client`. The API holds its
own credential, generated at start, and calls the RAS over HTTP at the
RAS's localhost transport whenever the presented token is not a JWS.
The RAS mints opaque tokens only through test control. The API treats
the response as validated claims: it rejects `active` false, applies
applicability and the `act` requirement, binds the DPoP proof to
`cnf.jkt`, and takes the tenant from `aud`. A call that does not return
a JSON object with a boolean `active`, such as an endpoint error, a
timeout or a malformed body, cannot complete: the API checks the DPoP
proof it has, and otherwise answers HTTP 503. Test control makes the
RAS's endpoint fail (`introspection_unavailable`: `error`, `malformed`
or `truncated`). S20 and S21 present tokens the API has not introspected
before, so an implementation that caches responses within its limits
still has to make the call. Nothing caches a response, and the suite tests no
freshness limit.

Some cases depend on choices made for the reference:

* Each S case's policy permits the positive path in both tenants and
  changes one member. S04 lets the actor gate permit both `user-108`
  and `user-109`, so that `user-108`'s denial comes from the user's own
  permission and not from the gate. S06's gate and user permissions
  cover both tenants, so that the request attribute naming `beta-data`
  would succeed if it replaced the token's tenant.
* S14 makes the actor gate fail through a categorical prohibition of
  `agent-42`, and S15 through an actor gate with no entry for it, so the
  two cases cover both forms.
* S25 and S28 pair the invalid argument with the API's own actor gate
  and scope check, and S26, S27, S29 and S30 with the policy service, so
  the argument's rank is tested under both.
* S03 mints the other agent's token, for `agent-43`, with the same
  `client_id` as `agent-42`'s. It stands for the platform JWT variant's
  shared client.
* S08 first reads with the API's own evaluation and its actor gate for
  `agent-42` closed, to show that no actor gate applies, and then reads
  through the policy service.
* For S12, the RAS returns the token's members with `active` false.
  RFC 7662 Section 2.2 discourages that but permits it, and it gives an
  API that ignores `active` something to accept. For an unknown or
  expired token, the RAS returns only `active`.
* S12 and S13 test introspection processing and leave the policy
  service off.
* `api.introspection_auth` is not a check. An API that stopped
  authenticating would be refused by the RAS on every introspection, so
  no case could observe it accepting an unauthenticated response.

## What the suite does not cover

The suite tests nothing outside the path above, including:

* governed agent access with unbound grants, except bearer issuance
  (P5 to P7), the single use of an unbound grant (N50, N51), and as
  the setup for N10, N30, and D08;
* the existing platform JWT input beyond P11, P12 and N36 to N39: JSON
  Pointer selectors, the binding of key-bound platform JWTs (which the
  reference refuses, N39), a configured maximum age, and self-acting
  presentation; and the inputs of the inputs draft;
* WAG issuance and redemption beyond P14, P15, N44 to N49, N51, N52
  and N54: presented evidence, the byte-identical subject token, the Agent
  Authorization's scope ceiling, deferred WAG redemption, and the other
  WAG rows of Redemption Errors; S08 and S09 use minted self-acting
  tokens;
* introspection beyond the API's processing in S10 to S13: the RAS's
  own introspection responses, caching and freshness limits,
  `authorization_details`, certificate-bound tokens, and opaque tokens
  issued by a redemption, for which a case that reads the access
  token's claims is reported as not run;
* a real policy decision point, and policy services at the IdP or the
  RAS;
* the error selection order under the API's own evaluation, except the
  actor gate (N20), the actor gate beside a missing scope (N53), and an
  invalid argument beside the API's own actor
  gate or scope (S25, S28), and a policy decision the API cannot
  interpret; the
  S cases test the order through the policy service, S17 an
  unreachable one, S18 and S19 one condition that cannot complete, and
  S20 and S21 an introspection call that cannot complete;
* argument contracts other than the read's one declared argument, and
  the precedence of a request whose operation, target or tenant cannot
  be identified, which Error Responses leaves outside its order; S32 to
  S34 test only Error Disclosure's recommendation to validate the token
  first;
* RAS refresh tokens other than those from a deferred redemption;
* Client ID Metadata Documents, including the rejection of a document
  whose authentication method a server does not accept (core: Client
  Metadata);
* mutual TLS, including the refusal to defer for a resource configured
  for mutual-TLS access tokens, and the refresh of a DPoP-bound grant
  whose access tokens are certificate-bound, which keeps the grant's
  DPoP binding (Optional RAS Refresh Tokens) and has no worked example
  in the core; bearer access tokens only as P5 to P7,
  N35, S38 and S39 test them, and DPoP nonces only as P8 to P10 do;
* continuation, including the CAI's refusal to attest an access token
  from a deferred redemption or one refreshed from it;
* in deferred redemption: grant-derived revocation while pending,
  cancellation by revoking the deferral code, a change of the user's
  account link while pending, an absolute expiration set before the
  deferral, and `slow_down`;
* other oversight, lifecycle propagation, and SCIM management.

## Running against another implementation

The cases in [suite.py](suite.py) use only HTTP. To run them against
another IdP, RAS or API:

1. Build a `suite.Config` with the deployment's issuers, token
   endpoints, API origin, transport URLs, client identifiers and keys,
   and the identities `expect` names: the agent's issuer and
   identifier, the user's subject in the grant, and the user's subject
   in the access token. Set `max_grant_lifetime` to the IdP's configured
   grant lifetime limit. N13 needs a second client registered at the RAS;
   N17 needs a second tenant in which the user and the agent also have
   rights. N27 needs `uncorrelated_agent`, an agent the RAS has no
   correlation for; N34 uses it too, with just-in-time correlation
   turned on (`set:ras.jit`). N33 needs `governance_tenant`, the tenant
   of the user and the agent at the IdP, and `set:idp.tenant_pair`.
   N41 to N43 run only where `multi_tenant_issuer` is set, and use
   `other_governance_tenant`, another tenant of the IdP's issuer: N41
   needs `set:idp.agent_governance_tenant`; N42 and N43 need
   `mint_grant`, `other_tenant_sub`, a subject of that tenant, and
   `set:ras.user_link`; N43 also needs `set:ras.tenant_trust`. D25 and
   D26 also run only where `multi_tenant_issuer` is set, and need
   `set:ras.tenant_trust`. P14, P15 and N44 to N49 need
   `self_acting_client_key`, the key of the RAS registration the IdP
   names in the client's WAGs (`self_acting_client_id`, which is
   `ras_client_id` where a deployment keeps one registration); N44 also
   needs `set:idp.self_acting_association`, N45 `set:idp.tenant_pair`,
   and N46 `mint_wag` and `multi_tenant_issuer`. N47 to N49 need
   `mint_wag`, `uncorrelated_agent`, `agent_record`, `set:ras.jit`,
   `set:ras.jit_eligible` and `set:ras.self_acting_rule`; N49 also needs
   `partner_agent_iss` and `set:ras.trusted_issuer`. N50 and N51 need
   `set:idp.client_profile` and `set:ras.client_profile`, N51 for the
   self-acting registration too; N52 needs `mint_grant`, `mint_wag` and
   the just-in-time controls of N47; N53 needs `extra_scope` and
   `set:idp.delegation_scope`; N54 needs the controls of N47 and
   `set:ras.remove_correlation`. D10 and D11 need
   `second_agent`, another agent the RAS correlates and lets act for
   the user; D12 needs `extra_scope`, a
   scope beyond `scope` the RAS can require approval for, and N25 and N28
   use it as a scope the IdP can exclude from the delegation or prohibit
   for the agent. The S cases
   need `tenant` and `other_tenant`, the Target Tenants of the two
   resources, and `self_acting_client_id` and `self_acting_sub`, a
   registration the API configures as the self-acting population for
   `resource` and the local agent principal its tokens name. S32 to S35
   use `unknown_path`, a path under the API that names no route, and
   `missing_path`, a well-formed read of a file that does not exist; by
   default, `read_path` plus `/unknown`, and `report-99` beside the
   read's file. S36 and S37 need `partner_agent_iss`, a second issuer
   whose agents the API trusts the RAS to assert, and
   `untrusted_agent_iss`, an issuer the API does not trust for agents.
   They assume the API's actor gate, and the policy S37 sets, permit the
   user's `agent-42` only under `expect["agent_iss"]`, with no entry for
   the partner issuer's. P11 to P13 and N36 to N39 need `shared_client`,
   P13 as a second IdP client, a
   `suite.SharedClient`: a shared client at the IdP and its RAS
   registration, a platform issuer whose JWTs the suite signs with a key
   the IdP approves, the workload `sub` the IdP binds exactly to an agent,
   and an audience the IdP accepts; the IdP also holds the Client
   Association and the user's Delegation Authorization for that agent
   through the shared client. Without it, those cases are not run.
2. Implement `suite.Adapter` for the deployment. Every case whose grant
   the IdP issues needs `id_token`; the "Test control" column lists the
   other capabilities. A case whose capability the deployment cannot
   provide is skipped by raising `suite.NotRun` from the adapter method
   it needs; `run_case` then reports it as not run. The base `Adapter`
   raises it from every capability method, so an adapter defines only
   what the deployment provides, and `reset`. Any other exception ends
   the run. N25 and N28 use `set` on the IdP
   (`delegation_scope`, `prohibited_scope`). The D cases use `set` on
   the RAS (`approval_required`, `refresh_permitted`,
   `max_pending_lifetime`, `authorization_lifetime`, `client_profile`),
   the Access Request Service hooks `tasks`, `approve`, `deny`, `revoke`,
   `shorten` and `substitute`, and `advance_clock`, which must advance
   every server's clock. The S cases use `set` on the API
   (`policy_service`, `actor_gate`, `policy_unavailable`,
   `condition_unavailable`, `evaluation_order`) and on the RAS
   (`introspection_omit_act`, `introspection_unavailable`), the policy
   service hooks `set_policy` and
   `evaluations`, `mint_access_token`, and `mint_opaque_token`. The
   `Adapter` docstring defines each one, including the policy document
   that `set_policy` takes. S22 to S31 send `version`, which the API
   must declare as a positive integer, and expect its rejection as
   `Adapter.argument_rejection` recognizes it: HTTP 400 with
   `invalid_request` unless the adapter overrides that for its protocol.
   They also set `evaluation_order`; a deployment that cannot switch it
   can skip them and report them as not run, or run them in its own
   order with an adapter whose `set` accepts that setting without acting
   on it. S32 and S33 ask `Adapter.route_rejection` whether an unknown
   path or an unsupported method was rejected; by default any response
   that does not serve the request counts, and only the reference
   adapter requires 404 and 405 with `Allow: GET`.
3. Call `suite.run_case` for each case in `suite.CASES`. It returns
   `None` in place of a pass or failure for a case it did not run.

`disable_check` exists only for the reference implementation's vacuity
mode.

The suite's client keeps any `DPoP-Nonce` a server returns and puts it
in later proofs to that server. When a server demands a nonce (HTTP 400
`use_dpop_nonce` at a token endpoint, or a 401 challenge with it at the
API, RFC 9449 Sections 8 and 9), the client retries once with a fresh
proof and fresh client authentication. N01 and N22 send a fixed client
assertion and D18 a fixed proof, so they do not retry; against a
server that demands a nonce on every request, they can fail for that
reason alone.

### RAS-only mode

A RAS and API can be tested without a governed IdP. Wrap the adapter in
`suite.SigningAdapter(adapter, issuer, key, audience)`: the suite then
signs ID-JAGs itself, for `issuer` and the RAS issuer `audience`, with a
private key whose public key the RAS trusts for that issuer. The grants
carry the claims the reference IdP issues (the user's subject in the
RAS namespace, the RAS registration as `client_id`, `resource`,
`scope`, `act`, `cnf.jkt` for the client's key, `tenant` where
`multi_tenant_issuer` is set, 300 s). IdP cases, and
any case that needs an ID Token, are reported as not run; `mint_grant`
needs no IdP test control. The suite signs WAGs the same way, including
N49's WAGs for `partner_agent_iss` with the same key, so the adapter's
`trusted_issuer` control must trust that key for the partner issuer.
With the reference, `run.py --ras-only` has
the reference RAS trust a key the suite generates for
`https://idp.example/`, and CI runs this mode with `--vacuity`.

## Configuration the reference assumes

The drafts leave these choices to deployments. The reference makes one
choice for each, and an implementation that chooses differently
interoperates only where the choice is agreed. The implementer's guide
lists what each pair of implementations exchanges and must agree on
([configuration exchanged between
implementations](../IMPLEMENTERS-GUIDE.md#configuration-exchanged-between-implementations)).

| Choice | The reference's choice | Drafts' text |
|---|---|---|
| How the API tells the governed delegated population apart | Trusted configuration keyed by the access token's `client_id` and audience | core: Profile Applicability ("no in-band discriminator") |
| How the API tells the self-acting population apart | A separate client identifier, `analysis-agent-client`, configured at the API as the self-acting population for the `acme-data` resource; P15 redeems a WAG the IdP issues for it, and S08 and S09 mint its tokens through test control | core: Profile Applicability (separate client registrations) |
| Where the tenant is carried | The tenant-specific resource URI, as the access token's audience | core: Access Token Issuance and Response (the default) |
| Client registration association | One RAS registration for each IdP client and acting relationship: `analysis-api` for the dedicated client `analysis-client`'s delegated grants and `analysis-agent-client` for its self-acting grants, and `platform-api` for the shared client `platform-client` | core: Issuance Prerequisites |
| Platform JWT credential class | A dedicated issuer, `https://platform.example/`, configured with `platform-client`; `ES256`; accepted audience `https://idp.example/`; evidence deadline from `exp`, with no maximum age; `workload-43` bound exactly to `agent-43` | core: Existing Platform JWT (Configuration) |
| Actor gate | An explicit entry of user, agent issuer, agent and tenant, at both the RAS and the API; at the RAS, a rule admitting every agent of an issuer for a tenant only under test control | core: Delegated Actor Authorization ("not a protocol object"); RAS and API implementation considerations ("another explicit rule") |
| Governance Tenants | The IdP's issuer is multi-tenant, with tenants `acme` and `beta`; Alice and both agents are in `acme`, and every grant names `acme` in `tenant`. Policy authorizes only (`acme`, `acme-data`) for issuance, and a refused pair gets `actor_unauthorized`. The RAS trusts the issuer's tenant `acme` for `acme-data`, and keys user links by issuer, issuer tenant, Target Tenant and subject | core: Canonical Identity and Tenant Boundaries; Issuance Authorization; Issuance Errors |
| Just-in-time correlation | Off unless test control turns it on for the IdP's issuer and `acme-data`, for ID-JAGs and WAGs; a created record is eligible, and the actor gate, or for a WAG the RAS's self-acting policy, still applies | core: Optional Just-in-Time Correlation |
| Delegation Authorization | Agent, user, client and resource, with a scope set; a request is narrowed to that set and away from scopes policy categorically prohibits for the agent there; if nothing remains, a requested scope that is prohibited gives `actor_unauthorized`, and otherwise the result is `invalid_scope` | core: Delegation Authorization; Issuance Authorization |
| Re-redeeming a bound grant | Not accepted: each grant is redeemed once | core: Common Grant Validation (MAY accept again under explicit policy) |
| Access tokens | JWT access tokens validated at the API, 600 s, no refresh token except after a deferred redemption; opaque tokens only through test control; bearer tokens only for a resource test control configures to permit them | core: Token Validation; Optional RAS Refresh Tokens; Access-Token Protection |
| Introspection | RFC 7662 at the RAS, for opaque tokens; the API authenticates with HTTP Basic, calls over HTTP, and caches nothing | core: Optional Opaque Access Tokens and Introspection |
| Agent namespaces | The API trusts the RAS to assert agents of `https://idp.example/` and `https://partner-idp.example/`; the RAS itself trusts only the first, so tokens naming the partner's agents come from test control. The API's actor gate and the policy service compare the issuer and the `sub` together | core: Delegated Access (Identity); Delegated Actor Authorization |
| Routing | The API validates the token, its proof against the request's own method, and its applicability before routing. An unknown path gets 404, a method the read does not support 405 with `Allow: GET`, and a missing file 404 only after authorization. While introspection cannot complete, an unknown path gets 503 | core: Error Disclosure (SHOULD; precedence not specified) |
| Declared argument contract | The read's `version`, where present, is one positive integer; any other value gets HTTP 400 `invalid_request` with a DPoP challenge | core: Error Responses (row 3) |
| Policy service | Off unless test control turns it on; in-process, replacing the API's own evaluation; policy set by test control; the decision names the first failing condition | core: Optional Policy Services |
| API denials | HTTP 403 `actor_unauthorized` for the actor gate; HTTP 403 `insufficient_scope`, with the required scope, for token authority; for any other denial, delegated or self-acting, HTTP 403 with `DPoP algs="ES256"` and an empty JSON body; HTTP 503 with `Retry-After: 5` and an empty JSON body when an evaluation cannot complete | core: Error Responses; Self-Acting Access |
| Approval at the RAS | Not required unless test control names the scopes that need it; the Access Request Service is in-process and test-controlled | oversight: Redemption Opt-In; Approval Binding |
| Deferral lifetimes | Maximum pending lifetime 3600 s; absolute authorization expiration 8 h after acceptance; polling interval 5 s | oversight: Deferring a Redemption |
| Refresh after a deferred redemption | Only where test control permits it; bound to the client and the DPoP key, not rotated | core: Optional RAS Refresh Tokens; oversight: Refresh and Continuation |
| Client assertion `aud` | The issuer identifier as a string or a one-element array | core: Dedicated Client Identity (Audience) |
| ID Token audience | Accepted when the `aud` string or array contains the authenticated client, without checking `azp` | ID-JAG Section 4.3.3 |
| Clock skew and DPoP proof age | 60 s each; nonces only under test control (P8 to P10) | core: Time, Replay, and Key Validation; RFC 9449 |
| Time claims | `exp` enforced on every JWT; `iat` required on ID Tokens, grants and access tokens; `iat` and `nbf`, where present, rejected beyond the skew | core: Time, Replay, and Key Validation; RFC 7519; RFC 7523 Section 3 |
| Explicit types | `typ` accepted with or without the `application/` prefix | RFC 7515 Section 4.1.9; RFC 9068 Section 4 |
| Lifetimes | ID Token 65 min (as the oversight walkthrough uses), grant 300 s, access token 600 s | core: Common Grant Claims |

## Draft questions found while implementing

These are places where the core leaves behavior that two implementations
could build differently. An entry marked resolved names the draft change
that settled it.

1. **The RAS's error for its own actor-gate denial.** Resolved. The
   core's Redemption Errors assigns `actor_unauthorized` when the actor
   gate refuses a valid ID-JAG's agent, and N16 asserts it. Since
   ID-JAG-06, other RAS policy refusals get `access_denied`.
2. **The RAS's error for a missing or disabled agent record.**
   Resolved. The core's Redemption Errors now assigns `invalid_grant`
   for an ID-JAG whose `act` agent has no authorized correlation or is
   not eligible, and widens the WAG row. N15 asserts it for a disabled
   agent, and N27 for an uncorrelated one.
3. **A delegation that covers none of the requested scope.** Resolved.
   The core's Issuance Errors and Issuance Authorization split
   `actor_unauthorized` (no applicable delegation, or a categorical
   prohibition) from `invalid_scope` (scope ceiling). N09 and N28 assert
   the first, and N25 the second.
4. **A grant with a missing or empty `scope` claim.** Resolved. The
   core's Common Grant Validation assigns `invalid_grant`, and N26
   asserts it.
5. **Check order for a bound redemption without a proof.** Resolved.
   The core's Access-Token Protection states that Grant Protection's
   checks come first, so N11's result, `invalid_grant` or
   `invalid_dpop_proof`, no longer depends on the reference's order.
6. **The API's error for a user-authority denial.** Resolved, with
   questions 7 and 8. The core's Error Responses defines the selection
   order, the no-code 403 and the 503. A user-permission denial is HTTP
   403 with a challenge that carries no `error` attribute (S04).
7. **The API's error for a self-acting denial.** Resolved by the same
   change: HTTP 403 with a challenge that carries no `error` attribute
   (S09).
8. **The API's error for a client, tenant or constraint policy
   denial.** Resolved by the same change. A client or tenant policy
   denial is HTTP 403 with a challenge that carries no `error` attribute
   (S05, S06); a scope the operation needs and the token lacks is HTTP
   403 `insufficient_scope` (S07). S14 to S19 test the order and the 503.
9. **The IdP's error when the agent's Governance Tenant is not
   authorized for the Target Tenant.** Resolved. The core's Issuance
   Errors assigns `actor_unauthorized` in delegated issuance, since
   Section 6.6.2 of Actor Profile requires it when local policy
   prohibits the relationship, and `invalid_target` in self-acting
   issuance, with the other refusals of an agent for a target. N33
   asserts the first and N45 the second.
10. **Whether two IdP clients may share one RAS registration.**
   Resolved. Issuance Prerequisites now permits several IdP clients to
   map to one registration, and states the consequences: the RAS cannot
   tell those clients apart, a restriction of an agent still follows
   the agent, and only a bound grant stays with the key that obtained
   it. The reference keeps a registration per IdP client and acting
   relationship; P13 maps `platform-client` to `analysis-api` through
   test control.

[core-scope]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-federation.html#scope
