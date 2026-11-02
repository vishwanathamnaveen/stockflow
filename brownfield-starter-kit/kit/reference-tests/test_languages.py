"""Any-language support: adapters, convention presets, coverage formats, QA test cases (docs/.../TEST-CASES.md, L*).

    python -m pytest tools/context/reference-tests/test_languages.py -q

Self-contained: every fixture is inline source text or a file under tmp_path, so these tests pass in any repository
the kit is installed in (they need the tree-sitter grammars graphify installs, nothing else).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import common  # noqa: E402
import conventions  # noqa: E402
import coverage_formats  # noqa: E402
import lang_python  # noqa: E402
import lang_treesitter as ts  # noqa: E402
import test_cases as qa  # noqa: E402

JAVA_CONTROLLER = '''package com.acme.orders;

import org.springframework.web.bind.annotation.*;

/** Orders API. */
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {
    private final OrderService orderService;

    @PostMapping
    public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
        return orderService.place(request);
    }

    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> get(@PathVariable Long id) {
        return ResponseEntity.ok(orderService.find(id));
    }

    @RequestMapping(value = "/{id}/cancel", method = RequestMethod.POST)
    public void cancel(@PathVariable Long id) { orderService.cancel(id); }
}
'''
JAVA_SERVICE = '''package com.acme.orders;

@Service
public class OrderService {
    private static final String TOPIC = "order.placed";
    private final KafkaTemplate<String, Object> kafkaTemplate;

    /** Places an order (BR-07). */
    public OrderResponse place(CreateOrderRequest request) {
        Order order = new Order();
        order.setShipDate(request.shipDate());
        kafkaTemplate.send(TOPIC, order);
        return null;
    }

    @KafkaListener(topics = "payment.settled", groupId = "orders")
    public void onPaymentSettled(String payload) { }
}
'''
JAVA_ENTITY = '''package com.acme.orders;

@Entity
@Table(name = "orders")
@Getter @Setter
public class Order {
    @Id private Long id;
    private LocalDate shipDate;
    @Enumerated(EnumType.STRING) private OrderStatus status;
}
'''
JAVA_ENUM = '''package com.acme.orders;
public enum OrderStatus { NEW, PAID, SHIPPED }
'''
JAVA_RECORD = '''package com.acme.orders;
public record CreateOrderRequest(String sku, int quantity, LocalDate shipDate) {}
'''
FEIGN = '''package com.acme.orders;
@FeignClient(name = "inventory")
public interface InventoryClient {
    @GetMapping("/stock/{sku}")
    StockLevel stock(@PathVariable String sku);
}
'''
CSHARP = '''using Microsoft.AspNetCore.Mvc;
[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase {
    private readonly IOrderRepo _repo;
    [HttpGet("{id}")]
    public ActionResult<OrderDto> Get(int id) => Ok(_repo.Find(id));
    [HttpPost]
    public IActionResult Create([FromBody] CreateOrder cmd) { return Ok(); }
}
'''
NEST = '''import { Controller, Get, Post, Body, Param } from '@nestjs/common';
@Controller('orders')
export class OrdersController {
  constructor(private readonly svc: OrdersService) {}
  @Get(':id')
  find(@Param('id') id: string): Promise<OrderDto> { return this.svc.find(id); }
  @Post()
  create(@Body() dto: CreateOrderDto): OrderDto { return this.svc.create(dto); }
}
'''
EXPRESS = '''const express = require('express');
const router = express.Router();
function listItems(req, res) { res.json([]); }
const getItem = async (req, res) => { res.json({}); };
router.get('/items', listItems);
router.get('/items/:id', auth, getItem);
module.exports = router;
'''
GO = '''package orders
import "github.com/gin-gonic/gin"
// Order is a customer order.
type Order struct {
    ID       int
    ShipDate string
}
// GetOrder returns one order.
func (h *Handler) GetOrder(c *gin.Context) { c.JSON(200, h.repo.Find(c.Param("id"))) }
func Routes(r *gin.Engine, h *Handler) { r.GET("/orders/:id", h.GetOrder) }
'''


def symbols_of(text: str, language: str, file: str, service: str = "svc") -> list[common.Symbol]:
    out = lang_python.extract(text) if language == "python" else ts.extract(text, language)
    return [common.Symbol(service, file, s["qualname"], s["kind"], s["start"], s["end"], set(s["refs"]),
                          set(s["strings"]), list(s["decorators"]), s["signature"], s["docstring"], list(s["bases"]),
                          dict(s["fields"]), language) for s in out["symbols"]]


def routes(text: str, language: str, presets: list[str], file: str = "src/X.java") -> dict[str, tuple]:
    syms = symbols_of(text, language, file)
    rules = conventions.rules(presets, common.ROOT, "routes")
    by_q = {s.qualname: s for s in syms}
    out = {}
    for s in syms:
        if s.kind == "class":
            continue
        owner = by_q.get(s.qualname.rsplit(".", 1)[0]) if "." in s.qualname else None
        r = conventions.decorator_route(s, owner, text, rules)
        if r:
            out[s.qualname] = r
    for found in conventions.source_routes(text, rules):
        out[found["handler"]] = (found["method"], found["path"])
    return out


# --------------------------------------------------------------------------- L1 adapters


def test_l1_java_symbols_fields_decorators_and_docs():
    syms = {s.qualname: s for s in symbols_of(JAVA_CONTROLLER, "java", "src/OrderController.java")}
    assert set(syms) == {"OrderController", "OrderController.create", "OrderController.get", "OrderController.cancel"}
    cls = syms["OrderController"]
    assert cls.kind == "class" and cls.decorators[:2] == ["RestController", 'RequestMapping("/api/v1/orders")']
    assert cls.docstring == "Orders API." and cls.fields == {"orderService": "OrderService"}
    assert syms["OrderController.create"].signature == "public OrderResponse create(CreateOrderRequest request)"
    assert syms["OrderController.create"].start == 11          # leading annotation included


def test_l1_records_enums_and_entities_expose_their_fields():
    assert list(symbols_of(JAVA_RECORD, "java", "R.java")[0].fields) == ["sku", "quantity", "shipDate"]
    assert list(symbols_of(JAVA_ENUM, "java", "E.java")[0].fields) == ["NEW", "PAID", "SHIPPED"]
    entity = symbols_of(JAVA_ENTITY, "java", "Order.java")[0]
    assert set(entity.fields) == {"id", "shipDate", "status"}


def test_l1_accessors_read_as_the_property_they_touch():
    """Lombok / JavaBeans: setShipDate(...) references the field shipDate (field lineage works without getters)."""
    place = next(s for s in symbols_of(JAVA_SERVICE, "java", "S.java") if s.name == "place")
    assert {"setShipDate", "shipDate"} <= place.refs and "order.placed" not in place.strings   # TOPIC is a constant


@pytest.mark.parametrize("language, text, expected", [
    ("csharp", CSHARP, {"OrdersController", "OrdersController.Get", "OrdersController.Create"}),
    ("typescript", NEST, {"OrdersController", "OrdersController.constructor", "OrdersController.find",
                          "OrdersController.create"}),
    ("javascript", EXPRESS, {"listItems", "getItem"}),
    ("go", GO, {"Order", "Handler.GetOrder", "Routes"}),
])
def test_l1_other_languages(language, text, expected):
    assert {s.qualname for s in symbols_of(text, language, "f")} == expected


def test_l1_go_receivers_and_docs():
    syms = {s.qualname: s for s in symbols_of(GO, "go", "orders.go")}
    assert syms["Order"].fields == {"ID": "int", "ShipDate": "string"}
    assert syms["Handler.GetOrder"].docstring == "GetOrder returns one order."


def test_l1_python_adapter_is_the_reference_ast():
    syms = symbols_of('"""m"""\nclass A(B):\n    x: int\n    def f(self) -> str:\n        return "t"\n', "python", "a.py")
    assert [(s.qualname, s.kind) for s in syms] == [("A", "class"), ("A.f", "method")]
    assert syms[0].fields == {"x": "int"} and syms[1].signature == "def f(self) -> str" and "t" in syms[1].strings


def test_l1_unparsable_file_yields_nothing_not_a_guess():
    assert lang_python.extract("def (:\n")["symbols"] == []


# --------------------------------------------------------------------------- L2 conventions


def test_l2_spring_routes_with_class_prefix_and_request_mapping():
    r = routes(JAVA_CONTROLLER, "java", ["spring"])
    assert r == {"OrderController.create": ("POST", "/api/v1/orders"),
                 "OrderController.get": ("GET", "/api/v1/orders/{id}"),
                 "OrderController.cancel": ("POST", "/api/v1/orders/{id}/cancel")}


def test_l2_aspnet_controller_token_and_nest_params():
    assert routes(CSHARP, "csharp", ["aspnet"]) == {"OrdersController.Get": ("GET", "/api/Orders/{id}"),
                                                    "OrdersController.Create": ("POST", "/api/Orders")}
    assert routes(NEST, "typescript", ["nestjs"]) == {"OrdersController.find": ("GET", "/orders/{id}"),
                                                      "OrdersController.create": ("POST", "/orders")}


def test_l2_call_style_routes_name_their_handler():
    assert routes(EXPRESS, "javascript", ["express"]) == {"listItems": ("GET", "/items"), "getItem": ("GET", "/items/{id}")}
    assert routes(GO, "go", ["go-http"]) == {"h.GetOrder": ("GET", "/orders/{id}")}


def test_l2_fastapi_keeps_the_reference_semantics():
    text = 'router = APIRouter(prefix="/products")\n@router.get("/")\ndef a(): ...\n@router.patch("/{sku}")\ndef b(): ...\n'
    assert routes(text, "python", ["fastapi"], "api.py") == {"a": ("GET", "/products/"), "b": ("PATCH", "/products/{sku}")}


def test_l2_mock_patch_decorators_are_not_routes():
    assert routes('@mock.patch("x.y")\ndef test_a(): ...\n', "python", ["fastapi"], "t.py") == {}


def test_l2_events_topics_constants_and_listeners():
    pubs = conventions.source_topics(JAVA_SERVICE, conventions.rules(["spring-messaging"], common.ROOT, "publishes"))
    assert [t for t, _ in pubs] == ["order.placed"]                       # resolved through the TOPIC constant
    listener = next(s for s in symbols_of(JAVA_SERVICE, "java", "S.java") if s.name == "onPaymentSettled")
    assert conventions.decorator_topics(listener, conventions.rules(["spring-messaging"], common.ROOT, "consumes")) \
        == ["payment.settled"]


def test_l2_tables_and_declarative_clients():
    entity = symbols_of(JAVA_ENTITY, "java", "Order.java")[0]
    assert conventions.class_table(entity, conventions.rules(["jpa"], common.ROOT, "tables")) == "orders"
    bare = symbols_of("@Entity\npublic class Invoice { private Long id; }\n", "java", "I.java")[0]
    assert conventions.class_table(bare, conventions.rules(["jpa"], common.ROOT, "tables")) == "Invoice"
    client = symbols_of(FEIGN, "java", "InventoryClient.java")[0]
    assert conventions.client_target(client, conventions.rules(["spring"], common.ROOT, "clients")) == "inventory"


def test_l2_detection_selects_presets_by_marker_and_language():
    texts = ["import org.springframework.web.bind.annotation.*;", "import jakarta.persistence.Entity;"]
    assert conventions.select("auto", {"java"}, texts, common.ROOT) == ["spring", "jpa"]
    assert conventions.select("auto", {"python"}, texts, common.ROOT) == []       # wrong language: not selected
    with pytest.raises(SystemExit):
        conventions.select(["no-such-preset"], {"java"}, texts, common.ROOT)


def test_l2_custom_presets_from_config(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "conventions.yaml").write_text(
        "presets:\n  acme:\n    detect: 'com\\.acme\\.rpc'\n    routes:\n"
        "      - {on: decorator, match: '^Endpoint\\(\"(?P<path>[^\"]+)\"\\)$', method: POST}\n", encoding="utf-8")
    sym = symbols_of('class X {\n  @Endpoint("/rpc/charge")\n  public void charge() {}\n}\n', "java", "X.java")[1]
    assert sym.qualname == "X.charge"
    rules = conventions.rules(["acme"], tmp_path, "routes")
    assert conventions.decorator_route(sym, None, "", rules) == ("POST", "/rpc/charge")
    assert conventions.select("auto", {"java"}, ["import com.acme.rpc.Endpoint;"], tmp_path) == ["acme"]


def test_l2_join_and_types():
    assert [conventions.join_path(a, b) for a, b in [("/a", "/b"), ("/a/", "/b"), ("a", "b"), ("", "/x/<int:id>"),
                                                      ("/products", "/")]] == ["/a/b", "/a/b", "/a/b", "/x/{id}", "/products/"]
    assert conventions.response_type("public ResponseEntity<OrderResponse> get(Long id)", "get") == "OrderResponse"
    assert conventions.response_type("find(id: string): Promise<OrderDto>", "find") == "OrderDto"
    assert conventions.response_type("public void cancel(Long id)", "cancel") is None
    assert conventions.request_type("create(@Valid @RequestBody CreateOrderRequest request)", ["spring"],
                                    common.ROOT) == "CreateOrderRequest"


def test_l2_env_vars_any_language():
    text = 'System.getenv("A"); process.env.B; os.Getenv("C"); os.environ.get("D"); ENV["E"]'
    assert conventions.env_vars(text) == ["A", "B", "C", "D", "E"]


# --------------------------------------------------------------------------- L3 tests, labels


def test_l3_test_paths_are_case_sensitive_on_every_os():
    assert common.is_test_path("src/test/java/a/OrderServiceTest.java")
    assert common.is_test_path("src/main/java/a/OrderFlowIT.java")
    assert not common.is_test_path("src/main/java/a/BusinessUnit.java")     # *IT.java must not match "Unit.java"
    assert common.is_test_path("web/src/orders.spec.ts") and common.is_test_path("pkg/orders_test.go")


def test_l3_labels_do_not_repeat_a_class_named_like_its_file():
    assert common.label_for("src/OrderService.java", "OrderService.place") == "OrderService.place"
    assert common.label_for("svc/domain.py", "update_product") == "domain.update_product"


def test_l3_camel_case_words():
    assert common.split_words("maxActiveProjectsPerFA") == ["max", "active", "projects", "per", "fa"]
    assert common.split_words("FINAL_QC_REVIEW") == ["final", "qc", "review"]


# --------------------------------------------------------------------------- L4 coverage formats


def _sources(tmp_path: Path, *files: str) -> list[Path]:
    out = []
    for f in files:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
        out.append(p)
    return out


def test_l4_jacoco_lines_map_to_source_files(tmp_path):
    src = _sources(tmp_path, "src/main/java/com/acme/OrderService.java")
    report = tmp_path / "jacoco.xml"
    report.write_text('<report name="x"><package name="com/acme"><sourcefile name="OrderService.java">'
                      '<line nr="3" mi="0" ci="2"/><line nr="4" mi="3" ci="0"/></sourcefile></package>'
                      '<package name="com/other"><sourcefile name="Gone.java"><line nr="1" mi="1" ci="0"/></sourcefile>'
                      '</package></report>', encoding="utf-8")
    data = coverage_formats.convert("jacoco", report, tmp_path, src)
    assert data["files"] == {"src/main/java/com/acme/OrderService.java":
                             {"executed_lines": [3], "missing_lines": [4], "contexts": {}}}
    assert data["meta"]["per_test"] is False and data["meta"]["unmatched"] == ["com/other/Gone.java"]


def test_l4_lcov_keeps_per_test_names(tmp_path):
    src = _sources(tmp_path, "src/orders.ts")
    report = tmp_path / "lcov.info"
    report.write_text("TN:creates an order\nSF:/ci/build/src/orders.ts\nDA:1,1\nDA:2,0\nend_of_record\n", encoding="utf-8")
    data = coverage_formats.convert("lcov", report, tmp_path, src)
    assert data["files"]["src/orders.ts"]["contexts"] == {"1": ["creates an order"]} and data["meta"]["per_test"]


def test_l4_cobertura_go_and_istanbul(tmp_path):
    src = _sources(tmp_path, "Billing/OrderService.cs", "orders/handler.go", "web/app.js")
    cob = tmp_path / "c.xml"
    cob.write_text('<coverage><sources><source>/build</source></sources><packages><package><classes>'
                   '<class filename="Billing/OrderService.cs"><lines><line number="5" hits="1"/><line number="6" hits="0"/>'
                   '</lines></class></classes></package></packages></coverage>', encoding="utf-8")
    assert coverage_formats.convert("cobertura", cob, tmp_path, src)["files"]["Billing/OrderService.cs"]["missing_lines"] == [6]
    go = tmp_path / "cover.out"
    go.write_text("mode: set\ngithub.com/acme/orders/handler.go:3.10,5.2 2 1\n", encoding="utf-8")
    assert coverage_formats.convert("go", go, tmp_path, src)["files"]["orders/handler.go"]["executed_lines"] == [3, 4, 5]
    ist = tmp_path / "coverage-final.json"
    ist.write_text(json.dumps({"/ci/web/app.js": {"path": "/ci/web/app.js", "statementMap": {
        "0": {"start": {"line": 2}, "end": {"line": 2}}}, "s": {"0": 0}}}), encoding="utf-8")
    assert coverage_formats.convert("istanbul", ist, tmp_path, src)["files"]["web/app.js"]["missing_lines"] == [2]


# --------------------------------------------------------------------------- L5 QA test cases


def _qa(tmp_path: Path) -> Path:
    root = tmp_path / "qa"
    (root / "cases").mkdir(parents=True)
    (root / "cases" / "ORD-T1.json").write_text(json.dumps({
        "key": "ORD-T1", "name": "Place an order", "folder": "/Orders", "priority": "High",
        "customFields": {"Covers": ["POST /api/v1/orders", "OrderService.place", "Order.shipDate"]},
        "testScript": {"steps": [{"inline": {"description": "POST /api/v1/orders"}}]}}), encoding="utf-8")
    (root / "cases" / "ORD-T2.json").write_text(json.dumps({
        "key": "ORD-T2", "name": "Read an order", "customFields": {"Covers": "GET /api/v1/orders/{id}; OrderController.get"}}),
        encoding="utf-8")
    (root / "orders.feature").write_text(
        "@component-orders\nFeature: Orders\n\n  @ORD-T1 @priority-high\n"
        "  # Covers: POST /api/v1/orders; OrderService.place\n  Scenario: Place an order\n    When I post\n\n"
        "  @ORD-T3\n  Scenario: Cancel\n    When the client sends \"POST /api/v1/orders/42/cancel\"\n", encoding="utf-8")
    (root / "export.csv").write_text("Key,Name,Covers\nORD-T4,Ship,ShipmentService.ship\n", encoding="utf-8")
    return root


def test_l5_loaders_read_zephyr_gherkin_and_csv(tmp_path):
    root = _qa(tmp_path)
    cases, summary = qa.load([{"path": str(root), "format": "auto"}], tmp_path, lambda p: p.relative_to(tmp_path).as_posix())
    assert sorted(c["key"] for c in cases) == ["ORD-T1", "ORD-T1", "ORD-T2", "ORD-T3", "ORD-T4"]
    t2 = next(c for c in cases if c["key"] == "ORD-T2")
    assert t2["covers"] == ["GET /api/v1/orders/{id}", "OrderController.get"]     # string field split on ';'
    feature_t1 = next(c for c in cases if c["key"] == "ORD-T1" and c["file"].endswith(".feature:6"))
    assert feature_t1["folder"] == "orders" and feature_t1["priority"] == "high"
    assert summary[0]["cases"] == 5 and summary[0]["exists"]


def test_l5_link_tiers_and_merges_formats(tmp_path):
    root = _qa(tmp_path)
    cases, _ = qa.load([{"path": str(root)}], tmp_path, lambda p: p.relative_to(tmp_path).as_posix())
    syms = {s.qualname: s for s in symbols_of(JAVA_SERVICE, "java", "OrderService.java")
            + symbols_of(JAVA_CONTROLLER, "java", "OrderController.java")}
    out = qa.link(cases, direct=[syms["OrderService.place"]], transitive=[syms["OrderController.get"]],
                  apis=[("POST", "/api/v1/orders/{id}/cancel")], reached_apis=[("POST", "/api/v1/orders")],
                  fields=["shipDate"], classes_of_fields={"Order"}, topics=[])
    tiers = {c["key"]: c["tier"] for c in out}
    assert tiers == {"ORD-T1": "direct", "ORD-T3": "direct", "ORD-T2": "transitive"}   # ORD-T4 unrelated
    t1 = next(c for c in out if c["key"] == "ORD-T1")
    assert isinstance(t1["file"], list) and len(t1["file"]) == 2                       # JSON + Gherkin merged
    assert "covers changed field Order.shipDate" in t1["via"]
    t3 = next(c for c in out if c["key"] == "ORD-T3")
    assert t3["via"] == ["step text: POST /api/v1/orders/42/cancel"]                  # no Covers: steps are used
