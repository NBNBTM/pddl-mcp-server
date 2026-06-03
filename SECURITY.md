# Security Policy

## Supported Versions

Security fixes are maintained for the current major version.

| Version | Supported |
| ------- | --------- |
| 4.x     | Yes       |
| < 4.0   | No        |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately through GitHub's security advisory flow if it is enabled for this repository. Do not open a public issue for sensitive security reports.

Never commit real `.env` files, API keys, model tokens, planner credentials, or generated private planning outputs. Use `.env.example` for public configuration documentation and keep deployment secrets in local environment variables or GitHub Secrets.
