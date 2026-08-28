# Corpus TEK — Redações Nota Mil

Esta árvore contém a implementação local do TEK no DOESTE.

- `xmlfiles_source/`: TEI-fonte canônicos. Não contêm anotação linguística derivada.
- `xmlfiles/`: TEI anotados derivados, destinados à publicação no TEITOK.
- `pipeline/`: pipeline lossless usado para gerar os TEI anotados de publicação.
- `Resources/settings.xml`: configuração TEITOK e dos filtros documentais.
- `Pages/` e `templates/`: documentação pública e interface do corpus.
- `scripts/build_cqp.py`: gerador reproduzível do vertical e dos índices CQP.
- `tests/`: testes de integridade textual e estrutural.

Arquitetura aprovada:

```text
TEI-fonte canônico → pipeline de anotação → TEI anotado de publicação → TEITOK/CQP
```

Os arquivos de `xmlfiles/` são completamente regeneráveis a partir de
`xmlfiles_source/`, do pipeline e do modelo UDPipe
`portuguese-bosque-ud-2.17-251125`, versão fixada no pipeline e registrada em
cada XML. Os índices CQP também são derivados.

O download em massa e a implantação pública não fazem parte desta fase.

## Índice CQP e XIDX do TEITOK

O corpus CQP principal mantém uma posição por unidade ortográfica. Em
multiword tokens, os atributos dos `dtok` são agregados com `+`; a coluna
`word` continua contendo a forma superficial, como `da`, sem expansão para
`de a`.

```bash
python3 tek/scripts/build_cqp.py
python3 tek/tests/test_local_configuration.py
```

O build de homologação ou produção requer `tt-cwb-encode`. O comando é
executado a partir da raiz de `tek/`, onde lê `Resources/settings.xml` e os
documentos de `xmlfiles/`. Além dos binários CWB, esse encoder gera
`cqp/xidx.rng` e os índices estruturais usados por `tt-cwb-xidx` e pela
apresentação KWIC do TEITOK. Em seguida, o script executa `cwb-makeall`.

O encoder CWB padrão não produz XIDX. Em um ambiente local sem
`tt-cwb-encode`, é possível validar explicitamente o vertical, as contagens e
as consultas CQP, mas o resultado não constitui um build de produção:

```bash
python3 tek/scripts/build_cqp.py --local-validation
python3 tek/tests/test_local_configuration.py
```

A validação final de publicação, incluindo a existência de `cqp/xidx.rng`,
deve ser executada no ambiente TEITOK que forneça `tt-cwb-encode`.

Os artefatos de `cqp/` são derivados e permanecem fora do Git pelas regras
gerais do DOESTE.

O registry é gerado em `cqp/tek`, pois o runtime do TEITOK usa
`registryfolder="cqp"` e resolve esse caminho diretamente a partir da raiz do
corpus. Os binários CWB, como `word.corpus`, também são gravados diretamente
em `cqp/`; o registry registra esse diretório absoluto em `HOME` e usa
`cqp/.info` em `INFO`. Os antigos diretórios `cqp/registry/` e `cqp/data/` não
fazem parte da arquitetura de publicação.

## Runtime TEITOK

O TEITOK continua sendo uma dependência externa. Para abrir a interface, o
ambiente local deve fornecer PHP e definir `TT_ROOT` para uma instalação
compatível do TEITOK. A instalação-base não é copiada para este repositório.
