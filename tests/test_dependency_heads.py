#!/usr/bin/env python3
"""Regressões da normalização estrutural das dependências TED/TEJ."""

from pathlib import Path
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tej.tools.normalize_dependency_heads import normalize_file as normalize_tej
from scripts_ted.normalize_dependency_heads import normalize_file as normalize_ted


def nodes(sentence):
    return sentence.xpath("./*[local-name()='tok' or local-name()='dtok']")


def assert_valid_corpus(testcase, corpus):
    for path in sorted((ROOT / corpus / "xmlfiles").rglob("*.xml")):
        tree = etree.parse(str(path))
        all_nodes = tree.xpath("//*[local-name()='tok' or local-name()='dtok']")
        ids = [node.get("id") for node in all_nodes]
        testcase.assertTrue(all(ids), path)
        testcase.assertEqual(len(ids), len(set(ids)), path)
        for sentence in tree.xpath("//*[local-name()='s']"):
            sentence_nodes = nodes(sentence)
            if not sentence_nodes:
                continue
            annotated = [node for node in sentence_nodes if node.get("head") is not None]
            if not annotated:
                continue
            testcase.assertEqual(len(annotated), len(sentence_nodes), path)
            sentence_ids = {node.get("id") for node in sentence_nodes}
            roots = [node for node in sentence_nodes if node.get("head") == "0"]
            testcase.assertEqual(len(roots), 1, f"{path} {sentence.get('id')}")
            parent = {}
            for node in sentence_nodes:
                head = node.get("head")
                testcase.assertFalse(head.isdigit() and head != "0", path)
                if head != "0":
                    testcase.assertIn(head, sentence_ids, path)
                    parent[node.get("id")] = head
            for start in parent:
                seen = set()
                current = start
                while current in parent:
                    testcase.assertNotIn(current, seen, f"ciclo em {path}")
                    seen.add(current)
                    current = parent[current]


class DependencyHeadsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = ROOT / "scripts_ted/annotate_ted_udpipe.py"
        spec = importlib.util.spec_from_file_location("annotate_ted_udpipe", script)
        cls.pipeline = importlib.util.module_from_spec(spec)
        tqdm_module = types.ModuleType("tqdm")
        tqdm_module.tqdm = lambda values: values
        requests_module = types.ModuleType("requests")
        with patch.dict(sys.modules, {"tqdm": tqdm_module, "requests": requests_module}), patch.object(Path, "mkdir"):
            spec.loader.exec_module(cls.pipeline)

    def test_ted_and_tej_are_structurally_valid(self):
        assert_valid_corpus(self, "ted")
        assert_valid_corpus(self, "tej")

    def test_ted_collision_and_dependencies(self):
        matches = list((ROOT / "ted/xmlfiles").rglob("nslm_1_12_eeoa.xml"))
        self.assertEqual(len(matches), 1)
        tree = etree.parse(str(matches[0]))
        sentence = tree.xpath("//*[local-name()='s' and @id='s-2']")[0]
        by_text = {(node.text or ""): node for node in nodes(sentence)}
        self.assertEqual(by_text["perto"].get("id"), "w-65")
        self.assertEqual(by_text["do"].get("id"), "w-148")
        self.assertEqual(by_text["mar"].get("id"), "w-149")
        self.assertEqual(by_text["do"].get("head"), "w-149")
        self.assertEqual(by_text["mar"].get("head"), "w-65")

    def test_tej_0007_calendar_targets_baseado(self):
        tree = etree.parse(str(ROOT / "tej/xmlfiles/TEJ_0007.xml"))
        calendar = tree.xpath("//*[local-name()='tok' and text()='calendário']")
        self.assertEqual(len(calendar), 1)
        self.assertEqual(calendar[0].get("head"), "w-115")
        target = tree.xpath("//*[local-name()='tok' and @id='w-115']")
        self.assertEqual(len(target), 1)
        self.assertEqual((target[0].text or ""), "baseado")

    def test_tej_converter_is_idempotent(self):
        changed = converted = 0
        for path in (ROOT / "tej/xmlfiles").rglob("*.xml"):
            file_changed, file_converted = normalize_tej(path, write=False)
            changed += int(file_changed)
            converted += file_converted
        self.assertEqual((changed, converted), (0, 0))

    def test_ted_converter_is_idempotent(self):
        changed = converted = 0
        root = ROOT / "ted/xmlfiles"
        for path in root.rglob("*.xml"):
            file_changed, file_converted = normalize_ted(path, root, write=False)
            changed += int(file_changed)
            converted += file_converted
        self.assertEqual((changed, converted), (0, 0))

    def test_ted_pipeline_maps_conllu_heads_to_xml_ids(self):
        xml = etree.fromstring(b'<s><tok id="x-9">A</tok><tok id="node-2">B</tok></s>')
        ud = [{"id": "1", "head": "2"}, {"id": "2", "head": "0"}]
        mapping = self.pipeline.dependency_head_map(xml.xpath("./tok"), ud)
        self.assertEqual(mapping, {"1": "x-9", "2": "node-2"})

    def test_ted_pipeline_writes_xml_head_references(self):
        sentence = etree.fromstring(
            b'<s><tok id="x-9">A</tok><tok id="node-2">B</tok></s>'
        )
        conllu = (
            "1\tA\ta\tNOUN\t_\t_\t2\tnsubj\t_\t_\n"
            "2\tB\tb\tVERB\t_\t_\t0\troot\t_\t_\n\n"
        )
        with patch.object(self.pipeline, "udpipe_process_conllu", return_value=conllu):
            self.pipeline.annotate_sentence(sentence)
        annotated = sentence.xpath("./tok")
        self.assertEqual(annotated[0].get("head"), "node-2")
        self.assertEqual(annotated[1].get("head"), "0")

    def test_ted_pipeline_rejects_dtok_explicitly(self):
        sentence = etree.fromstring(
            b'<s><tok id="x"><dtok id="d-1">de</dtok></tok></s>'
        )
        with self.assertRaisesRegex(ValueError, "dtok"):
            self.pipeline.annotate_sentence(sentence)

    def test_ted_pipeline_rejects_invalid_mapping(self):
        duplicate = etree.fromstring(b'<s><tok id="x">A</tok><tok id="x">B</tok></s>')
        ud = [{"id": "1", "head": "2"}, {"id": "2", "head": "0"}]
        with self.assertRaisesRegex(ValueError, "duplicados"):
            self.pipeline.dependency_head_map(duplicate.xpath("./tok"), ud)
        valid = etree.fromstring(b'<s><tok id="x">A</tok></s>')
        with self.assertRaisesRegex(ValueError, "sem alvo"):
            self.pipeline.dependency_head_map(
                valid.xpath("./tok"), [{"id": "1", "head": "2"}]
            )

    def test_ted_pipeline_rejects_document_wide_duplicate_ids(self):
        root = etree.fromstring(
            b'<TEI><s><tok id="x">A</tok></s><s><tok id="x">B</tok></s></TEI>'
        )
        with self.assertRaisesRegex(ValueError, "duplicados"):
            self.pipeline.validate_document_node_ids(root)


if __name__ == "__main__":
    unittest.main()
