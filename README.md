# INT Revenue Dashboard — MANCOM Weekly
## Comprehensive Project Summary

---

## Project Overview
A single-file HTML/JS revenue dashboard for the INT team's weekly MANCOM (Management Committee) meetings. It visualizes sales pipeline, BD leads, AM performance, win rates, and tribe attainment from a CSV dataset. The dashboard supports encrypted CSV files, dual-week comparison, light/dark themes, and is fully configurable via a JSON settings file.

**Output file:** `index.html` (single file, no build step)
**Source CSV:** `20260318_AMBD_Universe_Raw.csv` (335 rows, 51 columns)
**CSV location:** All CSVs load from the `data/` directory
**Config file:** `config.json` (auto-loaded from root on page load)
**Server:** `server.py` (HTTPS over LAN via `ThreadingHTTPServer` with self-signed cert)

---

## Tech Stack
- **PapaParse 5.4.1** — CSV parsing (CDN)
- **Chart.js 4.4.1** — Charts (CDN)
- **Google Fonts: DM Sans** — All text and numbers use DM Sans exclusively (Space Mono was removed)
- **Web Crypto API** — AES-GCM encryption with PBKDF2 key derivation (100K iterations, SHA-256)
- No build tools, no frameworks, no npm — pure vanilla HTML/CSS/JS

---

## CSV Data Structure (Key Columns)
```
Client, Project, Status, Confidence, Priority, Amount (VAT-Ex.) (PHP),
Amount (VAT-Ex.) (USD), Sign Date, Source, BD, AM, PM, MKT, Project Code,
VAT%, Amount (VAT-Inc.), GP%, GP, Week Number, RFP Received Date,
RFPR-WeekNum, Tribe, Pipeline Tier, Year, Month, Project Start, Project End,
AM Weight, Weighted Amount (PHP), Weighted Amount (USD),
Weighted Pitch Phase (PHP), Weighted Awarded Phase (PHP),
Weighted Collection Phase (PHP), Weighted Completed Cycle (PHP),
Lead Progress, Lead Phase, Lead Date, Lead Month, Lead Week,
Qualified Lead, % Collected, Amount Collected (PHP)
```

**Required columns for CSV verification:** Client, Project, Status, Amount (VAT-Ex.) (PHP), Year, Tribe, Pipeline Tier, BD, AM

---

## Constants & Business Logic

### Tribe Targets (stored in USD, converted to PHP at runtime via USD_RATE)
```javascript
TRIBE_TARGETS_USD = {
  'PDEI - Moonton': 982737.88,
  'PDEI - Tencent': 862996.28,
  'PDEI - Esports': 516434.10,
  'PDEI - Marketing': 4137831.73
}
// Total = $6,500,000.00 USD exactly
// rebuildTargets() multiplies by USD_RATE to produce TRIBE_TARGETS in PHP
```

### Quarterly Cumulative Targets (USD)
```javascript
Q_TARGETS_USD = [
  { label: 'Q1', amount: 1277001.02, pct: 19.65, qtrPip: 1277001.02 },
  { label: 'Q2', amount: 2790257.20, pct: 42.93, qtrPip: 1513256.19 },
  { label: 'Q3', amount: 5269982.97, pct: 81.08, qtrPip: 2479725.76 },
  { label: 'Q4', amount: 6500000.00, pct: 100.00, qtrPip: 1230017.03 }
]
// amount = cumulative target through that quarter
// pct = cumulative % of full-year target
// qtrPip = per-quarter pipeline target (Q amount minus previous Q amount)
```

### AM Targets (in PHP, static)
```javascript
AM_TARGETS = {
  'Alvaro Miguel Dela Vega Santos': 0,        // Iggy
  'Carla Andrea Calma Crespo': 25650000,      // Carla
  'Carlos Roberto Francisco, David, IV Coscolluela': 25650000, // CC
  'Marcus Joaquin Viray Gonzales': 57000000,   // Marcus
  'Shanna Mae Alindada Sacsi': 25650000        // Shanna
}
```

### BD Goals (dynamic discovery system)
- **Default goal per BD per month:** 15 leads
- **Exception:** Jorge Luis Tesoro (H) has a special goal of 10
- Goals are calculated dynamically based on which BDs have data for each Lead Month
- Diana (Diana Lou Perocho Gosamo) left in early Feb but her Jan/Feb historical data still shows
- New BDs are auto-discovered from CSV — no code changes needed
- `getActiveBDsForMonth(month)` scans data to find active BDs
- `getMonthGoal(month)` sums goals of active BDs for that month
- `getTotalGoalAllMonths()` sums across all available months

### BD Nicknames
```javascript
BD_NICKS = {
  'Diana Lou Perocho Gosamo': 'Diana',
  'Marinella M. Casabuena': 'Ella',
  'Kewen Ysan Tolentino Sy': 'Kewen',
  'Jorge Luis Tesoro': 'H'
}
```

### Won Statuses
```javascript
WS = ['Signed CE', 'Won - Awaiting CE Signature', 'Collected - For Closing',
      'For Collection - For Invoicing', 'For Collection - Invoice Sent', 'Fully Closed']
```

### Lead Filtering
- BD Leads include Archived and Stalled statuses (only `Status === 'Lost'` is excluded)
- Win Rate only counts `Status === 'Lost'` as losses (Stalled/Archived excluded)

---

## 7 Tabs

### 1. Overview (`sec-overview`)
- **KPI Strip** (5 cards with staggered fade-in): Total Wins 2026 (clickable — scrolls to wins table), Target, CEs Submitted, Pipeline, For Submission. Each shows delta triangles vs prev CSV.
- **Total Sales YTD**: Custom horizontal bar with gold fill, barbershop pole animation (diagonal stripes), last-week marker line, 5-point axis. Amount shown in black text on yellow badge (also with barbershop animation). Percentage in plain yellow text.
- **Quarterly Split Indicator**: Row of colored segments below Total Sales YTD bar (Q1 blue, Q2 green, Q3 amber, Q4 gold). Each segment is clickable and:
  - Dims non-active quarters to 35% opacity
  - Shows colored overlay on the main sales bar proportional to the quarter's cumulative %
  - Expands a detail panel below with: Q target, YTD sales (with % of quarter target), gap (or "Exceeded By" if target met), and pipeline required (quarter target / 30% vs current pipeline). When target is exceeded, the pipeline column is hidden and the grid becomes 3-column.
  - Click same quarter again to toggle off
- **Sales Attainment by Tribe**: Custom horizontal bars scaled to a shared axis (max of all targets x 1.05). Labels positioned inside bars (black) or outside (yellow) depending on bar width. Target marker line at correct position per tribe. Staggered grow-in + fade animations.
- **YTD + Pipeline by Tribe**: Chart.js horizontal stacked bar (gold = won, blue = pipeline)
- **All Wins — 2026**: Table sorted by month with monthly subtotals shown inline (count + amount). Uses `fmtF()` for full exact amounts (thousands separator + 2 decimal places). Clicking Total Wins KPI scrolls here.
- Sections: `ov-kpis`, `ov-totalSales`, `ov-tribeAtt`, `ov-ytdPipeline`, `ov-winsTable`

### 2. Sales Pipeline (`sec-pipeline`)
- **KPI Strip** (5 cards, animated): Recent Wins, Last Week, CEs Submitted, For Submission, New RFPs
- **Pipeline Columns** in a grid:
  - Recent Wins + Last Week Wins stacked vertically in same column (separate cards, top-aligned)
  - CEs Submitted, For Submission, New RFPs each in their own column
  - Each card shows **summary at top** (total amount, GP%, GP amount) with yellow-tinted background
  - Individual projects listed below with status pills, amounts, GP
  - Gross Revenue if 30% Win Rate shown on non-wins columns only
  - Staggered entrance animations on all cards
- Sections: `pl-kpis`

### 3. AM Performance (`sec-am`)
- **Horizontal stacked bars** per AM with specific colors:
  - Actual Collection: `#cc0000` (red)
  - Collection Phase: `#ffd966` (light yellow)
  - Awarded Phase: `#f0c132` (gold)
  - Pitch Phase: `#3c78d8` (blue)
  - Red target marker line
- Account count shown next to each AM name (excludes Talks In Progress)
- **Click to expand**: Shows phase value grid (4 colored cards with exact amounts) AND accounts table simultaneously
- **Accounts table**: Excludes Talks In Progress, shows Account/Client/Status/Amount/Pitch/Awarded/Collection/Actual columns
- Click again to collapse both
- Staggered row entrance animations
- Sections: `am-chart`, `am-detail`

### 4. BD Leads (`sec-bd`)
- **Stacked bar chart**: Qualified (#f1c232) + For Qualification (#3a74d0) per BD. Red dashed goal marker lines (no number labels — axis shows scale). Count labels inside bars.
- **Donut chart**: Total leads vs dynamic goal with percentage in center. Theme-aware text (reads CSS vars live in afterDraw).
- **Month filter**: Lead Month buttons. Current calendar month highlighted by default. Clicking filters re-renders everything including button highlights.
- **BD Cards**: Only show BDs that have leads for the selected month. Alphabetically sorted by nickname. Shows count, goal, progress bar, qualified/for-qualification split. Staggered entrance animations.
- **Click card** -> detail table with Client, Project, Lead Phase, Lead Progress, Projected Budget, Month
- BD discovery is fully dynamic — new BDs auto-appear when they have Lead Month data
- Sections: `bd-charts`, `bd-filter`

### 5. Win Rate (`sec-winrate`, hidden by default)
- **KPI Strip** (4 cards, animated): Win Rate %, Value Win Rate %, Won count, Lost count
- **4 Charts**: Win vs Loss Count (bar), Win vs Loss Value (bar), Win Rate Trend (line with 50% reference), Win Rate by Tribe (horizontal bar — hides tribes with no wins/losses)
- **Lost Projects table** with month filter (filter only updates table, not charts — no animation replay)
- All charts use computed CSS variable colors (not `var()` strings) for proper canvas rendering
- Sections: `wr-kpis`, `wr-count`, `wr-value`, `wr-trend`, `wr-tribe`, `wr-table`

### 6. Tribe Attainment (`sec-attainment`)
- **KPI Strip** (4 cards, animated): Total Won, Target, Pipeline, Gap
- **Attainment by Tribe**: Chart.js horizontal bar (gold won vs gray/transparent target)
- **YTD vs Pipeline**: Chart.js horizontal bar (gold YTD vs `rgba(100,116,139,.25)` pipeline — visible in both themes)
- **Tribe breakdown table** with progress bars and attainment %
- **Projects Won table** with tribe filter (filter only updates table, not charts — no animation replay). Uses `fmtF()` for full exact amounts (thousands separator + 2 decimal places).
- Sections: `at-kpis`, `at-attChart`, `at-ytdPipe`, `at-table`, `at-wonTable`

### 7. Encrypt/Decrypt (`sec-encrypt`, hidden by default)
- Upload field accepts `.csv` and `.enc` files
- **Encrypt**: CSV -> AES-GCM encrypted `.enc` file (uses PBKDF2 key derivation)
- **Decrypt**: `.enc` -> verified CSV (checks required columns after decryption)
- Downloaded filename mirrors input (e.g., `data.csv` -> `data.enc` and back)
- Field labeled "Encryption Key" (not "Password")
- Wrong password shows "Decryption Failure"

---

## Encryption & Security
- **On launch**: Password modal prompts for decryption key (blurred backdrop, no skip button)
- Empty key shows error "Please enter a decryption key"
- Key stored in `ENC_PW` variable (memory only)
- If config references `.enc` files and decryption fails, modal re-shows with "Decryption Failed" error
- **debugKey support**: If `config.json` contains a `debugKey` field, the dashboard auto-decrypts on load using that key — the password modal is skipped entirely
- **Loading modal**: After password entry (or debugKey auto-boot), a "Decrypting this database..." modal with spinner is shown for 1.5 seconds. The dashboard only renders after the loading modal dismisses.
- **Encryption**: AES-256-GCM with random 16-byte salt + 12-byte IV, PBKDF2 100K iterations SHA-256
- **Binary format**: `[16 bytes salt][12 bytes IV][ciphertext]`
- Both `.csv` and `.enc` files supported in settings upload and config filenames
- CSV verification runs after every load/decrypt to ensure correct columns
- **Invalid CSV modal**: If an uploaded or loaded file fails column verification, a modal with blurred backdrop displays the missing columns. The screen remains blurred until the user dismisses with OK.

---

## Settings Pane (gear icon)
- **Slides in from right**, blurred backdrop, body scroll locked while open
- **Theme**: System / Dark / Light as three buttons (not dropdown)
- **Data Sources**:
  - Upload buttons for Current Week and Last Week (accept `.csv` and `.enc`)
  - Collapsible config filename fields (hidden by default, toggle with "Show config filenames")
  - "Reload from data/ directory" button
- **Per-tab visibility**: Each tab has its own section with "Show Tab" master toggle + individual toggles for every element within that tab
- **Config export/import**: `config.json` file

---

## Config File Structure (`config.json`)
```json
{
  "theme": "dark",
  "defaultCSV": "20260318_AMBD_Universe_Raw.enc",
  "lastWeekCSV": "",
  "currency": "PHP",
  "usdRate": 57,
  "debugKey": "",
  "overview": { "visible": true, "ov-kpis": true, "ov-totalSales": true, "ov-tribeAtt": true, "ov-ytdPipeline": true, "ov-winsTable": true },
  "pipeline": { "visible": true, "pl-kpis": true },
  "am": { "visible": true, "am-chart": true, "am-detail": true },
  "bd": { "visible": true, "bd-charts": true, "bd-filter": true },
  "winrate": { "visible": false, "wr-kpis": true, "wr-count": true, "wr-value": true, "wr-trend": true, "wr-tribe": true, "wr-table": true },
  "attainment": { "visible": true, "at-kpis": true, "at-attChart": true, "at-ytdPipe": true, "at-table": true, "at-wonTable": true },
  "encrypt": { "visible": false }
}
```

---

## Dual CSV Comparison System
- Two CSV slots: current week and last week (optional)
- Filenames parsed for date pattern `YYYYMMDD` — newer = current, older = prev
- Delta indicators (triangle up/triangle down/dash) appear on KPIs and values when prev CSV is loaded
- Last-week marker line shown on Total Sales YTD bar

---

## Visual Style Guide
- **Primary yellow (charts)**: `#f1c232`
- **AM chart colors**: Pitch `#3c78d8`, Awarded `#f0c132`, Collection `#ffd966`, Actual Collection `#cc0000`
- **BD chart colors**: Qualified `#f1c232`, For Qualification `#3a74d0`
- **Pipeline bars**: target/gap uses `rgba(100,116,139,.25)` with `.5` border (visible both themes)
- **Quarterly overlay colors**: Q1 `#3b82f6` (blue), Q2 `#22c55e` (green), Q3 `#f59e0b` (amber), Q4 `#f1c232` (gold)
- **Font**: DM Sans everywhere (numbers included — no monospace)
- **Font sizes**: KPI values 26px, table body 14px, table headers 12px, amounts 13px, BD card counts 24px
- **Dark theme**: `--bg:#0B0E11`, `--surface:#141920`, `--text:#E8ECF1`
- **Light theme**: `--bg:#F3F4F6`, `--surface:#FFF`, `--text:#111827`
- **Chart.js colors**: Must use computed `getComputedStyle()` values, NOT `var()` strings (canvas can't resolve CSS variables)
- **Global user-select:none**: Applied via `* { user-select: none }` — except `td`, `th`, `input`, and `textarea` which re-enable `user-select: text`. This prevents the text caret from appearing on non-table/non-input elements.

---

## Animations
- **Tab switching**: `fadeUp .35s ease-out` on every section
- **Overview KPIs**: Staggered `fadeUp` with 50ms delays per card
- **Pipeline**: KPIs stagger 50ms, columns stagger 50ms (starting at index 5)
- **AM bars**: Stagger at 80ms intervals
- **BD cards**: Stagger at 80ms intervals
- **Win Rate / Attainment KPIs**: Stagger at 50ms intervals
- **Tribe attainment bars**: `growBar .8s` grow-in + staggered `fadeUp` per row
- **Total Sales bar**: `growBar .8s` + barbershop pole idle animation (`barberPole 1s linear infinite`)
- **Total Sales amount badge**: Same barbershop pole animation overlay
- **Quarterly detail panel**: Slides open with `max-height .4s ease` + `opacity .4s ease` transition
- **Quarterly overlay on main bar**: `opacity .3s ease` + `width .5s cubic-bezier(.16,1,.3,1)` transition
- **Helper functions**: `af(i)` returns `class="anim-fade" style="animation-delay:Xs"`, `afc(cls,i)` adds extra classes
- **Filter-only updates** (Tribe Wins filter, Win Rate Month filter) do NOT re-trigger chart animations

---

## Key Helper Functions
```javascript
pn(s)           // Parse number, strips currency symbols and commas
cx(v)           // Convert PHP to active currency
cs()            // Currency symbol (PHP or USD)
fmt(n)          // Format with K/M/B abbreviation
fmtF(n)         // Format with thousands separator + 2 decimal places (full exact amounts)
pct(v,t)        // Percentage string
dv(cur,prev,sm) // Delta indicator (up/down/flat triangle)
sp(st)          // Status pill HTML
gw()            // Current week number
dm(r)           // Derive month string from row
twp(d)          // Total wins PHP from dataset
twpT(d,t)       // Total wins PHP for specific tribe
hp()            // Has prev data?
curLeadMonth()  // Current month in "N - Mon" format
extractDate(n)  // Parse YYYYMMDD from filename
af(i)           // Animation helper: class + delay
afc(cls,i)      // Animation helper with extra class
verifyCSV(text) // Check required columns exist
showCSVInvalidModal(text) // Show invalid CSV modal with missing columns
rebuildTargets()// Recompute TRIBE_TARGETS from USD x rate
getBDGoal(bd)   // Get goal for a BD (15 default, 10 for H)
getActiveBDsForMonth(month) // Discover BDs with data
getMonthGoal(month)         // Sum goals for active BDs
getTotalGoalAllMonths()     // Sum all month goals
toggleQDetail(i)            // Toggle quarterly detail panel and overlay
```

---

## File Loading Sequence
1. Page loads — password modal shown (unless `debugKey` is present in config)
2. **If debugKey in config**: Auto-boot fetches `config.json`, sets `ENC_PW` to debugKey, hides password modal, shows loading modal for 1.5s, then calls `initLoad()`
3. **If no debugKey**: User enters decryption key -> `setPW()` -> loading modal shown for 1.5s -> `initLoad()`
4. `initLoad()` fetches `config.json` from root -> applies config
5. `reloadFromConfig()` fetches CSV/ENC files from `data/` directory
6. For `.enc` files: decrypt with stored password -> verify columns -> load
7. For `.csv` files: verify columns -> load
8. If enc decryption fails: re-show password modal with error
9. If CSV verification fails: show invalid CSV modal with missing columns (blurred backdrop)
10. `reconcile()` sorts slots by date -> sets DATA/DATA_PREV -> `renderAll()`
11. Loading modal dismissed -> dashboard visible

---

## Server (`server.py`)
- Uses Python `http.server.ThreadingHTTPServer` for concurrent request handling
- Serves over HTTPS on port 8089, bound to `0.0.0.0` (accessible over LAN)
- Requires self-signed cert (`cert.pem` + `key.pem`) in project root
- Generate certs with: `openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"`
- If certs are missing, prints error and exits

---

## Known Design Decisions
- Lost is the only status counted as a loss (Stalled/Archived excluded from Win Rate)
- BD Leads include Archived/Stalled as long as Lead Month exists (only Status=Lost excluded)
- AM Performance excludes Pipeline Tier=Lost from weighted calculations
- AM Accounts table excludes Talks In Progress from count and display
- Win Rate by Tribe hides tribes with zero wins and zero losses
- Tribe targets are in USD — changing the USD rate recalculates all PHP targets and re-renders
- BD cards only appear for months where that BD has actual lead data
- All numbers use DM Sans font (no monospace anywhere)
- Total target is exactly $6,500,000.00 USD (sum of four tribe targets)
- Quarterly cumulative targets: Q1 $1,277,001.02 (19.65%), Q2 $2,790,257.20 (42.93%), Q3 $5,269,982.97 (81.08%), Q4 $6,500,000.00 (100%)
- Per-quarter pipeline targets: Q1 $1,277,001.02, Q2 $1,513,256.19, Q3 $2,479,725.76, Q4 $1,230,017.03
- Pipeline Required in quarterly detail = quarter target / 30% (shown alongside current pipeline value)
- All Wins 2026 table and Tribe Attainment Projects Won table use `fmtF()` for full exact amounts instead of `fmt()` abbreviated amounts
- Global `user-select: none` prevents text selection and caret on non-interactive elements; tables and inputs are exempt
