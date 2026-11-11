```
src/
│
├── main_app/
│   │
│   ├── admin/
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── coordinators.py
│   │   │   ├── error_logs.py
│   │   │   ├── errors_route.py
│   │   │   ├── jobs.py
│   │   │   ├── settings.py
│   │   │   ├── toolforge_jobs_view.py
│   │   │   └── users.py
│   │   │
│   │   ├── routes_services/
│   │   │   ├── __init__.py
│   │   │   ├── tool_jobs.py
│   │   │   ├── toolforge_jobs_mapping.py
│   │   │   └── toolforge_jobs_service.py
│   │   │
│   │   ├── __init__.py
│   │   ├── admin_panel.py
│   │   ├── decorators.py
│   │   ├── flask_admin_panel.py
│   │   └── flask_admin_panel_models.py
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   ├── http_client.py
│   │   │   ├── objects.py
│   │   │   ├── toolforge_api_service.py
│   │   │   ├── toolforge_jobs_api_service.py
│   │   │   ├── toolforge_jobs_types.py
│   │   │   └── wiki_client.py
│   │   │
│   │   ├── mwclient_page/
│   │   │   ├── __init__.py
│   │   │   ├── mwclient_error.py
│   │   │   └── mwclient_wraper.py
│   │   │
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── citation_api.py
│   │   ├── enwiki_api.py
│   │   ├── query_api.py
│   │   └── README.md
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   ├── main_settings.py
│   │   └── README.md
│   │
│   ├── database/
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── error_log_models.py
│   │   │   ├── jobs.py
│   │   │   ├── settings.py
│   │   │   └── users.py
│   │   │
│   │   ├── services/
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   └── retry_on_disconnect.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── crud_service.py
│   │   │   ├── error_log_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── settings_service.py
│   │   │   ├── user_token_service.py
│   │   │   └── users_service.py
│   │   │
│   │   ├── __init__.py
│   │   ├── create_helper.py
│   │   ├── exceptions.py
│   │   └── README.md
│   │
│   ├── extensions/
│   │   ├── __init__.py
│   │   ├── _csrf.py
│   │   └── data_base.py
│   │
│   ├── io/
│   │   ├── __init__.py
│   │   ├── jobs_files_service.py
│   │   └── README.md
│   │
│   ├── jobs_workers/
│   │   │
│   │   ├── admin_jobs_workers/
│   │   │   └── workers_list.py
│   │   │
│   │   ├── public_jobs_workers/
│   │   │   │
│   │   │   ├── add_r_column/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── add_rtt.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── utils.py
│   │   │   │   ├── worker.py
│   │   │   │   └── wtp_table_manager.py
│   │   │   │
│   │   │   ├── add_rtt_template/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── archive_today/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── removers.py
│   │   │   │   ├── shared_wtp.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── create_redirects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── duplicate_redirect/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── find_and_replace/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── fix_cs1/
│   │   │   │   │
│   │   │   │   ├── text_changer/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── fix_p.py
│   │   │   │   │   └── pmid.py
│   │   │   │   │
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── fix_cs1_params/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── archive_date_maker.py
│   │   │   │   ├── bot.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── fixred_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── fixref/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── import_history/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── newupdater_all/
│   │   │   │   ├── __init__.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── owidpopup_all/
│   │   │   │   ├── mapping.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── README.md
│   │   │   └── workers_list_public.py
│   │   │
│   │   ├── __init__.py
│   │   ├── _shared_objects.py
│   │   ├── base_worker.py
│   │   ├── cli_jobs.py
│   │   ├── jobs_worker.py
│   │   ├── objects.py
│   │   ├── shared_objects.py
│   │   └── utils.py
│   │
│   ├── public/
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py
│   │   │   ├── rate_limit.py
│   │   │   └── routes.py
│   │   │
│   │   ├── main_routes/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   │
│   │   ├── newupdater/
│   │   │   ├── __init__.py
│   │   │   └── route.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── routes_utils.py
│   │   │
│   │   ├── __init__.py
│   │   ├── fixred.py
│   │   ├── profile.py
│   │   ├── public_jobs.py
│   │   ├── README.md
│   │   └── shared_jobs_routes.py
│   │
│   ├── services/
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── auth_exceptions.py
│   │   │   ├── auth_service.py
│   │   │   ├── current_user.py
│   │   │   ├── flow.py
│   │   │   ├── token_manager.py
│   │   │   └── utils.py
│   │   │
│   │   ├── core/
│   │   │   │
│   │   │   ├── cookies/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cookie.py
│   │   │   │   └── cookie_header_client.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── crypto.py
│   │   │   ├── jinja_filters.py
│   │   │   └── README.md
│   │   │
│   │   ├── fixref_shared/
│   │   │   ├── __init__.py
│   │   │   ├── fixred_worker.py
│   │   │   ├── fixref_text_new.py
│   │   │   ├── make_title_bot.py
│   │   │   └── objects.py
│   │   │
│   │   ├── named_param/
│   │   │   └── __init__.py
│   │   │
│   │   ├── new_updater/
│   │   │   │
│   │   │   ├── bots/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── expend.py
│   │   │   │   ├── expend_new.py
│   │   │   │   ├── old_params.py
│   │   │   │   └── remove_worker.py
│   │   │   │
│   │   │   ├── lists/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bot_params.py
│   │   │   │   ├── chem_params.py
│   │   │   │   ├── expend_lists.py
│   │   │   │   └── identifier_params.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── chembox.py
│   │   │   ├── drugbox.py
│   │   │   ├── med_work_new.py
│   │   │   ├── mv_section.py
│   │   │   └── resources_new.py
│   │   │
│   │   ├── replace_wikilink/
│   │   │   └── __init__.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── decode_bytes.py
│   │   │
│   │   ├── __init__.py
│   │   ├── fixred_one.py
│   │   ├── newupdater_service.py
│   │   ├── README.md
│   │   └── shared_classes.py
│   │
│   ├── templates_markups/
│   │   │
│   │   ├── admin_sidebar/
│   │   │   ├── __init__.py
│   │   │   ├── mapping.py
│   │   │   ├── sidebar.py
│   │   │   └── sidebar_list.py
│   │   │
│   │   ├── navbar/
│   │   │   ├── __init__.py
│   │   │   ├── nav_bar.py
│   │   │   ├── navbar_list.py
│   │   │   └── objects.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── README.md
│   │   └── verify.py
│   │
│   ├── __init__.py
│   ├── error_pages.py
│   ├── logger_config.py
│   ├── models.py
│   └── README.md
│
├── static/
│   │
│   ├── css/
│   │   ├── navbar.css
│   │   ├── sidebar-desktop.css
│   │   ├── sidebar-mobile.css
│   │   └── style.css
│   │
│   ├── js/
│   │   │
│   │   ├── data_table_ajax/
│   │   │   ├── macros.js
│   │   │   └── table.js
│   │   │
│   │   ├── auto-refresh.js
│   │   ├── autocomplete.js
│   │   ├── card-tools.js
│   │   ├── dark-mode.js
│   │   └── sidebar.js
│   │
│   └── favicon.ico
│
├── templates/
│   │
│   ├── _macros/
│   │   └── forms.html
│   │
│   ├── admin/
│   │   │
│   │   ├── bs4_admin/
│   │   │   │
│   │   │   ├── file/
│   │   │   │   │
│   │   │   │   ├── modals/
│   │   │   │   │   └── form.html
│   │   │   │   │
│   │   │   │   ├── form.html
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── model/
│   │   │   │   │
│   │   │   │   ├── modals/
│   │   │   │   │   ├── create.html
│   │   │   │   │   ├── details.html
│   │   │   │   │   └── edit.html
│   │   │   │   │
│   │   │   │   ├── create.html
│   │   │   │   ├── details.html
│   │   │   │   ├── edit.html
│   │   │   │   ├── inline_field_list.html
│   │   │   │   ├── inline_form.html
│   │   │   │   ├── inline_list_base.html
│   │   │   │   ├── layout.html
│   │   │   │   ├── list.html
│   │   │   │   └── row_actions.html
│   │   │   │
│   │   │   ├── rediscli/
│   │   │   │   ├── console.html
│   │   │   │   └── response.html
│   │   │   │
│   │   │   ├── actions.html
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── layout.html
│   │   │   ├── lib.html
│   │   │   ├── master.html
│   │   │   └── static.html
│   │   │
│   │   ├── base.html
│   │   ├── error_logs.html
│   │   ├── errors.html
│   │   └── index_with_sidebar.html
│   │
│   ├── admins/
│   │   │
│   │   ├── tf_jobs/
│   │   │   ├── _job_actions.html
│   │   │   ├── index.html
│   │   │   ├── job_details.html
│   │   │   └── job_logs.html
│   │   │
│   │   ├── _sidebar.html
│   │   ├── admin.html
│   │   ├── base1.html
│   │   ├── coordinators.html
│   │   ├── popup_action.html
│   │   ├── settings.html
│   │   └── users.html
│   │
│   ├── jobs_templates/
│   │   │
│   │   ├── _ajax_templates/
│   │   │   └── _ajax_table.html
│   │   │
│   │   ├── _help_templates/
│   │   │   ├── _job_summary.html
│   │   │   ├── _jobs_actions.html
│   │   │   └── shared_details.html
│   │   │
│   │   ├── public/
│   │   │   │
│   │   │   ├── add_rtt_template/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── archive_today/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── create_redirects/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── duplicate_redirect/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── find_and_replace/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── fix_cs1/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── fix_cs1_params/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── fixred_all/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── fixref/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── import_history/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   │
│   │   │   ├── newupdater_all/
│   │   │   │   └── list.html
│   │   │   │
│   │   │   └── owidpopup_all/
│   │   │       └── list.html
│   │   │
│   │   ├── _list_table.html
│   │   ├── all_jobs_list.html
│   │   ├── base_details_public.html
│   │   └── base_list_public.html
│   │
│   ├── one_page_templates/
│   │   │
│   │   └── add_r_column/
│   │       ├── details.html
│   │       └── list.html
│   │
│   ├── _macros.html
│   ├── _navbar.html
│   ├── base.html
│   ├── error.html
│   ├── fixred_one.html
│   ├── index.html
│   ├── index_db_error.html
│   ├── newupdater.html
│   └── profile.html
│
├── __init__.py
├── app.py
├── README.md
└── uwsgi.ini

```