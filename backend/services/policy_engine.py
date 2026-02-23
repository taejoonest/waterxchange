"""
WaterXchange Policy Engine
Loads real policy text from Kern County GSP and SGMA statute,
chunks it for retrieval, and provides policy-aware compliance analysis.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class PolicyChunk:
    """A chunk of policy text with metadata."""
    def __init__(self, text: str, source: str, page: int, category: str = "general"):
        self.text = text
        self.source = source
        self.page = page
        self.category = category  # e.g. "sustainability_criteria", "water_budget", "transfer", "monitoring"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source": self.source,
            "page": self.page,
            "category": self.category
        }


class PolicyEngine:
    """
    Loads, indexes, and retrieves policy text from:
    1. Kern County Subbasin Groundwater Sustainability Plan (GSP) 2025
    2. California Statutory Water Rights Law (SGMA statute)
    """

    # Categories and their keyword signatures
    CATEGORY_KEYWORDS = {
        "sustainability_criteria": [
            "minimum threshold", "measurable objective", "undesirable result",
            "sustainability indicator", "sustainable management criteria",
            "interim milestone", "significant and unreasonable"
        ],
        "water_budget": [
            "water budget", "sustainable yield", "overdraft", "change in storage",
            "total water use", "supply and demand", "groundwater extraction",
            "historical water budget", "projected water budget"
        ],
        "groundwater_levels": [
            "groundwater level", "water level", "chronic lowering",
            "groundwater elevation", "depth to water", "water table",
            "representative monitoring", "groundwater level decline"
        ],
        "subsidence": [
            "subsidence", "land subsidence", "inelastic", "compaction",
            "ground surface", "differential subsidence", "irreversible"
        ],
        "water_quality": [
            "water quality", "degraded", "contamination", "nitrate",
            "arsenic", "uranium", "tds", "total dissolved solids",
            "drinking water", "maximum contaminant level"
        ],
        "wells": [
            "well", "extraction well", "production well", "monitoring well",
            "well interference", "well capacity", "de minimis",
            "well depth", "pump", "metering"
        ],
        "transfer": [
            "transfer", "groundwater extraction", "allocation",
            "trading", "market", "buy", "sell", "exchange",
            "conveyance", "delivery", "water right"
        ],
        "monitoring": [
            "monitoring", "reporting", "data management", "annual report",
            "five-year assessment", "network", "measurement"
        ],
        "projects_actions": [
            "project", "management action", "recharge", "banking",
            "conservation", "demand reduction", "supply augmentation",
            "fallowing", "recycled water"
        ],
        "gsa_governance": [
            "groundwater sustainability agency", "gsa", "governance",
            "coordination", "inter-basin", "adjacent basin",
            "fee", "enforcement", "reporting requirement"
        ]
    }

    def __init__(self):
        self.gsp_chunks: List[PolicyChunk] = []
        self.sgma_chunks: List[PolicyChunk] = []
        self.all_chunks: List[PolicyChunk] = []
        self.category_index: Dict[str, List[PolicyChunk]] = {}

    def load_policies(self, data_dir: str = None):
        """Load pre-extracted policy chunks from JSON files."""
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policies")

        gsp_path = os.path.join(data_dir, "kern_gsp_chunks.json")
        sgma_path = os.path.join(data_dir, "sgma_statute_chunks.json")

        if os.path.exists(gsp_path):
            with open(gsp_path) as f:
                raw = json.load(f)
            for item in raw:
                cat = self._categorize(item["text"])
                chunk = PolicyChunk(
                    text=item["text"],
                    source=item["source"],
                    page=item["page"],
                    category=cat
                )
                self.gsp_chunks.append(chunk)

        if os.path.exists(sgma_path):
            with open(sgma_path) as f:
                raw = json.load(f)
            for item in raw:
                cat = self._categorize(item["text"])
                chunk = PolicyChunk(
                    text=item["text"],
                    source=item["source"],
                    page=item["page"],
                    category=cat
                )
                self.sgma_chunks.append(chunk)

        self.all_chunks = self.gsp_chunks + self.sgma_chunks
        self._build_category_index()

        return {
            "gsp_chunks": len(self.gsp_chunks),
            "sgma_chunks": len(self.sgma_chunks),
            "total_chunks": len(self.all_chunks),
            "categories": {k: len(v) for k, v in self.category_index.items()}
        }

    def _categorize(self, text: str) -> str:
        """Classify a chunk into the most relevant category."""
        text_lower = text.lower()
        best_cat = "general"
        best_score = 0
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_cat = cat
        return best_cat

    def _build_category_index(self):
        """Index chunks by category for fast retrieval."""
        self.category_index = {}
        for chunk in self.all_chunks:
            if chunk.category not in self.category_index:
                self.category_index[chunk.category] = []
            self.category_index[chunk.category].append(chunk)

    def retrieve_for_question(self, question: str, top_k: int = 5) -> List[PolicyChunk]:
        """
        Retrieve the most relevant policy chunks for a compliance question.
        Uses keyword-based relevance scoring (a real system would use embeddings).
        """
        question_lower = question.lower()
        scored = []

        for chunk in self.all_chunks:
            score = 0
            chunk_lower = chunk.text.lower()

            # Score based on keyword overlap with the question
            words = set(question_lower.split())
            for word in words:
                if len(word) > 3 and word in chunk_lower:
                    score += 1

            # Boost for category match
            for cat, keywords in self.CATEGORY_KEYWORDS.items():
                q_relevance = sum(1 for kw in keywords if kw in question_lower)
                if q_relevance > 0 and chunk.category == cat:
                    score += q_relevance * 3  # Strong category boost

            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def retrieve_by_categories(self, categories: List[str], max_per_cat: int = 3) -> List[PolicyChunk]:
        """Retrieve chunks from specific categories."""
        results = []
        for cat in categories:
            chunks = self.category_index.get(cat, [])
            results.extend(chunks[:max_per_cat])
        return results

    def get_policy_summary(self) -> str:
        """Get a summary of loaded policies for display."""
        lines = []
        lines.append(f"📄 Kern County GSP 2025: {len(self.gsp_chunks)} policy sections loaded")
        lines.append(f"📄 CA Water Rights Law (SGMA): {len(self.sgma_chunks)} statute sections loaded")
        lines.append(f"📊 Total policy chunks: {len(self.all_chunks)}")
        lines.append(f"\n📁 Policy Categories:")
        for cat, chunks in sorted(self.category_index.items(), key=lambda x: -len(x[1])):
            lines.append(f"   {cat}: {len(chunks)} sections")
        return "\n".join(lines)
