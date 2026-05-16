(function () {
  const data = window.BIBLE_DATA;
  const state = {
    script: localStorage.getItem("bible-script") || "simplified",
    book: localStorage.getItem("bible-book") || "JHN",
    chapter: Number(localStorage.getItem("bible-chapter") || 3),
    testament: "all",
    query: "",
    activeSearch: "",
  };

  const els = {
    root: document.documentElement,
    bookList: document.getElementById("bookList"),
    bookSelect: document.getElementById("bookSelect"),
    chapterSelect: document.getElementById("chapterSelect"),
    chapterTitle: document.getElementById("chapterTitle"),
    chapterSubtitle: document.getElementById("chapterSubtitle"),
    versionName: document.getElementById("versionName"),
    verses: document.getElementById("verses"),
    searchInput: document.getElementById("searchInput"),
    searchMeta: document.getElementById("searchMeta"),
    searchResults: document.getElementById("searchResults"),
    prevChapter: document.getElementById("prevChapter"),
    nextChapter: document.getElementById("nextChapter"),
    themeToggle: document.getElementById("themeToggle"),
  };

  const bookByCode = new Map(data.books.map((book) => [book.code, book]));
  const bookAliases = buildBookAliases();
  let searchTimer = 0;

  function bookName(book, script = state.script) {
    return book[script];
  }

  function chapterData(bookCode = state.book, chapter = state.chapter, script = state.script) {
    return data.chapters[script][bookCode][String(chapter)];
  }

  function otherScript() {
    return state.script === "simplified" ? "traditional" : "simplified";
  }

  function pairedVerseText(bookCode, chapter, verseNumber) {
    const pairedChapter = chapterData(bookCode, chapter, otherScript());
    const pairedVerse = pairedChapter.verses.find((verse) => verse.n === verseNumber);
    return pairedVerse ? pairedVerse.t : "";
  }

  function buildBookAliases() {
    const aliases = new Map();
    const extraAliases = {
      GEN: ["创", "創"],
      EXO: ["出"],
      LEV: ["利"],
      NUM: ["民"],
      DEU: ["申"],
      JOS: ["书", "書", "约书亚", "約書亞"],
      JDG: ["士"],
      RUT: ["得", "路得"],
      "1SA": ["撒上", "撒母耳上"],
      "2SA": ["撒下", "撒母耳下"],
      "1KI": ["王上", "列王上"],
      "2KI": ["王下", "列王下"],
      "1CH": ["代上", "历上", "歷上"],
      "2CH": ["代下", "历下", "歷下"],
      EZR: ["拉", "以斯拉"],
      NEH: ["尼", "尼希米"],
      EST: ["斯", "以斯帖"],
      JOB: ["伯", "约伯", "約伯"],
      PSA: ["诗", "詩", "诗篇", "詩篇"],
      PRO: ["箴"],
      ECC: ["传", "傳", "传道", "傳道"],
      SNG: ["歌", "雅"],
      ISA: ["赛", "賽", "以赛亚", "以賽亞"],
      JER: ["耶", "耶利米"],
      LAM: ["哀"],
      EZK: ["结", "結", "以西结", "以西結"],
      DAN: ["但"],
      HOS: ["何"],
      JOL: ["珥", "约珥", "約珥"],
      AMO: ["摩", "摩司", "阿摩司"],
      OBA: ["俄", "俄巴底亚", "俄巴底亞"],
      JON: ["拿", "约拿", "約拿"],
      MIC: ["弥", "彌", "弥迦", "彌迦"],
      NAM: ["鸿", "鴻", "那鸿", "那鴻"],
      HAB: ["哈", "哈巴谷"],
      ZEP: ["番", "西番雅"],
      HAG: ["该", "該", "哈该", "哈該"],
      ZEC: ["亚", "亞", "撒迦利亚", "撒迦利亞"],
      MAL: ["玛", "瑪", "玛拉基", "瑪拉基"],
      MAT: ["太", "马太", "馬太"],
      MRK: ["可", "马可", "馬可"],
      LUK: ["路"],
      JHN: ["约", "約", "约翰", "約翰"],
      ACT: ["徒", "使徒"],
      ROM: ["罗", "羅", "罗马", "羅馬"],
      "1CO": ["林前", "哥前"],
      "2CO": ["林后", "林後", "哥后", "哥後"],
      GAL: ["加", "加拉太"],
      EPH: ["弗", "以弗所"],
      PHP: ["腓", "腓立比"],
      COL: ["西", "歌罗西", "歌羅西"],
      "1TH": ["帖前"],
      "2TH": ["帖后", "帖後"],
      "1TI": ["提前", "提摩太前"],
      "2TI": ["提后", "提後", "提摩太后", "提摩太後"],
      TIT: ["多", "提多"],
      PHM: ["门", "門", "腓利门", "腓利門"],
      HEB: ["来", "來", "希伯来", "希伯來"],
      JAS: ["雅", "雅各"],
      "1PE": ["彼前"],
      "2PE": ["彼后", "彼後"],
      "1JN": ["约一", "約一", "约壹", "約壹", "约翰一", "約翰一"],
      "2JN": ["约二", "約二", "约贰", "約貳", "约翰二", "約翰二"],
      "3JN": ["约三", "約三", "约叁", "約參", "约翰三", "約翰三"],
      JUD: ["犹", "猶", "犹大", "猶大"],
      REV: ["启", "啟", "启示", "啟示"],
    };

    for (const book of data.books) {
      [
        book.code,
        book.code.toLowerCase(),
        book.simplified,
        book.traditional,
        book.simplified.replace(/[书记]$/, ""),
        book.traditional.replace(/[書記]$/, ""),
      ].forEach((alias) => aliases.set(alias.toLowerCase(), book));

      for (const alias of extraAliases[book.code] || []) {
        aliases.set(alias.toLowerCase(), book);
      }
    }

    return aliases;
  }

  function saveState() {
    localStorage.setItem("bible-script", state.script);
    localStorage.setItem("bible-book", state.book);
    localStorage.setItem("bible-chapter", String(state.chapter));
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[char]));
  }

  function highlightText(text, query) {
    const clean = query.trim();
    if (!clean) return escapeHtml(text);
    return highlightTextAtRanges(text, matchRanges(text, clean));
  }

  function matchRanges(text, query) {
    if (!query) return [];
    const ranges = [];
    let start = 0;
    let index = text.indexOf(query);

    while (index !== -1) {
      ranges.push({ start: index, end: index + query.length });
      start = index + query.length;
      index = text.indexOf(query, start);
    }

    return ranges;
  }

  function highlightTextAtRanges(text, ranges) {
    if (!ranges.length) return escapeHtml(text);
    const parts = [];
    let start = 0;

    for (const range of ranges) {
      parts.push(escapeHtml(text.slice(start, range.start)));
      parts.push("<mark>", escapeHtml(text.slice(range.start, range.end)), "</mark>");
      start = range.end;
    }

    parts.push(escapeHtml(text.slice(start)));
    return parts.join("");
  }

  function highlightVerseText(bookCode, chapter, verse, query) {
    const clean = query.trim();
    if (!clean) return escapeHtml(verse.t);

    const directRanges = matchRanges(verse.t, clean);
    if (directRanges.length) return highlightTextAtRanges(verse.t, directRanges);

    const pairedText = pairedVerseText(bookCode, chapter, verse.n);
    const pairedRanges = matchRanges(pairedText, clean)
      .filter((range) => range.end <= verse.t.length);
    return highlightTextAtRanges(verse.t, pairedRanges);
  }

  function searchHit(bookCode, chapter, verse, query) {
    const displayText = verse.t;
    const pairedText = pairedVerseText(bookCode, chapter, verse.n);
    return displayText.includes(query) || pairedText.includes(query);
  }

  function renderScriptButtons() {
    document.querySelectorAll("[data-script]").forEach((button) => {
      button.classList.toggle("active", button.dataset.script === state.script);
    });
    document.documentElement.lang = state.script === "simplified" ? "zh-Hans" : "zh-Hant";
  }

  function renderBookSelect() {
    els.bookSelect.innerHTML = data.books.map((book) => {
      const selected = book.code === state.book ? " selected" : "";
      return `<option value="${book.code}"${selected}>${bookName(book)}</option>`;
    }).join("");
  }

  function renderChapterSelect() {
    const book = bookByCode.get(state.book);
    els.chapterSelect.innerHTML = Array.from({ length: book.chapters }, (_, index) => {
      const chapter = index + 1;
      const selected = chapter === state.chapter ? " selected" : "";
      return `<option value="${chapter}"${selected}>${chapter}</option>`;
    }).join("");
  }

  function renderBookList() {
    els.bookList.innerHTML = data.books
      .filter((book) => state.testament === "all" || book.testament === state.testament)
      .map((book) => {
        const active = book.code === state.book ? " active" : "";
        return `<button class="${active}" type="button" data-book="${book.code}">${bookName(book)}</button>`;
      })
      .join("");
  }

  function renderChapter(targetRange) {
    const book = bookByCode.get(state.book);
    const chapter = chapterData();
    const range = normalizeRange(targetRange);
    els.versionName.textContent = state.script === "simplified" ? "新标点和合本" : "新標點和合本";
    els.chapterTitle.textContent = `${bookName(book)} ${state.chapter}`;
    els.chapterSubtitle.textContent = chapter.heading || "";
    els.verses.innerHTML = chapter.verses.map((verse) => {
      const notes = verse.notes.length
        ? `<div class="verse-notes">${verse.notes.map(escapeHtml).join("；")}</div>`
        : "";
      const highlightClass = range && verse.n >= range.start && verse.n <= range.end ? " highlight" : "";
      return `
        <div class="verse${highlightClass}" id="v${verse.n}">
          <span class="verse-number">${verse.n}</span>
          <div>
            <span>${highlightVerseText(state.book, state.chapter, verse, state.activeSearch)}</span>
            ${notes}
          </div>
        </div>
      `;
    }).join("");

    els.prevChapter.disabled = !previousRef();
    els.nextChapter.disabled = !nextRef();
    saveState();

    if (range) {
      document.getElementById(`v${range.start}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function renderAll(targetRange) {
    renderScriptButtons();
    renderBookSelect();
    renderChapterSelect();
    renderBookList();
    renderChapter(targetRange);
    runSearch();
  }

  function normalizeRange(range) {
    if (!range) return null;
    const start = Number(range.start || range.verse || range);
    const end = Number(range.end || start);
    if (!start) return null;
    return { start: Math.min(start, end), end: Math.max(start, end) };
  }

  function goTo(bookCode, chapter, range, activeSearch = "") {
    state.book = bookCode;
    state.chapter = Number(chapter);
    state.activeSearch = activeSearch;
    renderAll(range);
  }

  function previousRef() {
    const index = data.books.findIndex((book) => book.code === state.book);
    if (state.chapter > 1) return { book: state.book, chapter: state.chapter - 1 };
    if (index > 0) {
      const previousBook = data.books[index - 1];
      return { book: previousBook.code, chapter: previousBook.chapters };
    }
    return null;
  }

  function nextRef() {
    const book = bookByCode.get(state.book);
    const index = data.books.findIndex((item) => item.code === state.book);
    if (state.chapter < book.chapters) return { book: state.book, chapter: state.chapter + 1 };
    if (index < data.books.length - 1) return { book: data.books[index + 1].code, chapter: 1 };
    return null;
  }

  function parseReference(query) {
    const compact = query
      .replace(/\s+/g, "")
      .replace(/[：.]/g, ":")
      .replace(/[－–—]/g, "-")
      .replace(/章/g, ":")
      .replace(/节/g, "")
      .replace(/節/g, "")
      .replace(/:$/, "");
    const match = compact.match(/^(.+?)(\d+)(?::(\d+)(?:-(\d+))?)?$/);
    if (!match) return null;
    const name = match[1];
    const chapter = Number(match[2]);
    const verse = match[3] ? Number(match[3]) : null;
    const endVerse = match[4] ? Number(match[4]) : verse;
    const book = bookAliases.get(name.toLowerCase());
    if (!book || chapter < 1 || chapter > book.chapters) return null;
    const chapterVerses = chapterData(book.code, chapter).verses;
    const hasVerse = (number) => chapterVerses.some((item) => item.n === number);
    if (verse && (!hasVerse(verse) || !hasVerse(endVerse))) return null;
    return { book: book.code, chapter, verse, endVerse };
  }

  function searchVerses(query) {
    const results = [];
    for (const book of data.books) {
      for (let chapter = 1; chapter <= book.chapters; chapter += 1) {
        for (const verse of chapterData(book.code, chapter).verses) {
          if (searchHit(book.code, chapter, verse, query)) {
            results.push({ book, chapter, verse });
            if (results.length >= 80) return results;
          }
        }
      }
    }
    return results;
  }

  function runSearch() {
    const query = state.query.trim();
    if (!query) {
      els.searchMeta.textContent = "输入简体或繁体关键词搜索整本圣经";
      els.searchResults.innerHTML = "";
      return;
    }

    const ref = parseReference(query);
    if (ref) {
      els.searchMeta.textContent = "识别为经文引用";
      const verseLabel = ref.verse ? `:${ref.verse}${ref.endVerse && ref.endVerse !== ref.verse ? `-${ref.endVerse}` : ""}` : "";
      els.searchResults.innerHTML = `<button class="result-item" type="button" data-book="${ref.book}" data-chapter="${ref.chapter}" data-verse="${ref.verse || ""}" data-end-verse="${ref.endVerse || ""}">
        <span class="result-ref">${bookName(bookByCode.get(ref.book))} ${ref.chapter}${verseLabel}</span>
        <span class="result-text">打开这一处经文</span>
      </button>`;
      return;
    }

    const results = searchVerses(query);
    els.searchMeta.textContent = results.length ? `显示前 ${results.length} 条结果` : "没有找到匹配经文";
    els.searchResults.innerHTML = results.map(({ book, chapter, verse }) => `
      <button class="result-item" type="button" data-book="${book.code}" data-chapter="${chapter}" data-verse="${verse.n}" data-search-query="${escapeHtml(query)}">
        <span class="result-ref">${bookName(book)} ${chapter}:${verse.n}</span>
        <span class="result-text">${highlightVerseText(book.code, chapter, verse, query)}</span>
      </button>
    `).join("");
  }

  document.querySelectorAll("[data-script]").forEach((button) => {
    button.addEventListener("click", () => {
      state.script = button.dataset.script;
      renderAll();
    });
  });

  document.querySelectorAll("[data-testament]").forEach((button) => {
    button.addEventListener("click", () => {
      state.testament = button.dataset.testament;
      document.querySelectorAll("[data-testament]").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      renderBookList();
    });
  });

  els.bookList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-book]");
    if (button) goTo(button.dataset.book, 1);
  });

  els.bookSelect.addEventListener("change", () => goTo(els.bookSelect.value, 1));
  els.chapterSelect.addEventListener("change", () => goTo(state.book, Number(els.chapterSelect.value)));

  els.prevChapter.addEventListener("click", () => {
    const ref = previousRef();
    if (ref) goTo(ref.book, ref.chapter);
  });

  els.nextChapter.addEventListener("click", () => {
    const ref = nextRef();
    if (ref) goTo(ref.book, ref.chapter);
  });

  els.searchInput.addEventListener("input", () => {
    state.query = els.searchInput.value;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(runSearch, 120);
  });

  els.searchInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const ref = parseReference(els.searchInput.value);
    if (!ref) return;
    event.preventDefault();
    goTo(ref.book, ref.chapter, { start: ref.verse, end: ref.endVerse });
  });

  els.searchResults.addEventListener("click", (event) => {
    const button = event.target.closest("[data-book]");
    if (!button) return;
    const activeSearch = button.dataset.searchQuery || "";
    goTo(button.dataset.book, Number(button.dataset.chapter), {
      start: Number(button.dataset.verse || 0),
      end: Number(button.dataset.endVerse || button.dataset.verse || 0),
    }, activeSearch);
  });

  els.themeToggle.addEventListener("click", () => {
    els.root.classList.toggle("dark");
    localStorage.setItem("bible-theme", els.root.classList.contains("dark") ? "dark" : "light");
  });

  if (localStorage.getItem("bible-theme") === "dark") {
    els.root.classList.add("dark");
  }

  renderAll();
}());
