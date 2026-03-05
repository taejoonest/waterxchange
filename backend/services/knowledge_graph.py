"""
SGMA Knowledge Graph — Kern County Subbasin
Built from real policy text extracted from:
  1. Kern County Subbasin GSP 2025 (3,155 pages)
  2. CA Statutory Water Rights Law / SGMA (461 pages)

Entities and relationships were extracted using Gemini LLM
and stored in a NetworkX directed graph.
"""

import json
import networkx as nx
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from collections import Counter


class SGMAKnowledgeGraph:
    """
    Knowledge Graph for Kern County SGMA compliance.

    Built from real Kern County GSP 2025 and SGMA statute text.
    Uses NetworkX for graph storage and traversal.

    Node types: GSA, Basin, SustainabilityIndicator, Threshold, Rule,
                Statute, Requirement, Project, WaterBudgetComponent,
                HydrogeologicUnit, TransferType, MonitoringNetwork, Entity

    Edge types: MANAGES, HAS_INDICATOR, HAS_THRESHOLD, REQUIRES,
                RESTRICTS, DEFINED_BY, APPLIES_TO, REFERENCES,
                PART_OF, ALLOWS, PROHIBITS, MONITORS
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._entity_index: Dict[str, Dict] = {}       # id -> entity data
        self._type_index: Dict[str, List[str]] = {}     # type -> [entity ids]
        self._name_index: Dict[str, str] = {}           # lowercase name -> entity id

    def load_regulations(self, data_path: Optional[str] = None):
        """
        Load the knowledge graph from the Gemini-extracted JSON.
        Falls back to embedded defaults if file not found.
        """
        kg_data = None

        # Try to load from extracted data
        if data_path is None:
            # Prefer v3 (two-tree compliance) > v2 (layered) > v1 (hubbed)
            base = Path(__file__).parent.parent.parent / "data" / "policies"
            for version in ["knowledge_graph_v3.json", "knowledge_graph_v2.json", "knowledge_graph_data.json"]:
                candidate = str(base / version)
                if Path(candidate).exists():
                    data_path = candidate
                    break

        if data_path and Path(data_path).exists():
            with open(data_path) as f:
                kg_data = json.load(f)
        else:
            # Check alternate paths
            alt_path = str(Path(__file__).parent.parent / "data" / "policies" / "knowledge_graph_data.json")
            if Path(alt_path).exists():
                with open(alt_path) as f:
                    kg_data = json.load(f)

        if kg_data is None:
            # Fall back to minimal embedded data
            kg_data = self._get_default_kern_county_data()

        self._build_graph(kg_data)

    def _build_graph(self, kg_data: Dict):
        """Build NetworkX graph from extracted entities and relationships."""
        self.graph.clear()
        self._entity_index.clear()
        self._type_index.clear()
        self._name_index.clear()

        # Add entity nodes
        for entity in kg_data.get("entities", []):
            eid = entity["id"]
            etype = entity.get("type", "Entity")
            ename = entity.get("name", eid)
            props = entity.get("properties", {})

            self.graph.add_node(eid, type=etype, name=ename, **props)

            self._entity_index[eid] = {"id": eid, "type": etype, "name": ename, "properties": props}

            if etype not in self._type_index:
                self._type_index[etype] = []
            self._type_index[etype].append(eid)

            self._name_index[ename.lower()] = eid

        # Add relationship edges
        for rel in kg_data.get("relationships", []):
            src = rel["source"]
            tgt = rel["target"]
            rtype = rel.get("type", "RELATED_TO")
            props = rel.get("properties", {})

            # Only add edge if both nodes exist
            if src in self._entity_index and tgt in self._entity_index:
                self.graph.add_edge(src, tgt, relation=rtype, **props)
            elif src in self._entity_index:
                # Create a stub node for the target
                self.graph.add_node(tgt, type="Reference", name=tgt)
                self.graph.add_edge(src, tgt, relation=rtype, **props)

    # ─── Query Methods ───────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return graph statistics."""
        type_counts = Counter(
            data.get("type", "Unknown") for _, data in self.graph.nodes(data=True)
        )
        rel_counts = Counter(
            data.get("relation", "Unknown") for _, _, data in self.graph.edges(data=True)
        )
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": dict(type_counts.most_common()),
            "edge_types": dict(rel_counts.most_common()),
        }

    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """Get all entities of a given type."""
        ids = self._type_index.get(entity_type, [])
        return [self._entity_index[eid] for eid in ids if eid in self._entity_index]

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get a single entity by ID."""
        return self._entity_index.get(entity_id)

    def get_neighbors(self, entity_id: str, relation_type: Optional[str] = None) -> List[Dict]:
        """Get all entities connected to a given entity."""
        if entity_id not in self.graph:
            return []

        results = []
        # Outgoing edges
        for _, target, data in self.graph.out_edges(entity_id, data=True):
            if relation_type is None or data.get("relation") == relation_type:
                target_data = self._entity_index.get(target, {"id": target, "type": "Unknown", "name": target})
                results.append({
                    "direction": "outgoing",
                    "relation": data.get("relation", "RELATED_TO"),
                    "entity": target_data,
                })
        # Incoming edges
        for source, _, data in self.graph.in_edges(entity_id, data=True):
            if relation_type is None or data.get("relation") == relation_type:
                source_data = self._entity_index.get(source, {"id": source, "type": "Unknown", "name": source})
                results.append({
                    "direction": "incoming",
                    "relation": data.get("relation", "RELATED_TO"),
                    "entity": source_data,
                })
        return results

    def find_path(self, source_id: str, target_id: str) -> List[str]:
        """Find shortest path between two entities."""
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def query(self, question: str) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph using natural language.
        Finds relevant entities by matching keywords to entity names and properties.
        """
        results = []
        question_lower = question.lower()
        question_words = set(question_lower.split())

        scored_entities = []
        for eid, edata in self._entity_index.items():
            score = 0
            name_lower = edata["name"].lower()
            etype = edata["type"]

            # Name match
            name_words = set(name_lower.split())
            overlap = question_words & name_words
            score += len(overlap) * 3

            # Substring match
            if name_lower in question_lower or any(w in question_lower for w in name_words if len(w) > 3):
                score += 2

            # Property value match
            for k, v in edata.get("properties", {}).items():
                if isinstance(v, str) and any(w in v.lower() for w in question_words if len(w) > 3):
                    score += 1

            # Boost certain types based on question content
            if "transfer" in question_lower and etype in ("Rule", "TransferType", "Requirement"):
                score += 2
            if "threshold" in question_lower and etype == "Threshold":
                score += 3
            if "gsa" in question_lower and etype == "GSA":
                score += 3
            if ("subsidence" in question_lower or "sinking" in question_lower) and "subsid" in name_lower:
                score += 3
            if "water quality" in question_lower and "quality" in name_lower:
                score += 3
            if "well" in question_lower and etype in ("Rule", "Requirement") and "well" in name_lower:
                score += 3

            if score > 0:
                scored_entities.append((score, eid, edata))

        scored_entities.sort(key=lambda x: x[0], reverse=True)

        for score, eid, edata in scored_entities[:10]:
            # Get connected entities for context
            neighbors = self.get_neighbors(eid)
            results.append({
                "type": edata["type"],
                "data": {
                    "id": eid,
                    "name": edata["name"],
                    "type": edata["type"],
                    **edata.get("properties", {})
                },
                "source": f"Knowledge Graph ({edata['type']})",
                "connections": [
                    f"{n['relation']} → {n['entity']['name']}" for n in neighbors[:5]
                ]
            })

        return results

    def check_transfer_compliance(self, question: str) -> Dict[str, Any]:
        """Check transfer compliance using knowledge graph traversal."""
        question_lower = question.lower()

        # Find relevant rules
        rules = self.get_entities_by_type("Rule")
        requirements = self.get_entities_by_type("Requirement")
        thresholds = self.get_entities_by_type("Threshold")

        applicable_rules = []
        for rule in rules:
            name_lower = rule["name"].lower()
            if any(kw in question_lower for kw in name_lower.split() if len(kw) > 3):
                applicable_rules.append(rule)
            elif "transfer" in question_lower and "transfer" in name_lower:
                applicable_rules.append(rule)

        applicable_reqs = []
        for req in requirements:
            name_lower = req["name"].lower()
            if any(kw in question_lower for kw in name_lower.split() if len(kw) > 3):
                applicable_reqs.append(req)

        # Determine if same basin (intra-basin)
        is_intra_basin = "kern" in question_lower and question_lower.count("kern") <= 1
        is_intra_basin = is_intra_basin or "same basin" in question_lower or "intra" in question_lower

        # Find GSAs mentioned
        gsas = self.get_entities_by_type("GSA")
        mentioned_gsas = [g for g in gsas if g["name"].lower() in question_lower]

        return {
            "allowed": True,  # Intra-basin generally allowed
            "reason": "Intra-basin transfer within Kern County Subbasin. Subject to GSA coordination agreement and GSP requirements.",
            "requires_permit": len(mentioned_gsas) >= 2,
            "rules": [r["name"] for r in applicable_rules[:5]],
            "requirements": [r["name"] for r in applicable_reqs[:5]],
            "thresholds": [{"name": t["name"], **t.get("properties", {})} for t in thresholds[:5]],
            "gsas_involved": [g["name"] for g in mentioned_gsas],
        }

    def check_transfer_between_basins(
        self, from_basin: str, to_basin: str, quantity_af: float
    ) -> Dict[str, Any]:
        """Check compliance for a transfer between two locations."""
        same_basin = from_basin.lower() == to_basin.lower() or \
                     ("kern" in from_basin.lower() and "kern" in to_basin.lower())

        rules = self.get_entities_by_type("Rule")
        reqs = self.get_entities_by_type("Requirement")

        if same_basin:
            return {
                "allowed": True,
                "reason": f"Intra-basin transfer within Kern County Subbasin. "
                          f"Subject to GSP sustainable management criteria and GSA coordination.",
                "requires_permit": False,
                "rules": [r["name"] for r in rules[:3]],
                "requirements": [r["name"] for r in reqs[:3]],
            }
        else:
            return {
                "allowed": False,
                "reason": f"Inter-basin transfer from {from_basin} to {to_basin}. "
                          f"Kern County Subbasin is Critically Overdrafted — outbound transfers restricted.",
                "requires_permit": True,
                "may_be_denied": True,
                "rules": [r["name"] for r in rules[:3]],
            }

    def format_context(self, results: List[Dict]) -> str:
        """Format knowledge graph query results as context string."""
        if not results:
            return "No relevant SGMA entities found in knowledge graph."

        lines = ["Relevant SGMA Knowledge Graph Entities:\n"]
        for r in results:
            data = r["data"]
            lines.append(f"- [{data.get('type', 'Entity')}] {data.get('name', 'Unknown')}")
            props = {k: v for k, v in data.items() if k not in ('id', 'name', 'type')}
            if props:
                for k, v in list(props.items())[:3]:
                    lines.append(f"    {k}: {v}")
            if r.get("connections"):
                lines.append(f"    Connections: {', '.join(r['connections'][:3])}")
        return "\n".join(lines)

    def get_graph_for_display(self) -> Dict[str, Any]:
        """Export the graph in a format suitable for visualization."""
        nodes = []
        for nid, data in self.graph.nodes(data=True):
            nodes.append({
                "id": nid,
                "label": data.get("name", nid),
                "type": data.get("type", "Unknown"),
            })

        edges = []
        for src, tgt, data in self.graph.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                "label": data.get("relation", "RELATED"),
            })

        return {"nodes": nodes, "edges": edges}

    def print_graph_summary(self):
        """Print a human-readable summary of the knowledge graph."""
        stats = self.get_stats()
        print(f"\n{'═'*60}")
        print(f"  SGMA Knowledge Graph — Kern County Subbasin")
        print(f"{'═'*60}")
        print(f"  Nodes: {stats['total_nodes']}  |  Edges: {stats['total_edges']}")
        print(f"\n  Node Types:")
        for ntype, count in stats['node_types'].items():
            bar = '█' * min(count, 30)
            print(f"    {ntype:28s} {bar} ({count})")
        print(f"\n  Relationship Types:")
        for rtype, count in stats['edge_types'].items():
            bar = '▓' * min(count, 30)
            print(f"    {rtype:28s} {bar} ({count})")

        # Show some key entities
        print(f"\n  Key Entities:")
        for etype in ["GSA", "Basin", "SustainabilityIndicator", "Statute"]:
            entities = self.get_entities_by_type(etype)
            if entities:
                print(f"\n  [{etype}]:")
                for e in entities[:8]:
                    neighbors = self.get_neighbors(e["id"])
                    conn_str = ""
                    if neighbors:
                        conn_str = f" → {', '.join(n['entity']['name'] for n in neighbors[:2])}"
                    print(f"    • {e['name']}{conn_str}")

    # ─── Fallback Data ─────────────────────────────────────────

    def _get_default_kern_county_data(self) -> Dict:
        """Minimal embedded Kern County data if JSON file not found."""
        return {
            "entities": [
                {"id": "kern_subbasin", "type": "Basin", "name": "Kern County Subbasin",
                 "properties": {"dwr_number": "5-22.14", "priority": "Critically Overdrafted", "area_sq_mi": "2767"}},
                {"id": "rosedale_gsa", "type": "GSA", "name": "Rosedale-Rio Bravo Water Storage District GSA", "properties": {}},
                {"id": "semitropic_gsa", "type": "GSA", "name": "Semitropic Water Storage District GSA", "properties": {}},
                {"id": "kern_water_agency_gsa", "type": "GSA", "name": "Kern County Water Agency GSA", "properties": {}},
                {"id": "gw_levels", "type": "SustainabilityIndicator", "name": "Chronic Lowering of Groundwater Levels",
                 "properties": {"sgma_section": "10727.2(b)(1)"}},
                {"id": "subsidence", "type": "SustainabilityIndicator", "name": "Land Subsidence",
                 "properties": {"sgma_section": "10727.2(b)(3)"}},
                {"id": "water_quality", "type": "SustainabilityIndicator", "name": "Degraded Water Quality",
                 "properties": {"sgma_section": "10727.2(b)(4)"}},
                {"id": "storage", "type": "SustainabilityIndicator", "name": "Reduction in Groundwater Storage",
                 "properties": {"sgma_section": "10727.2(b)(2)"}},
                {"id": "sgma_10726_4", "type": "Statute", "name": "SGMA §10726.4",
                 "properties": {"description": "GSA authority to regulate extraction and transfers"}},
                {"id": "metering_req", "type": "Requirement", "name": "Well Metering Requirement",
                 "properties": {"description": "All extraction wells must be metered per GSP"}},
            ],
            "relationships": [
                {"source": "rosedale_gsa", "target": "kern_subbasin", "type": "MANAGES"},
                {"source": "semitropic_gsa", "target": "kern_subbasin", "type": "MANAGES"},
                {"source": "kern_subbasin", "target": "gw_levels", "type": "HAS_INDICATOR"},
                {"source": "kern_subbasin", "target": "subsidence", "type": "HAS_INDICATOR"},
                {"source": "kern_subbasin", "target": "water_quality", "type": "HAS_INDICATOR"},
                {"source": "kern_subbasin", "target": "storage", "type": "HAS_INDICATOR"},
                {"source": "sgma_10726_4", "target": "metering_req", "type": "REQUIRES"},
            ]
        }
