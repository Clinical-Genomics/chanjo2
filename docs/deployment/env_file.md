# Custom settings and the .env file

The demo server is connecting to a SQLite database whose temporary tables are destroyed and re-created every time the server is started.
In order to connect to a permanent MYSQL database instance, you'd need to customise the settings present on the [`.env`](https://github.com/Clinical-Genomics/chanjo2/blob/main/.env) file.

## Database settings
```
MYSQL_USER=dbUser
MYSQL_PASSWORD=dbPassword
MYSQL_DATABASE_NAME=chanjo2_test
MYSQL_HOST_NAME=localhost
MYSQL_PORT=3306
```

## Customising the coverage levels used to create coverage reports and genes overview reports

When generating coverage and genes overview reports, the metrics showcased in these documents are calculated across various coverage levels, such as 10x, 20x, and 50x.
These specific coverage levels can be directly specified in queries to the `/report` and `/overview` endpoints using the `completeness_thresholds parameter`, which accepts a list of integers. 
For detailed instructions, please refer to the [coverage-reports documentation](../usage/coverage-reports.md).
Alternatively, you can define these coverage levels in the .env file by adding the following line:

```
REPORT_COVERAGE_LEVELS=[100,150,,..]
```

If the `REPORT_COVERAGE_LEVELS` parameter is not present in the .env file and a request does not include a completeness_thresholds value, the report metrics will **default to the following coverage level values: [10, 15, 20, 50, 100]**.

It's important to note that if coverage level values are provided through multiple methods as described above, the application will prioritize them in the following order:

1. Values specified in the user's request
2. Values included in the .env file
3. Default coverage level values

Furthermore, it's worth considering that the more coverage levels provided, the longer it will take for the report pages to load.

## Endpoint Protection Using OIDC Authentication

Chanjo2 supports authenticated requests via OIDC. This functionality has been tested with Keycloak but should also work with Google authentication.
To enforce authentication for the /report, /overview, /gene_overview, /mane_overview and all /coverage endpoints, uncomment and customize the following parameter.

```
## Optional OIDC login settings
# JWKS_URL=https://example.com/realms/<realm-name>/protocol/openid-connect/certs
# AUDIENCE=account
```

More information about authenticated requests can be found in the following document: [Authorised Requests](../usage/authorised_requests.md).

The last line present on this file (`DEMO=Y`) should be removed or commented out when the app is not running in development mode.