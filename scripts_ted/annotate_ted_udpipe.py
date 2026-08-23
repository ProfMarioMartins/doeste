from pathlib import Path
from lxml import etree
from tqdm import tqdm
from datetime import datetime
import requests
import csv
import json
import hashlib
import time


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INPUT_DIR = Path(

    "/var/www/html/teitok/ted/xmlfiles_raw/Textos_Escola_SEM_DTOK"

)

OUTPUT_DIR = Path(

    "/var/www/html/teitok/ted/xmlfiles_annotated"

)

LOG_DIR = OUTPUT_DIR / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

UDPIPE_API = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
MODEL = "portuguese-bosque-ud-2.17"

TIMEOUT = 120


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_xml_namespace(root):
    if root.tag.startswith("{"):
        return root.tag.split("}")[0].strip("{")
    return None


def make_element(name, ns=None):
    if ns:
        return etree.Element(f"{{{ns}}}{name}")
    return etree.Element(name)


def token_original_form(tok):
    return (tok.text or "").strip()


def token_annotation_form(tok):
    """
    Usa nform quando existir.
    Caso contrário, usa o conteúdo textual original do <tok>.
    """
    nform = tok.get("nform")
    if nform and nform.strip():
        return nform.strip()
    return token_original_form(tok)


def sentence_to_conllu(tokens):
    """
    Cria CoNLL-U pré-tokenizado.
    Importante: isso preserva a tokenização existente no XML.
    Portanto, formas contraídas como 'no', 'da', 'pela'
    NÃO serão expandidas nesta etapa.
    """
    lines = []

    for i, tok in enumerate(tokens, start=1):
        form = token_annotation_form(tok)
        form = form.replace("\t", " ").replace("\n", " ").strip()

        if not form:
            form = "_"

        # ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
        lines.append(f"{i}\t{form}\t_\t_\t_\t_\t_\t_\t_\t_")

    return "\n".join(lines) + "\n\n"


def udpipe_process_conllu(conllu_text, retries=3, delay=5):

    payload = {

        "model": MODEL,

        "input": "conllu",

        "tagger": "",

        "parser": "",

        "data": conllu_text

    }

    for attempt in range(retries):

        try:

            response = requests.post(

                UDPIPE_API,

                data=payload,

                timeout=TIMEOUT

            )

            response.raise_for_status()

            data = response.json()

            if "result" not in data:

                raise ValueError("Resposta do UDPipe sem 'result'.")

            return data["result"]

        except Exception as e:

            if attempt < retries - 1:

                print(f"⚠ Retry {attempt+1} após erro: {e}")

                time.sleep(delay)

            else:

                raise


def parse_conllu_tokens(conllu_text):
    tokens = []

    for line in conllu_text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        cols = line.split("\t")

        if len(cols) < 8:
            continue

        # Ignora multiword tokens e empty nodes, se aparecerem
        if "-" in cols[0] or "." in cols[0]:
            continue

        tokens.append({
            "id": cols[0],
            "form": cols[1],
            "lemma": cols[2],
            "upos": cols[3],
            "xpos": cols[4],
            "feats": cols[5],
            "head": cols[6],
            "deprel": cols[7],
        })

    return tokens


def annotate_sentence(sentence):
    tokens_xml = sentence.xpath("./*[local-name()='tok']")

    if not tokens_xml:
        return {
            "sentences_processed": 0,
            "tokens_processed": 0,
            "skipped_sentences": 0
        }

    conllu_input = sentence_to_conllu(tokens_xml)
    conllu_output = udpipe_process_conllu(conllu_input)
    tokens_ud = parse_conllu_tokens(conllu_output)

    if len(tokens_xml) != len(tokens_ud):
        print("⚠ Diferença de tokens. Sentença ignorada.")
        print("XML:", [token_annotation_form(t) for t in tokens_xml])
        print("UDPipe:", [t["form"] for t in tokens_ud])

        return {
            "sentences_processed": 0,
            "tokens_processed": 0,
            "skipped_sentences": 1
        }

    for tok_xml, tok_ud in zip(tokens_xml, tokens_ud):
        original = token_original_form(tok_xml)

        # Preserva explicitamente a forma original do aluno
        tok_xml.set("form", original)

        # Mantém o conteúdo textual original
        tok_xml.text = original

        # Adiciona anotação linguística
        tok_xml.set("lemma", tok_ud["lemma"])
        tok_xml.set("upos", tok_ud["upos"])
        tok_xml.set("pos", tok_ud["upos"])

        if tok_ud["xpos"] and tok_ud["xpos"] != "_":
            tok_xml.set("xpos", tok_ud["xpos"])

        if tok_ud["feats"] and tok_ud["feats"] != "_":
            tok_xml.set("feats", tok_ud["feats"])

        tok_xml.set("head", tok_ud["head"])
        tok_xml.set("deprel", tok_ud["deprel"])

    return {
        "sentences_processed": 1,
        "tokens_processed": len(tokens_xml),
        "skipped_sentences": 0
    }


def add_revision_desc(root):
    ns = get_xml_namespace(root)

    tei_header_list = root.xpath("./*[local-name()='teiHeader']")
    if not tei_header_list:
        return

    tei_header = tei_header_list[0]

    revision_list = tei_header.xpath("./*[local-name()='revisionDesc']")

    if revision_list:
        revision_desc = revision_list[0]
    else:
        revision_desc = make_element("revisionDesc", ns)
        tei_header.append(revision_desc)

    change = make_element("change", ns)
    change.set("when", datetime.now().isoformat())
    change.set("who", "DOESTE_UDPIPE_TED_PIPELINE")
    change.text = (
        f"Automatic POS-tagging, lemmatization and dependency parsing "
        f"via UDPipe REST service. Model: {MODEL}. "
        f"Annotation used nform when available; otherwise tok text. "
        f"Original learner form preserved in tok text and form attribute. "
        f"Contractions were not expanded in this processing stage."
    )

    revision_desc.append(change)


def process_file(input_path, output_path):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(input_path), parser)
    root = tree.getroot()

    sentences = root.xpath(".//*[local-name()='s']")

    stats = {
        "sentences_total": len(sentences),
        "sentences_processed": 0,
        "tokens_processed": 0,
        "skipped_sentences": 0
    }

    for sentence in sentences:
        result = annotate_sentence(sentence)

        stats["sentences_processed"] += result["sentences_processed"]
        stats["tokens_processed"] += result["tokens_processed"]
        stats["skipped_sentences"] += result["skipped_sentences"]

    add_revision_desc(root)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    tree.write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True
    )

    return stats


# ==========================================================
# EXECUÇÃO EM LOTE
# ==========================================================

def main():
    ERROR_LIST = Path("/var/www/html/teitok/scripts_ted/arquivos_com_erro.txt")

    with open(ERROR_LIST, encoding="utf-8") as f:
        rel_paths = [line.strip() for line in f if line.strip()]

    files = [INPUT_DIR / p for p in rel_paths]

    print("======================================")
    print("INICIANDO REPROCESSAMENTO TED COM UDPIPE")
    print("Arquivos a reprocessar:", len(files))
    print("Entrada:", INPUT_DIR)
    print("Saída:", OUTPUT_DIR)
    print("Modelo:", MODEL)
    print("======================================")

    records = []

    for input_file in tqdm(files):
        relative_path = input_file.relative_to(INPUT_DIR)
        output_file = OUTPUT_DIR / relative_path

        record = {
            "file_name": input_file.name,
            "relative_path": str(relative_path),
            "input_path": str(input_file),
            "output_path": str(output_file),
            "model": MODEL,
            "endpoint": UDPIPE_API,
            "datetime": datetime.now().isoformat(),
            "status": "ok",
            "error": "",
            "input_sha256": "",
            "output_sha256": "",
            "sentences_total": 0,
            "sentences_processed": 0,
            "tokens_processed": 0,
            "skipped_sentences": 0
        }

        try:
            record["input_sha256"] = sha256_of_file(input_file)

            stats = process_file(input_file, output_file)

            record.update(stats)
            record["output_sha256"] = sha256_of_file(output_file)

        except Exception as e:
            record["status"] = "error"
            record["error"] = str(e)
            print(f"\n❌ Erro em {input_file.name}: {e}")

        records.append(record)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_log = LOG_DIR / f"ted_udpipe_retry_log_{timestamp}.csv"
    json_log = LOG_DIR / f"ted_udpipe_retry_log_{timestamp}.json"

    if records:
        with open(csv_log, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

        with open(json_log, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

    print("======================================")
    print("REPROCESSAMENTO CONCLUÍDO")
    print("Log CSV:", csv_log)
    print("Log JSON:", json_log)
    print("======================================")


if __name__ == "__main__":
    main()