**Plan: Refactor `src/main_app/shared` Structure**

### 1. Current State & Problems

`shared/` is currently a catch-all package mixing several concerns:

| Area | Contents | Problem |
|------|----------|---------|
| **Domain / wikitext** | `new_updater/`, `fixref_shared/`, `replace_wikilink/`, `named_param/`, `fixred_one.py` | Complex business logic living under a generic “shared” name; hard to find and test |
| **Auth** | `auth/` (CurrentUser, OAuth handshake, user service) | Auth is cross-cutting but currently mixed with domain code |
| **Core utilities** | `core/` (crypto, cookies, jinja filters) | Good isolation, but still under the overloaded `shared` |
| **Orchestration services** | `newupdater_service.py`, `fixred_one.py` | These are application-level use cases, not pure shared utilities |
| **Misc** | `decode_bytes.py`, `shared_classes.py` | Small helpers with unclear ownership |

Consequences:
- Unclear dependency direction (domain code can accidentally import Flask/auth concerns).
- Difficult to unit-test pure wikitext transforms in isolation.
- `shared/` grows into a god package.
- Onboarding cost is high (“where does the medical updater live?”).

### 2. Target Structure

Move toward a clearer separation while keeping the change incremental and low-risk:

```
src/main_app/
├── domain/                          # Pure business logic (no Flask, no DB, no network)
│   ├── wikitext/
│   │   ├── __init__.py
│   │   ├── redirects/               # former fixref_shared + replace_wikilink + fixred_one core
│   │   ├── references/              # fixref_text_new, make_title_bot
│   │   ├── medical/                 # former new_updater/ (drugbox, chembox, resources, …)
│   │   ├── named_param/
│   │   └── utils.py                 # small pure helpers (comment stripping, etc.)
│   ├── auth/                        # CurrentUser, pure token helpers (no I/O)
│   └── shared_classes.py            # UpdaterTextOutcome and other domain DTOs
│
├── application/                     # Use-case orchestration (may use infrastructure)
│   ├── content/
│   │   ├── fix_redirects.py         # former fixred_one.py (orchestration)
│   │   └── medical_updater.py       # former newupdater_service.py
│   └── auth/
│       └── oauth_callback.py        # former auth_service / auth_users_service orchestration
│
├── infrastructure/                  # External systems
│   ├── security/                    # former shared/core/crypto + cookies
│   ├── mediawiki/                   # already mostly in api_services/ — keep or thin-wrap
│   └── ...
│
├── interfaces/                      # Blueprints, templates, CLI (unchanged for now)
│
└── shared/                          # **Temporary** or reduced to truly cross-cutting only
    └── (eventually deleted or reduced to a few re-exports during migration)
```

**Key principles**
- `domain/` must stay pure: no Flask, no SQLAlchemy, no `mwclient`, no settings singleton.
- Application services own the “load page → transform → save / return outcome” flow.
- Infrastructure provides adapters (crypto, cookies, MediaWiki clients).
- `shared/` is either removed or kept only for a short migration period with deprecation re-exports.

### 3. Migration Phases

#### Phase 0 – Preparation (low risk)
- Inventory all imports of `main_app.shared.*`.
- Add a temporary compatibility layer so existing imports keep working during the move.
- Ensure the test suite and a small corpus of real pages are ready for regression checks.

#### Phase 1 – Extract pure domain wikitext (highest value)
1. Create `domain/wikitext/`.
2. Move in this order (least → most dependent):
   - `replace_wikilink/`
   - `fixref_shared/objects.py` + `fixred_worker.py` (core redirect logic)
   - `fixref_shared/fixref_text_new.py` + `make_title_bot.py`
   - `named_param/`
   - Entire `new_updater/` tree (`med_work_new`, `drugbox`, `chembox`, `resources_new`, `mv_section`, `bots/`, `lists/`)
3. While moving:
   - Remove any accidental infrastructure imports.
   - Turn remaining side-effect calls into parameters or return values.
   - Apply the earlier plans (reduce nesting in `drugbox.py` / `resources_new.py`, replace complex regex where decided).
4. Keep thin re-exports in the old locations for one or two releases.

#### Phase 2 – Domain auth objects
- Move `CurrentUser` and pure helpers to `domain/auth/`.
- Leave OAuth handshake and user persistence in application + infrastructure.

#### Phase 3 – Application services
- Move `fixred_one.py` → `application/content/fix_redirects.py`
- Move `newupdater_service.py` → `application/content/medical_updater.py`
- These services will:
  - Accept a user / site factory / page loader as dependencies.
  - Call pure domain transforms.
  - Return `UpdaterTextOutcome` (already a good domain DTO).

#### Phase 4 – Core utilities → infrastructure
- Move `shared/core/crypto.py` → `infrastructure/security/crypto.py`
- Move `shared/core/cookies/` → `infrastructure/security/cookies/`
- Move `jinja_filters` to a presentation/helpers location (or keep under `interfaces/`).

#### Phase 5 – Clean-up
- Delete or shrink `shared/` to a minimal compatibility package (or remove it).
- Update all internal imports.
- Update documentation and the main package README.
- Remove temporary re-exports after consumers are migrated.

### 4. Dependency Rules After Refactor

```
interfaces/  →  application/  →  domain/
                     ↓
              infrastructure/
```

- Domain never imports application or infrastructure.
- Application may import domain + infrastructure.
- Interfaces may import application (and domain DTOs only).

### 5. Concrete First Moves (recommended starting point)

1. Create the new package skeleton:
   ```bash
   mkdir -p src/main_app/domain/wikitext/{redirects,references,medical}
   mkdir -p src/main_app/application/content
   ```
2. Move `replace_wikilink` and the redirect core first (smallest, already fairly pure).
3. Move `new_updater/` next; this is the largest and most valuable pure domain block.
4. Immediately after each move, run the existing test suite + a small golden-file check on real pages.
5. Only then touch the orchestration services (`fixred_one`, `newupdater_service`).

### 6. Compatibility Strategy
During migration keep shims:

```python
# src/main_app/shared/new_updater/__init__.py  (temporary)
from main_app.domain.wikitext.medical import med_updater_one
__all__ = ["med_updater_one"]
```

This lets the rest of the codebase continue working while packages are relocated.

### 7. Testing & Safety
- After every package move: full unit-test run + a regression suite of 20–50 real pages through the medical updater and redirect fixer.
- Prefer pure-function tests for everything under `domain/wikitext/`.
- Keep the public outcome type (`UpdaterTextOutcome`) stable so callers do not break.

### 8. Expected Benefits
- Clear ownership: “medical content rules live in `domain/wikitext/medical`”.
- Easier unit testing of the highest-risk logic.
- Reduced risk of circular imports and accidental framework coupling.
- Natural place to apply the earlier refactoring plans (nesting reduction, regex → wtp).
- `shared/` stops being a dumping ground.

### 9. Out of Scope for This Refactor
- Changing the job worker system or admin blueprints.
- Introducing a full DI container (can be a later step).
- Moving `api_services/` (it already acts as infrastructure).

This plan is incremental, preserves behavior, and directly supports the previous plans for reducing nesting and replacing fragile regex. The first concrete action is creating the `domain/wikitext/` skeleton and moving the purest redirect/wikilink code.
