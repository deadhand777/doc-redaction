from pathlib import Path

import pytest

from doc_redaction.tool.store_data import save_as_json


class TestSaveAsJson:
    def test_save_as_json_writes_content_and_logs_path(self, tmp_path, capsys):
        target = tmp_path / "output.json"
        data = '{"key": "value"}'

        save_as_json(data, str(target))

        assert target.read_text() == data

    def test_save_as_json_overwrites_existing_file(self, tmp_path):
        target = tmp_path / "existing.json"
        target.write_text("OLD_CONTENT")
        new_data = "NEW_CONTENT"

        save_as_json(new_data, str(target))

        assert target.read_text() == new_data

    def test_save_as_json_handles_relative_and_absolute_paths(self, tmp_path, monkeypatch):
        # Relative path
        monkeypatch.chdir(tmp_path)
        rel_file = Path("relative.json")
        rel_data = "RELATIVE"

        save_as_json(rel_data, str(rel_file))
        assert rel_file.read_text() == rel_data

        # Absolute path
        abs_file = tmp_path / "absolute.json"
        abs_data = "ABSOLUTE"

        save_as_json(abs_data, str(abs_file))
        assert abs_file.read_text() == abs_data

    def test_save_as_json_raises_on_missing_or_unwritable_path(self, tmp_path, capsys):
        missing_dir = tmp_path / "does_not_exist"
        target = missing_dir / "file.json"

        with pytest.raises(OSError):
            save_as_json("DATA", str(target))

        captured = capsys.readouterr()
        assert "Saved structured output to" not in captured.err

    def test_save_as_json_raises_typeerror_on_non_string_data(self, tmp_path, capsys):
        file1 = tmp_path / "bytes.json"
        file2 = tmp_path / "dict.json"

        with pytest.raises(TypeError):
            save_as_json(b'{"a":1}', str(file1))

        with pytest.raises(TypeError):
            save_as_json({"a": 1}, str(file2))

        captured = capsys.readouterr()
        assert "Saved structured output to" not in captured.err

    def test_save_as_json_does_not_log_on_write_failure(self, tmp_path, capsys):
        # Attempt to write to a directory path should fail (IsADirectoryError/OSError)
        with pytest.raises(OSError):
            save_as_json("SHOULD_FAIL", str(tmp_path))

        captured = capsys.readouterr()
        assert "Saved structured output to" not in captured.err
