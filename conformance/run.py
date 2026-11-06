#!/usr/bin/env python3
"""Run the conformance suite against the reference servers.

    python3 conformance/run.py             run every case
    python3 conformance/run.py --vacuity   also show each negative case fails
                                           with each check it cites switched off,
                                           and why
    python3 conformance/run.py --list      list the cases, their sources and needs

Exits 1 if a case fails, or, with --vacuity, if a case still passes with one
of its checks switched off. The reference follows every recommendation the
suite notes, so a note from it counts as a failure here; against another
implementation, a note is reported and does not fail the case.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jws  # noqa: E402
import reference  # noqa: E402
import suite  # noqa: E402


def reference_config(ras_only=False):
    keys = {cid: jws.new_rsa_key() for cid in ("analysis-client", "analysis-api", "other-api")}
    signer = jws.new_rsa_key() if ras_only else None
    transports, servers = reference.start(
        keys, grant_signer=signer.public_key() if signer else None)
    cfg = suite.Config(
        idp=suite.Endpoint(reference.IDP_ISSUER, reference.IDP_ISSUER + "token",
                           transports["idp"]),
        ras=suite.Endpoint(reference.RAS_ISSUER, reference.RAS_ISSUER + "token",
                           transports["ras"]),
        api_base=reference.API_BASE, api_transport=transports["api"],
        resource=reference.RESOURCE, other_resource=reference.OTHER_RESOURCE,
        read_path="/tenants/acme-data/files/report-7",
        other_tenant_path="/tenants/beta-data/files/report-9",
        idp_client_id="analysis-client", idp_client_key=keys["analysis-client"],
        ras_client_id="analysis-api", ras_client_key=keys["analysis-api"],
        other_ras_client_id="other-api", other_ras_client_key=keys["other-api"],
        user="alice", scope="files.read",
        expect={"agent_iss": reference.IDP_ISSUER, "agent": "agent-42",
                "grant_sub": "alice-ras", "token_sub": "user-108"})
    adapter = suite.ReferenceAdapter(transports)
    if signer:
        adapter = suite.SigningAdapter(adapter, reference.IDP_ISSUER, signer,
                                       reference.RAS_ISSUER)
    return cfg, adapter, servers


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vacuity", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--ras-only", action="store_true",
                        help="sign grants in the suite; run no IdP case")
    args = parser.parse_args()

    if args.list:
        for c in suite.CASES:
            needs = ", ".join(c.needs) or "ID Token only"
            print(f"{c.id:4} {c.role:4} {c.title}\n           source: {c.source}\n"
                  f"           adapter: {needs}")
        return 0

    cfg, adapter, servers = reference_config(ras_only=args.ras_only)
    suite.wait_ready(cfg)
    failures = not_run = 0
    skipped = set()
    for c in suite.CASES:
        passed, detail, notes = suite.run_case(c, cfg, adapter)
        if passed is None:
            not_run += 1
            skipped.add(c.id)
            print(f"NOT RUN {c.id:4} {c.role:4} {c.title}  ({detail})")
            continue
        if passed and notes:
            passed, detail = False, "the reference produced a note"
        failures += not passed
        print(f"{'PASS' if passed else 'FAIL'}  {c.id:4} {c.role:4} {c.title}")
        for note in notes:
            print(f"            note: {note}")
        if not passed:
            print(f"            {detail}")
    run_count = len(suite.CASES) - not_run
    print(f"\n{run_count - failures} of {run_count} cases passed"
          + (f"; {not_run} not run" if not_run else ""))

    vacuous = checked = 0
    if args.vacuity:
        print("\nVacuity: each case must fail with each check it cites switched off")
        for c in suite.CASES:
            if c.id in skipped:
                continue
            for name in c.defeats:
                passed, detail, notes = suite.run_case(c, cfg, adapter, disable=(name,))
                if passed and notes:
                    passed, detail = False, "note: " + notes[0]
                vacuous += passed
                checked += 1
                print(f"{'VACUOUS' if passed else 'ok':7} {c.id:4} without {name}")
                if not passed:
                    print(f"            {detail[:120]}{'...' if len(detail) > 120 else ''}")
        cases = sum(1 for c in suite.CASES if c.defeats and c.id not in skipped)
        print(f"\n{checked - vacuous} of {checked} runs fail: {cases} cases, each without "
              "each check it cites")

    for server in servers:
        server.shutdown()
    return 1 if failures or vacuous else 0


if __name__ == "__main__":
    sys.exit(main())
