# Validator v2: Independent EMA-based Evaluation

## Summary

Replaces the shared-repo consensus validator (cold-start + `ScorePublisher`) with the INCENTIVE_MECHANISM v2.0 design: each validator independently evaluates miner policy packs via ClawBench, maintains per-scenario Exponential Moving Average (EMA) scores keyed by hotkey, and sets weights on-chain for YC3 aggregation.

## Changes

### Removed

- **`ScorePublisher`** (`trajectoryrl/utils/score_publisher.py`): Deleted the entire shared-repo scoring mechanism (GitHub fork, `gh` CLI, commit/push/PR, pull-all, signature verification, stake-weighted consensus).
- **`examples/score_publish_example.py`** and **`tests/sample_pack.json`**: Removed associated examples and test fixtures.
- **`neurons/validator.py` cold-start loop**: Replaced the 160-line standalone cold-start validator with a thin entry point that delegates to `TrajectoryValidator.main()`.
- **Docker `gh` CLI installation**: No longer needed in `Dockerfile.validator`.
- **Deprecated env vars**: `TARGET_UID`, `WEIGHT_INTERVAL`, `EPOCH_INTERVAL`, `GITHUB_TOKEN`, `VALIDATOR_SCORES_FORK_URL`.

### Added / Refactored

- **Per-scenario EMA** (`trajectoryrl/base/validator.py`):
  - `_update_ema()`: Applies exponential smoothing per scenario per hotkey. Resets EMA when a miner's `pack_hash` changes (new submission).
  - `compute_final_score_from_ema()`: Weighted mean of scenario EMA scores minus a variance penalty.
  - EMA state persistence to JSON (`_load_ema_state` / `_save_ema_state`) with scenario config hash invalidation.

- **Block-based cadences**:
  - `eval_interval_blocks` (default 1200, ~4h): Full evaluation cycle — fetch commitments, download packs, run ClawBench, update EMA.
  - `weight_interval_blocks` (default 360, ~72min): Recompute and set on-chain weights from cached EMA.

- **Block-based inactivity tracking**: Miners are marked inactive if not successfully evaluated within `inactivity_blocks` (default 14400, ~48h). Tracked via `last_eval_block` per hotkey.

- **Pre-launch gate**: `EVAL_START_BLOCK = 5_000_000` — before this block height, the validator skips all evaluation and only calls `_set_fallback_weights()`.

- **Fallback weights**: When no miners qualify (or pre-launch), 100% weight goes to `OWNER_UID = 74` instead of uniform distribution, keeping emissions directed and preventing validator deregistration.

- **Docker config hardening**: Clawbench commit verification gracefully degrades to a warning inside containers (no `.git` metadata after `COPY`).

### Config Changes (`ValidatorConfig`)

| Removed | Added |
|---|---|
| `github_token` | `eval_interval_blocks` (default: 1200) |
| `validator_scores_fork_url` | `weight_interval_blocks` (default: 360) |
| `validator_scores_local_path` | `ema_alpha` (default: 0.3) |
| `epoch_interval` | `inactivity_blocks` (default: 14400) |
| | `ema_state_path` |

### Docker Compose Updates

All compose files (`docker-compose.yml`, `validator.yml`, `validator-staging.yml`, `validator-dev.yml`) updated to:
- Remove `GITHUB_TOKEN`, `VALIDATOR_SCORES_FORK_URL`, `TARGET_UID`, `WEIGHT_INTERVAL`, `EPOCH_INTERVAL`
- Add `EVAL_INTERVAL_BLOCKS`, `WEIGHT_INTERVAL_BLOCKS`, `EMA_ALPHA`, `INACTIVITY_BLOCKS`, `LOG_LEVEL`
- Remove `git_cache` volume mount

### Tests

- Removed: `TestScoreConsensus`, `TestScorePublisherSignAndPublish`
- Added: `TestPerScenarioEMA` (12 tests) — EMA smoothing, pack hash reset, persistence, config hash invalidation
- Updated: `TestInactivityBlocks` (5 tests) — block-based inactivity replacing epoch-based

## Files Changed (14)

```
 .env.miner.example                          |   3 +-
 docker-compose.yml                          |   9 +-
 docker/Dockerfile.validator                 |  19 +-
 docker/docker-compose.validator-dev.yml     |   9 +-
 docker/docker-compose.validator-staging.yml |   9 +-
 docker/docker-compose.validator.yml         |  14 +-
 examples/score_publish_example.py           |  63 --
 neurons/validator.py                        | 163 +-----
 tests/sample_pack.json                      |  37 --
 tests/test_validator.py                     | 565 +++++++++---------
 trajectoryrl/base/validator.py              | 861 +++++++++++++----------
 trajectoryrl/utils/__init__.py              |   2 -
 trajectoryrl/utils/config.py                |  60 +-
 trajectoryrl/utils/score_publisher.py       | 434 --------------
 14 files changed, 747 insertions(+), 1501 deletions(-)
```

## Test Plan

- [ ] `pytest tests/test_validator.py` — all EMA and inactivity tests pass
- [ ] Docker build succeeds: `docker compose -f docker/docker-compose.validator-dev.yml --env-file .env.validator up --build`
- [ ] Validator starts, detects pre-launch phase (block < 5,000,000 on testnet), and sets fallback weights to UID 74
- [ ] After `EVAL_START_BLOCK`, validator enters evaluation loop and processes miner commitments
- [ ] EMA state persists across restarts (`ema_state.json`)
- [ ] Inactive miners are pruned after `inactivity_blocks`
