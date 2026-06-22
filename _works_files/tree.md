```
src/
├── main_app/
│   ├── admin/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── coordinators.py
│   │   │   ├── jobs.py
│   │   │   ├── settings.py
│   │   │   └── users.py
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── route.py
│   │   └── sidebar.py
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   └── wiki_client.py
│   │   ├── files_service/
│   │   ├── mwclient_page/
│   │   │   ├── __init__.py
│   │   │   ├── mwclient_error.py
│   │   │   └── mwclient_wraper.py
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── citation_api.py
│   │   ├── enwiki_api.py
│   │   ├── query_api.py
│   │   └── README.md
│   ├── public/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py
│   │   │   ├── routes.py
│   │   │   └── utils.py
│   │   ├── main_routes/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── newupdater/
│   │   │   ├── __init__.py
│   │   │   └── route.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── routes_utils.py
│   │   ├── __init__.py
│   │   ├── fixred.py
│   │   ├── jobs_routes_utils.py
│   │   ├── profile.py
│   │   ├── public_jobs.py
│   │   └── README.md
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   ├── main_settings.py
│   │   └── README.md
│   ├── core/
│   │   ├── cookies/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   └── cookie_header_client.py
│   │   ├── __init__.py
│   │   ├── crypto.py
│   │   ├── jinja_filters.py
│   │   └── README.md
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py
│   │   │   ├── settings.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── db_guard_model.py
│   │   │   │   └── retry_on_disconnect.py
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── delete_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── settings_service.py
│   │   │   ├── user_token_service.py
│   │   │   └── users_service.py
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── README.md
│   ├── jobs_workers/
│   │   ├── admin_jobs_workers/
│   │   │   └── workers_list.py
│   │   ├── public_jobs_workers/
│   │   │   ├── add_r_column/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── add_rtt.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── add_rtt_template/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── create_redirects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── duplicate_redirect/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── find_and_replace/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── fixred_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── fixref/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── import_history/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   ├── newupdater_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   ├── __init__.py
│   │   │   ├── README.md
│   │   │   └── workers_list_public.py
│   │   ├── __init__.py
│   │   ├── base_worker_object.py
│   │   ├── cli_jobs.py
│   │   ├── jobs_worker.py
│   │   ├── objects.py
│   │   ├── shared_objects.py
│   │   └── utils.py
│   ├── shared/
│   │   ├── fixref_shared/
│   │   │   ├── __init__.py
│   │   │   ├── fixred_worker.py
│   │   │   ├── fixref_text_new.py
│   │   │   ├── make_title_bot.py
│   │   │   └── objects.py
│   │   ├── named_param/
│   │   │   └── __init__.py
│   │   ├── new_updater/
│   │   │   ├── bots/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── expend.py
│   │   │   │   ├── expend_new.py
│   │   │   │   ├── old_params.py
│   │   │   │   └── Remove.py
│   │   │   ├── lists/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bot_params.py
│   │   │   │   ├── chem_params.py
│   │   │   │   ├── expend_lists.py
│   │   │   │   └── identifier_params.py
│   │   │   ├── __init__.py
│   │   │   ├── chembox.py
│   │   │   ├── drugbox.py
│   │   │   ├── MedWorkNew.py
│   │   │   ├── mv_section.py
│   │   │   └── resources_new.py
│   │   ├── replace_wikilink/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── decode_bytes.py
│   │   ├── fixred_one.py
│   │   ├── newupdater_service.py
│   │   ├── README.md
│   │   └── shared_classes.py
│   ├── su_services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── auth_users_service.py
│   │   ├── current_user.py
│   │   ├── jobs_files_service.py
│   │   ├── mwoauth_handshake.py
│   │   └── README.md
│   ├── utils/
│   │   ├── README.md
│   │   └── verify.py
│   ├── __init__.py
│   ├── extensions.py
│   └── README.md
├── static/
│   ├── css/
│   │   ├── navbar.css
│   │   ├── sidebar-desktop.css
│   │   ├── sidebar-mobile.css
│   │   └── style.css
│   └── js/
│       ├── auto-refresh.js
│       ├── autocomplete.js
│       ├── card-tools.js
│       ├── dark-mode.js
│       └── sidebar.js
├── templates/
│   ├── _macros/
│   ├── admins/
│   ├── jobs_templates/
│   │   ├── _help_templates/
│   │   └── public/
│   │       ├── add_rtt_template/
│   │       ├── add_unlinkedwikibase/
│   │       ├── create_redirects/
│   │       ├── duplicate_redirect/
│   │       ├── find_and_replace/
│   │       ├── fixred_all/
│   │       ├── fixref/
│   │       ├── import_history/
│   │       └── newupdater_all/
│   └── one_page_templates/
│       └── add_r_column/
├── __init__.py
├── app.py
├── logger_config.py
├── README.md
└── uwsgi.ini

```
