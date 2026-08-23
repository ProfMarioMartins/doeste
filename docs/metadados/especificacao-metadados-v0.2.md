# Especificação de Metadados do DOESTE v0.2

**Status:** especificação conceitual aprovada  
**Escopo:** DOESTE, TED e TEJ  
**Baseline Git:** `1edd46b — Versão inicial do DOESTE`

## 1. Natureza e modelo conceitual

Os nomes `document_id`, `corpus_id`, `document_date`, `creator_agent`, `provenance` e similares identificam conceitos do modelo DOESTE. Eles não constituem novos elementos XML e não devem ser transformados automaticamente em elementos. A implementação continuará baseada em TEI, com mapeamentos TEI/XPath documentados por perfil.

```text
DOESTE
├── Repositório: identidade, versão, baseline e manifesto
├── Corpus: corpus_id, perfil, metodologia, vocabulários e acesso
├── Documento
│   ├── document_id, corpus_id, language e domain
│   ├── communicative_purpose e document_date
│   ├── title, creator_agent e provenance
│   └── rights_access e revision_history
├── Agente: participante, autor, instituição ou publisher
└── Anotação linguística: token, lema, classe, traços e dependências
```

Distinções obrigatórias:

- propósito comunicativo, gênero e domínio são conceitos distintos;
- gênero não será inferido nem normalizado nesta etapa;
- participante do TED e autor do TEJ são papéis distintos de `creator_agent`;
- escola, publisher e URL são componentes distintos de `provenance`;
- produção, publicação, coleta, recuperação e atualização Git são datas distintas;
- existência, disponibilidade para pesquisa e exposição pública são dimensões independentes;
- consentimento científico não equivale a licença de redistribuição.

## 2. Núcleo comum

| Conceito | Cardinalidade | Obrigatoriedade | Aplicabilidade | Exposição padrão |
|---|---:|---|---|---|
| `document_id` | `1` | Obrigatório | Todos | Pública/técnica |
| `corpus_id` | `1` | Obrigatório | Todos | Pública |
| `language` | `1..*` | Obrigatório | Todos | Pública |
| `domain` | `1` | Obrigatório | Todos | Pública |
| `communicative_purpose` | `0..1` | Recomendado | Quando identificável | Pública |
| `document_date` | `1..*` | Obrigatório com tipo | Todos | Pública |
| `title` | `0..1` | Condicional | Quando autêntico | Pública |
| `creator_agent` | `0..*` | Condicional | Conforme corpus | Dependente do papel |
| `provenance` | `1..*` | Obrigatório | Todos | Variável |
| `revision_history` | `0..*` | Recomendado | Documentos processados | Técnica |
| `rights_access` | `0..*` | Recomendado | Corpus/documento | Pública/técnica |

`document_id` deve ser estável, único no corpus, não reutilizável e independente do nome do arquivo. A forma `DOESTE:{corpus_id}:{document_id}` é conceitual e não precisa ser armazenada literalmente.

Valores atuais de `corpus_id`: `TED` e `TEJ`.

### 2.1 Vocabulários controlados

Língua, em BCP 47:

| Valor | Rótulo |
|---|---|
| `pt-BR` | Português brasileiro |
| `pt-PT` | Português europeu |

Domínio, exatamente um por documento:

| Corpus | Valor |
|---|---|
| TED | `Escolar` |
| TEJ | `Jornalístico` |

Propósito comunicativo, no máximo um por documento:

| Valor | Nota de escopo |
|---|---|
| `Narrar` | Relatar uma sequência de acontecimentos, reais ou imaginados, organizados temporalmente. |
| `Argumentar` | Defender, justificar ou discutir uma posição por meio de razões, argumentos ou evidências. |
| `Noticiar` | Informar sobre acontecimentos de interesse público em contexto jornalístico. |

O propósito não será usado para inferir gênero.

Tipos de data:

| Tipo | Significado |
|---|---|
| `production` | Produção do texto |
| `publication` | Publicação |
| `collection` | Coleta |
| `digitization` | Digitalização |
| `retrieval` | Recuperação de recurso externo |

TED usa principalmente `production`; TEJ, `publication`. As datas seguirão ISO 8601 na precisão conhecida, sem completar artificialmente mês ou dia.

## 3. Mapeamento TEI/XPath atual

| Conceito | TED atual | TEJ atual | Estado |
|---|---|---|---|
| `document_id` | `/TEI/teiHeader/fileDesc/sourceDesc/bibl/idno[@type='internal']` | Equivalente com namespace | Existente |
| ID XML | Não padronizado | `/tei:TEI/@xml:id` | Específico do TEJ |
| `corpus_id` | Ausente | `//tei:keywords[@type='corpus']/tei:term` | Lacuna no TED |
| `language` | `//langUsage/language/@ident` | Equivalente com namespace | Existente |
| `domain` | `//textClass/keywords/term` | `//tei:keywords[@type='domain']/tei:term` | TED incompleto/pouco tipado |
| `communicative_purpose` | `//textDesc/purpose` | Equivalente com namespace | Existente |
| `production_date` | `//settingDesc/setting/date` | Não é data principal | TED |
| `publication_date` | Não aplicável | `//publicationStmt/date[@type='publication']` | TEJ |
| `title` | Ausente atualmente | `//titleStmt/title` | Opcional/obrigatório |
| participante | `//particDesc/listPerson/person/persName` | Não aplicável | Existente |
| autor | Não aplicável | `//titleStmt/author` | Configurado, ausente |
| `publisher` | Não aplicável | `//publicationStmt/publisher` | Existente |
| URL | Não aplicável | `//sourceDesc/bibl/ref/@target` | Existente |
| `revision_history` | `//revisionDesc/change` | Equivalente com namespace | Existente |
| `rights_access` | Ausente | Ausente | Futuro |

`tei:` representa `http://www.tei-c.org/ns/1.0`. O TED não usa uniformemente o namespace oficial. A migração é desejável, mas não será feita agora.

Direções futuras, sujeitas a homologação:

```text
TED domain    → keywords[@type='domain']/term
TED corpus_id → keywords[@type='corpus']/term
```

Toda migração deverá preservar ou adaptar controladamente TEITOK, XPaths, Query Builder, CQP, índices e visualização/edição. Nenhuma migração estrutural será testada primeiro em produção.

## 4. Perfil TED v0.2

### 4.1 Campos comuns

| Conceito | Cardinalidade | Obrigatoriedade | Cobertura atual | Exposição |
|---|---:|---|---:|---|
| `document_id` | `1` | Obrigatório | 634/638 | Pública/técnica |
| `corpus_id` | `1` | Obrigatório | 0/638 | Pública |
| `language` | `1` | Obrigatório | ~635/638 | Pública |
| `domain` | `1` | Obrigatório | 2/638 | Pública |
| `communicative_purpose` | `0..1` | Recomendado | ~635/638 | Pública |
| `production_date` | `1` | Obrigatório | ~635/638 | Pública |
| `title` | `0..1` | Opcional | 0/638 | Pública se autêntico |
| `creator_agent` | `1..*` | Obrigatório no perfil atual | ~635/638 | Potencialmente sensível |
| `provenance` | `1..*` | Obrigatório | Parcial | Variável |
| `revision_history` | `0..*` | Recomendado | Maioria | Técnica |
| `rights_access` | `0..*` | Recomendado | Ausente | Pública/técnica |

### 4.2 Campos específicos

| Conceito | XPath atual | Cardinalidade | Obrigatoriedade | Exposição |
|---|---|---:|---|---|
| `participant_id` | `//person/persName` | `1` | Obrigatório | Pendente/restrita |
| `age_at_production` | `//person/age` | `0..1` | Recomendado | Sensível em combinação |
| `participant_gender` | `//person/sex` | `0..1` | Opcional | Sensível em combinação |
| `participant_residence` | `//person/residence` | `0..1` | Recomendado | Sensível em combinação |
| `educational_institution_id` | `//person/affiliation` | `0..1` | Recomendado | Sensível em combinação |
| `education_system` | Ausente | `1` | Obrigatório no perfil futuro | Sensível em combinação |
| `school_year` | `//person/education` | `1` | Obrigatório no perfil futuro | Sensível em combinação |
| `title` | Ausente | `0..1` | Opcional | Pública se autêntico |
| `production_place` | Ausente | `0..1` | Opcional | Sensível |
| `collection_cohort` | Ausente | `0..1` | Opcional | Restrita/técnica |
| `original_witness` | `//pb/@facs` | `0..*` | Opcional | Após anonimização |

Decisões semânticas:

- `age_at_production` é a idade no momento da produção.
- O `<sex>` atual representa gênero informado pelo participante; o conceito é `participant_gender`, sem mudança física agora.
- `participant_residence` é a residência no momento da produção, não local da escola, coleta, produção ou naturalidade.
- `education_system` (`BR` ou `PT`) e `school_year` são separados, sem equivalência automática.
- A fonte de `education_system` deverá ser documentada e revisável.
- `affiliation` contém identificadores institucionais internos; não expandir ou publicar nomes sem documentação e revisão ética.
- Título autêntico é opcional; não criar título editorial para preencher ausência.
- A tarefa de escrita será documentada prioritariamente na metodologia, não obrigatoriamente em cada XML.
- Fac-símiles dependem de verificação de anonimização. Nomes ficcionais, inclusive da Turma da Mônica, não são por si identificação pessoal.

Anotações em `tok/text()` e nos atributos `form`, `nform`, `lemma`, `upos`, `pos`, `feats`, `head`, `deprel`, `semclass` e `process` são dados. Alterá-las atualiza a data dos dados.

## 5. Perfil TEJ v0.2

### 5.1 Campos comuns

| Conceito | Cardinalidade | Obrigatoriedade | Cobertura | Exposição |
|---|---:|---|---:|---|
| `document_id` | `1` | Obrigatório | 1.146/1.146 | Pública/técnica |
| `corpus_id` | `1` | Obrigatório | 1.146/1.146 | Pública |
| `language` | `1` | Obrigatório | 1.146/1.146 | Pública |
| `domain` | `1` | Obrigatório | 1.146/1.146 | Pública |
| `communicative_purpose` | `0..1` | Recomendado | 1.146/1.146 | Pública |
| `publication_date` | `1` | Obrigatório | 1.146/1.146 | Pública |
| `title` | principal `1`; subtítulo opcional | Obrigatório | Completo | Pública |
| `creator_agent` | `0..*` | Opcional | Autor ausente | Pública se registrado |
| `provenance` | `1..*` | Obrigatório | Completo | Pública |
| `revision_history` | `0..*` | Recomendado | Completo | Técnica |
| `rights_access` | `0..*` | Recomendado | Ausente | Pública/técnica |

### 5.2 Campos específicos

| Conceito | XPath atual | Cardinalidade | Obrigatoriedade | Exposição |
|---|---|---:|---|---|
| `main_title` | `//title[@type='main']` | `1` | Obrigatório | Pública |
| `subtitle` | `//title[@type='sub']` | `0..1` | Opcional | Pública |
| `article_author` | `//titleStmt/author` | `0..*` | Opcional | Pública se conhecido |
| `publisher` | `//publicationStmt/publisher` | `1` | Obrigatório | Pública |
| `source_url` | `//sourceDesc/bibl/ref/@target` | `1` | Obrigatório | Pública |
| `publication_date` | `//date[@type='publication']` | `1` | Obrigatório | Pública |
| `theme` | `//keywords[@type='theme']/term` | `1` atual | Recomendado | Pública |
| `journalistic_genre` | Ausente | `0..1` | Não normalizar | Pública quando definido |
| `section` | Ausente | `0..1` | Opcional | Pública |
| `retrieval_date` | Ausente | `0..1` | Recomendada para novas coletas | Técnica/pública |
| `content_snapshot_status` | Ausente | `0..1` | Opcional | Técnica |

O autor não será recuperado retroativamente: sua ausência no legado é `not_recorded`. Manter apenas `publisher`, sem `source_publication`. Não inventar `retrieval_date`. Alterações em `<tok>` e atributos contam como atualização dos dados.

## 6. Política de valores ausentes

| Estado | Significado |
|---|---|
| `unknown` | Aplicável, mas desconhecido |
| `not_recorded` | Não coletado ou registrado |
| `not_applicable` | Não se aplica |
| `withheld` | Existe, mas foi retido |
| `pending_review` | Aguarda validação |

Os estados permanecem conceituais; o mapeamento TEI será proposto posteriormente.

Regras: ausência não equivale a `not_applicable`; campo obrigatório ausente é lacuna; não usar vazio para ocultar ausência; não inferir sem regra; não confundir retido e desconhecido; complementações deverão ser reproduzíveis e revisadas por diff. `domain=Escolar` e `corpus_id=TED` são lacunas conhecidas. Autor ausente no TEJ existente é `not_recorded`.

## 7. Consentimento, acesso e exposição

As amostras brasileira e portuguesa do TED foram coletadas com autorização formal equivalente para participação, uso científico e proteção. Isso não determina acesso aberto, exposição individual, licença ou redistribuição.

Devem ser distinguidos:

1. consentimento para participação e uso científico;
2. política de acesso aos dados;
3. licença de reutilização e redistribuição.

Nenhuma licença é definida nesta etapa.

| Campo TED | Existe | Pesquisa | Exposição individual |
|---|---|---|---|
| IDs, idade, gênero, residência e instituição | Sim | Condicionada à política | Pendente |
| `education_system` e `school_year` | Sim/futuro | Sim | Avaliar em combinação |
| fac-símile | Sim | Condicionada | Somente após anonimização |
| língua, domínio e propósito | Sim | Sim | Pública |

Combinações de participante, instituição, idade, cidade/residência, ano escolar, gênero e fac-símile são potencialmente sensíveis. Códigos pseudonímicos podem ser reidentificáveis quando cruzados. A avaliação deve considerar filtros, tamanho de grupos, cruzamento externo, raridade e exposição conjunta de texto e metadados.

Fac-símiles públicos exigem verificação de nomes reais, assinaturas, dados escolares, identificadores, referências familiares, marcas no suporte e metadados embutidos.

## 8. Validação formal futura

É desejável um perfil ODD/RNG próprio do DOESTE, baseado em TEI, com núcleo comum, especializações, cardinalidades, vocabulários e XPaths. Deve respeitar a diferença atual de namespace e ser testado primeiro em homologação. Criar o esquema não autoriza migrar XML.

## 9. Manifesto de publicação

O manifesto será preferencialmente XML, gerado na implantação, separado dos XML dos corpora e sem consulta ao Git em tempo de execução.

Versão global:

```text
DOESTE vX.Y.Z
```

Baseline:

```text
1edd46b — Versão inicial do DOESTE
incorporação: 23 de agosto de 2026
```

Escopos de dados: `ted/xmlfiles/**/*.xml` e `tej/xmlfiles/**/*.xml`. Interface/documentação, configuração, portal e scripts terão escopos separados.

Sem commit posterior ao baseline que altere XML:

> Dados incorporados ao histórico versionado do DOESTE em 23 de agosto de 2026.

Após a primeira alteração pós-baseline:

> Última atualização dos dados: [data].

Alteram a data: inclusão/remoção de XML, metadados TEI, texto, normalização, `<tok>`, atributos, anotação e estrutura. Não alteram: páginas, CSS, templates, documentação, traduções, configuração sem XML e scripts sem XML versionado.

Na página principal aparecerá somente a data dos dados. Versão, SHA, commits, datas de interface/configuração/implantação e validação ficarão em Informações técnicas.

Timestamps serão ISO 8601 UTC, localizados somente na interface.

Estrutura conceitual:

```xml
<doesteReleaseManifest schemaVersion="0.2">
  <baseline>...</baseline>
  <release>...</release>
  <corpora>
    <corpus id="TED">...</corpus>
    <corpus id="TEJ">...</corpus>
  </corpora>
</doesteReleaseManifest>
```

O esquema XML definitivo ainda será refinado.

## 10. Regras para futuros corpora

Todo corpus terá perfil próprio com ID, descrição, domínio único, BCP 47, data tipada, propósito quando identificável, proveniência, acesso, TEI/XPath, cardinalidades, vocabulários, campos específicos, exposição e escopo Git.

Não poderá redefinir conceitos comuns, fundir propósito/gênero/domínio, usar ano sem tipo, equiparar papéis, presumir equivalências educacionais, criar valores sem registro, interpretar ausência como não aplicabilidade ou migrar diretamente em produção.

## 11. Decisões aprovadas

- modelo conceitual separado da representação TEI;
- `domain` obrigatório, único e canônico (`Escolar`/`Jornalístico`);
- `corpus_id` obrigatório;
- BCP 47;
- propósito monovalorado com notas de escopo;
- propósito, gênero e domínio distintos;
- sem inferência de gênero textual;
- semântica aprovada de idade, gênero e residência;
- `education_system` separado de `school_year`;
- códigos institucionais internos;
- título TED opcional e autêntico;
- tarefa de escrita prioritariamente na metodologia;
- fac-símiles condicionados à anonimização;
- autor TEJ não recuperado retroativamente;
- `retrieval_date` apenas recomendada para futuras coletas;
- somente `publisher` por enquanto;
- namespace TED, XPaths tipados e ODD/RNG como direções futuras;
- homologação obrigatória;
- consentimentos BR/PT equivalentes para uso científico;
- existência, acesso e exposição separados;
- risco combinatório de reidentificação;
- consentimento, acesso e licença separados;
- manifesto XML, SemVer global e baseline `1edd46b`;
- atualização pública derivada do Git pós-baseline;
- `<tok>` conta como dado; interface/documentação não altera data dos dados.

## 12. Decisões futuras orientadas

- namespace TEI oficial no TED;
- `keywords[@type='domain']/term` e `keywords[@type='corpus']/term` no TED;
- ODD/RNG e mapeamento TEI da ausência;
- manifesto e página técnica;
- normalização e completude;
- políticas formais de acesso e licença;
- avaliação de fac-símiles.

## 13. Questões abertas

1. Política concreta de acesso aos XML, metadados e fac-símiles do TED.
2. Licença de reutilização e redistribuição.
3. Combinações publicamente exibíveis no TED.
4. Procedimento formal de anonimização de fac-símiles.
5. Fonte de `education_system`.
6. Vocabulário de `participant_gender`.
7. Apresentação dos anos BR/PT sem equivalência automática.
8. Mapeamento TEI dos estados de ausência.
9. Desenho ODD/RNG.
10. Integração e esquema definitivo do manifesto XML.
11. Primeira versão SemVer e critérios `major/minor/patch`.
12. Página de Informações técnicas.
13. Obrigatoriedade final de `communicative_purpose` nos perfis TED e TEJ.
