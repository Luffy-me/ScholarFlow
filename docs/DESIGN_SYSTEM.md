# Design System

Path: `design/`

## Tokens

| File | Purpose |
|---|---|
| `colors.json` | Neutral / accent / dark palettes |
| `spacing.json` | 8px scale + slide padding |
| `typography.json` | Families, sizes, weights |
| `icons.json` | Libraries + role aliases |
| `themes.json` | Brand themes |
| `layouts/*.json` | Region templates |

## Themes

Apple, Stripe, Linear, Anthropic, OpenAI, Notion, Minimal, Dark

Each theme defines: `bg`, `fg`, `accent`, `muted`, `radius`, `density`

## Icons

Libraries: Lucide, Heroicons, Material, Phosphor, Tabler

Icon engine returns IDs only (`lucide:lightbulb`).

## Components

`components/` provides reusable content objects (Heading, Card, Metric, …) that map into Scene Graph elements.
