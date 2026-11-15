"""Testes do núcleo menu-reversa-openclaude.py.

Execução:
    python3 tests/test_menu_reversa_openclaude.py
    python3 -m unittest discover -s tests -p "test_*.py"
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "menu-reversa-openclaude.py"
WRAPPER_SH = REPO_ROOT / "bin" / "install.sh"


def load_core():
    spec = importlib.util.spec_from_file_location("menu_reversa_openclaude", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def symlink_supported() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.symlink("target", os.path.join(tmp, "link"))
            return True
        except (OSError, NotImplementedError):
            return False


def write_skill(skills_root: Path, name: str, description: str = "Descrição.") -> Path:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return skill_file


def make_fixture(root: Path) -> Path:
    skills = root / ".agents" / "skills"
    write_skill(skills, "reversa-scout")
    write_skill(skills, "reversa-architect")
    write_skill(skills, "reversa")
    write_skill(skills, "impeccable")
    return skills


def run_cli(cwd: Path, *args, stdin=None, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        stdin=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class CoreUnitTests(unittest.TestCase):
    def test_find_skill_dirs_only_reversa(self):
        core = load_core()
        with tempfile.TemporaryDirectory() as tmp:
            skills = make_fixture(Path(tmp))
            names = core.find_skill_dirs(skills)
        self.assertEqual(names, ["reversa", "reversa-architect", "reversa-scout"])

    def test_dirs_equal(self):
        core = load_core()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a = base / "a"
            b = base / "b"
            write_skill(a, "x")
            shutil.copytree(a, b)
            self.assertTrue(core.dirs_equal(a, b))
            (b / "x" / "SKILL.md").write_text("mudou", encoding="utf-8")
            self.assertFalse(core.dirs_equal(a, b))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def oc_dir(self):
        return self.root / ".openclaude" / "skills"

    def test_install_creates_correct_symlinks(self):
        result = run_cli(self.root, "install", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        link = self.oc_dir() / "reversa-scout"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../../.agents/skills/reversa-scout")
        self.assertTrue((link / "SKILL.md").is_file())
        self.assertFalse((self.oc_dir() / "impeccable").exists())

    def test_install_is_idempotent(self):
        run_cli(self.root, "install", "--yes")
        second = run_cli(self.root, "install", "--yes")
        self.assertIn("Criados: 0", second.stdout)
        self.assertIn("OK (existente)", second.stdout)

    def test_conflict_replaced_with_backup(self):
        conflict = self.oc_dir() / "reversa-scout"
        conflict.mkdir(parents=True)
        (conflict / "old.txt").write_text("antigo", encoding="utf-8")
        result = run_cli(self.root, "install", "--yes")
        self.assertIn("Conflito em reversa-scout", result.stdout)
        self.assertTrue(conflict.is_symlink())
        backups = list((self.root / ".openclaude").glob("skills.bak.*"))
        self.assertEqual(len(backups), 1)

    def test_sync_removes_orphan(self):
        run_cli(self.root, "install", "--yes")
        orphan = self.oc_dir() / "reversa-old"
        os.symlink("../../.agents/skills/reversa-old", orphan)
        result = run_cli(self.root, "sync", "--yes")
        self.assertIn("Órfão detectado: reversa-old", result.stdout)
        self.assertFalse(orphan.is_symlink())
        self.assertFalse(orphan.exists())

    def test_copy_mode_creates_real_dirs(self):
        result = run_cli(self.root, "install", "--yes", "--copy")
        self.assertEqual(result.returncode, 0, result.stderr)
        dest = self.oc_dir() / "reversa-architect"
        self.assertFalse(dest.is_symlink())
        self.assertTrue((dest / "SKILL.md").is_file())
        second = run_cli(self.root, "install", "--yes", "--copy")
        self.assertIn("OK (existente)", second.stdout)

    def test_global_scope_uses_absolute_targets(self):
        home = self.root / "home"
        home.mkdir()
        env = dict(os.environ, HOME=str(home))
        result = run_cli(self.root, "install", "--yes", "--global", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        link = home / ".openclaude" / "skills" / "reversa"
        self.assertTrue(link.is_symlink())
        self.assertTrue(os.readlink(link).startswith("/"))

    def test_dry_run_changes_nothing(self):
        result = run_cli(self.root, "install", "--dry-run", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.oc_dir().exists())

    def test_no_yes_defaults_to_cancel(self):
        result = run_cli(self.root, "install", stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Operação cancelada", result.stdout)
        links = list(self.oc_dir().iterdir()) if self.oc_dir().exists() else []
        self.assertEqual(links, [])

    def test_missing_skills_root_errors(self):
        result = run_cli(self.root, "install", "--yes", "--skills-root", ".does-not-exist")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERRO", result.stderr + result.stdout)

    def test_determinism_across_runs(self):
        run_cli(self.root, "install", "--yes")
        first = {p.name: os.readlink(p) for p in sorted(self.oc_dir().iterdir())}
        shutil.rmtree(self.oc_dir())
        run_cli(self.root, "install", "--yes")
        second = {p.name: os.readlink(p) for p in sorted(self.oc_dir().iterdir())}
        self.assertEqual(first, second)


@unittest.skipUnless(symlink_supported(), "symlinks indisponíveis neste sistema")
@unittest.skipUnless(shutil.which("bash"), "bash indisponível")
class WrapperTests(unittest.TestCase):
    def test_bash_wrapper_runs_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_fixture(root)
            result = subprocess.run(
                ["bash", str(WRAPPER_SH), "--yes"],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / ".openclaude" / "skills" / "reversa").is_symlink())


if __name__ == "__main__":
    unittest.main(verbosity=2)
