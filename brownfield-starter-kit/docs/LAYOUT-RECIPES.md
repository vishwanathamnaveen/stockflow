# Layout recipes: fitting your repo onto what the tools read

The tools are written in Python; the code they read can be in any of these languages:

| Language | Symbols, fields, annotations | Adapter |
|---|---|---|
| Python | exact (`ast`) | `tools/context/lang_python.py` |
| Java, Kotlin, Groovy, Scala, C#, TypeScript / TSX, JavaScript, Go, Ruby, PHP, Rust, Swift, C, C++ | tree-sitter (the grammars graphify installs) | `tools/context/lang_treesitter.py` |

Framework idioms (HTTP routes, event publishing and handling, calls to other services, tables, configuration keys)
come from **convention presets** (`tools/context/conventions.py`), detected per service from the code. Do not move
product code to fit the kit: describe the repo instead, in two files.

You rarely write them by hand: `install.py <application folder>` runs `tools/context/discover.py`, which finds the
build units (Maven / Gradle modules, npm workspaces, .NET projects, Go modules, Python packages with tests), tells
containers (parent POMs, workspace roots) from services and shared libraries (depended on by other units), attaches
.NET test projects to their project, proposes test commands and coverage reports, and finds QA test-case folders and
business-rule tables. The recipes below show what it writes, and what to correct when a repo is unusual. Git is
optional throughout.

`.claude/config.yaml`:

```yaml
brownfield:
  layout:
    services_root: services     # default folder of service <name>: <services_root>/<name>
    common_root: libs/common    # shared library, graphed as the extra target "common"; null = none
    common_package: null        # its source folder; null = its only Python package, else the folder itself
    exclude: []                 # repo-relative globs left out of every code graph (generated code, fixtures)
  business_rules: {files: [docs/business-rules.md]}
  test_cases: []                # QA test cases: Zephyr / Xray JSON, Gherkin, CSV (see the last section)
```

`config/services.yaml`:

```yaml
services:
  <name>:
    path: <folder>              # default <services_root>/<name>; "." = the service is the repo root
    package: <source folder>    # Python package, src/main/java, src, ... (optional)
    owner: <team>               # or TBD (forces guarded)
    description: <one business-language line, written by a human>
    test_command: "<runs the tests with coverage>"   # omit for Python: pytest --cov runs by default
    coverage: {format: jacoco|cobertura|lcov|go|istanbul|coverage-py, path: <report, relative to the service>}
    conventions: [auto]         # or preset names; custom presets in config/conventions.yaml
    aliases: []                 # other names callers use for it (URL hosts, Feign client names)
    exclude: []                 # globs (repo-relative) left out of its graph
```

Check what the tools see after any change to these files:

```bash
python tools/context/conventions.py          # languages, presets, routes / handlers / calls / tables per service
python tools/context/test_cases.py           # QA test cases loaded per source
python scripts/run_tests.py <service>        # without test_command: prints a suggested one
```

## A. Python services monorepo (the reference layout)

```
services/orders/orders_service/   services/orders/tests/
services/billing/billing_service/ services/billing/tests/
libs/common/shop_common/          libs/common/tests/
```

Defaults work (`package: orders_service`). If the shared library has more than one package, set `common_package`.

## B. Python services under another root, no shared library

```yaml
layout: {services_root: apps, common_root: null}
```

## C. One Python application, package and tests in one folder

```
shop/shop/    shop/tests/
```

`layout: {services_root: ".", common_root: null}` and `shop: {package: shop, ...}`. The overall graph and the `shop`
graph are separate targets.

## D. Python `src/` layout

`src/shop/` + `tests/` at the root: `services_root: "."`, service `src` with `package: shop` builds graphs and
manifests; per-test coverage needs the tests inside the service folder (`src/tests/`), or a `test_command`:

```yaml
shop:
  path: "."
  package: src/shop
  test_command: "python -m pytest tests --cov=src/shop --cov-context=test --cov-report=json:coverage.json"
  coverage: {format: coverage-py, path: coverage.json}
```

## E. A single Java / Kotlin service (Maven or Gradle) at the repo root

```
pom.xml   src/main/java/com/acme/...   src/test/java/com/acme/...   src/main/resources/application.yml
```

```yaml
# .claude/config.yaml
brownfield:
  layout: {services_root: ".", common_root: null}
# config/services.yaml
services:
  orders:
    path: "."
    package: src/main/java
    owner: orders-team
    description: Customer orders and order status.
    test_command: "mvn -q -B test jacoco:report"          # Gradle: ./gradlew test jacocoTestReport
    coverage: {format: jacoco, path: target/site/jacoco/jacoco.xml}
    junit: "target/surefire-reports/*.xml"
```

No JaCoCo plugin in the POM? Run it from the command line without editing the build:
`mvn -q -B org.jacoco:jacoco-maven-plugin:0.8.12:prepare-agent test org.jacoco:jacoco-maven-plugin:0.8.12:report`.
Spring MVC, Feign, RestTemplate / WebClient, Kafka / RabbitMQ / JMS listeners and JPA `@Table` / `@Entity` are
detected automatically (`spring`, `spring-messaging`, `jpa`); JAX-RS / Quarkus and Micronaut likewise. Verified on a
Java 17 / Spring Boot 3 service: 13 endpoints, 7 tables, JaCoCo coverage, 41 Zephyr test cases linked.

## F. Maven / Gradle multi-module, or several services in one repo

```
orders-service/pom.xml   orders-service/src/main/java/...
billing-service/pom.xml  billing-service/src/main/java/...
shared-lib/src/main/java/...
```

```yaml
layout: {services_root: ".", common_root: shared-lib, common_package: src/main/java}
services:
  orders:  {path: orders-service,  package: src/main/java, test_command: "mvn -q -B test jacoco:report", coverage: {format: jacoco, path: target/site/jacoco/jacoco.xml}, ...}
  billing: {path: billing-service, package: src/main/java, ...}
```

Run each service's command from its own folder (default), or from the reactor root with `test_cwd: ".."` and
`-pl <module>`. Calls between services are found from Feign clients (`@FeignClient(name = "billing")`) and from URLs
whose host is a service name or one of its `aliases`.

## G. .NET (ASP.NET Core)

```yaml
orders:
  path: src/Orders.Api
  test_command: 'dotnet test ../../tests/Orders.Tests --collect:"XPlat Code Coverage" --results-directory TestResults'
  coverage: {format: cobertura, path: TestResults/*/coverage.cobertura.xml}
```

`[Route("api/[controller]")]` + `[HttpGet("{id}")]` routes and EF Core `[Table]` are detected (`aspnet`, `efcore`).

## H. Node / TypeScript (NestJS, Express) and Go

```yaml
web:   {path: apps/web, package: src, test_command: "npx jest --coverage --coverageReporters=lcov", coverage: {format: lcov, path: coverage/lcov.info}}
stock: {path: services/stock, test_command: "go test ./... -coverprofile=cover.out", coverage: {format: go, path: cover.out}}
```

NestJS decorators, Express / gin / echo / chi / net/http call-style routes (`router.get('/x', handler)`), kafkajs
publishers and TypeORM entities are detected. Most JS coverage tools leave lcov's `TN:` (test name) empty, so expect
line coverage plus static test references rather than per-test selection.

## I. A framework the presets do not know

Symptom: `conventions.py` shows 0 routes for a service that has endpoints (or no handlers / calls). Write a preset in
`config/conventions.yaml` (annotated example in that file) and name it in the service's `conventions:` or give it a
`detect` marker. Rules are regular expressions over a symbol's own annotations (`decorator`), its class's annotations
(`class_decorator`), or the source text (`source`). `python tools/context/conventions.py --list` shows the built-ins.

## Coverage formats

| Format | Producers | Per-test data |
|---|---|---|
| `coverage-py` | pytest-cov (`--cov-context=test`) | yes |
| `lcov` | Jest, Vitest, nyc / c8, gcov, grcov, simplecov-lcov | when the report has `TN:` records |
| `jacoco` | Maven / Gradle JaCoCo | no |
| `cobertura` | coverlet (`dotnet test`), gcovr, pytest-cov XML, Istanbul | no |
| `go` | `go test -coverprofile` | no |
| `istanbul` | `coverage-final.json` | no |

Without per-test data the manifest still gets line coverage (`test_evidence`), lists the tests that reference the
changed code (`tests.static_test_refs`), and says so as a minor unknown. A report older than the test run is never
used.

## Cross-service edges

| Edge | Found from |
|---|---|
| API | `contracts/openapi/<service>.json\|yaml` (or the service's `openapi:`); without one, the code's routes (`source: code`) |
| REST call | Feign / declarative clients, RestTemplate / WebClient / HttpClient / axios / `http.Get` calls whose URL host is a service, `ServiceClient` in Python `clients.py` |
| event published | KafkaTemplate / RabbitTemplate / JmsTemplate / StreamBridge `send`, NestJS `emit`, kafkajs `producer.send`, Python `publish_event(topic=...)`; topic constants are resolved in the same file |
| event handled | `@KafkaListener` / `@RabbitListener` / `@JmsListener` / `@SqsListener`, `@EventPattern`, Python `HANDLERS = {...}` |
| subscription routing | `config/subscriptions.yaml` when the repo has a routing file; otherwise the handler annotations are the subscriptions |
| topics | `contracts/events.yaml` |

Communication the presets do not see (gRPC stubs, an in-house client) leaves the service graph without that edge:
manifests then report cross-service consumers as "not found" (never "absent"), and owners of other services confirm
impact (rule 40.12). A custom preset closes the gap.

## QA test cases in another repository

```yaml
brownfield:
  test_cases:
    - {path: ../orders-qa/testcases, format: zephyr-json}   # one JSON per case, or an export array
    - {path: ../orders-qa/features, format: gherkin}        # scenario tags carry the key, `# Covers:` the links
    - {path: qa/xray-export.csv, format: csv}               # columns found by header (Key, Name, Covers, ...)
```

Each case is linked to code through its traceability field (`Covers`: endpoints, classes, `Class.method`,
`Class.field`) or, without one, through endpoints named in its steps. The manifest lists `tests.test_cases.direct`
(review the assertions) and `.transitive` (regression run); the same key in two formats is one case. Cases are read,
never followed (rule 31), and the QA repository is never edited by `/implement-change`.
