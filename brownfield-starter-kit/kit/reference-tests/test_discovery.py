"""Layout discovery from an application folder (tools/context/discover.py).

    python -m pytest tools/context/reference-tests/test_discovery.py -q

Portable: every repository shape is built under tmp_path. No git anywhere (git is optional).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import discover  # noqa: E402


def put(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


JAVA_PKG = "src/main/java/com/acme/{m}/deep/er/still/{c}.java"
POM = "<project><artifactId>{a}</artifactId>{deps}</project>"


def maven_multi(root: Path) -> Path:
    return put(root, {
        "pom.xml": "<project><artifactId>parent</artifactId><packaging>pom</packaging>"
                   "<modules><module>orders-service</module><module>billing-service</module><module>shared-lib</module></modules></project>",
        "orders-service/pom.xml": POM.format(a="orders-service", deps="<dependencies><dependency><artifactId>shared-lib</artifactId></dependency></dependencies>"),
        "orders-service/" + JAVA_PKG.format(m="orders", c="OrdersApp"): "@SpringBootApplication public class OrdersApp { public static void main(String[] a) {} }",
        "orders-service/src/test/java/com/acme/orders/OrdersAppTest.java": "class OrdersAppTest {}",
        "billing-service/pom.xml": POM.format(a="billing-service", deps="<dependencies><dependency><artifactId>shared-lib</artifactId></dependency></dependencies>"),
        "billing-service/" + JAVA_PKG.format(m="billing", c="BillingApp"): "@SpringBootApplication class BillingApp {}",
        "shared-lib/pom.xml": POM.format(a="shared-lib", deps=""),
        "shared-lib/" + JAVA_PKG.format(m="shared", c="Money"): "public record Money(long cents) {}",
        "docs/business-rules.md": "| ID | Rule | Where |\n|---|---|---|\n| BR-1 | a | `OrdersApp` |\n| BR-2 | b | `BillingApp` |\n",
    })


def test_d1_maven_multi_module_with_shared_library(tmp_path):
    p = discover.plan(maven_multi(tmp_path))
    by_path = {s["path"]: s for s in p["services"]}
    assert set(by_path) == {"orders-service", "billing-service"}            # the parent POM is a container
    assert p["common"]["path"] == "shared-lib" and p["common"]["package"] == "src/main/java"
    assert set(p["common"]["used_by"]) == {"billing-service", "orders-service"}
    orders = by_path["orders-service"]
    assert orders["name"] == "orders" and orders["package"] == "src/main/java" and orders["language"] == "java"
    assert orders["test_command"].startswith("mvn -q -B -pl orders-service -am ") and orders["test_cwd"] == ".."
    assert "jacoco-maven-plugin" in orders["test_command"]                 # no plugin in the POM: run it from the CLI
    assert orders["coverage"] == {"format": "jacoco", "path": "target/site/jacoco/jacoco.xml"}
    assert p["business_rules"] == ["docs/business-rules.md"] and p["git"] is False


def test_d2_npm_workspace_dotnet_go_and_qa_in_one_folder(tmp_path):
    put(tmp_path, {
        "package.json": json.dumps({"name": "mono", "private": True, "workspaces": ["apps/*", "packages/*"]}),
        "apps/web/package.json": json.dumps({"name": "web", "dependencies": {"@acme/common": "*", "@nestjs/core": "1"},
                                             "devDependencies": {"jest": "29"}, "scripts": {"test": "jest"}}),
        "apps/web/src/main.ts": "async function bootstrap() { await NestFactory.create(AppModule); }",
        "apps/web/src/orders.controller.ts": "export class OrdersController {}",
        "packages/common/package.json": json.dumps({"name": "@acme/common"}),
        "packages/common/src/money.ts": "export const cents = 1;",
        "dotnet/Orders.Api/Orders.Api.csproj": "<Project Sdk=\"Microsoft.NET.Sdk.Web\"></Project>",
        "dotnet/Orders.Api/Program.cs": "var app = WebApplication.CreateBuilder(args).Build();",
        "dotnet/Orders.Api.Tests/Orders.Api.Tests.csproj": '<Project><ItemGroup><PackageReference Include="xunit" />'
                                                           '<ProjectReference Include="..\\Orders.Api\\Orders.Api.csproj" /></ItemGroup></Project>',
        "dotnet/Orders.Api.Tests/OrdersTests.cs": "public class OrdersTests {}",
        "stock/go.mod": "module github.com/acme/stock\n",
        "stock/main.go": "package main\nfunc main() {}\n",
        "qa/features/orders.feature": "Feature: Orders\n  @ORD-T1\n  Scenario: x\n",
        "qa/cases/ORD-T2.json": json.dumps({"key": "ORD-T2", "name": "y", "testScript": {"steps": []}}),
        "qa/tools/score.py": "print(1)\n",
    })
    p = discover.plan(tmp_path)
    by_path = {s["path"]: s for s in p["services"]}
    assert set(by_path) == {"apps/web", "dotnet/Orders.Api", "stock"}      # workspace root and the test project: not services
    assert p["common"]["path"] == "packages/common"                         # the workspace package web depends on
    web = by_path["apps/web"]
    assert web["package"] == "src" and web["coverage"] == {"format": "lcov", "path": "coverage/lcov.info"}
    api = by_path["dotnet/Orders.Api"]
    assert "dotnet test ../../dotnet/Orders.Api.Tests/Orders.Api.Tests.csproj" in api["test_command"]
    assert by_path["stock"]["coverage"]["format"] == "go"
    assert sorted((t["path"], t["format"]) for t in p["test_cases"]) == [("qa/cases", "zephyr-json"), ("qa/features", "gherkin")]
    assert p["unassigned_source"] == {"python": 1}                         # qa/tools/score.py: reported, not a service


def test_d3_python_services_without_build_files(tmp_path):
    put(tmp_path, {
        "requirements.txt": "fastapi\n",
        "services/orders/orders_service/__init__.py": "", "services/orders/orders_service/api.py": "from shop_common import db\n",
        "services/orders/tests/test_api.py": "def test_x(): pass\n",
        "services/billing/billing_service/__init__.py": "", "services/billing/billing_service/api.py": "import shop_common\n",
        "services/billing/tests/test_api.py": "def test_y(): pass\n",
        "libs/common/shop_common/__init__.py": "", "libs/common/shop_common/db.py": "def app(): return FastAPI()\n",
        "libs/common/tests/test_db.py": "def test_z(): pass\n",
        "scripts/run_local.py": "print(1)\n",
    })
    p = discover.plan(tmp_path)
    assert {s["path"]: s["package"] for s in p["services"]} == {"services/orders": "orders_service",
                                                                "services/billing": "billing_service"}
    assert all("test_command" not in s for s in p["services"])               # Python default: pytest --cov per test
    assert p["common"]["path"] == "libs/common" and p["common"]["package"] == "shop_common"   # an app factory is not a main


def test_d4_a_single_application_without_any_build_file(tmp_path):
    put(tmp_path, {"app/handlers.go": "package app\n", "app/routes.go": "package app\n"})
    p = discover.plan(tmp_path)
    assert [(s["path"], s["language"]) for s in p["services"]] == [(".", "go")] and "gap" in p["services"][0]


def test_d5_write_registry_and_layout_keeps_comments(tmp_path):
    root = maven_multi(tmp_path)
    put(root, {".claude/config.yaml": "brownfield:\n  layout:                # where\n    services_root: services  # c1\n"
                                      "    common_root: libs/common  # c2\n    common_package: null\n"
                                      "  business_rules:\n    files: [docs/business-rules.md]\n    id_pattern: 'BR-\\d+'\n"
                                      "  test_cases: []                       # external QA\n"})
    p = discover.plan(root)
    written = discover.write(root, p)
    assert written[0] == "config/services.yaml"
    reg = (root / "config" / "services.yaml").read_text(encoding="utf-8")
    assert "  orders:\n    path: orders-service\n    package: src/main/java\n    owner: TBD" in reg
    assert "test_cwd: .." in reg and "coverage: {format: jacoco, path: target/site/jacoco/jacoco.xml}" in reg
    cfg = (root / ".claude" / "config.yaml").read_text(encoding="utf-8")
    assert 'services_root: "."  # c1' in cfg and "common_root: shared-lib  # c2" in cfg
    assert "common_package: src/main/java" in cfg
    assert discover.write(root, p) == []                                     # an existing registry is kept
    assert discover.write(root, p, force=True)[0] == "config/services.yaml"
