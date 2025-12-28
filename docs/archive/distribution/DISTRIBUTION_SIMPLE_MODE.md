# Distribution System - Simple Mode

## Overview

The distribution system has been updated to support **two modes**:

1. **SIMPLE MODE** (current default) - One trigger at a time, easy to configure
2. **COMPLEX MODE** (legacy, for future) - Multiple triggers with safety checks

## Simple Mode Configuration

### Three Trigger Types (Choose ONE)

#### 1. Year-Based Trigger
Start distributions in a specific year.

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "startYear": 22
    },
    "distribution": {
      "distributionPct": 1.0
    }
  }
}
```

**Example:** Distributions start in Year 22, paying out 100% of distributable cash.

---

#### 2. LTV-Based Trigger
Start distributions when portfolio LTV drops to or below a threshold.

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "maxLTV": 30.0
    },
    "distribution": {
      "distributionPct": 0.80
    }
  }
}
```

**Example:** Distributions start when LTV ≤ 30%, paying out 80% of distributable cash.

---

#### 3. Distributable Amount Trigger
Start distributions when a minimum amount of cash is available for distribution.

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "minDistributableAmount": 50000.0
    },
    "distribution": {
      "distributionPct": 1.0
    }
  }
}
```

**Example:** Distributions start when $50k+ is available, paying out 100%.

---

## How Distributable Cash is Calculated

**Distributable Cash** = Operating Cash - Minimum Operating Balance

- **Operating Cash:** Available after all expenses and debt service
- **Minimum Operating Balance:** Configured months of fixed costs (default: 1 month)
- **What's Left:** Can be distributed to investors

All reserves (Rainy-Day, CapEx) are **fully funded first** before any distributions.

---

## Distribution Percentage

The `distributionPct` controls what percentage of distributable cash gets paid out:

- **1.0 (100%):** Distribute all available cash (aggressive)
- **0.80 (80%):** Distribute 80%, retain 20% for extra cushion (balanced)
- **0.50 (50%):** Distribute half, retain half (conservative)

---

## Current Configuration (Default)

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "startYear": 22
    },
    "distribution": {
      "distributionPct": 1.0
    }
  }
}
```

### Results with Default Config

- **Total Distributions:** $10.58 million over 9 years
- **Start:** Year 22, Month 1
- **Monthly Income:**
  - Year 22: ~$81k/month
  - Year 30: ~$116k/month
- **Final Portfolio Value:** $13.3 million (equity + cash reserves)

---

## UI Configuration

The Streamlit UI provides a **Distributions tab** with:

1. **Enable/Disable** toggle
2. **Trigger Type** selector (Year-Based, LTV-Based, or Distributable Amount)
3. **Distribution Percentage** slider with live example
4. **Quick Presets:**
   - Debt-Free (Year 22): 100% distribution when debt-free
   - Low Leverage (30% LTV): 80% distribution at 30% LTV
   - $50k Threshold: 100% distribution when $50k+ available

Access via:
```bash
streamlit run ui/app.py
```

Navigate to **Run Control** → **Distributions** tab

---

## Switching Between Modes

### Current: Simple Mode (Default)
No configuration needed - just set ONE of the three triggers.

### Future: Complex Mode
To enable the legacy complex trigger system:

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "useComplexTriggers": true,
      "targetAnnualIncome": 100000,
      "minPropertiesOwned": 3,
      "maxPortfolioLTV": 30.0,
      "allowDebtFreeOverride": true,
      "minReserveCushion": 200000,
      "minMonthsFixedCostsReserve": 12,
      "minDSCR": 1.5
    },
    "distribution": {
      "distributionPct": 0.75,
      "minRetainedNOI": 0.15,
      "prioritizeReserveTopUp": true
    },
    "safety": {
      "suspendIfLTVExceeds": 50.0,
      "suspendIfReservesBelowMonths": 6,
      "suspendIfDSCRBelow": 1.2
    }
  }
}
```

---

## Testing Different Scenarios

### Scenario 1: Start distributions ASAP (Year 17-18)
```json
"triggers": {
  "maxLTV": 50.0
},
"distribution": {
  "distributionPct": 0.70
}
```

### Scenario 2: Conservative (Year 22+, debt-free)
```json
"triggers": {
  "startYear": 22
},
"distribution": {
  "distributionPct": 1.0
}
```

### Scenario 3: Balanced (Year 19-20)
```json
"triggers": {
  "maxLTV": 35.0
},
"distribution": {
  "distributionPct": 0.80
}
```

### Scenario 4: Cash threshold (flexible timing)
```json
"triggers": {
  "minDistributableAmount": 75000.0
},
"distribution": {
  "distributionPct": 1.0
}
```

---

## Key Differences: Simple vs Complex Mode

| Feature | Simple Mode | Complex Mode |
|---------|-------------|--------------|
| Number of triggers | 1 | Multiple (ALL must be met) |
| Trigger types | Year, LTV, or Cash Amount | Income, Properties, LTV, Reserves, DSCR, etc. |
| Safety suspensions | None | LTV, Reserves, DSCR checks can suspend |
| Complexity | Easy to understand | More sophisticated |
| Use case | Quick modeling, clean testing | Advanced risk management |

---

## Quick Start

1. **Edit config:**
   ```
   notepad ob_str_engine\OB_STR_ENGINE_V2_3.json
   ```

2. **Choose ONE trigger type** (startYear, maxLTV, or minDistributableAmount)

3. **Set distribution percentage** (0.5 - 1.0)

4. **Run simulation:**
   ```bash
   python run_quick.py
   python analyze_distributions_simple.py
   ```

5. **View results:** Check when distributions start and total payout

---

## Output Columns

The simulator adds these distribution columns to the CSV output:

- `Distribution Enabled`: 0 or 1
- `Distribution Eligible`: 1 if trigger condition is met
- `Distribution Safe`: 1 if safety checks pass (always 1 in simple mode)
- `Distribution Amount`: Dollars distributed this month
- `Distribution Reason`: Why distribution was/wasn't paid
- `Distributable Cash Flow`: Cash available for distribution

---

## Files

- **Configuration:** `ob_str_engine/OB_STR_ENGINE_V2_3.json`
- **Backend Logic:** `ob_str_engine/engine/distributions.py`
- **Simulator Integration:** `ob_str_engine/engine/simulator.py`
- **UI Controls:** `ui/components/config_editor.py`
- **Analysis Tool:** `analyze_distributions_simple.py`

---

## Support

The distribution system is now fully functional with both simple and complex modes. Use simple mode for clean, easy-to-understand scenarios, or enable complex mode later for sophisticated multi-trigger strategies with safety checks.

**Default behavior:** Start distributing 100% of available cash in Year 22 when the portfolio is debt-free.
