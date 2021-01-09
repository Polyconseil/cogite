import os
from unittest import mock

from cogite import shell


# Automated tests run on Linux (and I use Linux, too), so use Windows
# line separators in tests to make sure we do not hard-code "\n"
# anywhere.
@mock.patch("os.linesep", "\r\n")
class TestGetLines:
    def test_basics(self):
        input_ = f"line 1{os.linesep}line 2".encode("utf-8")
        assert shell.get_lines(input_) == ["line 1", "line 2"]

    def test_remote_empty_lines(self):
        input_ = f"line 1{os.linesep}{os.linesep}line 2{os.linesep}".encode("utf-8")
        assert shell.get_lines(input_) == ["line 1", "line 2"]

    def test_empty_output(self):
        assert shell.get_lines(b"") == []

    def test_handle_carriage_return(self):
        input_ = "line 1\r\nthis will not appear\rline 2\r\n".encode("utf-8")
        assert shell.get_lines(input_) == ["line 1", "line 2"]
