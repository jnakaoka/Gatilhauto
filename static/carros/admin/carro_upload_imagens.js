(function () {
  function getEndpoint() {
    const match = window.location.pathname.match(/(\/admin\/carros\/carro\/)(add\/|\d+\/change\/)?/);
    const base = match ? match[1] : "/admin/carros/carro/";
    return base + "upload-imagem-temporaria/";
  }

  function getCookie(name) {
    return document.cookie
      .split(";")
      .map((item) => item.trim())
      .find((item) => item.startsWith(name + "="))
      ?.split("=")
      .slice(1)
      .join("=") || "";
  }

  function readItems(hidden) {
    try {
      const value = JSON.parse(hidden.value || "[]");
      return Array.isArray(value) ? value : [];
    } catch (_error) {
      return [];
    }
  }

  function renderStatus(status, items, message) {
    const names = items.map((item) => item.nome).filter(Boolean);
    status.textContent = message || (names.length
      ? `${names.length} imagem(ns) pronta(s): ${names.join(", ")}`
      : "Selecione uma ou mais imagens.");
  }

  async function uploadOne(file) {
    const body = new FormData();
    body.append("imagem", file);
    const response = await fetch(getEndpoint(), {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": decodeURIComponent(getCookie("csrftoken")) },
      body,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.erro || `Erro HTTP ${response.status}`);
    return result;
  }

  document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("id_novas_imagens");
    const hidden = document.getElementById("id_imagens_temporarias");
    if (!input || !hidden) return;

    const status = document.createElement("div");
    status.className = "help";
    status.style.marginTop = "8px";
    input.insertAdjacentElement("afterend", status);

    let items = readItems(hidden);
    renderStatus(status, items);

    input.addEventListener("change", async function () {
      const files = Array.from(input.files || []);
      if (!files.length) return;

      input.disabled = true;
      try {
        for (let index = 0; index < files.length; index += 1) {
          renderStatus(status, items, `A enviar ${index + 1} de ${files.length}: ${files[index].name}`);
          const uploaded = await uploadOne(files[index]);
          items.push({ token: uploaded.token, nome: uploaded.nome });
          hidden.value = JSON.stringify(items);
        }
        // Os arquivos já estão temporariamente no servidor; assim não são
        // reenviados junto com o formulário e sobrevivem a erros de validação.
        input.value = "";
        renderStatus(status, items);
      } catch (error) {
        renderStatus(status, items, `Falha no upload: ${error.message}`);
      } finally {
        input.value = "";
        input.disabled = false;
      }
    });
  });
})();
