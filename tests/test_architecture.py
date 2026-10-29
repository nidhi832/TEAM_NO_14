"""BL-34 / MPMS-NF-006: the code is layered (data -> business -> UI).

Dependencies may only point downwards:
    routes (UI)  ->  services (business)  ->  models (data)
These tests read the source files and fail if a lower layer imports a higher
one, or if the UI layer contains raw SQL.
"""
import ast
import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"


def imports_in(source):
    """Every module name imported by a piece of source code."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


def imports_of(path):
    return imports_in(path.read_text(encoding="utf-8"))


def starts_with_any(names, prefixes):
    return sorted(n for n in names
                  if any(n == p or n.startswith(p + ".") for p in prefixes))


def test_the_checker_itself_finds_violations():
    found = imports_in("from app.routes import auth\nimport flask\n")
    assert starts_with_any(found, ["app.routes"]) == [
        "app.routes", "app.routes.auth"]
    assert starts_with_any(found, ["flask"]) == ["flask"]


def test_data_layer_does_not_import_business_or_ui_layers():
    for name in ("models.py", "models_session.py"):
        bad = starts_with_any(imports_of(APP / name),
                              ["app.routes", "app.services", "app.auth_utils",
                               "flask"])
        assert bad == [], f"{name} imports {bad}"


def test_business_layer_does_not_import_ui_layer_or_flask():
    for path in sorted((APP / "services").glob("*.py")):
        bad = starts_with_any(imports_of(path), ["app.routes", "flask"])
        assert bad == [], f"{path.name} imports {bad}"


def test_auth_service_stays_pure():
    """Its docstring promises: no Flask and no database imports."""
    bad = starts_with_any(imports_of(APP / "services" / "auth_service.py"),
                          ["app", "flask", "sqlalchemy", "flask_sqlalchemy"])
    assert bad == []


# Real SQL statements only. Plain English such as a docstring "Update the
# task..." or a flash message "Delete this task?" must NOT match.
SQL_SHAPE = re.compile(
    r"^\s*(SELECT\s.+\sFROM\s|INSERT\s+INTO\s|UPDATE\s+\w+\s+SET\s"
    r"|DELETE\s+FROM\s|DROP\s+TABLE\s)", re.IGNORECASE | re.DOTALL)


def test_sql_detector_ignores_plain_english():
    assert SQL_SHAPE.match("SELECT id FROM users WHERE id = 1")
    assert SQL_SHAPE.match("update tasks set status = 'Done'")
    assert not SQL_SHAPE.match("Update a task's title and due date.")
    assert not SQL_SHAPE.match("Delete this task? Select Confirm.")


def test_ui_layer_has_no_raw_sql():
    for path in sorted((APP / "routes").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(
                    node.func, ast.Attribute) and node.func.attr == "execute":
                raise AssertionError(f"{path.name}: raw .execute() call")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not SQL_SHAPE.match(node.value), \
                    f"{path.name}: SQL text {node.value[:30]!r}"


def test_every_route_module_defines_one_blueprint():
    for path in sorted((APP / "routes").glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert source.count("Blueprint(") == 1, path.name
