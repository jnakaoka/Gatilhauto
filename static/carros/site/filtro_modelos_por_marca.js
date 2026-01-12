(function () {
  const marcaEl = document.getElementById("marcaSelect");
  const modeloEl = document.getElementById("modeloSelect");
  if (!marcaEl || !modeloEl) return;

  function setLoading() {
    modeloEl.innerHTML = '<option value="">A carregar...</option>';
    modeloEl.disabled = true;
  }

  function setEmpty(disabledText) {
    modeloEl.innerHTML = `<option value="">${disabledText}</option>`;
    modeloEl.disabled = true;
  }

  function fill(modelos, selectedId) {
    let html = '<option value="">Modelo</option>';
    modelos.forEach((m) => {
      const sel = selectedId && String(m.id) === String(selectedId) ? " selected" : "";
      html += `<option value="${m.id}"${sel}>${m.nome}</option>`;
    });
    modeloEl.innerHTML = html;
    modeloEl.disabled = false;
  }

  async function load(marcaId, selectedId) {
    if (!marcaId) {
      setEmpty("Escolha a marca primeiro");
      return;
    }

    setLoading();
    const url = new URL("/api/modelos-por-marca/", window.location.origin);
    url.searchParams.set("marca_id", marcaId);

    try {
      const res = await fetch(url.toString());
      const data = await res.json();
      fill(data, selectedId);
    } catch (e) {
      console.error(e);
      setEmpty("Erro ao carregar modelos");
    }
  }

  // Inicial (se veio marca/modelo na querystring)
  const params = new URLSearchParams(window.location.search);
  const selectedModelo = params.get("modelo");

  if (marcaEl.value) {
    load(marcaEl.value, selectedModelo);
  } else {
    setEmpty("Escolha a marca primeiro");
  }

  // Ao mudar marca
  marcaEl.addEventListener("change", () => {
    load(marcaEl.value, "");
  });
})();
