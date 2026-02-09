"""Policy contract explorer — builds a graph from the policy model + test suite
and serves it as an interactive visualization."""

import ast
import json
import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from policy.green_cross import green_cross_policy


def extract_test_info():
    """Parse test files with ast to get classes, methods, and risk docstrings."""
    tests_dir = ROOT / "tests"
    results = []

    for test_file in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(test_file.read_text())
        module_name = test_file.stem

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    methods.append({
                        "name": item.name,
                        "risk": ast.get_docstring(item) or "",
                    })

            results.append({
                "module": module_name,
                "class_name": node.name,
                "docstring": ast.get_docstring(node) or "",
                "test_count": len(methods),
                "tests": methods,
            })

    return results


# Mapping from test class → policy section
CLASS_SECTION = {
    "TestDeductibles": "deductibles",
    "TestOOPMax": "oop_max",
    "TestAccumulatorAdjustment": "oop_max",
    "TestERFinancials": "emergency",
    "TestPriorAuthPenalties": "prior_authorization",
    "TestPharmacyFinancials": "pharmacy",
    "TestPreventiveCare": "preventive_care",
    "TestObservationStatus": "inpatient",
    "TestVisitLimits": "rehab",
    "TestDentalBenefits": "dental",
    "TestDentalWaitingPeriods": "dental",
    "TestStepTherapy": "pharmacy",
    "TestMaintenanceMeds": "pharmacy",
    "TestMentalHealthParity": "mental_health",
    "TestNoSurprisesAct": "emergency",
    "TestNewbornsAct": "inpatient",
    "TestCOBRA": "special_provisions",
    "TestClaimsAndAppeals": "claims_and_appeals",
    "TestRegulatoryTraceability": None,  # cross-cutting
    "TestGenderedLanguage": "correspondence",
    "TestLanguageRequirements": "correspondence",
    "TestSurpriseBillingNotices": "correspondence",
    "TestRequiredDisclosures": "correspondence",
    "TestDocumentFields": "correspondence",
}

MODULE_RISK = {
    "test_financial_accuracy": "financial",
    "test_benefit_determination": "coverage",
    "test_regulatory": "regulatory",
    "test_correspondence": "correspondence",
}

SERVICE_SECTION = {
    "laboratory": "primary_care",
    "anesthesia": "inpatient",
    "surgery": "inpatient",
    "outpatient_hospital": "inpatient",
    "imaging": "prior_authorization",
    "emergency": "emergency",
    "inpatient": "inpatient",
    "preventive_care": "preventive_care",
    "colonoscopy": "preventive_care",
    "telehealth": "primary_care",
    "follow_up": "emergency",
}


def build_graph():
    p = green_cross_policy
    nodes, edges = [], []

    # --- statute nodes ---
    for bp in p.base_policies:
        ref_parts = []
        if bp.references:
            r = bp.references[0]
            if r.citation:
                ref_parts.append(r.citation)
            if r.cfr:
                ref_parts.append(r.cfr)
        nodes.append({
            "id": f"statute_{bp.id}",
            "label": bp.id,
            "title": bp.name,
            "subtitle": bp.description or "",
            "citation": " | ".join(ref_parts),
            "type": "statute",
            "group": "statute",
        })

    # --- section nodes ---
    sections = [
        ("deductibles", "Deductibles", []),
        ("oop_max", "OOP Maximum", []),
        ("preventive_care", "Preventive Care", p.preventive_care.base_policies),
        ("primary_care", "Primary Care", []),
        ("specialist_care", "Specialist Care", []),
        ("emergency", "Emergency", p.emergency.base_policies),
        ("inpatient", "Inpatient", p.inpatient.base_policies),
        ("mental_health", "Mental Health", p.mental_health.base_policies),
        ("pharmacy", "Pharmacy", []),
        ("dental", "Dental", []),
        ("vision", "Vision", []),
        ("rehab", "Rehab", []),
        ("prior_authorization", "Prior Auth", []),
        ("correspondence", "Correspondence", []),
        ("claims_and_appeals", "Claims & Appeals", []),
        ("special_provisions", "Special Provisions", []),
    ]

    for sec_id, label, base_pols in sections:
        nodes.append({
            "id": f"section_{sec_id}",
            "label": label,
            "type": "section",
            "group": "section",
        })
        for bp_id in base_pols:
            edges.append({
                "from": f"statute_{bp_id}",
                "to": f"section_{sec_id}",
                "type": "governs",
            })

    # implicit statute→section links
    implicit = [
        ("ACA", "preventive_care"), ("ACA", "oop_max"),
        ("ERISA", "claims_and_appeals"), ("COBRA", "special_provisions"),
    ]
    existing = {(e["from"], e["to"]) for e in edges}
    for stat, sec in implicit:
        key = (f"statute_{stat}", f"section_{sec}")
        if key not in existing:
            edges.append({"from": key[0], "to": key[1], "type": "governs"})

    # --- test nodes ---
    for tc in extract_test_info():
        risk_cat = MODULE_RISK.get(tc["module"], "unknown")
        nid = f"test_{tc['class_name']}"
        nodes.append({
            "id": nid,
            "label": tc["class_name"].replace("Test", ""),
            "type": "test",
            "group": f"risk_{risk_cat}",
            "risk_category": risk_cat,
            "test_count": tc["test_count"],
            "tests": tc["tests"],
            "docstring": tc["docstring"],
        })
        sec = CLASS_SECTION.get(tc["class_name"])
        if sec:
            edges.append({"from": f"section_{sec}", "to": nid, "type": "tested_by"})

    # --- quirk nodes ---
    for q in p.network_quirks:
        nid = f"quirk_{q.id}"
        nodes.append({
            "id": nid,
            "label": q.name,
            "type": "quirk",
            "group": "quirk",
            "description": q.description,
            "risk": q.risk,
            "affected_services": q.affected_services,
        })
        seen = set()
        for svc in q.affected_services:
            target = SERVICE_SECTION.get(svc)
            if target and target not in seen:
                seen.add(target)
                edges.append({"from": nid, "to": f"section_{target}", "type": "affects"})

    # --- summary stats ---
    total_tests = sum(n.get("test_count", 0) for n in nodes if n["type"] == "test")
    stats = {
        "statutes": sum(1 for n in nodes if n["type"] == "statute"),
        "sections": sum(1 for n in nodes if n["type"] == "section"),
        "test_classes": sum(1 for n in nodes if n["type"] == "test"),
        "total_tests": total_tests,
        "quirks": sum(1 for n in nodes if n["type"] == "quirk"),
        "edges": len(edges),
    }

    return {"nodes": nodes, "edges": edges, "stats": stats}


class Handler(SimpleHTTPRequestHandler):
    graph_data = None
    html_content = None

    def do_GET(self):
        if self.path == "/api/graph":
            body = json.dumps(self.graph_data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/", "/index.html"):
            body = self.html_content.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787

    print("Building graph from policy + tests...")
    Handler.graph_data = build_graph()
    Handler.html_content = (Path(__file__).parent / "index.html").read_text()

    s = Handler.graph_data["stats"]
    print(f"  {s['statutes']} statutes | {s['sections']} sections | "
          f"{s['test_classes']} test classes ({s['total_tests']} tests) | "
          f"{s['quirks']} quirks | {s['edges']} edges")

    url = f"http://localhost:{port}"
    print(f"Serving → {url}")
    webbrowser.open(url)

    try:
        HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nDone.")


if __name__ == "__main__":
    main()
