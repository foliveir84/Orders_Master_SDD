import io

from orders_master.ingestion.codes_txt_parser import parse_codes_txt


def test_parse_codes_txt_valid_file():
    content = b"1234567\n2345678\n3456789"
    file_like = io.BytesIO(content)
    result = parse_codes_txt(file_like)
    assert result == [1234567, 2345678, 3456789]


def test_parse_codes_txt_with_garbage():
    content = b"Header\n1234567\n\nInvalid123\n2345678\n   3456789   \nEnd"
    file_like = io.BytesIO(content)
    result = parse_codes_txt(file_like)
    # 1234567, 2345678, 3456789
    assert result == [1234567, 2345678, 3456789]


def test_parse_codes_txt_empty_file():
    file_like = io.BytesIO(b"")
    result = parse_codes_txt(file_like)
    assert result == []


def test_parse_codes_txt_only_invalid():
    content = b"Header\nInvalid\nMoreGarbage"
    file_like = io.BytesIO(content)
    result = parse_codes_txt(file_like)
    assert result == []


def test_parse_codes_txt_utf8_bom():
    # UTF-8 with BOM: \xef\xbb\xbf
    content = b"\xef\xbb\xbf1234567\n2345678"
    file_like = io.BytesIO(content)
    result = parse_codes_txt(file_like)
    # With BOM handling, the first line should be recognized as a digit.
    assert result == [1234567, 2345678]


def test_parse_codes_txt_from_fixture():
    with open("tests/fixtures/codigos_sample.txt", "rb") as f:
        result = parse_codes_txt(f)
    assert result == [1234567, 7654321, 1111111, 2222222, 3333333, 4444444]
