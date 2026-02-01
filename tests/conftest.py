"""Shared test fixtures."""

import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REPOS_DIR = FIXTURES_DIR / "repos"
GIT_CONFIGS_DIR = FIXTURES_DIR / "git_configs"


def copy_repo_fixture(fixture_name: str, dest: str) -> None:
    """Copy project files from a fixture template into the destination directory."""
    src = REPOS_DIR / fixture_name
    for item in src.iterdir():
        shutil.copy2(item, dest)


def init_git_with_config(config_name: str, dest: str) -> None:
    """Initialize a git repo and apply a config template (remote sections)."""
    subprocess.run(["git", "init"], cwd=dest, capture_output=True, check=True)
    git_config = Path(dest) / ".git" / "config"
    template = GIT_CONFIGS_DIR / config_name
    # Append remote sections to the git-init-generated config
    with open(git_config, "a") as f:
        f.write(template.read_text())


# =============================================================================
# Base fixture
# =============================================================================


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# Git repo fixtures
# =============================================================================


@pytest.fixture
def temp_git_repo(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with a GitHub SSH origin remote."""
    init_git_with_config("github_ssh", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_git_repo_https(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with a GitHub HTTPS origin remote."""
    init_git_with_config("github_https", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_git_repo_gitlab(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with a GitLab SSH origin remote."""
    init_git_with_config("gitlab_ssh", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_git_repo_bitbucket(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with a Bitbucket SSH origin remote."""
    init_git_with_config("bitbucket_ssh", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_git_repo_bitbucket_https(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with a Bitbucket HTTPS origin remote."""
    init_git_with_config("bitbucket_https", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_git_repo_with_upstream(temp_dir: str) -> Iterator[str]:
    """Create a temporary git repository with both origin and upstream remotes."""
    init_git_with_config("with_upstream", temp_dir)
    yield temp_dir


# =============================================================================
# Project file fixtures
# =============================================================================


@pytest.fixture
def temp_pyproject(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a pyproject.toml."""
    copy_repo_fixture("python_project", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_package_json(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a package.json."""
    copy_repo_fixture("npm_project", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_package_json_scoped(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a scoped npm package.json."""
    copy_repo_fixture("npm_scoped", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_cargo_toml(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a Cargo.toml."""
    copy_repo_fixture("rust_project", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_go_mod(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a go.mod."""
    copy_repo_fixture("go_project", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_gemspec(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with a .gemspec file."""
    copy_repo_fixture("ruby_project", temp_dir)
    yield temp_dir


@pytest.fixture
def temp_multi_ecosystem(temp_dir: str) -> Iterator[str]:
    """Create a temporary directory with both pyproject.toml and package.json."""
    copy_repo_fixture("multi_ecosystem", temp_dir)
    yield temp_dir
