import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evidence import append, evidence_batch, package_digest, verify


def test_append_builds_chain():
    chain = append(append([], {"id": "a", "payload": "alpha"}), {"id": "b", "payload": "beta"})
    assert len(chain) == 2
    assert chain[0]["seq"] == 1
    assert chain[1]["seq"] == 2
    assert chain[1]["prev"] == chain[0]["hash"]


def test_complete_chain_passes_verification():
    chain = append(
        append(append([], {"id": "a", "payload": "alpha"}), {"id": "b", "payload": "beta"}),
        {"id": "c", "payload": "gamma"},
    )
    result = verify(chain)
    assert result["ok"] is True
    assert result["first_bad"] is None


def test_modified_entry_is_detected():
    chain = append(append([], {"id": "a", "payload": "alpha"}), {"id": "b", "payload": "beta"})
    chain[1]["entry"]["payload"] = "tampered"
    result = verify(chain)
    assert result["ok"] is False
    assert result["first_bad"] == 2


def test_package_digest_is_stable_and_content_bound():
    chain = append(append([], {"id": "a", "payload": "alpha"}), {"id": "b", "payload": "beta"})
    assert package_digest(chain) == package_digest(chain)
    changed = append(append([], {"id": "a", "payload": "ALPHA"}), {"id": "b", "payload": "beta"})
    assert package_digest(chain) != package_digest(changed)


def test_batch_keeps_packages_independent():
    first = append(append([], {"id": "a", "payload": "alpha"}), {"id": "b", "payload": "beta"})
    second = append(append([], {"id": "c", "payload": "gamma"}), {"id": "d", "payload": "delta"})
    result = evidence_batch({"pkg-a": first, "pkg-b": second})
    assert result["pkg-a"]["ok"] is True
    assert result["pkg-b"]["ok"] is True