# Baseball Feature Atlas — hosting

Password-protected Railway host for the per-feature diagnostic page covering the two
baseball moneyline models:

* **3L** — `mlb_kbo_lmb_3league_final.py`, the production 3-league model (KBO + LMB +
  MLB, 12 inputs) that prices the daily card.
* **2L** — `mlb_kbo_2league_park_experimental.py`, the fork that drops LMB and adds
  `Park_Factor` / `Park_Factor_Sq` (14 inputs).

The report itself is generated elsewhere, by
`C:\AntiGravity Odds Scrapper\baseball_atlas\build_atlas.py`. This repo only serves it.

## Environment variables

Set these in Railway (Service → Variables). They are deliberately **not** in the repo:

| variable | value |
|---|---|
| `ATLAS_USER` | the login |
| `ATLAS_PASS` | the password |

The app refuses to boot if either is missing, so a misconfigured deploy fails loudly
instead of silently serving the report to the internet.

`PORT` is supplied by Railway automatically.

## Publishing a new version of the report

From `C:\AntiGravity Odds Scrapper\baseball_atlas`:

```
powershell -ExecutionPolicy Bypass -File publish.ps1
```

That regenerates the report, copies it to `static/index.html` here, commits and pushes.
Railway redeploys on push.

To skip regeneration and just publish the current HTML:

```
powershell -ExecutionPolicy Bypass -File publish.ps1 -SkipBuild
```

Note that `build_atlas.py` only reads the frozen baseline parquets and the cached
leave-one-out results — it never re-runs the betting pipeline. If the leave-one-out
numbers need refreshing after a model change, delete `baseball_atlas/results/*.json`
and run `python run_loo.py` first (about 20 minutes for both models).

## Routes

- `/` — the report, behind HTTP Basic Auth
- `/healthz` — unauthenticated healthcheck for Railway; returns `{"ok":true}` and the
  report's byte count, nothing else
