# Enforcing OIDC Authentication in Requests

By default, Chanjo2 endpoints are open to unauthenticated access. To enforce OIDC (OpenID Connect) authentication, you can configure your `.env` file by uncommenting and updating the following lines:

```dotenv
## Optional OIDC login settings
# JWKS_URL=https://example.com/realms/<realm-name>/protocol/openid-connect/certs
# AUDIENCE=account
```

> ✅ `JWKS_URL` should point to your OIDC provider’s JSON Web Key Set (JWKS).  
> ✅ `AUDIENCE` must match the `aud` claim in the access token issued by your provider.

### Provider-specific JWKS URLs

| Provider   | Example JWKS URL                                              |
|------------|---------------------------------------------------------------|
| **Google** | `https://www.googleapis.com/oauth2/v3/certs`                  |
| **Auth0**  | `https://<your-domain>/.well-known/jwks.json`                |
| **Keycloak** | `https://example.com/realms/<realm-name>/protocol/openid-connect/certs` |

### What is `AUDIENCE`?

The `AUDIENCE` setting tells your server what client/app the token is intended for.

- For **Keycloak**, it's typically the client ID.
- For **Google**, it's your OAuth2 client ID.
- For **Auth0**, it's the API identifier you configured.

---

## Protected Endpoints

Once the `.env` file is configured with valid `JWKS_URL` and `AUDIENCE`, the following endpoints will require an access token:

| Endpoint                             | Token Method(s)              |
|--------------------------------------|------------------------------|
| `/report`                            | Form field, Cookie           |
| `/overview`                          | Form field, Cookie           |
| `/gene_overview`                     | Form field, Cookie           |
| `/mane_overview`                     | Form field, Cookie           |
| `/coverage/d4/interval/`             | Authorization header          |
| `/coverage/d4/interval_file/`        | Authorization header         |
| `/coverage/d4/genes/summary`         | Authorization header         |
| `/coverage/samples/predicted_sex`    | Authorization header         |


If no token is provided, or the token is invalid or expired, the server will return **HTTP 401 Unauthorized**.

---

## Providing the `access_token` in Requests

There are three supported methods for including the access token in a request:

### 1. ✅ As a Form Field

**curl example:**

```bash
curl -X POST https://your-chanjo2-url/report \
  -d "other_form_field" \
  -d "access_token=eyJhbGciOi..." \
  -H "Content-Type: application/x-www-form-urlencoded"
```

---

### 2. ✅ As a Cookie

**curl example:**

```bash
curl https://your-chanjo2-url/overview \
  --cookie "access_token=eyJhbGciOi..."
```

---

### 3. ✅ As an Authorization Header

Standard for APIs and OAuth2-based integrations.

**curl example:**

```bash
curl https://your-chanjo2-url/gene_overview \
  -H "Authorization: Bearer eyJhbGciOi..."
```

Let us know if you run into issues or want to validate token claims manually.