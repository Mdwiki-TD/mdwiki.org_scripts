**Plan: Evaluate Replacing Complex Regex with Deeper `wikitextparser` Usage or a Small Custom AST Walker**

### 1. Goal
Determine which of the more complex/fragile regex patterns in the medical content updater, redirect fixer, reference normalizer, and related modules can be safely replaced by:
- Deeper, more consistent use of the already-present `wikitextparser` (wtp), or
- A small, focused custom AST walker / visitor on top of wtp’s parse tree.

Success criteria:
- Equivalent or better correctness on real wiki pages.
- Reduced fragility (less breakage on whitespace, comment variations, nested templates).
- Improved readability and testability.
- No significant performance regression for typical page sizes.

### 2. Inventory of High-Complexity Regex (Real Code)

**A. Section comment markers & cleanup (`drugbox.py` / `med_work_new.py`)**

```python
# shared/new_updater/drugbox.py (and duplicated in med_work_new.py)
lkj = r"<!--\s*(Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status|Identifiers)\s*-->"

lkj2 = r"(<!--\s*(?:Monoclonal antibody data|External links|Names*|Clinical data|Legal data|Legal status|Pharmacokinetic data|Chemical and physical data|Definition and medical uses|Chemical data|Chemical and physical data|index_label\s*=\s*Free Base|\w+ \w+ data|\w+ \w+ \w+ data|\w+ data|\w+ status)\s*-->)"

# Later usage
drugbox2 = re.sub(lkj2, "", self.olddrugbox)
drug_box_new = re.sub(rf"\s*{lkj2}\s*", r"\n\n\g<1>\n", drug_box_new, flags=re.DOTALL)
drug_box_new = re.sub(r"\n\s*\n\s*[\n\s]+", "\n\n", drug_box_new, flags=re.DOTALL | re.MULTILINE)
```

**B. Moving “External links” section (`mv_section.py`)**

```python
# shared/new_updater/mv_section.py
categoryPattern = r"\[\[\s*(Category)\s*:[^\n]*\]\]\s*"
interwikiPattern = r"\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]\s*"
templatePattern = r"\r?\n{{((?!}}).)+?}}\s*"
commentPattern = r"<!--((?!-->).)*?-->\s*"

metadataR = re.compile(
    rf"(\r?\n)?({categoryPattern}|{interwikiPattern}|{templatePattern}|{commentPattern})$", re.DOTALL
)

# + reflist matching
mata = re.search(r"^{{reflist(?:[^{]|{[^{]|{{[^{}]+}}|)+}}", l_c, flags=re.IGNORECASE)
```

**C. Identifier extraction & NLM cite-web cleanup (`resources_new.py` + `remove_worker.py`)**

```python
# resources_new.py
dng = r"\=\=\s*External links\s*\=\=\s*\*\s*\{\{cite web\s*\|\s*\|\s*url\s*\=\s*https\:\/\/druginfo.*?\}\}"

# remove_worker.py
ioireg = rf"\s*cite web\s*\|\s*url\s*\=\s*https\:\/\/druginfo\.nlm\.nih\.gov\/drugportal\/(?:name|category)\/{title2}\s*\|\s*publisher\s*\=\s*U\.S\. National Library of Medicine\s*\|\s*work\s*\=\s*Drug Information Portal\s*\|\s*title\s*\=\s*{title2}\s*"
ioireg = r"(\*\s*{{" + ioireg + "}})"
```

**D. Bad-title blacklist (`make_title_bot.py`)**

Large verbose regex compiled with `re.I | re.S | re.X` that matches many “error / login / 404” patterns. This one is less structural and more content-filter oriented.

**E. Smaller but still brittle patterns**
- Newline collapsing and template formatting in multiple places.
- Portal-bar removal: `r"\{\{\s*portal bar\s*\|\s*Medicine\s*\}\}"`.

### 3. Evaluation Approach

**Step 1 – Collect real test corpus**
- Extract 30–50 real pages from mdwiki / enwiki that exercise the pipelines:
  - Pages with `{{Drugbox}}` / `{{Infobox drug}}` in various states (with/without section comments, identifiers still inside, External links present/absent, nested templates, HTML comments with extra whitespace).
  - Pages with double redirects, lay-source refs, NLM cite-web links.
  - Edge cases: empty sections, comments inside parameter values, unusual whitespace, nested `{{reflist}}`.

**Step 2 – Characterize each regex**
For every complex pattern above, document:
- Intent (what it is trying to achieve).
- Current failure modes observed on the corpus.
- Whether the information is already available (or easily obtainable) from a `wtp.parse()` tree.

**Step 3 – Prototype replacements**

**Preferred: deeper `wikitextparser` usage**

Example – replace section-comment stripping & re-insertion:

```python
import wikitextparser as wtp

def strip_section_comments(text: str) -> str:
    parsed = wtp.parse(text)
    # Walk comments or use string replacement only on known comment nodes if exposed
    # Or rebuild the Drugbox template from its arguments while ignoring comment-only “parameters”
    ...

def normalize_drugbox_sections(template: wtp.Template) -> str:
    # Rebuild the template using the ordered section list already defined in bot_params.py
    # Insert the exact <!-- Section Name --> comments programmatically
    sections = [
        ("", "first"),
        ("Monoclonal antibody data", "combo"),  # etc.
    ]
    parts = [f"{{{{{template.normal_name()}}}"]
    for comment, section_key in sections:
        if comment:
            parts.append(f"\n\n<!-- {comment} -->")
        # emit parameters belonging to this section
    parts.append("\n}}")
    return "\n".join(parts)
```

Example – moving External links section with wtp:

```python
def move_external_links(text: str) -> str:
    parsed = wtp.parse(text)
    sections = parsed.get_sections(include_subsections=True)
    ext = next((s for s in sections if s.title and s.title.strip().lower() == "external links"), None)
    if not ext:
        return text
    # Remove the section, then re-insert just before the last metadata (categories / interwikis)
    # by walking the remaining top-level nodes or by reconstructing from sections + trailing content
    ...
```

Example – NLM cite-web detection:

```python
def find_nlm_cite_web(parsed: wtp.WikiText, title: str):
    for tag in parsed.get_tags("ref") + parsed.templates:  # or top-level
        for t in (tag.templates if hasattr(tag, "templates") else [tag]):
            if t.normal_name().lower() == "cite web":
                url = (t.get_arg("url") or "").value or ""
                if "druginfo.nlm.nih.gov/drugportal" in url and title.lower() in url.lower():
                    return t
    return None
```

**Fallback / complementary: small custom AST walker**

If wtp’s public API is insufficient for some cases (e.g. precise comment positioning or mixed content), write a thin visitor:

```python
from typing import Callable
import wikitextparser as wtp

def walk(node, visitors: dict[type, Callable]):
    visitor = visitors.get(type(node))
    if visitor:
        visitor(node)
    # Recurse into .templates, .wikilinks, .tags, .sections, .arguments, etc.
    for child in getattr(node, "templates", []) + getattr(node, "wikilinks", []) + ...:
        walk(child, visitors)
```

Use it only for the few remaining cases that pure wtp cannot express cleanly.

**Step 4 – Side-by-side comparison**
- Run old regex path and new path on the corpus.
- Diff the resulting wikitext (normalize whitespace first if needed).
- Measure: correctness (manual review of diffs), runtime, and number of edge-case failures.

**Step 5 – Decision matrix**

| Pattern group                  | Replace with wtp? | Custom walker needed? | Priority | Risk |
|--------------------------------|-------------------|-----------------------|----------|------|
| Drugbox section comments       | Yes               | Low                   | High     | Med  |
| External-links section move    | Yes               | Possibly              | High     | Med  |
| NLM / cite-web cleanup         | Yes               | No                    | High     | Low  |
| Metadata stripping (cats/iw)   | Yes               | Low                   | Medium   | Low  |
| Bad-title blacklist            | Keep regex or move to list of compiled patterns | No | Low | Low |
| Simple portal-bar / newline    | Yes or keep simple regex | No                | Low      | Low  |

### 4. Implementation Roadmap

1. **Prepare** (1–2 days)
   - Build the real-page corpus + golden expected outputs (or at least “before/after” pairs from current production runs).
   - Add a small test harness that can run both old and new pipelines and produce unified diffs.

2. **Pilot on one high-value module** (2–4 days)
   - Start with `remove_worker.py` + NLM detection (clearest win, lowest risk).
   - Then tackle `resources_new.py` identifier move.
   - Then `mv_section.py`.
   - Finally the Drugbox section-comment logic (most complex).

3. **Harden**
   - Make the new helpers pure (text in → text out + optional metadata).
   - Add unit tests for every transformed pattern using real snippets.
   - Keep the old regex path behind a feature flag or dual-run mode during transition.

4. **Roll out**
   - Shadow mode: new path computes result, old path is still applied; log differences.
   - Switch after confidence is high.
   - Remove the complex regex once the new path is the only one.

5. **Documentation**
   - Document the ordered section list and the exact comment strings that must be emitted.
   - Note any remaining intentional regex (content filters, simple one-liners).

### 5. Risks & Mitigations
- **Subtle behavioral differences** (whitespace, comment placement, parameter order) → mitigated by corpus diffs + dual-run logging.
- **Performance** on very large pages → measure; wtp is already used heavily, so incremental cost should be modest.
- **wtp limitations** on certain comment / mixed-content cases → fall back to a tiny custom walker only where needed; keep the surface area small.
- **Regression in production jobs** → feature flag + careful canary on a subset of job types.

### 6. Expected Outcome
- Most structural regex (section comments, External links movement, template/parameter surgery, NLM cite detection) replaced by clearer wtp-based or walker-based code.
- Remaining regex limited to simple, well-tested content filters (bad titles, portal bar, trivial cleanups).
- Higher confidence, easier future changes to the medical-content pipeline, and better unit-test coverage of the highest-risk domain logic.

This plan stays tightly scoped to the real code that already exists and prioritizes the patterns that have historically been the most fragile.
