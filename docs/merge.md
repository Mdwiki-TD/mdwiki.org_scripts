# Overview

# Code Sources

| Endpoint    | status | Method | Description | Source                                                                              |
| ----------- | ------ | ------ | ----------- | ----------------------------------------------------------------------------------- |
| `/tools`    |        | GET    | Tools       | [Mdwiki-TD/mdwiki.toolforge.org](https://github.com/Mdwiki-TD/mdwiki.toolforge.org) |
| `/new_html` |        | GET    | -           | [mdwikicx/new_html](https://github.com/mdwikicx/new_html)                           |

# End points

## Tools

### Source Endpoints

| Endpoint                       | Method | Description            |
| ------------------------------ | ------ | ---------------------- |
| `/mdwiki4.php`, `/mdwiki5.php` | GET    | mdw updater            |
| `/redirect.php`                | GET    | create redirects job   |
| `/fixred.php`                  | GET    | fix redlinks           |
| `/fixref.php`                  | GET    | fix references job     |
| `/dup.php`                     | GET    | duplicate redirect job |
| `/import-history.php`          | GET    | import history job     |
| `/replace.php`                 | GET    | find & replace job     |

### Flask Endpoints

| Route | Method | Description | Status |
| ----- | ------ | ----------- | ------ |
| `/`   | GET    | Homepage    |        |

## new html

### Source Endpoints

| Endpoint             | Method | Description                                                             |
| -------------------- | ------ | ----------------------------------------------------------------------- |
| `/`                  | GET    | Main entry - router (redirects to dashboard or processes `title` param) |
| `/check.php`         | GET    | Check if cached content exists for a revision ID                        |
| `/open.php`          | GET    | View generated files (wikitext, HTML, segments) by revision ID          |
| `/fix.php`           | GET    | Wikitext fix testing form                                               |
| `/fix.php`           | POST   | Apply wikitext fixes and display result                                 |
| `/revisions.php`     | GET    | Revisions dashboard (HTML table)                                        |
| `/revisions_api.php` | GET    | Revisions API (JSON payload)                                            |
| `/revisions.html`    | GET    | Static dashboard page                                                   |

### Flask Endpoints

| Route | Method | Description | Status |
| ----- | ------ | ----------- | ------ |
| `/`   | GET    | Homepage    |        |
