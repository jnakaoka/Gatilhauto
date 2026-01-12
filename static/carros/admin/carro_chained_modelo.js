(function () {
  const $ = window.django && window.django.jQuery ? window.django.jQuery : null;
  if (!$) return;

  function getMarcaId() {
    const marcaEl = document.getElementById("id_marca");
    return marcaEl ? marcaEl.value : "";
  }

  function clearModelo() {
    const modeloEl = document.getElementById("id_modelo");
    if (!modeloEl) return;
    $(modeloEl).val(null).trigger("change");
    modeloEl.value = "";
  }

  function toggleModeloEnabled() {
    const modeloEl = document.getElementById("id_modelo");
    if (!modeloEl) return;
    const marcaId = getMarcaId();
    modeloEl.disabled = !marcaId;
    if (!marcaId) clearModelo();
  }

  // ✅ Intercepta TODAS as chamadas do autocomplete e injeta marca_id quando for o campo modelo
  $.ajaxPrefilter(function (options) {
    if (!options.url) return;

    // só mexe no autocomplete do admin
    if (!options.url.includes("/admin/autocomplete/")) return;

    try {
      const url = new URL(options.url, window.location.origin);

      // garante que é o autocomplete do nosso "modelo"
      const modelName = url.searchParams.get("model_name");
      const fieldName = url.searchParams.get("field_name");

      // no Django, normalmente vem model_name=modelo e field_name=modelo (ou algo próximo)
      // aqui filtramos quando o autocomplete é do Modelo do app carros
      const isModelo = modelName === "modelo" || fieldName === "modelo";

      if (!isModelo) return;

      const marcaId = getMarcaId();
      if (marcaId) {
        url.searchParams.set("marca_id", marcaId);
        options.url = url.toString();
      }
    } catch (e) {
      // se der algo estranho, não quebra
    }
  });

  $(document).ready(function () {
    toggleModeloEnabled();

    $("#id_marca").on("change", function () {
      clearModelo();
      toggleModeloEnabled();
    });
  });
})();
