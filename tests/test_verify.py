from var_runner.verify import normalize_newlines, sha256_hex, verify_bytes


def test_identical():
    r = verify_bytes(b"abc", b"abc")
    assert r.ok and bool(r) and r.first_diff_offset is None
    assert r.local_sha256 == r.remote_sha256 == sha256_hex(b"abc")


def test_mismatch_middle():
    r = verify_bytes(b"abcdef", b"abXdef")
    assert not r.ok and r.first_diff_offset == 2


def test_mismatch_truncation():
    r = verify_bytes(b"abcdef", b"abc")
    assert not r.ok and r.first_diff_offset == 3
    assert "6B" in r.detail and "3B" in r.detail


def test_normalize_newlines_is_diagnostic_only():
    assert normalize_newlines(b"a\r\nb\rc\n") == b"a\nb\nc\n"
    # CRLF-mangled remote must still FAIL strict verification
    assert not verify_bytes(b"a\nb\n", b"a\r\nb\r\n").ok
