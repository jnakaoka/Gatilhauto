(function () {
  // Só pra garantir que estás a ver execução
  console.log("[carro_modelos_por_marca] carregado");

  function getEndpoint() {
    // Funciona em:
    // /admin/carros/carro/add/
    // /admin/carros/carro/1/change/
    const path = window.location.pathname;

    // pega a base "/admin/carros/carro/"
    const match = path.match(/(\/admin\/carros\/carro\/)(add\/|\d+\/change\/)?/);
    const base = match ? match[1] : "/admin/carros/carro/";

    return base + "modelos-por-marca/";
  }

  function setLoading(modeloEl) {
    modeloEl.innerHTML = '<option value="">A carregar modelos...</option>';
    modeloEl.disabled = true;
  }

  function fillModelos(modeloEl, modelos, modeloSelecionado) {
    modeloEl.innerHTML = '<option value="">Selecione o modelo</option>';
    modelos.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = String(m.id);
      opt.textContent = m.nome;
      modeloEl.appendChild(opt);
    });
    if (modeloSelecionado && modelos.some((m) => String(m.id) === String(modeloSelecionado))) {
      modeloEl.value = String(modeloSelecionado);
      const modeloAtual = document.getElementById("id_modelo_atual");
      if (modeloAtual) modeloAtual.value = String(modeloSelecionado);
    }
    modeloEl.disabled = false;
  }

  async function loadModelosByMarca(marcaId, modeloSelecionado = "") {
    const modeloEl = document.getElementById("id_modelo");
    if (!modeloEl) return;

    console.log("[carro_modelos_por_marca] marcaId =", marcaId);

    if (!marcaId) {
      modeloEl.innerHTML = '<option value="">Selecione a marca primeiro</option>';
      modeloEl.disabled = true;
      return;
    }

    setLoading(modeloEl);

    try {
      const url = new URL(getEndpoint(), window.location.origin);
      url.searchParams.set("marca_id", marcaId);

      console.log("[carro_modelos_por_marca] GET", url.toString());

      const res = await fetch(url.toString(), {
        method: "GET",
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      fillModelos(modeloEl, data, modeloSelecionado);
    } catch (e) {
      console.error("[carro_modelos_por_marca] erro", e);
      modeloEl.innerHTML = '<option value="">Erro ao carregar modelos</option>';
      modeloEl.disabled = true;
    }
  }

  // ✅ Event delegation: não quebra se o admin recriar o select
  document.addEventListener("change", function (e) {
    if (e.target && e.target.id === "id_marca") {
      const modeloAtual = document.getElementById("id_modelo_atual");
      if (modeloAtual) modeloAtual.value = "";
      loadModelosByMarca(e.target.value);
    }
    if (e.target && e.target.id === "id_modelo") {
      const modeloAtual = document.getElementById("id_modelo_atual");
      if (modeloAtual) modeloAtual.value = e.target.value;
    }
  });

  // Estado inicial (no change/edit, quando abre a página com marca já definida)
  document.addEventListener("DOMContentLoaded", function () {
    const marcaEl = document.getElementById("id_marca");
    const modeloEl = document.getElementById("id_modelo");
    if (!marcaEl || !modeloEl) return;

    if (!marcaEl.value) {
      modeloEl.innerHTML = '<option value="">Selecione a marca primeiro</option>';
      modeloEl.disabled = true;
    } else {
      // Preserva o modelo atual ao editar ou quando o formulário volta com erros.
      const modeloAtual = document.getElementById("id_modelo_atual");
      const modeloSelecionado = (modeloAtual && modeloAtual.value) || modeloEl.value;
      loadModelosByMarca(marcaEl.value, modeloSelecionado);
    }
  });
})();
