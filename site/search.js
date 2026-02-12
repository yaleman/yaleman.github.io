(() => {
  const searchInput = document.getElementById("repo-search");
  if (!(searchInput instanceof HTMLInputElement)) {
    return;
  }

  const cards = Array.from(document.querySelectorAll(".repo-card[data-repo-name]"));
  const sections = Array.from(document.querySelectorAll(".repo-section"));
  const emptyState = document.getElementById("search-empty");
  const searchableText = (card) => {
    const repoName = card.dataset.repoName || "";
    const repoLanguage = card.dataset.repoLanguage || "";
    const repoDescription = card.dataset.repoDescription || "";
    return `${repoName} ${repoLanguage} ${repoDescription}`.toLowerCase();
  };

  const applyFilter = () => {
    const query = searchInput.value.trim().toLowerCase();
    let visibleCards = 0;

    for (const card of cards) {
      const isVisible = query === "" || searchableText(card).includes(query);
      card.hidden = !isVisible;
      if (isVisible) {
        visibleCards += 1;
      }
    }

    for (const section of sections) {
      if (query === "") {
        section.hidden = false;
        continue;
      }
      const hasVisibleCard = section.querySelector(".repo-card:not([hidden])") !== null;
      section.hidden = !hasVisibleCard;
    }

    if (emptyState) {
      emptyState.hidden = query === "" || visibleCards > 0;
    }
  };

  searchInput.addEventListener("input", applyFilter);
  applyFilter();
})();
