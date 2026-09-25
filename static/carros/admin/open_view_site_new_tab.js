document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("#user-tools a").forEach(function (link) {
    const text = link.textContent.trim().toLowerCase();
    if (text === "ver site" || text === "view site") {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  });
});
