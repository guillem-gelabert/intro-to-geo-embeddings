// Reader for the prebuilt course bundle. No Python runs here and none ever will:
// every figure and printed table below came out of the executed solution notebooks
// at build time. Progress lives in localStorage -- single-device by design.

const main = document.getElementById("main");
const crumb = document.getElementById("crumb");
const back = document.getElementById("back");
const pct = document.getElementById("pct");
const rail = document.getElementById("rail");
const foot = document.getElementById("foot");
const prev = document.getElementById("prev");
const next = document.getElementById("next");

const STORE = "geo-course-progress";

function progress() {
  try {
    return JSON.parse(localStorage.getItem(STORE) || "{}");
  } catch {
    return {};
  }
}

function markDone(slug, key) {
  const all = progress();
  const done = new Set(all[slug] || []);
  done.add(key);
  all[slug] = [...done];
  try {
    localStorage.setItem(STORE, JSON.stringify(all));
  } catch {
    /* private browsing; progress is a convenience, not a requirement */
  }
}

function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

// Answers are compared shape-first: whitespace and quote style are not the lesson.
function normalize(text) {
  return text.trim().replace(/\s+/g, " ").replace(/'/g, '"').replace(/,$/, "");
}

async function get(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} -> ${response.status}`);
  return response.json();
}

/* -------------------------------------------------------------- index --- */

async function renderIndex() {
  const { modules } = await get("/api/index");
  const done = progress();
  crumb.textContent = "Geospatial Embeddings";
  back.hidden = true;
  foot.hidden = true;
  pct.textContent = "";
  rail.style.width = "0%";
  document.title = "Geospatial Embeddings";

  main.replaceChildren();
  main.append(el("h1", null, "Geospatial embeddings"));
  main.append(
    el(
      "p",
      "lede",
      "Read-along companion. Figures and tables are the real notebook output, " +
        "baked in at build time. Code runs in the notebooks, not here."
    )
  );

  const list = el("ul", "toc");
  modules.forEach((module) => {
    const total = module.blanks + module.quiz;
    const finished = (done[module.slug] || []).length;
    const item = el("li");
    const link = el("a");
    link.href = `/m/${module.slug}`;
    // The slug prefix, not a loop counter -- the titles carry their own module
    // numbering and two competing numbers on one row is just noise.
    link.append(el("span", "num", module.slug.split("-")[0]));
    link.append(el("span", "name", module.title));
    const meta = el(
      "span",
      total && finished >= total ? "meta done" : "meta",
      total ? `${finished}/${total}` : `${module.blocks} blocks`
    );
    link.append(meta);
    link.addEventListener("click", route);
    item.append(link);
    list.append(item);
  });
  main.append(list);
}

/* ------------------------------------------------------------- blocks --- */

function renderOutput(block) {
  const wrap = document.createDocumentFragment();
  if (block.text) wrap.append(el("pre", "out", escapeHtml(block.text)));
  for (const src of block.images) {
    const figure = el("figure");
    const img = el("img");
    img.src = src;
    img.loading = "lazy";
    img.alt = "Figure from the executed notebook";
    figure.append(img);
    wrap.append(figure);
  }
  return wrap;
}

function escapeHtml(text) {
  return text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
}

function renderBlank(block, slug, key, onDone) {
  const card = el("div", "card");
  card.append(el("h4", null, "Fill in the blanks"));
  if (block.before) card.append(el("pre", null, escapeHtml(block.before)));

  const inputs = [];
  for (const line of block.lines) {
    if (line.kind === "given") {
      card.append(el("div", "given", escapeHtml(line.text)));
      continue;
    }
    const row = el("div", "blank-line");
    row.append(el("span", "lhs", escapeHtml(`${line.indent}${line.lhs} =`)));
    const input = el("input");
    input.type = "text";
    input.autocapitalize = "off";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.setAttribute("aria-label", `value for ${line.lhs}`);
    row.append(input);
    card.append(row);
    inputs.push({ input, row, answer: line.answer });
  }

  if (block.after) card.append(el("pre", null, escapeHtml(block.after)));

  const verdict = el("div", "verdict");
  const row = el("div", "row");
  const check = el("button", null, "Check");
  const reveal = el("button", "ghost", "Reveal");

  check.addEventListener("click", () => {
    let allRight = true;
    for (const item of inputs) {
      const right = normalize(item.input.value) === normalize(item.answer);
      item.row.className = `blank-line ${right ? "right" : "wrong"}`;
      allRight = allRight && right;
    }
    verdict.className = `verdict ${allRight ? "right" : "wrong"}`;
    verdict.textContent = allRight
      ? "Matches the notebook."
      : "Not yet — compare against the surrounding lines.";
    if (allRight) {
      markDone(slug, key);
      onDone();
    }
  });

  reveal.addEventListener("click", () => {
    for (const item of inputs) {
      item.input.value = item.answer;
      item.row.className = "blank-line";
    }
    verdict.className = "verdict";
    verdict.textContent = "Revealed — this is the notebook's line.";
  });

  row.append(check, reveal);
  card.append(row, verdict);
  return card;
}

function renderTrap(block) {
  const card = el("div", "card trap");
  card.append(el("h4", null, "The wrong conclusion"));
  card.append(el("pre", null, escapeHtml(block.code)));
  card.append(renderOutput(block.output));
  if (block.why_html) {
    const details = el("details");
    details.append(el("summary", null, "Why this is wrong"));
    details.append(el("div", "why", block.why_html));
    card.append(details);
  }
  return card;
}

function renderQuestion(question, slug, onDone) {
  const card = el("div", "card");
  card.append(el("h4", null, question.id));
  card.append(el("div", "prose", question.prompt_html));

  const why = el("div", "why");
  why.hidden = true;

  question.options.forEach((option) => {
    const button = el("button", "opt");
    button.innerHTML = `<span class="key">${option.label}</span>`;
    button.append(document.createTextNode(option.text));
    button.addEventListener("click", () => {
      for (const other of card.querySelectorAll(".opt")) other.disabled = true;
      for (const [i, other] of [...card.querySelectorAll(".opt")].entries()) {
        if (question.options[i].correct) other.dataset.state = "right";
      }
      if (!option.correct) button.dataset.state = "wrong";
      why.innerHTML = option.explanation_html || "";
      why.hidden = !option.explanation_html;
      markDone(slug, `${question.id}`);
      onDone();
    });
    card.append(button);
  });

  card.append(why);
  return card;
}

/* ------------------------------------------------------------- module --- */

let order = [];

async function renderModule(slug) {
  const [{ modules }, module] = await Promise.all([get("/api/index"), get(`/api/module/${slug}`)]);
  order = modules.map((m) => m.slug);
  crumb.textContent = module.title;
  document.title = module.title;
  back.hidden = false;

  const total =
    module.blocks.filter((b) => b.type === "blank").length + module.quiz.length;

  const tick = () => {
    const done = (progress()[slug] || []).length;
    const share = total ? Math.min(100, Math.round((done / total) * 100)) : 0;
    pct.textContent = total ? `${share}%` : "";
    rail.style.width = `${share}%`;
  };

  main.replaceChildren();
  main.append(el("h1", null, module.title));

  let blankIndex = 0;
  module.blocks.forEach((block) => {
    if (block.type === "prose") {
      main.append(el("div", "prose", block.html));
    } else if (block.type === "code") {
      main.append(el("pre", null, escapeHtml(block.code)));
      if (!block.executed) {
        main.append(el("div", "skipped", "Illustrative only — not executed in the course run."));
      }
    } else if (block.type === "output") {
      main.append(renderOutput(block));
    } else if (block.type === "blank") {
      main.append(renderBlank(block, slug, `blank-${blankIndex++}`, tick));
    } else if (block.type === "trap") {
      main.append(renderTrap(block));
    }
  });

  if (module.quiz.length) {
    main.append(el("h2", null, "Check yourself"));
    module.quiz.forEach((question) => main.append(renderQuestion(question, slug, tick)));
  }

  const at = order.indexOf(slug);
  foot.hidden = false;
  setNav(prev, order[at - 1], "Prev");
  setNav(next, order[at + 1], "Next");
  tick();
  window.scrollTo(0, 0);
}

function setNav(node, slug, label) {
  if (!slug) {
    node.setAttribute("aria-disabled", "true");
    node.removeAttribute("href");
    node.textContent = label;
    return;
  }
  node.removeAttribute("aria-disabled");
  node.href = `/m/${slug}`;
  node.textContent = label;
}

/* -------------------------------------------------------------- router -- */

function route(event) {
  if (event) {
    const href = event.currentTarget.getAttribute("href");
    if (!href) return;
    event.preventDefault();
    history.pushState({}, "", href);
  }
  draw();
}

function draw() {
  const match = location.pathname.match(/^\/m\/([\w-]+)$/);
  const render = match ? renderModule(match[1]) : renderIndex();
  render.catch((error) => {
    main.replaceChildren(el("p", "lede", `Could not load: ${error.message}`));
  });
}

for (const node of [back, prev, next]) node.addEventListener("click", route);
window.addEventListener("popstate", () => draw());
draw();
