# Initiative Analyzer

Analyzes CSV backlog items against organizational initiatives using Microsoft Foundry to generate markdown reports showing how backlog work supports strategic goals.

## Prerequisites

- Python 3.8+
- Microsoft Foundry project with deployed language model
- Azure authentication configured

## Installation

```bash
cd samples/python/src/azure_ai_inference/initiative_analyzer
pip install -r requirements.txt
```

## Configuration

Set environment variables:

- `PROJECT_ENDPOINT` (required): Microsoft Foundry project endpoint
- `MODEL_DEPLOYMENT_NAME` (optional): Model name (default: "gpt-4o")

Or create a `.env` file:

```env
PROJECT_ENDPOINT=https://your-project.eastus.api.azureml.ms
MODEL_DEPLOYMENT_NAME=gpt-4o
```

## Usage

```bash
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/
```

### Options

- `--confidence-threshold 70` - Minimum confidence for associations (default: 60)
- `--filter-backlog-title "pattern"` - Filter backlog items by regex pattern
- `--filter-initiatives-title "pattern"` - Filter initiatives by regex pattern
- `--processing-mode initiative-centric` - Processing approach (item-centric/initiative-centric, default: initiative-centric)
- `--chunk-size 20` - Batch size for initiative-centric processing (default: 20)
- `--additional-instructions "text"` - Additional instructions to include in AI analysis prompts
- `--verbose DEBUG` - Enable debug logging

### Filtering Examples

```bash
# Filter backlog items containing "onboard" in the title
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/ --filter-backlog-title "onboard.*"

# Filter initiatives containing "security" in the title
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/ --filter-initiatives-title "security.*"

# Use both filters together
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/ \
  --filter-backlog-title "user.*" \
  --filter-initiatives-title "excellence.*"

# Add custom instructions to AI analysis
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/ \
  --additional-instructions "Exclude backlog items that would require very detailed and specific engineering understanding of the code base to implement"

# Combine filtering with additional instructions
python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output reports/ \
  --filter-backlog-title "user.*" \
  --additional-instructions "Focus on items that provide immediate business value"
```

## Input Format

### Backlog CSV

Required columns: `category`, `title`, `goal`, `stream`

```csv
category,title,goal,stream
"User Experience","Simplify onboarding","Reduce onboarding time","Product Team"
```

### Initiatives CSV

Required columns: `area`, `title`, `details`, `description`, `kpi`, `current_state`, `solutions`

```csv
area,title,details,description,kpi,current_state,solutions
"Developer Excellence","Improve onboarding","Streamline dev onboarding","Comprehensive guide","Time to onboard","Low adoption","Bootcamp, workshops"
```

## Output

Generates markdown reports for each initiative with associated backlog items:

- Initiative overview and KPIs
- Associated backlog items with confidence scores
- Impact analysis and strategic recommendations

## Authentication

Uses `DefaultAzureCredential` - ensure you're logged in via:

- Azure CLI (`az login`)
- Visual Studio Code Azure extension
- Environment variables
- Managed Identity (when on Azure)
