# UI Distribution Controls - Added

## What Was Added

A new **"💸 Distributions"** tab has been added to the Configuration Editor in the Streamlit UI.

## Location

**File:** `ui/components/config_editor.py`

**Access:**
1. Launch the UI: `streamlit run ui/app.py` (or use `Launch_STR_Dashboard.bat`)
2. Navigate to "Run Control" page
3. Click the "Distributions" tab in the configuration editor

## Features

### Main Toggle
- **Enable Distributions** checkbox - Turn distributions on/off entirely

### Distribution Triggers Section
Configure when distributions start (all conditions must be met):

**Income & Portfolio Size:**
- Target Annual Income ($25k-$500k)
- Min Properties Owned (1-10)

**Leverage & Safety:**
- Max Portfolio LTV (0%-75%)
- Debt-Free Override (checkbox)
- Min DSCR (1.0-2.5) - only shown if LTV > 0

**Reserve Requirements:**
- Min Reserve Cushion ($50k-$1M)
- Min Months Fixed Costs (3-24 months)

### Distribution Amount Section
Configure how much to distribute:

- **Distribution Percentage** (50%-95%) - Slider with live example calculation
- **Prioritize Reserve Top-Up** - Checkbox
- **Min Retained NOI %** (5%-30%) - Safety net

### Safety Suspensions Section
Emergency brakes that override triggers:

- Suspend if LTV Exceeds (30%-75%)
- Suspend if Reserves Below (3-18 months)
- Suspend if DSCR Below (1.0-2.0)

### Quick Presets
Three one-click configuration presets:

1. **🐢 Conservative**
   - Target: $75k/year
   - LTV: 0% (debt-free only)
   - Reserves: $500k
   - Distribution: 80%
   - **Expected start: Year 22+**

2. **⚖️ Balanced** (RECOMMENDED)
   - Target: $100k/year
   - Min properties: 5
   - LTV: 35%
   - Reserves: $250k
   - Distribution: 75%
   - **Expected start: Year 19-20**

3. **🚀 Aggressive**
   - Target: $100k/year
   - LTV: 50%
   - Reserves: $100k
   - Distribution: 70%
   - **Expected start: Year 17-18**

## Visual Design

The tab includes:
- Clear section headers with emojis for visual hierarchy
- Helpful tooltips on every input
- Live example calculation for distribution percentage
- Info message when distributions are disabled
- Three-column responsive layout for compact organization
- Horizontal dividers between sections

## Integration with Backend

All UI controls map directly to the JSON configuration structure:

```json
"distribution": {
  "enabled": true/false,
  "triggers": { ... },
  "distribution": { ... },
  "safety": { ... }
}
```

Changes in the UI update the form values, which are then saved to the scenario configuration when the user saves.

## Workflow

1. User opens UI and navigates to Run Control
2. Clicks "Distributions" tab
3. Checks "Enable Distributions"
4. Either:
   - Clicks a preset button for quick setup, OR
   - Manually adjusts individual levers
5. Saves scenario
6. Runs simulation
7. Views distribution results in output

## Testing the UI

To test the new controls:

```bash
# Launch the dashboard
streamlit run ui/app.py

# Or use the batch file
Launch_STR_Dashboard.bat
```

Navigate to the Distributions tab and verify:
- All controls load with correct default values
- Preset buttons update multiple fields correctly
- Help text appears on hover
- Example calculation updates when distribution % changes
- DSCR field appears/disappears based on LTV setting

## Benefits

1. **User-friendly** - No need to edit JSON files manually
2. **Discoverable** - All distribution options visible in one place
3. **Quick testing** - Preset buttons enable rapid scenario comparison
4. **Safe defaults** - Sensible starting values prevent configuration errors
5. **Visual feedback** - Live example shows impact of settings
6. **Integrated** - Part of existing configuration workflow

## Next Steps

Users can now:
1. Model different "financial freedom" scenarios through the UI
2. Compare Conservative vs Balanced vs Aggressive strategies
3. Find their optimal distribution start year
4. Experiment with different income targets
5. Test sensitivity to reserve requirements

The distribution system is now fully accessible through both:
- **JSON config** (for advanced users)
- **UI controls** (for everyone)
