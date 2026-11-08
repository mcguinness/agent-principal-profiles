<!-- regenerate: off (set to off if you edit this file) -->

# Governed Agent Profiles

Internet-Drafts for governing agents across the platforms that run them
and the resource domains they reach. An enterprise identity provider
(IdP) resolves each agent's execution identity, its OAuth client or
workload credential, to a governed Agent Principal. Resource domains
recognize, authorize, and audit that principal without knowing the
platform. Today's common alternative, one shared OAuth client per
platform, makes every agent behind it look the same: attribution is lost
and revocation is all or nothing.

## How it works

Three parties decide. The enterprise IdP identifies the agent and
authorizes a grant naming it; the resource domain's authorization server
(RAS) decides what access to issue; and the API enforces that access
with its own checks. The agent runs on an agent platform, whose OAuth
client carries the grant between them. The grant depends on whom the
agent acts for:

| The agent acts | Grant | The resource domain sees |
|---|---|---|
| For a user | Identity Assertion JWT Authorization Grant (ID-JAG) | The user as subject and the agent as actor |
| For itself | Workload Authorization Grant (WAG) | The agent as subject |

```mermaid
flowchart TB
  subgraph platform["Agent platform"]
    agent["Agent<br/>identified by a client key,<br/>platform JWT, SVID,<br/>or attestation"]
    client["OAuth client<br/>one per agent, or shared"]
  end
  idp["Governing IdP<br/>resolves the Agent Principal<br/>and authorizes the grant"]
  subgraph domain["Resource domain"]
    ras["RAS<br/>decides what access<br/>to issue"]
    api["API<br/>enforces access"]
  end
  agent -->|"its credential"| client
  client <-->|"token exchange,<br/>ID-JAG or WAG"| idp
  client <-->|"redeem the grant,<br/>access token"| ras
  client -->|"call"| api
```

Around that path, SCIM keeps the IdP, the platform, and the resource
domains in step, and optional Shared Signals Framework (SSF) streams
carry events between them:

```mermaid
flowchart LR
  platform["Agent platform<br/>SCIM connector"]
  idp["Governing IdP"]
  domain["Resource domain<br/>RAS and API"]
  platform -->|"SCIM: register agents,<br/>bindings, client associations"| idp
  idp -->|"SCIM: status of the<br/>agents it hosts"| platform
  platform <-.->|"SSF: WISE and CAEP events, SCIM<br/>change notices, about the agents it hosts"| idp
  idp -->|"SCIM: provision agents<br/>and their status"| domain
  idp -.->|"SSF: SCIM events,<br/>CAEP session revocation"| domain
```

| Connection | What happens | Defined in |
|---|---|---|
| Token exchange (OAuth) | The platform's OAuth client presents the agent's identity: its own client authentication when it serves one agent, the platform's JWT for the agent when it is shared, or a SPIFFE SVID or Client Attestation. The IdP trusts only issuers and key sources configured in advance, and resolves the identity to the Agent Principal through an enabled Identity Binding | [Core][core]; [input profiles][inputs] for SVIDs and Client Attestation |
| Registration (SCIM, platform to IdP) | The platform's SCIM connector registers each agent at the IdP. For an agent that obtains grants, it also binds the agent's identity to it and, for delegated access, associates the OAuth clients that may use it; client use for self-acting access is configured at the IdP. Each is a separate permission the IdP grants the connector | [SCIM management][management]; [SCIM OAuth client management][oauth-client] for the clients themselves |
| Provisioning (SCIM, from the IdP) | Agents and their status are provisioned to each resource domain, and a platform obtains the status of the agents it hosts, pushed or retrieved on a change notice. Each applies a disablement to the authorization it issued | [Lifecycle][lifecycle] |
| Signals (SSF, optional) | Resource domains receive SCIM change notices and CAEP session revocation. A platform can send WISE credential and posture events and CAEP session revocation about the agents it hosts, and receive SCIM change notices and CAEP risk changes. No event activates an agent: a SCIM change notice triggers retrieval of the current state | [Lifecycle][lifecycle] |

Companion profiles also add gateways that call further resource domains,
and human oversight, without changing this path; the architecture
overview shows [how they all connect](ARCHITECTURE.md#how-they-connect).

## The drafts

Start with the [OAuth 2.0 Profile for Governed Agent Federation][core]
([source](draft-mcguinness-oauth-governed-agent-federation.md), OAuth
working group). A client, IdP, RAS, and API can implement
dedicated-client federation, one OAuth client per agent, from it alone.
The core also supports shared clients that present an existing platform
JWT identifying the agent. Add a companion when you need what it
addresses:

| When you need | Add | Working group |
|---|---|---|
| SPIFFE or Client Attestation evidence, including several managed installations behind one client | [Agent Resolution Input Profiles][inputs] ([source](draft-mcguinness-oauth-governed-agent-inputs.md)) | OAuth |
| A gateway that calls further resource domains for the agent | [Identity Continuation Profile][continuation] ([source](draft-mcguinness-oauth-governed-agent-continuation.md)) | OAuth |
| Platforms that register agents and their relationships at the IdP | [SCIM Profile for Governed Agent Federation Management][management] ([source](draft-mcguinness-scim-agent-federation.md)) | SCIM |
| OAuth client registrations managed through SCIM | [SCIM Profile for OAuth 2.0 Client Management][oauth-client] ([source](draft-mcguinness-scim-oauth-client-management.md)) | SCIM |
| Resource domains provisioned with agents and their disablement | [Governed Agent Lifecycle Profile][lifecycle] ([source](draft-mcguinness-oauth-governed-agent-lifecycle.md)) | SCIM |
| A person to approve, or to observe and end, an agent's grants, redemptions, and actions | [Human Oversight Profile][oversight] ([source](draft-mcguinness-oauth-governed-agent-oversight.md)) | OAuth |

The draft names link to the editor's copies. All seven are individual
drafts under development. An implementation that claims none of the
optional inputs needs only the core; the core and the input profiles
reference each other normatively and are published together.

## Where to start

| You are | Start with | Then |
|---|---|---|
| Evaluating the approach | The [architecture overview](ARCHITECTURE.md) | The [first transaction](EXAMPLES.md#first-delegated-transaction) of the end-to-end examples |
| An enterprise identity team | The [playbook for identity teams](PLAYBOOK.md): owners, exit checks, recipes, and runbooks | The architecture overview |
| Building an IdP, RAS, API, or client | The [implementer's guide](IMPLEMENTERS-GUIDE.md): what each role builds and configures, and the errors it returns | The core, and the [end-to-end examples](EXAMPLES.md) for the messages |
| Adding an optional capability | The guide's chapter for it: continuation for gateways and scheduled work, human oversight for approval at the IdP, the RAS, or an action, AuthZEN for policy services | The companion profile that defines it |
| Building an agent platform | The guide, then [SCIM management][management] to register agents | [Lifecycle][lifecycle] for agents the platform hosts |
| Building a SCIM service for OAuth clients | [SCIM OAuth client management][oauth-client] | |
| Testing an implementation | The [conformance suite](conformance/README.md): cases for the delegated path, deferred redemption at the RAS, and an API's policy service, each listing the control of the implementation it needs, with a test-only reference IdP, RAS, and API | |
| Tracking dependencies | The [coordination notes](COORDINATION.md): what the drafts need from the specifications they depend on | |

## Contributing

See the
[guidelines for contributions](https://github.com/mcguinness/governed-agent-profiles/blob/main/CONTRIBUTING.md).

The contributing file also has tips on how to make contributions, if you
don't already know how to do that.

## Command Line Usage

Formatted text and HTML versions of all drafts can be built using `make`.

```sh
$ make
```

Command line usage requires that you have the necessary software installed.  See
[the instructions](https://github.com/martinthomson/i-d-template/blob/main/doc/SETUP.md).

Continuous integration also runs:

* the conformance suite with its vacuity check, in full and RAS-only
  modes (`conformance/run.py --vacuity`, with and without `--ras-only`;
  setup in [conformance/README.md](conformance/README.md));
* `tools/check_examples.py`, which checks the messages EXAMPLES.md copies
  from the drafts; and
* `tools/check_citations.py`, which fails when an Internet-Draft
  reference is not pinned to a revision, or when a draft cites a section
  of another specification that `tools/cited-sections.json` does not
  record at the referenced revision.

After changing a pin or citing a new section, run
`python3 tools/check_citations.py --fetch --update` and review what it
prints: it records the heading of each newly cited section at the
referenced revision, and `--fetch` alone compares every recorded heading
with that revision's text. The check finds renumbered, missing and
unverified sections; it cannot tell that a real section does not
support the sentence citing it.

[core]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-federation.html
[inputs]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-inputs.html
[continuation]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-continuation.html
[management]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-scim-agent-federation.html
[lifecycle]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-lifecycle.html
[oversight]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-oauth-governed-agent-oversight.html
[oauth-client]: https://mcguinness.github.io/governed-agent-profiles/draft-mcguinness-scim-oauth-client-management.html
