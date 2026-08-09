**Plan: Refactor Deep Nesting and Long Methods in `drugbox.py` and `resources_new.py`**

### 1. Goals
- Reduce cognitive load and nesting depth (target ≤ 3–4 levels).
- Shorten methods (most < 30–40 lines; extract helpers aggressively).
- Separate concerns: parsing → data model → section/parameter assembly → text emission.
- Make the pipelines data-driven and easier to unit-test.
- Preserve exact current behavior (section order, comment markers, parameter placement, identifier move logic).

### 2. Current Problems (Real Code)

**`drugbox.py` – `TextProcessor`**
- `run()` → `get_txt_params()` → `new_temp()` → many `create_section()` calls.
- `create_section()` is long and branches heavily on `sectionname` (`first`, `combo`, `chemical`, `last`…).
- `get_combo()` and `get_chemical()` contain nested conditionals and list mutations.
- Parameter tracking via mutable `self.params_done_lowers`.
- Repeated string building and regex clean-ups mixed with logic.
- Deep nesting example pattern:
  ```python
  if sectionname == "combo":
      ...
      if _type:
          if empty: ...
          if _type in combo_titles:
              for p in all_combo: ...
  ```

**`resources_new.py`**
- `move_resources()` is a long procedural function doing:
  1. Parse templates
  2. Extract identifiers from Drugbox
  3. Mutate the Drugbox
  4. Update or create `{{drug resources}}`
  5. Handle External-links placement
  6. Call side-effect helpers (`remove_cite_web`, `portal_remove`)
- Nested loops + multiple early-exit style checks mixed with mutations.
- Local dict `page_identifier_params` passed around; Arabic comments still present.
- `add_resources()` also mixes detection of External links / reflist with template construction.

### 3. Target Design

**For Drugbox processing**
```
DrugboxModel          # pure data: title, ordered params, section membership
SectionBuilder        # knows section order + comment titles + which params belong where
DrugboxRenderer       # turns model → final wikitext (including <!-- comments -->)
TextProcessor         # thin orchestrator (parse → model → render → replace)
```

**For resources / identifiers**
```
IdentifierExtractor   # finds identifiers inside Drugbox, returns clean dict + cleaned template
DrugResourcesUpdater  # updates existing {{drug resources}} or builds a new one
ExternalLinksPlacer   # decides where to insert the resources template
move_resources()      # thin coordinator calling the above
```

Key principles:
- Early returns / guard clauses instead of deep `if` nesting.
- Data-driven section definitions (already partially present in `bot_params.py` — lean on them harder).
- Pure functions where possible (text/model in → text/model out).
- No mutation of shared lists while iterating; build new structures.

### 4. Concrete Refactor Steps

#### Phase 1 – `drugbox.py` (highest complexity)

1. **Extract data model**
   ```python
   @dataclass
   class DrugboxModel:
       title: str
       params: dict[str, str]          # original order preserved if needed
       used_params: set[str] = field(default_factory=set)
   ```

2. **Make section definition fully data-driven**
   - Expand / clean `all_params` + `params_to_add` + section comment titles into a single ordered list of `SectionSpec`:
     ```python
     @dataclass(frozen=True)
     class SectionSpec:
         key: str
         comment: str | None
         params: list[str]
         always_add: list[str] = field(default_factory=list)
     ```
   - Special cases (`combo`, `chemical`) become small strategy functions that return a `SectionSpec` or a list of lines.

3. **Split `create_section`**
   - `build_combo_section(model) → SectionSpec | None`
   - `build_chemical_section(model) → tuple[str, list[str]]` (pre-rendered formula lines + remaining params)
   - `render_section(spec, model) → str` (emits comment + `| param = value` lines)
   - Main loop in `new_temp()` becomes:
     ```python
     parts = [f"{{{{{model.title}}}"]
     for spec in SECTION_ORDER:
         rendered = render_section(spec, model)
         if rendered:
             parts.append(rendered)
     parts.append("}}")
     return "\n".join(parts)
     ```

4. **Reduce nesting with guards**
   ```python
   def get_combo(self) -> tuple[str, list[str]]:
       _type = self.drugbox_params.get("type", "").lower().strip()
       if not _type:
           return "| type = mab / vaccine / combo", all_combo

       _type = re.sub(r"<!--.*?-->", "", _type).strip()
       if re.match(r"<!--\s*empty\s*-->", _type):
           return "", all_combo

       title = combo_titles.get(_type)
       params = list(all_params["combo"].get(_type, [])) + all_combo
       return title or default_title, list(dict.fromkeys(params))  # preserve order, unique
   ```

5. **Move regex clean-ups out of the class**
   - Small pure helpers: `normalize_section_comments(text)`, `collapse_blank_lines(text)`.

#### Phase 2 – `resources_new.py`

1. **Extract `IdentifierExtractor`**
   ```python
   def extract_identifiers(infobox: wtp.Template) -> tuple[dict[str, str], wtp.Template]:
       found = {}
       for param in identifiers_params:
           if not infobox.has_arg(param):
               continue
           arg = infobox.get_arg(param)
           value = clean_comment_from_value(arg.value)  # small helper
           if value.strip():
               found[param] = value
           infobox.del_arg(param)
       # also strip <!-- Identifiers --> comment
       return found, infobox
   ```

2. **Extract `DrugResourcesUpdater`**
   - `update_existing(resources_temp, identifiers) → str`
   - `build_new(identifiers) → str`
   - Keep the “add after External links / reflist / end” decision in a separate `find_insertion_point(text)`.

3. **Thin `move_resources`**
   ```python
   def move_resources(text: str, title: str, ...) -> str:
       parsed = wtp.parse(text)
       infobox = find_template(parsed, {"drugbox", "infobox drug"})
       if not infobox:
           return text

       identifiers, cleaned_infobox = extract_identifiers(infobox)
       text = text.replace(str(infobox), str(cleaned_infobox))  # or better: rebuild

       resources = find_template(parsed, {"drug resources"})
       if resources:
           text = update_existing_resources(text, resources, identifiers)
       elif identifiers:
           text = insert_new_resources(text, identifiers)

       text = remove_cite_web(...)
       text = portal_remove(text)
       return text
   ```

4. **Eliminate remaining deep nesting**
   - Replace long `if External: … elif External2: … elif External3:` chains with a small ordered list of detectors that return an insertion index or sentinel.

#### Phase 3 – Cross-cutting clean-ups
- Move shared comment-stripping and blank-line normalization into a tiny `wikitext_utils.py`.
- Ensure all helpers are pure or take explicit arguments (no hidden module state).
- Translate remaining Arabic comments to English.
- Add type hints and short docstrings to every extracted function.

### 5. Testing Strategy
- Keep the existing golden / before-after pairs from real pages.
- After each extraction, run the full pipeline on the corpus and assert byte-for-byte (or whitespace-normalized) equivalence with the old output.
- Unit-test the new pure helpers in isolation:
  - `extract_identifiers`
  - `render_section`
  - `build_combo_section`
  - insertion-point logic
- Add a few targeted tests for the previous deep-nesting edge cases (empty type, formula parameters, missing External links, already-present drug resources, etc.).

### 6. Suggested Order of Work
1. Introduce `SectionSpec` + data-driven loop in `drugbox.py` (biggest readability win).
2. Extract `get_combo` / `get_chemical` / `render_section`.
3. Extract identifier logic from `resources_new.py`.
4. Thin `move_resources` and `add_resources`.
5. Clean up remaining regex and comments.
6. Final pass: ensure no method exceeds ~40 lines and nesting stays shallow.

### 7. Risks & Mitigations
- **Behavioral drift** (parameter order, extra/missing blank lines, comment placement) → dual-run + corpus diff at every step; keep old methods behind a temporary flag if needed.
- **Over-abstraction** → stop at the level of clear, named helpers; do not introduce a full visitor framework unless later evaluation shows it is warranted.
- **Performance** → negligible; the work is still dominated by parsing and string replaces.

### Expected Result
- `TextProcessor.new_temp()` becomes a short loop over section specs.
- `move_resources()` becomes a readable 15–25-line coordinator.
- Deep nesting disappears; each helper has a single responsibility.
- Future changes to section order or identifier lists become data changes instead of control-flow changes.
- The code is far easier to unit-test and to reason about when the earlier “replace regex with wtp” work is also applied.
