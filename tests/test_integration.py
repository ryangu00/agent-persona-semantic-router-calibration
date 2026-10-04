"""Opt-in local-server smoke test; never probes an endpoint by default."""
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from embeddings import OneTextEncoder


class OllamaIntegration(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("RUN_OLLAMA_TESTS") == "1", "live Ollama integration disabled")
    def test_local_model_vectors(self):
        encoder = OneTextEncoder()
        try:
            vectors = encoder(["Inspect the compiler proposal"])
        except Exception:
            self.skipTest("local embedding model unavailable")
        self.assertTrue(vectors and vectors[0])
