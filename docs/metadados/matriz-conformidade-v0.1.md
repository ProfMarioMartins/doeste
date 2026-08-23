# Matriz de Conformidade do DOESTE v0.1

> Esta matriz é um diagnóstico do estado dos dados em 23 de agosto de 2026 e não constitui autorização para correção automática dos XML.

**Status:** documentação de referência aprovada  
**Base normativa:** Especificação de Metadados do DOESTE v0.2  
**Escopo auditado:** 638 XML do TED e 1.146 XML do TEJ

Todos os 1.784 XML são bem-formados. As porcentagens consideram documentos, não ocorrências.

## 1. Matriz de Conformidade TED

### 1.1 Metadados comuns

| Conceito | TEI/XPath atual | Card. / obrigação | Presença | Ausência | Valores encontrados | Classificação | Ação futura |
|---|---|---|---:|---:|---|---|---|
| `document_id` | `//idno[@type='internal']` | `1`, obrigatório | 634 | 4 — 0,63% | 630 distintos; 4 IDs duplicados | `INCOMPLETO`, `AUSENTE_MAS_OBRIGATORIO` | Resolver ausências e duplicidades com revisão humana |
| `corpus_id` | Ausente | `1`, obrigatório | 0 | 638 — 100% | Nenhum | `AUSENTE_MAS_OBRIGATORIO` | Inserir futuramente `TED`, após homologação |
| `language` | `//language/@ident` | `1`, obrigatório | 635 | 3 — 0,47% | `pt-BR`: 392; `pt-PT`: 243 | `INCOMPLETO` | Completar após verificar fontes |
| `domain` | `//keywords/term`, sem `@type` | `1`, obrigatório | 2 | 636 — 99,69% | `escolar`: 2 | `INCOMPLETO`, `VALOR_NAO_CANONICO`, `ESTRUTURA_NAO_PADRONIZADA` | Migrar para estrutura tipada e `Escolar` após homologação |
| `communicative_purpose` | `//textDesc/purpose` | `0..1`, recomendado | 636 | 2 — 0,31% | `Narrar`: 320; `Argumentar`: 315; `argumentative`: 1 | `INCOMPLETO`, `VALOR_NAO_CANONICO` | Revisar ausências e variante |
| `production_date` | `//settingDesc/setting/date`, com variantes | `1`, obrigatório | 636 | 2 — 0,31% | 2011: 242; 2017: 218; 2018: 117; 2019: 70 | `INCOMPLETO`, `ESTRUTURA_NAO_PADRONIZADA` | Consolidar após revisar duplicações |
| `title` | Ausente | `0..1`, opcional | 0 | 638 — 100% | Nenhum | `CONFORME` | Registrar somente título autêntico |
| `creator_agent` | Participante | `1..*`, obrigatório no perfil | 636 | 2 — 0,31% | 325 códigos | `INCOMPLETO`, `RISCO_DE_EXPOSICAO` | Completar com fonte segura; revisar exposição |
| `provenance` | `affiliation` e `pb/@facs` parcialmente | `1..*`, obrigatório | Parcial | Não mensurável como campo único | 12 códigos; 261 fac-símiles | `ESTRUTURA_NAO_PADRONIZADA`, `RISCO_DE_EXPOSICAO` | Formalizar componentes sem expandir códigos |
| `revision_history` | `//revisionDesc/change` | Recomendado | 638 | 0 | Quatro descrições | `CONFORME` | Preservar |
| `rights_access` | Ausente | Recomendado | 0 | 638 — 100% | Nenhum | `AUSENTE_MAS_RECOMENDADO`, `DECISAO_PENDENTE` | Definir acesso e licença |

### 1.2 Metadados específicos

| Conceito | TEI/XPath atual | Card. / obrigação | Presença | Ausência | Valores encontrados | Classificação | Ação futura |
|---|---|---|---:|---:|---|---|---|
| `participant_id` | `//person/persName` | `1`, obrigatório | 636 | 2 — 0,31% | 325 códigos | `INCOMPLETO`, `RISCO_DE_EXPOSICAO` | Revisar completude e exposição combinada |
| `age_at_production` | `//person/age` | `0..1`, recomendado | 636 | 2 — 0,31% | Faixa numérica 10–34; uma ocorrência `1O` | `INCOMPLETO`, `VALOR_NAO_CANONICO`, `RISCO_DE_EXPOSICAO` | Confirmar `1O` documentalmente |
| `participant_gender` | Fisicamente `//person/sex` | `0..1`, opcional | 636 | 2 — 0,31% | `Male`: 293; `Female`: 353; `female`: 1 | `VALOR_NAO_CANONICO`, `ESTRUTURA_NAO_PADRONIZADA`, `RISCO_DE_EXPOSICAO` | Definir vocabulário antes de normalizar |
| `participant_residence` | `//person/residence` | `0..1`, recomendado | 636 | 2 — 0,31% | Caraúbas: 215; Lisboa: 243; Mossoró: 70; Umarizal: 108 | `INCOMPLETO`, `RISCO_DE_EXPOSICAO` | Preservar; revisar combinações públicas |
| `educational_institution_id` | `//person/affiliation` | `0..1`, recomendado | 636 | 2 — 0,31% | 12 códigos internos | `INCOMPLETO`, `RISCO_DE_EXPOSICAO` | Não expandir códigos; revisar acesso |
| `education_system` | Ausente | `1`, obrigatório no perfil futuro | 0 | 638 — 100% | Nenhum | `AUSENTE_MAS_OBRIGATORIO`, `DECISAO_PENDENTE` | Preencher futuramente com fonte documentada |
| `school_year` | `//person/education` | `1`, obrigatório no perfil futuro | 636 | 2 — 0,31% | `5`: 128; `7`: 92; `9`: 82; `10`: 99; `12`: 234; `12th`: 1 | `INCOMPLETO`, `VALOR_NAO_CANONICO`, `RISCO_DE_EXPOSICAO` | Revisar `12th`; não equiparar BR/PT |
| `production_place` | Ausente | Opcional | 0 | 638 | Nenhum | `DECISAO_PENDENTE` | Não inferir de residência ou escola |
| `collection_cohort` | Ausente | Opcional | 0 | 638 | Nenhum | `CONFORME` | Registrar somente com fonte |
| `original_witness` | `//pb/@facs` | Opcional | 261 | 377 — 59,09% | 261 referências | `CONFORME`, `RISCO_DE_EXPOSICAO` | Verificar anonimização |
| tarefa/proposta | Metodologia | Não obrigatória por XML | — | — | — | `NAO_APLICAVEL` | Documentar metodologicamente |

### 1.3 Distribuição linguística

| Língua | Documentos | Percentual |
|---|---:|---:|
| `pt-BR` | 392 | 61,44% |
| `pt-PT` | 243 | 38,09% |
| Sem `@ident` válido | 3 | 0,47% |

Língua, residência, instituição e diretórios oferecem indícios para `education_system`, mas nenhum deve ser usado isoladamente para inferência automática. É necessária fonte metodológica documentada.

## 2. Matriz de Conformidade TEJ

### 2.1 Metadados comuns

| Conceito | TEI/XPath atual | Card. / obrigação | Presença | Ausência | Valores encontrados | Classificação | Ação futura |
|---|---|---|---:|---:|---|---|---|
| `document_id` | `//tei:idno[@type='internal']` e `TEI/@xml:id` | `1`, obrigatório | 1.146 | 0 | 1.146 distintos | `CONFORME` | Preservar |
| `corpus_id` | `//tei:keywords[@type='corpus']/tei:term` | `1`, obrigatório | 1.146 | 0 | `TEJ`: 1.146 | `CONFORME` | Preservar |
| `language` | `//tei:language/@ident` | `1`, obrigatório | 1.146 | 0 | `pt-BR`: 1.146 | `CONFORME` | Preservar |
| `domain` | `//tei:keywords[@type='domain']/tei:term` | `1`, obrigatório | 1.146 | 0 | `Jornalístico`: 1.146 | `CONFORME` | Preservar |
| `communicative_purpose` | `//tei:textDesc/tei:purpose` | `0..1`, recomendado | 1.146 | 0 | `Noticiar`: 1.146 | `CONFORME` | Preservar |
| `publication_date` | `//tei:date[@type='publication']/@when` | `1`, obrigatório | 1.146 | 0 | 2020–2025 | `CONFORME` | Preservar precisão |
| `title` | Principal e subtítulo | Principal obrigatório | 1.146 | 0 | 1.140 títulos principais distintos | `CONFORME` | Não normalizar duplicações textuais automaticamente |
| `creator_agent` | `//tei:titleStmt/tei:author` | Opcional | 0 | 1.146 | Nenhum | `CONFORME` | `not_recorded`; sem recuperação retroativa |
| `provenance` | `publisher` e `ref/@target` | Obrigatório | 1.146 | 0 | `G1`; 1.146 URLs | `CONFORME` | Preservar |
| `revision_history` | `//tei:revisionDesc/tei:change` | Recomendado | 1.146 | 0 | Uma descrição | `CONFORME` | Preservar |
| `rights_access` | Ausente | Recomendado | 0 | 1.146 | Nenhum | `AUSENTE_MAS_RECOMENDADO`, `DECISAO_PENDENTE` | Definir acesso e licença |

### 2.2 Metadados específicos

| Conceito | TEI/XPath atual | Card. / obrigação | Presença | Ausência | Valores encontrados | Classificação | Ação futura |
|---|---|---|---:|---:|---|---|---|
| `main_title` | `//title[@type='main']` | `1`, obrigatório | 1.146 | 0 | 1.140 distintos | `CONFORME` | Preservar |
| `subtitle` | `//title[@type='sub']` | Opcional | 1.146 | 0 | 1.126 distintos | `CONFORME` | Preservar |
| `article_author` | `//titleStmt/author` | Opcional | 0 | 1.146 | Nenhum | `CONFORME` | Não recuperar retroativamente |
| `publisher` | `//publicationStmt/publisher` | `1`, obrigatório | 1.146 | 0 | `G1`: 1.146 | `CONFORME` | Preservar |
| `source_url` | `//sourceDesc/bibl/ref/@target` | `1`, obrigatório | 1.146 | 0 | 1.146 URLs | `CONFORME` | Futuramente testar sintaxe/disponibilidade |
| `theme` | `//keywords[@type='theme']/term` | Recomendado | 1.146 | 0 | Educação: 296; Economia: 300; Política: 300; Saúde: 250 | `CONFORME` | Documentar vocabulário |
| `journalistic_genre` | Ausente | Não normalizar | 0 | 1.146 | Nenhum | `DECISAO_PENDENTE` | Não inferir de `Noticiar` |
| `section` | Ausente | Opcional | 0 | 1.146 | Nenhum | `CONFORME` | Considerar em novas coletas |
| `retrieval_date` | Ausente | Recomendada apenas futuramente | 0 | 1.146 | Nenhum | `CONFORME` para o legado | Não inventar |
| `content_snapshot_status` | Ausente | Opcional | 0 | 1.146 | Nenhum | `CONFORME` | Avaliar em novas coletas |

Todos os IDs do TEJ são únicos; `document_id`, `xml:id` e nome do arquivo coincidem. Datas textuais e `@when` coincidem. Não há valores não canônicos nos campos controlados examinados.

A numeração vai a `TEJ_1150`, sem `TEJ_0047` a `TEJ_0050`. É lacuna de sequência, não não conformidade.

## 3. Inconsistências estruturais do TED

### 3.1 Namespace

637 documentos não usam namespace TEI e um usa o namespace oficial:

- `ted/xmlfiles/Quinto_Fundamental/aaos_2_5_ejo.xml`

Ele também não possui `document_id` e registra língua como texto, não em `@ident`.

Classificação: `ESTRUTURA_NAO_PADRONIZADA`.

### 3.2 Cabeçalhos incompletos

- `ted/xmlfiles/Quinto_Fundamental/.xml`
- `ted/xmlfiles/Terceiro_Médio/ovm_2_12_esg.xml`

Possuem texto e histórico, mas não o conjunto esperado de metadados. `.xml` também é nome físico excepcional.

Classificação: `AUSENTE_MAS_OBRIGATORIO`, `ESTRUTURA_NAO_PADRONIZADA`.

### 3.3 Estruturas duplicadas

Há 13 documentos com mais de um `<person>`. Em vários, o segundo contém somente gênero duplicado. Parte do grupo tem datas duplicadas. Isso parece duplicação parcial, não dois participantes plenamente documentados, e não deve ser removido automaticamente.

Classificação: `ESTRUTURA_NAO_PADRONIZADA`.

### 3.4 IDs duplicados

| ID | Arquivos |
|---|---|
| `CS22` | `cs2_2_10a_fdl.xml`; `csf_2_10a_hnn.xml` |
| `MFSX1` | `mfsx_1_5_ejo.xml`; `mfsx_1_12_esg.xml` |
| `MFSX2` | `mfsx_2_5_ejo.xml`; `mfsx_2_12_esg.xml` |
| `CS32` | `cs3_1_7a_atd.xml`; `cs3_2_7a_atd.xml` |

Oito arquivos são afetados. Novos IDs exigem revisão humana.

## 4. Divergências entre XML e `settings.xml`

### TED

- `corpus_id`: obrigatório na v0.2, ausente nos XML e configuração atual.
- `domain`: XPath genérico; somente dois XML, sem `keywords/@type`.
- `language`: o XPath espera `@ident`; um documento usa texto.
- `participant_gender`: conceito v0.2, chave física ainda `sex` por decisão.
- `education_system`: sem representação ou filtro.
- `title`: opcional, sem representação atual.
- fac-símile: existe no corpo, não como metadado editável.
- datas e `<person>` duplicados podem produzir valores duplicados no TEITOK.

### TEJ

- autor configurado, mas ausente e opcional;
- `retrieval_date` ausente e não configurada, aceitável para legado;
- corpus e domínio são editáveis, mas não filtros documentais atuais;
- namespace uniforme;
- campos obrigatórios alinhados;
- XPaths sem prefixo explícito dependem do TEITOK e devem ser testados em homologação.

## 5. Resumo quantitativo

### TED

- 638/638 sem `corpus_id`;
- 636/638 sem `domain`;
- 638/638 sem `education_system`;
- 4 sem `document_id`;
- 4 IDs duplicados, afetando 8 arquivos;
- 3 sem língua BCP 47 em `@ident`;
- 2 sem propósito;
- 2 sem data de produção;
- 2 sem participante e metadados associados;
- 1 propósito não canônico;
- 1 gênero com capitalização não canônica;
- 1 ano escolar não canônico;
- 1 idade `1O`;
- 13 com mais de um `<person>`;
- 11 com mais de uma data de produção detectada;
- 1 com namespace divergente;
- 2 cabeçalhos substancialmente incompletos;
- 1 nome excepcional `.xml`;
- 261 com fac-símile sujeito a avaliação.

Excluindo lacunas globais, 25 XML possuem ao menos um problema individualizado.

### TEJ

- nenhum obrigatório ausente;
- nenhum ID duplicado ou divergente;
- nenhum valor controlado não canônico;
- nenhum problema de namespace;
- autor ausente, mas opcional e `not_recorded`;
- `retrieval_date` ausente, mas não exigida no legado;
- política de direitos/acesso ainda ausente.

## 6. Lista dos 25 XML para análise individual

1. `ted/xmlfiles/Primeiro_Médio/cs2_2_10a_fdl.xml`
2. `ted/xmlfiles/Primeiro_Médio/csf_2_10a_hnn.xml`
3. `ted/xmlfiles/Quinto_Fundamental/.xml`
4. `ted/xmlfiles/Quinto_Fundamental/aaos_2_5_ejo.xml`
5. `ted/xmlfiles/Quinto_Fundamental/dsra_2_5h_mda.xml`
6. `ted/xmlfiles/Quinto_Fundamental/mfsx_1_5_ejo.xml`
7. `ted/xmlfiles/Quinto_Fundamental/mfsx_2_5_ejo.xml`
8. `ted/xmlfiles/Sétimo_Fundamental/cs3_1_7a_atd.xml`
9. `ted/xmlfiles/Sétimo_Fundamental/cs3_2_7a_atd.xml`
10. `ted/xmlfiles/Terceiro_Médio/aklm_2_12_elgo.xml`
11. `ted/xmlfiles/Terceiro_Médio/cbco_2_12_eeoa.xml`
12. `ted/xmlfiles/Terceiro_Médio/dwsc_1_12_eeoa.xml`
13. `ted/xmlfiles/Terceiro_Médio/jwcj_1_12_esg.xml`
14. `ted/xmlfiles/Terceiro_Médio/jwcj_2_12_esg.xml`
15. `ted/xmlfiles/Terceiro_Médio/mfsx_1_12_esg.xml`
16. `ted/xmlfiles/Terceiro_Médio/mfsx_2_12_esg.xml`
17. `ted/xmlfiles/Terceiro_Médio/nfgp_2_12_elgo.xml`
18. `ted/xmlfiles/Terceiro_Médio/nswx_1_12_esg.xml`
19. `ted/xmlfiles/Terceiro_Médio/ovm_2_12_esg.xml`
20. `ted/xmlfiles/Terceiro_Médio/prsp_1_12_elgo.xml`
21. `ted/xmlfiles/Terceiro_Médio/rbsx_1_12_elgo.xml`
22. `ted/xmlfiles/Terceiro_Médio/slsy_1_12_eeoa.xml`
23. `ted/xmlfiles/Terceiro_Médio/vccs_1_12_esg.xml`
24. `ted/xmlfiles/Terceiro_Médio/vccs_2_12_esg.xml`
25. `ted/xmlfiles/Terceiro_Médio/wmsx_2_12_elgo.xml`

Todos os 638 XML do TED exigirão intervenção futura para `corpus_id`, `domain` e, após definição de fonte, `education_system`. O TEJ não possui XML que exija intervenção por campo obrigatório na v0.2.

## 7. Correções potencialmente automáticas de baixo risco

Ainda exigem homologação, transformação reproduzível e revisão de diff:

1. inserir `corpus_id=TED` após confirmar XPath;
2. inserir/normalizar `domain=Escolar`;
3. mapear `argumentative` para `Argumentar` após confirmação;
4. normalizar `female` após aprovar vocabulário;
5. normalizar `12th` após confirmar semântica;
6. ajustar língua para `@ident` quando inequívoca;
7. detectar IDs, ausências e cardinalidades, sem escolher novos IDs;
8. detectar duplicações idênticas, sem removê-las automaticamente.

`education_system` não é de baixo risco até a fonte ser formalizada.

## 8. Problemas que exigem decisão humana

- IDs ausentes e duplicados;
- arquivo `.xml` e cabeçalhos incompletos;
- elementos `<person>` adicionais e datas duplicadas;
- idade `1O`;
- fonte de `education_system`;
- namespace TED;
- vocabulário de `participant_gender`;
- direitos e acesso;
- títulos autênticos;
- propósito e metadados ausentes;
- filtros públicos de corpus/domínio no TEJ.

## 9. Problemas que exigem revisão ética

- combinação de participante, instituição, idade, residência, ano, gênero e texto;
- códigos pseudonímicos;
- expansão de códigos escolares;
- fac-símiles;
- valores raros e grupos pequenos;
- filtros que permitam reidentificação;
- licença de reutilização/redistribuição;
- diferença entre acesso científico e acesso público.

## 10. Ordem de migração recomendada

1. Preservar esta matriz como baseline de conformidade.
2. Resolver `.xml`, cabeçalhos, IDs e duplicações estruturais individualizadas.
3. Aprovar vocabulários e fontes de gênero, sistema e ano escolar.
4. Testar em homologação os XPaths tipados, TEITOK, CQP e reindexação.
5. Migrar, em commits separados, `corpus_id=TED` e `domain=Escolar`.
6. Normalizar separadamente propósito, gênero, ano, língua e idade.
7. Preencher `education_system` somente com fonte e regra auditável.
8. Reindexar e validar em homologação.
9. Aplicar política de exposição antes de ampliar filtros.
10. Implantar em produção somente após aprovação e plano de rollback.

## 11. Estrutura futura dos relatórios completos

```text
docs/auditoria/metadados-v0.1/
├── README.md
├── matriz-ted.csv
├── matriz-tej.csv
├── diagnostico-documentos-ted.csv
├── diagnostico-documentos-tej.csv
├── valores-distintos-ted.csv
├── valores-distintos-tej.csv
└── resumo.md
```

Os relatórios documentais deverão evitar reproduzir valores sensíveis: poderão registrar presença, cardinalidade, classificação, hash e identificador controlado.
