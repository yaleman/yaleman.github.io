(() => {
  const searchInput = document.getElementById("repo-search");
  if (!(searchInput instanceof HTMLInputElement)) {
    return;
  }

  const cards = Array.from(document.querySelectorAll(".repo-card[data-repo-name]"));
  const sections = Array.from(document.querySelectorAll(".repo-section"));
  const emptyState = document.getElementById("search-empty");
  const totalCount = cards.length;
  const totalCountLabel = document.getElementById("repo-total-count");
  const languageFilters = Array.from(
    document.querySelectorAll(".language-filter[data-language]"),
  );
  const searchableText = (card) => {
    const repoName = card.dataset.repoName || "";
    const repoLanguage = card.dataset.repoLanguage || "";
    const repoDescription = card.dataset.repoDescription || "";
    return `${repoName} ${repoLanguage} ${repoDescription}`.toLowerCase();
  };

  const selectedLanguages = () =>
    new Set(
      languageFilters
        .filter(
          (button) =>
            button.dataset.language &&
            button.getAttribute("aria-pressed") === "true",
        )
        .map((button) => button.dataset.language || ""),
    );

  const setButtonPressed = (button, isPressed) => {
    button.setAttribute("aria-pressed", isPressed ? "true" : "false");
    button.classList.toggle("is-active", isPressed);
  };

  const applyLanguageAvailability = () => {
    const availableLanguages = new Set(
      cards.map((card) => (card.dataset.repoLanguage || "unknown").toLowerCase()),
    );
    const allButton = languageFilters.find(
      (button) => (button.dataset.language || "") === "",
    );

    for (const button of languageFilters) {
      const language = (button.dataset.language || "").toLowerCase();
      if (language === "") {
        button.hidden = false;
        continue;
      }
      const isAvailable = availableLanguages.has(language);
      button.hidden = !isAvailable;
      if (!isAvailable) {
        setButtonPressed(button, false);
      }
    }

    if (allButton && selectedLanguages().size === 0) {
      setButtonPressed(allButton, true);
    }
  };

  const applyFilter = () => {
    const query = searchInput.value.trim().toLowerCase();
    const activeLanguages = selectedLanguages();
    const hasLanguageFilter = activeLanguages.size > 0;
    const isFiltering = query !== "" || hasLanguageFilter;
    let visibleCards = 0;

    for (const card of cards) {
      const cardLanguage = (card.dataset.repoLanguage || "unknown").toLowerCase();
      const queryMatches = query === "" || searchableText(card).includes(query);
      const languageMatches =
        !hasLanguageFilter || activeLanguages.has(cardLanguage);
      const isVisible = queryMatches && languageMatches;
      card.hidden = !isVisible;
      if (isVisible) {
        visibleCards += 1;
      }
    }

    for (const section of sections) {
      if (!isFiltering) {
        section.hidden = false;
        continue;
      }
      const hasVisibleCard = section.querySelector(".repo-card:not([hidden])") !== null;
      section.hidden = !hasVisibleCard;
    }

    if (emptyState) {
      emptyState.hidden = !isFiltering || visibleCards > 0;
    }

    if (totalCountLabel) {
      totalCountLabel.textContent = `Public repositories: ${visibleCards}/${totalCount}`;
    }

    for (const section of sections) {
      const sectionCount = section.querySelector(".section-count");
      if (!(sectionCount instanceof HTMLElement)) {
        continue;
      }
      const sectionTotal = Number.parseInt(sectionCount.dataset.total || "0", 10);
      const sectionVisible = section.querySelectorAll(".repo-card:not([hidden])").length;
      sectionCount.textContent = `Repositories: ${sectionVisible}/${sectionTotal}`;
    }
  };

  for (const button of languageFilters) {
    button.addEventListener("click", () => {
      const language = button.dataset.language || "";
      const allButton = languageFilters.find(
        (filterButton) => (filterButton.dataset.language || "") === "",
      );

      if (language === "") {
        for (const filterButton of languageFilters) {
          setButtonPressed(
            filterButton,
            (filterButton.dataset.language || "") === "",
          );
        }
        applyFilter();
        return;
      }

      setButtonPressed(button, button.getAttribute("aria-pressed") !== "true");
      if (allButton) {
        setButtonPressed(allButton, false);
      }

      const hasAnySpecificFilter = selectedLanguages().size > 0;
      if (!hasAnySpecificFilter && allButton) {
        setButtonPressed(allButton, true);
      }
      applyFilter();
    });
  }

  applyLanguageAvailability();
  searchInput.addEventListener("input", applyFilter);
  applyFilter();
})();
