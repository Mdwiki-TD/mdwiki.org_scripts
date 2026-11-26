```
tests/
│
├── integration/
│   │
│   ├── database/
│   │   └── test_connection_reuse.py
│   │
│   └── routes/
│       │
│       ├── admin/
│       │   │
│       │   ├── views/
│       │   │   └── test_settings_integration.py
│       │   │
│       │   └── test_admin_routes.py
│       │
│       └── public/
│           │
│           ├── views/
│           │   ├── test_auth_routes.py
│           │   └── test_main_route.py
│           │
│           └── test_jobs_routes.py
│
├── unit/
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │   │
│   │   │   ├── toolforge/
│   │   │   │   ├── test_toolforge_api_service.py
│   │   │   │   ├── test_toolforge_jobs_api_service.py
│   │   │   │   ├── test_toolforge_jobs_api_service2.py
│   │   │   │   └── test_toolforge_jobs_types.py
│   │   │   │
│   │   │   ├── test_category_members_api.py
│   │   │   └── test_wikisite_client.py
│   │   │
│   │   ├── utils/
│   │   │
│   │   ├── test_mwclient_page.py
│   │   └── test_query_api.py
│   │
│   ├── app_services/
│   │   │
│   │   ├── fixref_shared/
│   │   │   ├── test_fixred_objects.py
│   │   │   ├── test_fixred_worker.py
│   │   │   ├── test_fixref_text_new.py
│   │   │   └── test_make_title_bot.py
│   │   │
│   │   ├── new_updater/
│   │   │   │
│   │   │   ├── bots/
│   │   │   │   ├── test_expend.py
│   │   │   │   ├── test_expend_new.py
│   │   │   │   ├── test_old_params.py
│   │   │   │   └── test_remove_worker.py
│   │   │   │
│   │   │   ├── lists/
│   │   │   │   ├── test_bot_params.py
│   │   │   │   ├── test_chem_params.py
│   │   │   │   ├── test_expend_lists.py
│   │   │   │   └── test_identifier_params.py
│   │   │   │
│   │   │   ├── tests/
│   │   │   │   │
│   │   │   │   ├── texts/
│   │   │   │   │   │
│   │   │   │   │   ├── chembox/
│   │   │   │   │   │   ├── work_on_text_expected.wiki
│   │   │   │   │   │   ├── work_on_text_result.wiki
│   │   │   │   │   │   └── work_on_text_source.wiki
│   │   │   │   │   │
│   │   │   │   │   ├── test1/
│   │   │   │   │   │   ├── work_on_text_expected.wiki
│   │   │   │   │   │   ├── work_on_text_result.wiki
│   │   │   │   │   │   └── work_on_text_source.wiki
│   │   │   │   │   │
│   │   │   │   │   ├── test2/
│   │   │   │   │   │   ├── work_on_text_expected.wiki
│   │   │   │   │   │   ├── work_on_text_result.wiki
│   │   │   │   │   │   └── work_on_text_source.wiki
│   │   │   │   │   │
│   │   │   │   │   └── test3/
│   │   │   │   │       ├── work_on_text_expected.wiki
│   │   │   │   │       ├── work_on_text_result.wiki
│   │   │   │   │       └── work_on_text_source.wiki
│   │   │   │   │
│   │   │   │   ├── test_chembox1.py
│   │   │   │   ├── test_mv_section1.py
│   │   │   │   ├── test_portal_remove.py
│   │   │   │   ├── test_rename_params.py
│   │   │   │   └── test_work_on_text.py
│   │   │   │
│   │   │   ├── test_chembox.py
│   │   │   ├── test_drugbox.py
│   │   │   ├── test_med_work_new.py
│   │   │   ├── test_mv_section.py
│   │   │   └── test_resources_new.py
│   │   │
│   │   ├── replace_wikilink/
│   │   │   ├── test_init.py
│   │   │   └── test_replace_wikilink.py
│   │   │
│   │   ├── test_newupdater_service.py
│   │   └── test_shared_classes.py
│   │
│   ├── config/
│   │   ├── test_classes.py
│   │   ├── test_config_engine_options.py
│   │   ├── test_flask_config.py
│   │   └── test_main_settings.py
│   │
│   ├── core/
│   │   │
│   │   ├── cookies/
│   │   │   ├── test_cookie_header_client.py
│   │   │   └── test_signing.py
│   │   │
│   │   ├── test_crypto.py
│   │   ├── test_extensions.py
│   │   ├── test_jinja_filters.py
│   │   └── test_rate_limit.py
│   │
│   ├── database/
│   │   │
│   │   ├── models/
│   │   │   │
│   │   │   ├── users/
│   │   │   │   └── test_user_token_model.py
│   │   │   │
│   │   │   ├── test_error_log_models.py
│   │   │   ├── test_jobs_model.py
│   │   │   └── test_users.py
│   │   │
│   │   ├── services/
│   │   │   │
│   │   │   ├── config/
│   │   │   │   └── test_settings_service.py
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── test_admin_service.py
│   │   │   │   ├── test_user_token_service.py
│   │   │   │   └── test_users_service.py
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── test_detached_instance_error.py
│   │   │   │   └── test_retry_on_disconnect.py
│   │   │   │
│   │   │   ├── test_error_log_service.py
│   │   │   └── test_jobs_service.py
│   │   │
│   │   └── test_exceptions.py
│   │
│   ├── decorators/
│   │   ├── test_admin_decorators.py
│   │   ├── test_admins_required.py
│   │   └── test_auth_decorators.py
│   │
│   ├── io/
│   │   └── test_jobs_files_service.py
│   │
│   ├── jobs/
│   │   │
│   │   ├── backends/
│   │   │   ├── test_backend_registry.py
│   │   │   ├── test_base.py
│   │   │   ├── test_thread_backend.py
│   │   │   └── test_toolforge_backend.py
│   │   │
│   │   ├── jobs_lifetime/
│   │   │   ├── test_job_creator.py
│   │   │   ├── test_jobs_canceller.py
│   │   │   ├── test_jobs_starter.py
│   │   │   └── test_reconcile.py
│   │   │
│   │   ├── conftest.py
│   │   ├── test_cli_jobs.py
│   │   ├── test_job_executor.py
│   │   ├── test_job_user.py
│   │   └── test_registry.py
│   │
│   ├── jobs_workers/
│   │   │
│   │   ├── base_worker/
│   │   │   ├── test_base_worker.py
│   │   │   ├── test_base_worker_object.py
│   │   │   └── test_job_lifecycle_updates.py
│   │   │
│   │   ├── public_jobs_workers/
│   │   │   │
│   │   │   ├── add_r_column/
│   │   │   │   ├── test_add_r_column_objects.py
│   │   │   │   ├── test_add_r_column_worker.py
│   │   │   │   ├── test_add_rtt.py
│   │   │   │   ├── test_add_rtt_extra.py
│   │   │   │   ├── test_add_rtt_real.py
│   │   │   │   ├── test_add_rtt_utils.py
│   │   │   │   ├── test_wtp_table_manager.py
│   │   │   │   └── test_wtp_tables.py
│   │   │   │
│   │   │   ├── add_unlinkedwikibase/
│   │   │   │   └── test_add_unlinkedwikibase_worker.py
│   │   │   │
│   │   │   ├── archive_today/
│   │   │   │   ├── test_archive_params_data.py
│   │   │   │   ├── test_archive_today_worker.py
│   │   │   │   └── test_removers.py
│   │   │   │
│   │   │   ├── create_redirects/
│   │   │   │   ├── test_create_redirects_objects.py
│   │   │   │   └── test_create_redirects_worker.py
│   │   │   │
│   │   │   ├── duplicate_redirect/
│   │   │   │   └── test_duplicate_redirect_worker.py
│   │   │   │
│   │   │   ├── find_and_replace/
│   │   │   │   ├── test_find_and_replace_objects.py
│   │   │   │   └── test_find_and_replace_worker.py
│   │   │   │
│   │   │   ├── fixred_all/
│   │   │   │   └── test_fixred_all_worker.py
│   │   │   │
│   │   │   ├── fixref/
│   │   │   │   └── test_fixref_worker.py
│   │   │   │
│   │   │   ├── import_history/
│   │   │   │   ├── test_import_history_objects.py
│   │   │   │   └── test_import_history_worker.py
│   │   │   │
│   │   │   ├── medicine_articles/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_medicine_articles_objects.py
│   │   │   │   └── test_medicine_articles_worker.py
│   │   │   │
│   │   │   ├── newupdater_all/
│   │   │   │   └── test_newupdater_all_worker.py
│   │   │   │
│   │   │   ├── owidpopup_all/
│   │   │   │   └── test_owidpopup_all_worker.py
│   │   │   │
│   │   │   └── webarchive_remover/
│   │   │       ├── __init__.py
│   │   │       └── test_webarchive_remover.py
│   │   │
│   │   ├── utils/
│   │   │   └── test_utils_init.py
│   │   │
│   │   ├── test_jobs_worker.py
│   │   ├── test_new_jobs_utils.py
│   │   ├── test_shared_objects.py
│   │   ├── test_utils.py
│   │   ├── test_workers_list.py
│   │   └── test_workers_utils.py
│   │
│   ├── parsers/
│   │   │
│   │   ├── wtp_mapping/
│   │   │   │
│   │   │   ├── data/
│   │   │   │   └── source-1.wiki
│   │   │   │
│   │   │   ├── test_wtp_refs.py
│   │   │   ├── test_wtp_refs_temps.py
│   │   │   └── test_wtp_temps.py
│   │   │
│   │   └── test_shared_wtp.py
│   │
│   ├── routes/
│   │   │
│   │   ├── admin/
│   │   │   │
│   │   │   ├── views/
│   │   │   │   ├── test_admin_endpoints.py
│   │   │   │   ├── test_error_logs.py
│   │   │   │   ├── test_errors_route.py
│   │   │   │   └── test_settings.py
│   │   │   │
│   │   │   └── test_admin_sidebar.py
│   │   │
│   │   └── public/
│   │       │
│   │       ├── newupdater/
│   │       │   ├── test_newupdater_worker.py
│   │       │   └── test_route.py
│   │       │
│   │       ├── routes_services/
│   │       │   └── test_fixred_one.py
│   │       │
│   │       ├── views/
│   │       │   ├── test_fixred.py
│   │       │   └── test_profile.py
│   │       │
│   │       ├── test_legacy_endpoints.py
│   │       ├── test_new_jobs.py
│   │       ├── test_public_init.py
│   │       ├── test_routes_utils.py
│   │       └── test_shared_jobs_routes.py
│   │
│   ├── services/
│   │   │
│   │   ├── auth/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_current_user.py
│   │   │   ├── test_current_user_resolver.py
│   │   │   ├── test_flow.py
│   │   │   └── test_token_manager.py
│   │   │
│   │   └── utils/
│   │       └── test_decode_bytes.py
│   │
│   ├── templates_markups/
│   │   └── test_sidebar.py
│   │
│   ├── utils/
│   │   └── test_verify.py
│   │
│   ├── test_app_factory.py
│   └── test_logging_setup.py
│
├── __init__.py
├── conftest.py
└── README.md

```