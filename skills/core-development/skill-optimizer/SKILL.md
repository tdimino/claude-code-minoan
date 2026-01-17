---
name: skill-optimizer
description: Guide for creating and reviewing skills. This skill should be used when users want to create a new skill, review an existing skill for quality, or optimize a skill that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
license: Complete terms in LICENSE.txt
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it. Use the third-person (e.g. "This skill should be used when..." instead of "Use this skill when...").

**Field Limits:**
- `name`: 64 characters maximum
- `description`: 1024 characters maximum
- **Only** `name` and `description` are supported in YAML frontmatter (no custom fields)

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

**Content Type: Code** - Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, **script code never enters context - only output does**
- **Key advantage**: A 200-line script only costs ~20 tokens (the output), not 2000+ tokens (the code)
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments

##### References (`references/`)

**Content Type: Instructions** - Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

- **When to include**: For documentation that Claude should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when Claude determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.

##### Assets (`assets/`)

**Content Type: Resources** - Files not intended to be loaded into context, but rather used within the output Claude produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables Claude to use files without loading them into context

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

| Level | When Loaded | Token Cost | Content |
|-------|-------------|------------|---------|
| **Level 1: Metadata** | Always (at startup) | ~100 tokens per Skill | `name` and `description` from YAML frontmatter |
| **Level 2: Instructions** | When Skill is triggered | Under 5k tokens | SKILL.md body with instructions and guidance |
| **Level 3+: Resources** | As needed | Effectively unlimited* | Bundled files executed via bash without loading into context |

*Scripts are executed without loading code into context (only output enters context). Reference files and assets are loaded only when Claude explicitly accesses them via bash commands.

**Key insight**: You can install dozens of Skills with minimal context penalty. Claude only knows each Skill exists and when to use it until one is triggered.

### The Skills Filesystem Architecture

Skills exist as directories on the local filesystem, and Claude interacts with them using bash commands and file operations.

**How Claude accesses Skill content:**

1. **Reading instructions**: When a Skill is triggered, Claude reads SKILL.md from the filesystem via bash, bringing its instructions into context
2. **Loading references**: If instructions reference other files (like `references/api_docs.md` or database schemas), Claude reads those files using additional bash commands
3. **Executing scripts**: When instructions mention executable scripts, Claude runs them via bash. **Only the script output enters context, not the code itself**

**What this enables:**

- **On-demand file access**: Claude reads only the files needed for each task. A Skill can include dozens of reference files, but if your task only needs one schema, Claude loads just that file. The rest consume zero tokens
- **Efficient script execution**: When Claude runs `validate_form.py`, only the output consumes tokens, not the 200-line script. This makes scripts far more efficient than having Claude generate equivalent code on the fly
- **No practical limit on bundled content**: Because files don't consume context until accessed, Skills can include comprehensive documentation, datasets, examples, or reference materials without context penalty

**Example workflow:**
```
1. User: "Process this PDF and extract tables"
2. Claude: bash: read pdf-skill/SKILL.md
3. SKILL.md mentions scripts/extract_tables.py
4. Claude: bash: python scripts/extract_tables.py input.pdf
5. Script output: "Extracted 3 tables: [table data...]"
6. Claude proceeds using the extracted data (script code never entered context)
```

## Skill Creation Process

To create a skill, follow the "Skill Creation Process" in order, skipping steps only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 3: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates example resource directories: `scripts/`, `references/`, and `assets/`
- Adds example files in each directory that can be customized or deleted

After initialization, customize or remove the generated SKILL.md and example files as needed.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Focus on including information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Also, delete any example files and directories not needed for the skill. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Populating References from Documentation (Optional)

For skills based on existing frameworks, libraries, or tools with online documentation, use [Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) (v2.0.0+) to automatically scrape and organize documentation into the `references/` directory. Skill_Seekers now supports unified multi-source scraping, combining documentation websites, GitHub repositories, and PDF files into comprehensive reference materials.

**When to use this approach:**
- Building skills for frameworks with comprehensive online docs (React, Django, FastAPI, etc.)
- Creating skills for game engines (Godot, Unity)
- Documenting APIs or libraries with web-based documentation
- Extracting API references directly from GitHub source code
- Combining multiple sources (docs + code + PDFs) for comprehensive skills
- Detecting discrepancies between documentation and actual implementation

**Quick Start:**

```bash
# One-time setup
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git ~/Skill_Seekers
cd ~/Skill_Seekers
pip install requests beautifulsoup4

# Option 1: Documentation-only scraping (classic approach)
python3 cli/doc_scraper.py --config configs/react.json
cp -r output/react/references/* /path/to/your-skill/references/

# Option 2: GitHub-only scraping (extract API from source code)
python3 cli/github_scraper.py --repo facebook/react --extract-api
cp -r output/react_github/references/* /path/to/your-skill/references/

# Option 3: Unified multi-source scraping (RECOMMENDED)
# Combines documentation + GitHub code + PDFs into one comprehensive skill
python3 cli/unified_scraper.py --config configs/react_unified.json
cp -r output/react_complete/references/* /path/to/your-skill/references/

# Option 4: Custom unified config
python3 cli/config_validator.py configs/myframework_unified.json
python3 cli/unified_scraper.py --config configs/myframework_unified.json
```

**Unified Config Example:**

For comprehensive skills that combine multiple sources, create a unified config:

```json
{
  "name": "myframework_complete",
  "description": "Complete reference combining docs, code, and PDFs",
  "merge_mode": "claude-enhanced",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.myframework.com/",
      "selectors": {
        "main_content": "article",
        "title": "h1",
        "code_blocks": "pre code"
      }
    },
    {
      "type": "github",
      "repo": "user/myframework",
      "extract_api": true,
      "languages": ["python", "javascript"]
    },
    {
      "type": "pdf",
      "path": "path/to/api-spec.pdf",
      "extract_code": true
    }
  ]
}
```

**Advanced Features:**

1. **Conflict Detection** - Compare documentation against actual code:

   ```bash
   python3 cli/conflict_detector.py --config configs/myframework_unified.json
   # Detects: missing APIs, undocumented APIs, signature mismatches
   ```

2. **GitHub AST Analysis** - Deep code analysis with Abstract Syntax Tree parsing:

   ```bash
   python3 cli/code_analyzer.py --repo user/myframework
   # Extracts: functions, classes, types with full signatures
   ```

3. **Source Merging Strategies**:

   - `rule-based`: Fast, deterministic merging using predefined rules
   - `claude-enhanced`: AI-powered merging for complex conflicts

4. **Async/Parallel Scraping** - 2-3x performance boost:

   ```bash
   python3 cli/doc_scraper.py --config configs/react.json --async
   ```

**Helper Script:**

Use the included helper script for guided workflow:

```bash
python3 scripts/scrape_documentation_helper.py
```

This interactive script will guide through:

1. Checking if Skill_Seekers is available
2. Choosing between documentation-only, GitHub-only, or unified multi-source scraping
3. Selecting merge strategy (rule-based vs claude-enhanced)
4. Generating the correct commands
5. Running conflict detection (optional)
6. Copying references to the skill directory

**Benefits:**

- **Multi-source scraping**: Combine docs + GitHub repos + PDFs into one skill
- **GitHub code analysis**: AST parsing for Python, JS, TS, Java, C++, Go
- **Conflict detection**: Find discrepancies between documentation and implementation
- **Automatic categorization**: Smart organization of documentation content
- **Code language detection**: Syntax highlighting for 10+ languages
- **Pattern extraction**: Extract common code patterns from examples
- **llms.txt support**: 10x faster scraping when sites provide llms.txt (e.g., hono.dev)
- **Large documentation handling**: Auto-splitting for 10K-40K+ page docs
- **Production-tested configs**: 15+ ready-to-use configs for popular frameworks
- **Async/parallel scraping**: 2-3x performance boost with `--async` flag
- **Repository metadata**: Extract README, CHANGELOG, issues, PRs, stars/forks

**Common Workflows:**

1. **Framework with docs + code**:

   ```bash
   # Create unified config, scrape both sources, detect conflicts
   python3 cli/unified_scraper.py --config configs/fastapi_unified.json
   python3 cli/conflict_detector.py --config configs/fastapi_unified.json
   ```

2. **Open source library** (code is the source of truth):

   ```bash
   # Extract API directly from source code
   python3 cli/github_scraper.py --repo pallets/flask --extract-api
   ```

3. **Enterprise API with PDFs**:

   ```bash
   # Combine web docs + PDF specifications
   python3 cli/unified_scraper.py --config configs/enterprise_api.json
   ```

**Alternative:** For simpler needs or when documentation is not web-based, manually create reference files in the `references/` directory.

#### Update SKILL.md

**Writing Style:** Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X" or "If you need to do X"). This maintains consistency and clarity for AI consumption.

To complete SKILL.md, answer the following questions:

1. What is the purpose of the skill, in a few sentences?
2. When should the skill be used?
3. In practice, how should Claude use the skill? All reusable skill contents developed above should be referenced so that Claude knows how to use them.

### Step 5: Packaging a Skill

Once the skill is ready, it should be packaged into a distributable zip file that gets shared with the user. The packaging process automatically validates the skill first to ensure it meets all requirements:

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Optional output directory specification:

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

The packaging script will:

1. **Validate** the skill automatically, checking:
   - YAML frontmatter format and required fields
   - Skill naming conventions and directory structure
   - Description completeness and quality
   - File organization and resource references

2. **Package** the skill if validation passes, creating a zip file named after the skill (e.g., `my-skill.zip`) that includes all files and maintains the proper directory structure for distribution.

If validation fails, the script will report the errors and exit without creating a package. Fix any validation errors and run the packaging command again.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
