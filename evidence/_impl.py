"""Core evidence-chain primitives.

A chain is an ordered list of sealed entries. Each item carries:

* ``seq``  — one-based, gap-free sequence number,
* ``prev`` — digest of the previous item (the genesis digest for the first),
* ``entry``— the evidence payload (at least ``id`` and ``payload``),
* ``hash`` — digest covering the previous digest, the sequence number and the
  entry content, so replacing, deleting or reordering any single item breaks
  the link and is reported at that item's sequence number.
"""

import hashlib
import json

GENESIS = "0" * 64
_DIGEST_LEN = 64


def _digest(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def entry_hash(prev, entry):
    """Return the digest of a single evidence entry.

    The digest is bound to the previous entry's digest, the entry's sequence
    number and its full content. Two entries with identical content but
    different positions or predecessors therefore get different digests.
    """
    material = {"prev": prev, "entry": entry}
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True)
    return _digest(raw)


def append(chain, entry):
    """Append one evidence entry and return the new chain.

    Sequence numbers start at one and increase without gaps. The caller's
    entry is copied; the assigned ``seq`` is authoritative even if the
    supplied entry already carries one.
    """
    seq = len(chain) + 1
    sealed = dict(entry)
    sealed["seq"] = seq
    prev = chain[-1]["hash"] if chain else GENESIS
    digest = entry_hash(prev, sealed)
    item = {"seq": seq, "prev": prev, "entry": sealed, "hash": digest}
    return list(chain) + [item]


def verify(chain):
    """Verify a whole chain.

    Returns ``{"ok": bool, "first_bad": seq_or_None}``. The first break
    found — wrong sequence number, broken predecessor link, or mismatched
    entry digest — determines ``first_bad``.
    """
    expected_prev = GENESIS
    for index, item in enumerate(chain, start=1):
        seq = item.get("seq")
        if seq != index:
            return {"ok": False, "first_bad": index}
        if item.get("prev") != expected_prev:
            return {"ok": False, "first_bad": index}
        if entry_hash(item.get("prev"), item.get("entry", {})) != item.get("hash"):
            return {"ok": False, "first_bad": index}
        expected_prev = item.get("hash")
    return {"ok": True, "first_bad": None}


def package_digest(chain):
    """Return the package digest, bound to every entry's actual content.

    Each entry digest is recomputed from the predecessor link and the entry
    itself rather than trusted from storage, so any change to any entry —
    content, sequence number or link — changes the result even when the
    stored ``hash`` field is left untouched.
    """
    acc = GENESIS
    prev = GENESIS
    for item in chain:
        recomputed = entry_hash(item.get("prev", prev), item.get("entry", {}))
        raw = json.dumps(
            {"acc": acc, "prev": item.get("prev"), "hash": recomputed},
            sort_keys=True,
        )
        acc = _digest(raw)
        prev = item.get("hash")
    return acc


def handover(chain, from_party, to_party, now):
    """Build a handover record naming both parties, the time and the digest."""
    return {
        "from": from_party,
        "to": to_party,
        "time": now,
        "now": now,
        "digest": package_digest(chain),
        "count": len(chain),
    }


def duplicate_check(packages, entry_id):
    """Return the names of packages containing an evidence with ``entry_id``."""
    found = []
    for name, chain in packages.items():
        for item in chain:
            if isinstance(item, dict) and item.get("entry", {}).get("id") == entry_id:
                found.append(name)
                break
    return found


def validate_chain(chain):
    """Return structural problem descriptions for a chain.

    Covers missing sequence numbers, duplicate sequence numbers and digests
    whose length is not the 64-character SHA-256 width.
    """
    problems = []
    seen = set()
    for index, item in enumerate(chain):
        seq = item.get("seq")
        if seq is None:
            problems.append("第{}条缺少序号".format(index + 1))
        else:
            if seq in seen:
                problems.append("序号{}重复".format(seq))
            seen.add(seq)
        digest = item.get("hash")
        if not isinstance(digest, str) or len(digest) != _DIGEST_LEN:
            problems.append("第{}条摘要长度错误".format(index + 1))
    return problems


def evidence_batch(packages):
    """Verify several packages independently; one bad package cannot affect
    the result of another."""
    return {name: verify(chain) for name, chain in packages.items()}
