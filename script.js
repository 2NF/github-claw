const menuToggle = document.querySelector(".menu-toggle");
const siteNav = document.querySelector("#site-nav");
const filterStatus = document.querySelector("#filter-status");
const filterLabels = {
  all: "全部主题",
  foundation: "基础认知",
  build: "构建应用",
  practice: "实践工具",
};
const topicCards = [...document.querySelectorAll(".topic-card")];

function closeSiteNav(restoreFocus = false) {
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "打开导航");
  siteNav.classList.remove("is-open");
  if (restoreFocus) menuToggle.focus();
}

filterStatus.textContent = `显示全部 ${topicCards.length} 个精选主题`;

menuToggle.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  if (isOpen) {
    closeSiteNav();
    return;
  }
  menuToggle.setAttribute("aria-expanded", "true");
  menuToggle.setAttribute("aria-label", "关闭导航");
  siteNav.classList.add("is-open");
});

siteNav.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    closeSiteNav();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
    closeSiteNav(true);
  }
});

document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    document.querySelectorAll(".filter-chip").forEach((chip) => {
      const isActive = chip === button;
      chip.classList.toggle("is-active", isActive);
      chip.setAttribute("aria-pressed", String(isActive));
    });
    let visibleCount = 0;
    topicCards.forEach((card) => {
      card.hidden = filter !== "all" && card.dataset.category !== filter;
      if (!card.hidden) visibleCount += 1;
    });
    filterStatus.textContent = `显示${filterLabels[filter]} ${visibleCount} 个精选主题`;
  });
});
