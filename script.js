// script.js

let corpus = [];
let featsLabels = {};
let posToFeats = {};  // Mapa: POS -> Set de feats
let featsChoices = null;

// Carrega o corpus JSON quando a página abre
fetch("doeste_teste.json")
  .then(response => response.json())
  .then(data => {
    corpus = data;
    console.log("Corpus carregado:", corpus.length, "sentenças");

    const featsSet = new Set();
    posToFeats = {};

    // Coletar feats únicos e construir o mapa pos -> feats
    corpus.forEach(sent => {
      sent.tokens.forEach(tok => {
        if (!posToFeats[tok.pos]) posToFeats[tok.pos] = new Set();
        if (tok.feats) {
          tok.feats.split("|").forEach(feat => {
            featsSet.add(feat.trim());
            posToFeats[tok.pos].add(feat.trim());
          });
        }
      });
    });

    featsLabels = {
      "Mood=Sub": "Modo subjuntivo",
      "Mood=Ind": "Modo indicativo",
      "Mood=Imp": "Modo imperativo",
      "Tense=Past": "Tempo passado",
      "Tense=Pres": "Tempo presente",
      "VerbForm=Inf": "Forma infinitiva",
      "VerbForm=Fin": "Forma finita",
      "VerbForm=Part": "Particípio",
      "VerbForm=Ger": "Gerúndio",
      "PronType=Int": "Pronome interrogativo",
      "PronType=Rel": "Pronome relativo",
      "PronType=Dem": "Pronome demonstrativo",
      "Number=Sing": "Número singular",
      "Number=Plur": "Número plural",
      "Gender=Masc": "Gênero masculino",
      "Gender=Fem": "Gênero feminino",
      "Person=1": "1ª pessoa",
      "Person=2": "2ª pessoa",
      "Person=3": "3ª pessoa"
    };

    inicializarFeats(Array.from(featsSet));
  });

// Inicializa o seletor feats com um conjunto de traços
function inicializarFeats(featsArray) {
  const featsSelect = document.getElementById("featsOpcional");
  featsSelect.innerHTML = "";

  featsArray.sort().forEach(feat => {
    const opt = document.createElement("option");
    opt.value = feat;
    opt.textContent = (featsLabels[feat] || feat) + " (" + feat + ")";
    featsSelect.appendChild(opt);
  });

  if (featsChoices) featsChoices.destroy();
  featsChoices = new Choices(featsSelect, {
    removeItemButton: true,
    shouldSort: true,
    placeholderValue: "Selecione um ou mais traços...",
    searchEnabled: false
  });
}

// Atualiza dinamicamente os traços com base nos POS selecionados
function atualizarFeatsComBaseNosPOS() {
  const posSelecionadas = Array.from(document.getElementById("posOpcional").selectedOptions).map(opt => opt.value);
  if (posSelecionadas.length === 0) {
    // Se nada selecionado, mostra todos os feats
    const todas = new Set();
    Object.values(posToFeats).forEach(set => set.forEach(feat => todas.add(feat)));
    inicializarFeats(Array.from(todas));
  } else {
    const filtrados = new Set();
    posSelecionadas.forEach(pos => {
      const feats = posToFeats[pos];
      if (feats) feats.forEach(f => filtrados.add(f));
    });
    inicializarFeats(Array.from(filtrados));
  }
}

// Atualiza a versão do script no rodapé
document.addEventListener("DOMContentLoaded", function () {
  const agora = new Date();
  const dataHora = agora.toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
  const spanVersao = document.getElementById("versao-script");
  if (spanVersao) {
    spanVersao.textContent = dataHora;
  }
});


function buscar() {
  const termo = document.getElementById("busca").value.trim().toLowerCase();
  const tipoBusca = document.getElementById("tipoBusca").value;
  const posSelecionadas = Array.from(document.getElementById("posOpcional").selectedOptions).map(opt => opt.value);
  const featsSelecionadas = Array.from(document.getElementById("featsOpcional").selectedOptions).map(opt => opt.value);

  const resultados = document.getElementById("resultados");
  resultados.innerHTML = "";

  if (!corpus || corpus.length === 0) {
    resultados.innerHTML = "<p>Corpus não carregado.</p>";
    return;
  }

  let encontrados = corpus.filter(sent =>
    sent.tokens.some(tok => {
      const formaOk = !termo || (
        tipoBusca === "forma" && tok.forma?.toLowerCase().includes(termo) ||
        tipoBusca === "lema" && tok.lema?.toLowerCase().includes(termo) ||
        tipoBusca === "pos" && tok.pos?.toLowerCase().includes(termo) ||
        tipoBusca === "feats" && tok.feats?.toLowerCase().includes(termo) ||
        tipoBusca === "todos" && (
          tok.forma?.toLowerCase().includes(termo) ||
          tok.lema?.toLowerCase().includes(termo) ||
          tok.pos?.toLowerCase().includes(termo) ||
          tok.feats?.toLowerCase().includes(termo)
        )
      );

      const posOk = posSelecionadas.length === 0 || posSelecionadas.includes(tok.pos);
      const featsOk = featsSelecionadas.length === 0 || featsSelecionadas.every(f => tok.feats?.includes(f));

      return formaOk && posOk && featsOk;
    })
  );

  const total = encontrados.reduce((acc, sent) =>
    acc + sent.tokens.filter(tok => {
      const formaOk = !termo || (
        tipoBusca === "forma" && tok.forma?.toLowerCase().includes(termo) ||
        tipoBusca === "lema" && tok.lema?.toLowerCase().includes(termo) ||
        tipoBusca === "pos" && tok.pos?.toLowerCase().includes(termo) ||
        tipoBusca === "feats" && tok.feats?.toLowerCase().includes(termo) ||
        tipoBusca === "todos" && (
          tok.forma?.toLowerCase().includes(termo) ||
          tok.lema?.toLowerCase().includes(termo) ||
          tok.pos?.toLowerCase().includes(termo) ||
          tok.feats?.toLowerCase().includes(termo)
        )
      );
      const posOk = posSelecionadas.length === 0 || posSelecionadas.includes(tok.pos);
      const featsOk = featsSelecionadas.length === 0 || featsSelecionadas.every(f => tok.feats?.includes(f));
      return formaOk && posOk && featsOk;
    }).length, 0);

  resultados.innerHTML += `<p><strong>${total}</strong> ocorrência(s) encontrada(s).</p>`;

  encontrados.forEach(sent => {
    sent.tokens.forEach((tok, idx) => {
      const match =
        (!termo || tok.forma?.toLowerCase().includes(termo) || tok.lema?.toLowerCase().includes(termo)) &&
        (posSelecionadas.length === 0 || posSelecionadas.includes(tok.pos)) &&
        (featsSelecionadas.length === 0 || featsSelecionadas.every(f => tok.feats?.includes(f)));

      if (match) {
        const esquerda = sent.tokens.slice(Math.max(0, idx - 5), idx).map(t => t.forma).join(" ");
        const centro = `<strong>${tok.forma}</strong>`;
        const direita = sent.tokens.slice(idx + 1, idx + 6).map(t => t.forma).join(" ");
        resultados.innerHTML += `
          <pre>${esquerda.padStart(30)}  |  ${centro}  |  ${direita}</pre>
        `;
      }
    });
  });
}

function exportarCSV() {
  const preTags = document.querySelectorAll("#resultados pre");
  if (!preTags.length) return alert("Nenhum resultado para exportar.");

  const linhas = ["esquerda,termo,direita"];
  preTags.forEach(pre => {
    const partes = pre.textContent.trim().split("  |  ");
    if (partes.length === 3) {
      const [esq, centro, dir] = partes.map(s => s.trim().replace(/,/g, ""));
      linhas.push(`"${esq}","${centro}","${dir}"`);
    }
  });

  const blob = new Blob([linhas.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resultados_doeste.csv";
  a.click();
  URL.revokeObjectURL(url);
}
