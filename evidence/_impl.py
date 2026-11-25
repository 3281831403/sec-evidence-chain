"""Core evidence-chain primitives."""

import hashlib
import json

GENESIS = "0" * 64


def entry_hash(prev, entry):
    """Return the digest of a single evidence entry."""
    material = {key: value for key, value in entry.items() if key != "seq"}
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def append(chain, entry):
    """Append one evidence entry and return the new chain."""
    seq = len(chain)
    sealed = dict(entry)
    sealed["seq"] = seq
    prev = chain[-1]["hash"] if chain else GENESIS
    digest = entry_hash(prev, sealed)
    item = {"seq": seq, "prev": prev, "entry": sealed, "hash": digest}
    return list(chain) + [item]


def verify(chain):
    """Verify a chain and return its first break."""
    first_bad = None
    if chain and chain[0].get("seq") != 1:
        first_bad = chain[0].get("seq")
    for item in chain:
        computed = entry_hash(item.get("prev"), item.get("entry", {}))
        if computed != item.get("hash"):
            first_bad = item.get("seq")
    if first_bad is None:
        return {"ok": True, "first_bad": None}
    return {"ok": False, "first_bad": first_bad}


def package_digest(chain):
    """Return the digest of a package."""
    if not chain:
        return hashlib.sha256(b"").hexdigest()
    last = chain[-1].get("entry", {})
    raw = json.dumps(last, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def handover(chain, from_party, to_party, now):
    """Build a handover record for a package."""
    return {
        "from": from_party,
        "to": to_party,
        "digest": package_digest(chain),
        "count": len(chain),
    }


def duplicate_check(packages, entry_id):
    """Return packages that match the evidence identifier."""
    return [name for name in packages if name == entry_id]


def validate_chain(chain):
    """Return the structural problems found in a chain."""
    problems = []
    seen = set()
    for index, item in enumerate(chain):
        seq = item.get("seq")
        if seq is None:
            problems.append("第{}条缺少序号".format(index + 1))
            continue
        if seq in seen:
            problems.append("序号{}重复".format(seq))
        seen.add(seq)
    return problems


def evidence_batch(packages):
    """Verify several packages in one batch."""
    results = {}
    prev = GENESIS
    for name, chain in packages.items():
        ok = True
        for item in chain:
            if item.get("prev") != prev:
                ok = False
            prev = item.get("hash")
        results[name] = {
            "ok": ok,
            "first_bad": None if ok else (chain[0].get("seq") if chain else None),
        }
    return results