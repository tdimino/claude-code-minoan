# Firecrawl Agent API Reference

The `/agent` endpoint is Firecrawl's newest feature (December 2025) that enables autonomous web browsing and data extraction. Unlike traditional scraping, you describe what data you want in natural language, and the agent searches, navigates, and gathers it automatically.

**Status**: Research Preview - expect improvements over time.

## Key Differentiators

| Feature | Agent | Extract | Scrape | Search |
|---------|-------|---------|--------|--------|
| URLs Required | Optional | Required | Required | N/A |
| Web Search | Built-in | None | None | Built-in |
| Navigation | Autonomous multi-page | Single page | Single page | Search results |
| Browser Actions | Full support | Limited | Limited | None |
| Scale | One to thousands of records | Per URL | Per URL | Per query |
| Natural Language | Full prompt support | Schema only | No | Query only |

## When to Use Agent

**Use Agent when:**
- You don't have specific URLs but know what data you need
- Data is scattered across multiple pages/sites
- Complex navigation is required (login flows, pagination, dynamic content)
- Building lead lists, competitive research, or dataset curation
- The extraction task would take hours manually

**Use traditional tools when:**
- You have a specific URL and just need its content (use `firecrawl URL` CLI)
- Simple single-page extraction (use Scrape or Extract)
- Web search without deep extraction (use Search or Exa)

## Installation

```python
# Python
pip install firecrawl-py

from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key="fc-YOUR_API_KEY")
```

```javascript
// Node.js
npm install @mendable/firecrawl-js

import Firecrawl from '@mendable/firecrawl-js';
const app = new Firecrawl({ apiKey: 'fc-YOUR_API_KEY' });
```

## API Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description of data to extract (max 10,000 chars) |
| `urls` | array | No | Optional URLs to focus extraction on specific pages |
| `schema` | object | No | JSON schema for structured output (Pydantic/Zod) |
| `model` | string | No | Agent model: `spark-1-mini` (default, 60% cheaper) or `spark-1-pro` (more capable) |
| `maxCredits` | integer | No | Maximum credits to spend on this job (budget limit) |

## Model Selection

Firecrawl offers two agent models:

### spark-1-mini (Default)
- **Cost**: 60% cheaper than spark-1-pro
- **Speed**: Faster execution
- **Best for**: Simple extractions, well-structured data, quick research
- **Use when**: Budget-conscious, standard data extraction tasks

### spark-1-pro
- **Cost**: Premium pricing
- **Capability**: More sophisticated reasoning
- **Best for**: Complex extractions, nuanced data, multi-step reasoning
- **Use when**: High-value extractions, complex navigation, better accuracy needed

```python
# Use mini for simple tasks (default)
result = app.agent(
    prompt="Find company contact info",
    model="spark-1-mini"  # default, can be omitted
)

# Use pro for complex tasks
result = app.agent(
    prompt="Analyze competitor pricing strategies and extract nuanced feature comparisons",
    model="spark-1-pro"
)
```

## Budget Control with maxCredits

Limit spending on agent jobs:

```python
# Cap at 50 credits
result = app.agent(
    prompt="Find 100 AI startups",
    maxCredits=50
)
```

The job will stop when the credit limit is reached, returning partial results.

## Basic Usage

### Simple Prompt (No URLs)

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

result = app.agent(
    prompt="Find the founders of Firecrawl, their backgrounds, and the company's funding"
)

print(result.data)
```

### With Structured Schema

```python
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

class Company(BaseModel):
    name: str = Field(description="Company name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    employee_count: Optional[int] = Field(None, description="Number of employees")

class CompaniesSchema(BaseModel):
    companies: List[Company] = Field(description="List of companies found")

result = app.agent(
    prompt="Find YC W24 dev tool companies with their contact info",
    schema=CompaniesSchema
)

for company in result.data.companies:
    print(f"{company.name}: {company.contact_email}")
```

### With Specific URLs

```python
result = app.agent(
    urls=["https://firecrawl.dev", "https://docs.firecrawl.dev"],
    prompt="Extract all pricing tiers and their features"
)
```

## Async Job Processing

For longer extractions, use async pattern:

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

# Start the job
agent_job = app.start_agent(
    prompt="Find all AI startups from YC batches W23-W24 with funding info"
)

# Check status (poll until complete)
import time
while True:
    status = app.get_agent_status(agent_job.id)
    if status.status == 'completed':
        print(f"Success! Credits used: {status.credits_used}")
        print(status.data)
        break
    elif status.status == 'failed':
        print("Job failed")
        break
    time.sleep(5)  # Wait before checking again
```

**Status values:**
- `processing` - Agent is working
- `completed` - Extraction finished successfully
- `failed` - Error occurred

**Note:** Results expire after 24 hours.

### Cancel Agent Job

Cancel a running agent job:

```python
# Via CLI
# python3 firecrawl_api.py agent-cancel <job_id>

# Via API
import requests

response = requests.delete(
    f"https://api.firecrawl.dev/v2/agent/{job_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)
```

## Use Case Examples

### 1. Lead Generation

```python
class Lead(BaseModel):
    company: str
    contact_name: Optional[str]
    email: Optional[str]
    linkedin: Optional[str]

class LeadsSchema(BaseModel):
    leads: List[Lead]

result = app.agent(
    prompt="Find 20 B2B SaaS companies in the developer tools space with contact info",
    schema=LeadsSchema
)
```

### 2. Competitive Pricing Research

```python
class PricingTier(BaseModel):
    name: str
    price: str
    features: List[str]

class CompetitorPricing(BaseModel):
    company: str
    tiers: List[PricingTier]

class PricingComparisonSchema(BaseModel):
    competitors: List[CompetitorPricing]

result = app.agent(
    urls=[
        "https://competitor1.com/pricing",
        "https://competitor2.com/pricing",
        "https://competitor3.com/pricing"
    ],
    prompt="Extract all pricing tiers with features for comparison",
    schema=PricingComparisonSchema
)
```

### 3. Dataset Curation

```python
class Paper(BaseModel):
    title: str
    authors: List[str]
    year: int
    abstract: str
    citations: Optional[int]

class PapersSchema(BaseModel):
    papers: List[Paper]

result = app.agent(
    prompt="Find the top 10 most cited papers on transformer architectures from 2023-2024",
    schema=PapersSchema
)
```

### 4. E-commerce Product Research

```python
class Product(BaseModel):
    name: str
    price: str
    rating: Optional[float]
    reviews_count: Optional[int]
    availability: str

class ProductsSchema(BaseModel):
    products: List[Product]

result = app.agent(
    urls=["https://nike.com"],
    prompt="Find all Jordan basketball shoes with prices and ratings",
    schema=ProductsSchema
)
```

## Best Practices

1. **Write specific prompts** - "Find the founders, their LinkedIn profiles, and the company's total funding" is better than "find company info"

2. **Use schemas for structured data** - Always define a Pydantic/Zod schema when you need consistent output format

3. **Provide URLs when known** - If you know which sites have the data, provide them to speed up extraction

4. **Use async for large jobs** - For extractions that may take minutes, use `start_agent` + `get_agent_status`

5. **Set field descriptions** - In your schema, use `Field(description="...")` to guide the agent

6. **Handle failures gracefully** - Check `status.status` and implement retry logic

## Limitations (Research Preview)

- May have edge cases with certain site types
- Performance varies by site complexity
- No real-time streaming of partial results
- Results expire after 24 hours
- Credit costs vary by extraction complexity

## Error Handling

```python
try:
    result = app.agent(
        prompt="Find company information",
        schema=MySchema
    )

    if hasattr(result, 'success') and not result.success:
        print(f"Extraction failed: {result.error}")
    else:
        print(result.data)

except Exception as e:
    print(f"API error: {str(e)}")
```

## Comparison with Exa MCP

| Task | Use Firecrawl Agent | Use Exa |
|------|---------------------|---------|
| Find + extract structured data | Yes | No |
| Simple web search | No (overkill) | Yes |
| Code/GitHub search | No | Yes (`get_code_context_exa`) |
| Multi-page navigation | Yes | No |
| Known URL extraction | Use firecrawl CLI | Use `exa_api.py contents` |
| Deep research with summaries | Either | `exa_api.py research` |

## Additional Resources

- Official Docs: https://docs.firecrawl.dev/features/agent
- Blog Announcement: https://www.firecrawl.dev/blog/introducing-agent
- Playground: https://www.firecrawl.dev/app/agent
- Python SDK: https://github.com/mendableai/firecrawl
