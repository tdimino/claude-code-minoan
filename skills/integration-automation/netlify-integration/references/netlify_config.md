# netlify.toml Configuration Guide

Complete reference for configuring Netlify deployments using `netlify.toml`.

## File Location

Place `netlify.toml` in the **root** of your repository.

## Basic Structure

```toml
[build]
  # Build configuration

[build.environment]
  # Environment variables for build process

[functions]
  # Serverless functions configuration

[dev]
  # Local development settings

[[redirects]]
  # URL redirects and rewrites

[[headers]]
  # HTTP headers configuration

[context.production]
  # Production-specific overrides

[context.deploy-preview]
  # Preview deploy overrides

[context.branch-deploy]
  # Branch deploy overrides
```

## Build Configuration

### Basic Build Settings

```toml
[build]
  # Command to build your site
  command = "npm run build"

  # Directory to publish (relative to repository root)
  publish = ".next"

  # Directory containing serverless functions
  functions = ".netlify/functions"

  # Base directory for the build (if site is in subdirectory)
  base = ""

  # Skip automatic dependency installation
  ignore = "git diff --quiet $CACHED_COMMIT_REF $COMMIT_REF ."
```

### Build Environment Variables

```toml
[build.environment]
  # Node.js version
  NODE_VERSION = "18"

  # NPM flags
  NPM_FLAGS = "--legacy-peer-deps"

  # Enable TypeScript strict mode
  TS_NODE_SKIP_IGNORE = "true"

  # Next.js specific
  NEXT_TELEMETRY_DISABLED = "1"
```

### Build Processing

```toml
[build.processing]
  # Skip all post-processing
  skip_processing = false

  # CSS configuration
  [build.processing.css]
    bundle = true
    minify = true

  # JavaScript configuration
  [build.processing.js]
    bundle = true
    minify = true

  # Image configuration
  [build.processing.images]
    compress = true
```

## Functions Configuration

### Basic Functions Settings

```toml
[functions]
  # Directory containing your functions
  directory = ".netlify/functions"

  # Node bundler (esbuild or nft)
  node_bundler = "esbuild"

  # Files to include in function deployment
  included_files = [
    ".netlify/functions/**",
    "src/lib/**"
  ]

  # External Node.js modules (not bundled)
  external_node_modules = ["sharp", "pg-native"]

  # Default timeout in seconds (max 26 for Pro, 10 for free)
  timeout = 10
```

### Function-Specific Configuration

```toml
# Configure individual functions
[[functions."webhook"]]
  timeout = 26
  memory = 1024

[[functions."sms-processor"]]
  timeout = 26
  memory = 512
```

### Scheduled Functions

```toml
[[functions."scheduled-task"]]
  schedule = "@daily"  # Cron syntax
```

Common schedule values:
- `@hourly` - Every hour
- `@daily` - Every day at midnight UTC
- `@weekly` - Every Sunday at midnight UTC
- `@monthly` - First day of month at midnight UTC
- Custom: `"0 9 * * 1-5"` - 9 AM weekdays

## Redirects and Rewrites

### API Rewrites

```toml
[[redirects]]
  # Rewrite /api/* to Netlify Functions
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
  force = true
```

### URL Redirects

```toml
[[redirects]]
  # 301 permanent redirect
  from = "/old-path"
  to = "/new-path"
  status = 301

[[redirects]]
  # 302 temporary redirect
  from = "/temp"
  to = "/new-location"
  status = 302
```

### Conditional Redirects

```toml
[[redirects]]
  # Redirect based on country
  from = "/"
  to = "/uk"
  status = 302
  conditions = {Country = ["GB"]}

[[redirects]]
  # Redirect based on language
  from = "/"
  to = "/fr"
  status = 302
  conditions = {Language = ["fr"]}

[[redirects]]
  # Redirect based on role (requires Netlify Identity)
  from = "/admin/*"
  to = "/login"
  status = 401
  conditions = {Role = ["!admin"]}
```

### Proxy Rewrites

```toml
[[redirects]]
  # Proxy to external API (avoid CORS)
  from = "/proxy/api/*"
  to = "https://api.external.com/:splat"
  status = 200
  force = true
  headers = {X-From = "Netlify"}
```

### SPA Fallback

```toml
[[redirects]]
  # Single Page Application fallback
  from = "/*"
  to = "/index.html"
  status = 200
```

## Headers Configuration

### Security Headers

```toml
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Permissions-Policy = "geolocation=(), microphone=(), camera=()"
```

### CORS Headers

```toml
[[headers]]
  for = "/api/*"
  [headers.values]
    Access-Control-Allow-Origin = "*"
    Access-Control-Allow-Methods = "GET, POST, PUT, DELETE, OPTIONS"
    Access-Control-Allow-Headers = "Content-Type, Authorization"
```

### Caching Headers

```toml
[[headers]]
  for = "/static/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
```

## Context-Specific Configuration

### Production Context

```toml
[context.production]
  command = "npm run build:production"
  publish = ".next"

  [context.production.environment]
    NODE_ENV = "production"
    NEXT_PUBLIC_API_URL = "https://api.production.com"
```

### Deploy Preview Context

```toml
[context.deploy-preview]
  command = "npm run build:staging"

  [context.deploy-preview.environment]
    NODE_ENV = "staging"
    NEXT_PUBLIC_API_URL = "https://api.staging.com"
```

### Branch Deploy Context

```toml
[context.branch-deploy]
  command = "npm run build:dev"

  [context.branch-deploy.environment]
    NODE_ENV = "development"
```

### Branch-Specific Context

```toml
[context.develop]
  command = "npm run build:dev"

  [context.develop.environment]
    DEBUG = "true"
```

## Local Development (Netlify Dev)

```toml
[dev]
  # Command to start local dev server
  command = "npm run dev"

  # Port for local dev server
  port = 3000

  # Port for functions
  functions = 9999

  # Auto-open browser
  autoLaunch = true

  # Target URL for proxy mode
  targetPort = 3000

  # Framework detection override
  framework = "#custom"
```

## Plugins Configuration

Note: For Next.js projects, the OpenNext adapter (`@opennextjs/netlify`) now auto-detects and requires no plugin entry. The `@netlify/plugin-nextjs` package is legacy.

```toml
[[plugins]]
  package = "@netlify/plugin-nextjs"

  [plugins.inputs]
    # Plugin-specific configuration

[[plugins]]
  package = "@netlify/plugin-lighthouse"

  [plugins.inputs.thresholds]
    performance = 0.9
    accessibility = 0.9
    best-practices = 0.9
    seo = 0.9
```

## Edge Functions (Beta)

```toml
[[edge_functions]]
  path = "/api/edge"
  function = "edge-handler"

[[edge_functions]]
  path = "/geolocation"
  function = "geo-redirect"
```

## Complete Example for Twilio-Aldea

```toml
# Netlify configuration for Twilio-Aldea

[build]
  command = "npm run build"
  publish = ".next"
  functions = ".netlify/functions"

[build.environment]
  NODE_VERSION = "18"
  NEXT_TELEMETRY_DISABLED = "1"
  NPM_FLAGS = "--legacy-peer-deps"

[functions]
  directory = ".netlify/functions"
  node_bundler = "esbuild"
  included_files = [".netlify/functions/**", "src/lib/**"]
  timeout = 10

# Webhook function with extended timeout
[[functions."sms-webhook"]]
  timeout = 26

# API rewrites
[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
  force = true

# Security headers
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Content-Security-Policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"

# CORS for API endpoints
[[headers]]
  for = "/api/*"
  [headers.values]
    Access-Control-Allow-Origin = "*"
    Access-Control-Allow-Methods = "GET, POST, OPTIONS"
    Access-Control-Allow-Headers = "Content-Type, Authorization"

# Production environment
[context.production]
  [context.production.environment]
    NODE_ENV = "production"

# Preview environment
[context.deploy-preview]
  [context.deploy-preview.environment]
    NODE_ENV = "staging"

# Local development
[dev]
  command = "npm run dev"
  port = 3000
  functions = 9999
```

## Common Patterns

### Monorepo Configuration

```toml
[build]
  base = "apps/web"
  command = "npm run build"
  publish = ".next"
```

### Environment-Specific Builds

```toml
[context.production.environment]
  REACT_APP_ENV = "production"

[context.deploy-preview.environment]
  REACT_APP_ENV = "staging"

[context.branch-deploy.environment]
  REACT_APP_ENV = "development"
```

### Custom Build Conditions

```toml
[build]
  # Only build if specific files changed
  ignore = "git diff --quiet $CACHED_COMMIT_REF $COMMIT_REF -- src/"
```

### Function Memory Allocation

```toml
[[functions."high-memory-function"]]
  memory = 3008  # Max memory in MB
  timeout = 26
```

## Best Practices

1. **Always set NODE_VERSION** - Ensures consistent builds
2. **Use function-specific timeouts** - Only increase timeout for functions that need it
3. **Leverage context-specific configs** - Different settings for production vs preview
4. **Set security headers** - Protect against common vulnerabilities
5. **Use force = true for rewrites** - Ensures rewrites take precedence
6. **Include necessary files in functions** - Use `included_files` for shared code
7. **Optimize build performance** - Use ignore rules to skip unnecessary builds
8. **Set appropriate cache headers** - Balance freshness with performance

## Troubleshooting

### Build fails with "command not found"

Check NODE_VERSION and ensure all dependencies are in package.json.

### Functions return 404

Verify:
- Functions directory is correct
- Redirects are configured
- Function files are properly exported

### Environment variables not available

Set in Netlify Dashboard (not in netlify.toml for secrets).

### Timeout errors

Increase function timeout:
```toml
[[functions."slow-function"]]
  timeout = 26
```

## Resources

- [Official netlify.toml reference](https://docs.netlify.com/configure-builds/file-based-configuration/)
- [Functions configuration](https://docs.netlify.com/functions/configure-and-deploy/)
- [Redirects and rewrites](https://docs.netlify.com/routing/redirects/)
- [Headers configuration](https://docs.netlify.com/routing/headers/)
