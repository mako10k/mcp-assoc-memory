"""Unified application path resolution following XDG/Platformdirs.

Contract rules:
- Validate inputs and resolved paths with assert (fail-fast)
- No silent fallbacks to project workspace (e.g., ./data)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    from platformdirs import PlatformDirs
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Missing dependency 'platformdirs'. Please add it to requirements and install."
    ) from e


APP_NAME = "mcp-assoc-memory"


def _env_dir(var_name: str) -> Optional[Path]:
    val = os.getenv(var_name)
    if not val:
        return None
    # Expand ~ and env vars, make absolute
    p = Path(os.path.expandvars(os.path.expanduser(val))).resolve()
    assert str(p) != ".", f"Environment override {var_name} resolved to invalid path"  # fail-fast
    return p


def _ensure_dir(p: Path) -> Path:
    assert p.is_absolute(), f"Path must be absolute: {p}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _dirs() -> PlatformDirs:
    return PlatformDirs(appname=APP_NAME)


def get_data_dir(override: Optional[str] = None) -> Path:
    # Priority: explicit override > env > platformdirs
    if override:
        p = Path(os.path.expanduser(override)).resolve()
    else:
        p = _env_dir("MCP_AM_DATA_DIR") or Path(_dirs().user_data_dir)
    assert p.is_absolute(), f"Data dir must be absolute: {p}"
    return _ensure_dir(p)


def get_config_dir(override: Optional[str] = None) -> Path:
    if override:
        p = Path(os.path.expanduser(override)).resolve()
    else:
        p = _env_dir("MCP_AM_CONFIG_DIR") or Path(_dirs().user_config_dir)
    assert p.is_absolute(), f"Config dir must be absolute: {p}"
    return _ensure_dir(p)


def get_cache_dir(override: Optional[str] = None) -> Path:
    if override:
        p = Path(os.path.expanduser(override)).resolve()
    else:
        p = _env_dir("MCP_AM_CACHE_DIR") or Path(_dirs().user_cache_dir)
    assert p.is_absolute(), f"Cache dir must be absolute: {p}"
    return _ensure_dir(p)


def get_state_dir(override: Optional[str] = None) -> Path:
    if override:
        p = Path(os.path.expanduser(override)).resolve()
    else:
        # Prefer user_state_dir if available, fallback to data dir/state
        state = getattr(_dirs(), "user_state_dir", None)
        p = _env_dir("MCP_AM_STATE_DIR") or Path(state or (Path(_dirs().user_data_dir) / "state"))
    assert p.is_absolute(), f"State dir must be absolute: {p}"
    return _ensure_dir(p)


def get_log_dir(override: Optional[str] = None) -> Path:
    if override:
        p = Path(os.path.expanduser(override)).resolve()
    else:
        p = _env_dir("MCP_AM_LOG_DIR") or (get_state_dir() / "logs")
    assert p.is_absolute(), f"Log dir must be absolute: {p}"
    return _ensure_dir(p)


def get_database_path(file_name: str = "memory.db", data_dir_override: Optional[str] = None) -> Path:
    assert file_name.endswith(".db"), "Database file must end with .db"
    base = get_data_dir(data_dir_override)
    return base / file_name


def get_chroma_dir(data_dir_override: Optional[str] = None) -> Path:
    return _ensure_dir(get_data_dir(data_dir_override) / "chroma_db")


def get_graph_path(file_name: str = "memory_graph.pkl", data_dir_override: Optional[str] = None) -> Path:
    base = get_data_dir(data_dir_override)
    return base / file_name


def get_exports_dir(data_dir_override: Optional[str] = None) -> Path:
    return _ensure_dir(get_data_dir(data_dir_override) / "exports")


def get_imports_dir(data_dir_override: Optional[str] = None) -> Path:
    return _ensure_dir(get_data_dir(data_dir_override) / "imports")


def detect_legacy_project_data(project_root: Path) -> Tuple[bool, Path]:
    """Detect legacy ./data directory in project workspace.

    Returns (exists, path). Do not use as fallback – only for migration tooling/logging.
    """
    p = (project_root / "data").resolve()
    return p.exists(), p
