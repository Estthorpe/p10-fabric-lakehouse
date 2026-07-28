# %% [markdown]
# # P10 | Food Distribution — Bronze Source Profiling
# ## Clarivance Analytics Group
#
# **Analyst:** Esther Uzor
# **Date:** 28 July 2026
# **Dataset:** Ingrifoods operational extract — orders, deliveries, products, depots
#
# ### Objective
# Profile the four raw source extracts *before* they are modelled, and produce a
# defect register that the Silver data quality contracts will be written against.
#
# ### Why this comes first
# Contracts invented before looking at data test imagination. Contracts derived
# from profiling test the data. This notebook is the evidence base for every
# `fail-closed` rule in `src/contracts/`.
#
# ### Deviation from the standard EDA framework
# The Clarivance 7-phase EDA framework assumes a single table with a target
# column. This is a four-table relational extract with no target, so Phase 6
# (bivariate vs target) and Phase 7 (multicollinearity) are replaced by
# **referential integrity** and **business-rule** checks — the failure modes that
# actually matter in a lakehouse ingestion layer.

# %% [markdown]
# ---
# ## Section 2 — Environment

# %%
# ── Data manipulation ────────────────────────────────────────
import pandas as pd
import numpy as np
from pathlib import Path

# ── Visualisation ────────────────────────────────────────────
import matplotlib.pyplot as plt
import seaborn as sns

# ── Configuration ────────────────────────────────────────────
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
sns.set_theme(style='whitegrid')

# Clarivance brand colours
NAVY  = '#0D1F3C'   # Midnight Navy — titles
TEAL  = '#00B4A6'   # Signal Teal   — primary series
GOLD  = '#F5A623'   # Amber Gold    — warnings
RED   = '#E03E3E'   # Signal Red    — defects
GREEN = '#2ECC8F'   # Sage Green    — healthy
GREY  = '#8A9BB0'   # Cool Grey     — baselines

FIGDIR = Path('../docs/eda')
FIGDIR.mkdir(parents=True, exist_ok=True)

# display() is an IPython builtin — fall back to print if run as a plain script
try:
    display
except NameError:
    display = print

print("Environment ready.")

# %% [markdown]
# ---
# ## Section 3 — Load the raw extracts
#
# Loaded with **no type coercion and no parsing**. Reading raw exactly as the
# source system produced it is the point — if a date arrives as a string or a
# flag arrives as text, that is a finding, not an inconvenience to be silently
# fixed on import.

# %%
RAW = Path('../data/raw')

tables = {
    'products':   pd.read_csv(RAW / 'products.csv'),
    'depots':     pd.read_csv(RAW / 'depots.csv'),
    'orders':     pd.read_csv(RAW / 'orders.csv'),
    'deliveries': pd.read_csv(RAW / 'deliveries.csv'),
}

for name, df in tables.items():
    print(f"{name:<12} {df.shape[0]:>7,} rows  x  {df.shape[1]} cols")

# %% [markdown]
# ---
# ## Phase 1 — Shape & schema audit
#
# Looking for columns whose storage type disagrees with their meaning: dates held
# as strings, flags held as objects, numerics that arrived as text because one bad
# value poisoned the whole column.

# %%
def schema_audit(name, df):
    out = pd.DataFrame({
        'dtype': df.dtypes.astype(str),
        'non_null': df.notna().sum(),
        'nulls': df.isna().sum(),
        'null_pct': (df.isna().sum() / len(df) * 100).round(2),
        'n_unique': df.nunique(),
        'sample': [df[c].dropna().iloc[0] if df[c].notna().any() else None
                   for c in df.columns],
    })
    print(f"\n{'='*72}\n{name.upper()}  —  {len(df):,} rows\n{'='*72}")
    display(out)
    return out

audits = {name: schema_audit(name, df) for name, df in tables.items()}

# %% [markdown]
# **Your read.** Which columns are stored as the wrong type, and which of those
# matter? Not every string-typed date is a problem — but a flag column that is
# `object` instead of `bool` usually means something non-boolean got in.

# %% [markdown]
# ---
# ## Phase 2 — Missingness: count *and* pattern
#
# A count tells you how much is missing. The pattern tells you whether it is
# random or systematic — and systematic missingness is informative, not noise.
# If a column is null only when another column takes a particular value, that is
# a finding worth a contract.

# %%
for name, df in tables.items():
    miss = (pd.DataFrame({'nulls': df.isna().sum(),
                          'pct': (df.isna().sum() / len(df) * 100).round(2)})
            .query('nulls > 0').sort_values('pct', ascending=False))
    if len(miss):
        print(f"\n{name}:")
        display(miss)
    else:
        print(f"\n{name}: no nulls")

# %% [markdown]
# **Your investigation.** For each column with nulls, test whether the
# missingness is random. Pick one and slice the data by another column to see
# whether nulls concentrate anywhere. Write down what you find.

# %%
# YOUR CODE — is the missingness random or systematic?

# %% [markdown]
# ---
# ## Phase 3 — Key integrity: uniqueness and duplication
#
# Every table has a column that is *supposed* to be unique. Where it isn't, every
# downstream join silently multiplies rows — and the number that reaches a
# dashboard is wrong in a way nobody notices for months.

# %%
candidate_keys = {
    'products':   'product_id',
    'depots':     'depot_id',
    'orders':     'order_line_id',
    'deliveries': 'delivery_id',
}

for name, key in candidate_keys.items():
    df = tables[name]
    n_rows, n_keys = len(df), df[key].nunique()
    dup_keys = n_rows - n_keys
    full_dupes = df.duplicated().sum()
    flag = 'OK ' if dup_keys == 0 else 'DUP'
    print(f"[{flag}] {name:<12} {key:<16} "
          f"rows={n_rows:>7,}  distinct={n_keys:>7,}  "
          f"dup_keys={dup_keys:>5,}  identical_rows={full_dupes:>5,}")

# %% [markdown]
# **Your read.** Where a key duplicates, inspect the offending rows. Are they
# byte-identical (a double-load) or genuinely different records sharing a key
# (a source-system bug)? The two need different contracts.

# %%
# YOUR CODE — inspect the duplicate rows

# %% [markdown]
# ---
# ## Phase 4 — Numeric distributions and impossible values
#
# Two different questions, and it is worth keeping them apart:
#
# - **Outlier** — unusual but possible. A 210 km delivery is long, not wrong.
# - **Impossible** — violates the definition of the column. A negative distance
#   is not a large number in the wrong direction; it is not a distance at all.
#
# Outliers get investigated. Impossible values get a fail-closed contract.

# %%
def numeric_profile(name, df):
    num = df.select_dtypes(include='number')
    if num.empty:
        return
    prof = pd.DataFrame({
        'min': num.min(), 'p05': num.quantile(0.05),
        'median': num.median(), 'p95': num.quantile(0.95),
        'max': num.max(), 'mean': num.mean().round(2),
        'skew': num.skew().round(2),
        'n_negative': (num < 0).sum(),
        'n_zero': (num == 0).sum(),
    })
    print(f"\n{name}:")
    display(prof.round(2))

for name, df in tables.items():
    numeric_profile(name, df)

# %% [markdown]
# Distribution grid — the visual pass. Look for values clustered where they
# should not be, and for tails that run past the edge of what the column can
# legitimately mean.

# %%
num_targets = [
    ('orders', 'quantity'), ('orders', 'unit_price'),
    ('deliveries', 'distance_km'),
    ('products', 'unit_cost'), ('products', 'unit_price'),
    ('products', 'shelf_life_days'),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, (tname, col) in zip(axes.flatten(), num_targets):
    s = tables[tname][col].dropna()
    ax.hist(s, bins=45, color=TEAL, edgecolor='white', alpha=0.88)
    ax.axvline(s.median(), color=RED, linestyle='--', lw=1.4, label='median')
    ax.set_title(f'{tname}.{col}\nskew={s.skew():.2f}  min={s.min():,.2f}',
                 fontsize=10, color=NAVY)
    ax.legend(fontsize=8)

plt.suptitle('Bronze Source Distributions', fontsize=14,
             fontweight='bold', color=NAVY, y=1.00)
plt.tight_layout()
plt.savefig(FIGDIR / 'eda_01_distributions.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ---
# ## Phase 5 — Categorical conformance
#
# The classic silent killer: `'DELIVERED'`, `'Delivered'` and `' DELIVERED'` are
# three different strings and one real category. Every `GROUP BY` splits them,
# every count is wrong, and nothing errors.

# %%
def categorical_profile(name, df, max_card=60):
    cats = df.select_dtypes(include='object')
    for col in cats.columns:
        n_unique = df[col].nunique()
        if n_unique > max_card:
            print(f"{name}.{col}: {n_unique:,} distinct — high cardinality, skipped")
            continue
        vc = df[col].value_counts(dropna=False)
        print(f"\n{name}.{col}  ({n_unique} distinct)")
        display(vc.to_frame('count').head(20))

for name in ['products', 'depots', 'deliveries']:
    categorical_profile(name, tables[name])

# %% [markdown]
# **Your read.** Which of these columns contain the same real-world value more
# than once under different spellings? A useful trick: compare the raw distinct
# count against the distinct count after `.str.strip().str.upper()`. If the two
# numbers disagree, you have a conformance defect and you know its size.

# %%
# YOUR CODE — quantify the conformance gap

# %% [markdown]
# ---
# ## Phase 6 — Referential integrity *(replaces bivariate-vs-target)*
#
# Every foreign key is a promise: *this value exists in the parent table*. Broken
# promises do not raise errors — they quietly drop rows at join time, and the
# total on the dashboard comes out low with no indication why.
#
# One worked example below. **The rest are yours** — there are four more foreign
# key relationships in this schema.

# %%
def fk_check(child_df, child_col, parent_df, parent_col, label):
    child_vals = child_df[child_col].dropna()
    orphan_mask = ~child_vals.isin(parent_df[parent_col])
    n_orphan = int(orphan_mask.sum())
    n_distinct = child_vals[orphan_mask].nunique()
    pct = n_orphan / len(child_vals) * 100 if len(child_vals) else 0
    status = 'PASS' if n_orphan == 0 else 'FAIL'
    print(f"[{status}] {label:<42} orphans={n_orphan:>6,} "
          f"({pct:.2f}%)  distinct_bad_keys={n_distinct}")
    if n_orphan:
        print(f"         offending values: "
              f"{sorted(child_vals[orphan_mask].unique())[:10]}")
    return n_orphan


# WORKED EXAMPLE
fk_check(tables['orders'], 'product_id',
         tables['products'], 'product_id',
         'orders.product_id -> products')

# %% [markdown]
# **Your turn.** Write the remaining foreign key checks. The relationships to
# test are the ones implied by the schema — think about which columns in one
# table are meant to point at another. Reuse `fk_check`; it takes five arguments
# and prints its own verdict.

# %%
# YOUR CODE — the remaining foreign key checks

# %% [markdown]
# ---
# ## Phase 7 — Business rules *(replaces multicollinearity)*
#
# The defects that no generic profiler will ever catch, because they are not
# statistical — they are violations of how the business actually works. Each one
# is a candidate **singular test** in dbt.
#
# One worked example. **At least three more are findable** in this schema.

# %%
def rule_check(mask, label, df=None):
    n = int(mask.sum())
    status = 'PASS' if n == 0 else 'FAIL'
    print(f"[{status}] {label:<52} violations={n:>6,}")
    if n and df is not None:
        display(df[mask].head(5))
    return n


# WORKED EXAMPLE — a delivery cannot complete before it departs
d = tables['deliveries'].copy()
d['dispatched_at'] = pd.to_datetime(d['dispatched_at'])
d['delivered_at']  = pd.to_datetime(d['delivered_at'])

rule_check(d['delivered_at'] < d['dispatched_at'],
           'delivered_at earlier than dispatched_at', d)

# %% [markdown]
# **Your turn.** What else must be true in a food distribution business that a
# schema cannot enforce? Consider: the relationship between an order and its
# delivery in time · the relationship between cost and price on a product ·
# what a quantity is allowed to be · what a distance is allowed to be · whether
# an order line's price should agree with the product master.
#
# Write a `rule_check` for each rule you can articulate.

# %%
# YOUR CODE — business rule checks

# %% [markdown]
# ---
# ## Defect register — the deliverable
#
# This table is the whole point of the notebook. Everything above is evidence;
# this is the finding. Each row becomes a data quality contract in
# `src/contracts/`, and the **Action** column is the judgement call.
#
# **Fail-closed** — the pipeline stops. Use when the defect makes downstream
# numbers *wrong* rather than *incomplete*: broken keys, duplicated grain,
# impossible values, violated business rules.
#
# **Warn** — the row is quarantined or flagged and the pipeline continues. Use
# when the defect is tolerable, expected at some background rate, or when
# stopping would cause more harm than the bad data.
#
# **Cleanse** — silver fixes it deterministically. Use for conformance issues
# where the correct value is unambiguous, e.g. trimming and upper-casing a status.
#
# | # | Table | Column(s) | Defect | Rows | Action | Rationale |
# |---|-------|-----------|--------|------|--------|-----------|
# | 1 |  |  |  |  |  |  |
# | 2 |  |  |  |  |  |  |
# | 3 |  |  |  |  |  |  |
#
# > Fill this in from what you actually found. Row counts must come from the
# > checks above — not estimates. The rationale column is what a reviewer reads.

# %% [markdown]
# ---
# ## Summary — carry into F-A silver
#
# | Check | Finding | Contract |
# |-------|---------|----------|
# | Schema / dtypes |  |  |
# | Missingness |  |  |
# | Key uniqueness |  |  |
# | Impossible values |  |  |
# | Categorical conformance |  |  |
# | Referential integrity |  |  |
# | Business rules |  |  |
#
# **Commit message when done:**
# `[EDA] Bronze source profiling complete — N defects registered across 4 tables`
