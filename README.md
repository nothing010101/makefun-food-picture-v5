# Best-looking food picture — gourmet cheeseburger (make.fun bounty entry)

A tall, glossy gourmet cheeseburger drawn from scratch in pure Python
(stdlib only, deterministic, no network): golden brioche dome with
sesame and a gloss highlight, ruffled lettuce, dill pickles, red onion
rings, tomato, melted cheddar draped over a seared patty with molten
drips, a toasted bottom bun, a sauce drip, golden fries, and soft steam
rising over a dark wooden board. Warm directional light, dark moody
background, burger fills the frame so it reads clearly even at 300 px.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024 PNG, ~170 KB (limit 1 MiB)
```

Two runs produce byte-identical output (verified with `cmp`).
Runtime ~2.3 s per run (limit 60 s). Python 3.13, standard library only.

## Files

- `main.py` — the program (rasterizer + scene, written fresh this session)
- `LICENSE` — MIT
- `.makefun/owner.json` — payout wallet claim
