# Trading interface design

The primary job is to let a visitor react to observable order intent, place a virtual trade and understand the resulting risk. The market itself is the focal visual. No promotional hero or repeated statistic-card grid precedes it.

## Tokens and visual choices

- Research navy `#173e60`: inherited site identity and primary controls.
- Plot ink `#243b4d`: price labels and high-contrast body text.
- Up teal `#197b70`: rising candles, long-side execution.
- Down rust `#b34e43`: falling candles, short-side execution; functional colour, not decoration.
- Slate `#667785`: secondary data and metadata.
- Grid/paper `#dce5eb` / `#f5f8fa`: plot rhythm and workspace background; main plot remains white.

Source Sans 3 carries controls, readable data and body text. Source Serif 4 carries the restrained page title, following the existing research site. All data uses tabular figures; no tiny all-caps or mandatory monospace labels.

## Layout

Desktop: inherited site header; compact title; single setup/playback strip; main market frame split into chart/events on the left and account/order ticket on the right. The bottom continuation contains a small mechanism view, clear rules and research links.

```
site navigation
title                            short synthetic-market marker
scenario / guided-experiment / playback / retry
market name + last price         account net value
candle chart                     position, trade size, order actions
volume chart                     trades + available capital
event tape                       account history
phase/fast/slow view              review rules / mathematics link
```

Mobile stacks market, ticket and event tape; controls wrap into purposeful rows, plot axes remain inside the viewport, and order actions are reachable with touch. No hover-only explanation or drag-only control is required.

## Brief review

A black terminal with neon gain labels would not match the existing academic site. A white board with restrained market colours and a genuine interactive candle plot provides the trading character without changing the site's identity. The chart, price markers and readable order ticket are the deliberate visual focus; model commentary remains quieter and follows the action.

## Content and states

The fictional instrument is named Collective Index. A concise synthetic-market label is always visible. Guided mode describes set teaching conditions; experiment mode shows only current intent. The empty chart tells users to start or advance one tick. Order feedback uses plain bilingual explanations. End-of-round review opens after all positions settle, with numbers from the accounting module and the engine's actual path. Scores never imply real-world predictive success.

Keyboard focus, reduced motion, dialog dismissal, 390-pixel layout, bilingual state changes and real-engine interactions are acceptance requirements. SVG/canvas assets are native and require no external chart service or remote font requests.

## Review iteration

Real-engine desktop/mobile review identified three interaction issues: a narrow mobile title, order messages below the mobile fold and native-dialog positioning. The title now has a full-width line with the synthetic marker beside the back link; the latest intent/execution message is repeated inside the chart frame; and the modal uses explicit viewport positioning with internal scroll. Guided playback pauses when an intent arrives, giving visitors time to choose before continuing. Experiment playback does not pause automatically. The detailed event tape remains available for chronological review.

The root acceptance run has already exercised long/short entry, partial exit, final settlement, mode/settings changes and language switching with no console or HTTP errors. Final visual screenshots and bounds are checked by root after the iteration; this note does not substitute for those exported QA records.
