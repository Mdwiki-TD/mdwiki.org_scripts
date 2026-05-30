Analyze all functions that connect to the database within the flask_app/main_app/db/services folder:

-   If they use try/except or @db_guard, skip them.
-   If not:

    -   Look for their usage; if they are protected by try/except, skip them.
    -   If not:

        -   If they are used only once or twice, add try/except protection,
            -   for example:
                ```python
                	try:
                		coordinators = admin_service.list_coordinators()
                	except Exception:  # pragma: no cover - defensive guard
                		logger.exception("Unable to list coordinators.")
                		flash("Unable to list coordinators.", "danger")
                		coordinators = []
                ```
        -   If they are used frequently (more than 3 times), such as the active_coordinators function:

            -   Add @db_guard, for example:

                ````python
                @db_guard(default_return=[], msg="Failed to active coordinators")
                def active_coordinators() -> list[str]:
                	"""Get a list of active coordinator usernames from the database."""
                	records = db.session.query(AdminUserRecord).filter(AdminUserRecord.is_active).all()
                	return [u.username for u in records]
                	```
                ````
