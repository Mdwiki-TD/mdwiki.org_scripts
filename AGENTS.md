# Development Entry Point

Use the following command for local development:

    flask --app src.app1 run

The src.app1 module is the preferred Flask entry point for development tasks.

# UI Testing

The admin interface normally requires the authenticated user to be present in the coordinators table.

For local UI/E2E testing only, agents may enable:

    UI_TEST_BYPASS_COORDINATOR_CHECK=true

This bypass is honored only in DevelopmentConfig and is ignored in ProductionConfig.

Do not use this bypass when testing authorization or permission-related behavior.
