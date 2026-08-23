import os
import xml.etree.ElementTree as ET

PASTA_XML = "/var/www/html/teitok/tej/xmlfiles"

upos_set = set()
deprel_set = set()

for root_dir, _, files in os.walk(PASTA_XML):
    for file in files:
        if file.endswith(".xml"):
            caminho = os.path.join(root_dir, file)
            try:
                tree = ET.parse(caminho)
                root = tree.getroot()

                for elem in root.iter():
                    if elem.tag.endswith("tok"):
                        if "upos" in elem.attrib:
                            upos_set.add(elem.attrib["upos"])
                        if "deprel" in elem.attrib:
                            deprel_set.add(elem.attrib["deprel"])

            except Exception as e:
                print(f"Erro em {file}: {e}")

def gerar_select(nome, valores):
    print(f'\n<select name="{nome}" attribute="{nome}">')
    for v in sorted(valores):
        print(f'  <option value="{v}">{v}</option>')
    print('</select>')

print("=== UPOS ===")
gerar_select("upos", upos_set)

print("\n=== DEPREL ===")
gerar_select("deprel", deprel_set)
