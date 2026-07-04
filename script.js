const filterButtons = Array.from(document.querySelectorAll("[data-filter]"));
const publicationsSection = document.querySelector(".publications");
const publications = Array.from(document.querySelectorAll(".publication"));

function keywordsFor(publication) {
  return (publication.dataset.keywords || "")
    .split("|")
    .map((keyword) => keyword.trim())
    .filter(Boolean);
}

function setActiveFilter(keyword) {
  const nextKeyword =
    publicationsSection.dataset.activeFilter === keyword ? "" : keyword;

  publicationsSection.dataset.activeFilter = nextKeyword;
  publicationsSection.classList.toggle("has-active-filter", Boolean(nextKeyword));

  filterButtons.forEach((button) => {
    const isActive = button.dataset.filter === nextKeyword;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  publications.forEach((publication) => {
    const isMatch = nextKeyword && keywordsFor(publication).includes(nextKeyword);
    publication.classList.toggle("is-highlighted", Boolean(isMatch));

    publication.querySelectorAll(".pub-keywords [data-filter]").forEach((chip) => {
      chip.classList.toggle("is-matched", chip.dataset.filter === nextKeyword);
    });
  });
}

filterButtons.forEach((button) => {
  button.setAttribute("aria-pressed", "false");
  button.addEventListener("click", () => setActiveFilter(button.dataset.filter));
});
