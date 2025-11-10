"""Nox configuration for ARBYS testing, linting, and building."""

import nox

# Reuse existing virtualenvs
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["lint", "typecheck", "test"]

PYTHON_VERSIONS = ["3.10"]


@nox.session(python=PYTHON_VERSIONS)
def deps(session):
    """Install dependencies and dev tools."""
    session.install("uv")
    session.run("uv", "pip", "install", "-r", "requirements.txt")

    # Install dev dependencies
    session.install(
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "pytest-benchmark>=4.0.0",
        "pytest-qt>=4.2.0",
        "pytest-asyncio>=0.21.0",
        "hypothesis>=6.0.0",
    )

    # Install linting and formatting tools
    session.install(
        "black>=23.0.0",
        "ruff>=0.1.0",
        "isort>=5.12.0",
        "mypy>=1.0.0",
        "bandit>=1.7.0",
        "deptry>=0.8.0",
        "vulture>=2.10.0",
        "pyinstrument>=5.0.0",
    )


@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    """Run linting tools (ruff, isort, black)."""
    session.install("ruff", "isort", "black")

    # Ruff check and auto-fix
    session.run("ruff", "check", "--fix", ".")

    # Isort
    session.run("isort", ".")

    # Black check (will fail if formatting needed)
    session.run("black", "--check", ".")


@nox.session(python=PYTHON_VERSIONS)
def format(session):
    """Format code with black and isort."""
    session.install("black", "isort")
    session.run("isort", ".")
    session.run("black", ".")


@nox.session(python=PYTHON_VERSIONS)
def typecheck(session):
    """Run mypy type checking."""
    session.install("mypy")
    session.run("mypy", "src", "gui", "onboarding", "tests", "--ignore-missing-imports")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run pytest with coverage."""
    session.install("-r", "requirements.txt")
    session.install(
        "pytest",
        "pytest-cov",
        "pytest-qt",
        "pytest-asyncio",
        "hypothesis",
    )

    session.run(
        "pytest",
        "--cov=src",
        "--cov=gui",
        "--cov=onboarding",
        "--cov-report=xml",
        "--cov-report=term",
        "--cov-report=html",
        "tests",
    )


@nox.session(python=PYTHON_VERSIONS)
def bench(session):
    """Run performance benchmarks."""
    session.install("-r", "requirements.txt")
    session.install("pytest", "pytest-benchmark")

    session.run("pytest", "tests/perf", "--benchmark-only", "-v")


@nox.session(python=PYTHON_VERSIONS)
def sec(session):
    """Run security checks with bandit."""
    session.install("bandit")
    session.run("bandit", "-r", "src", "-q", "-f", "json", "-o", "bandit-report.json")


@nox.session(python=PYTHON_VERSIONS)
def hygiene(session):
    """Run code hygiene checks (deptry, vulture)."""
    session.install("deptry", "vulture")

    # Check for unused/missing dependencies
    session.run("deptry", ".", "--json", "--output", "deptry-report.json")

    # Find dead code (with whitelist for dynamic/test/framework usage)
    session.run("vulture", ".", ".vulture_whitelist.py", "--min-confidence", "80")


@nox.session(python=PYTHON_VERSIONS)
def all(session):
    """Run all checks (lint, typecheck, test, sec, hygiene)."""
    session.install("-r", "requirements.txt")
    session.install(
        "pytest",
        "pytest-cov",
        "pytest-qt",
        "pytest-asyncio",
        "hypothesis",
        "black",
        "ruff",
        "isort",
        "mypy",
        "bandit",
        "deptry",
        "vulture",
    )

    # Run in order
    lint(session)
    typecheck(session)
    test(session)
    sec(session)
    hygiene(session)
