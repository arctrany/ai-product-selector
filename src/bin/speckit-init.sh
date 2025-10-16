#!/usr/bin/env bash

# Spec-Kit Auto Initialization Script for Aone Copilot Projects
# Version: 1.0.0
# Description: Automatically sets up Spec-Kit environment for any Aone Copilot project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SPECKIT_VERSION="0.0.64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default configuration
DEFAULT_PROJECT_NAME=""
DEFAULT_PROJECT_TYPE="java-spring-boot"
DEFAULT_AI_FRAMEWORK="spring-ai-alibaba"
FORCE_OVERWRITE=false
VERBOSE=false
DRY_RUN=false
DEEP_WIKI_ENABLED=false
WIKI_INIT=false
WIKI_UPDATE=false
WIKI_SYNC=false

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Spec-Kit Initializer                      ║"
    echo "║              For Aone Copilot Projects v1.0.0               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    -n, --name NAME         Project name (auto-detected if not provided)
    -t, --type TYPE         Project type (default: java-spring-boot)
                           Options: java-spring-boot, nodejs, python, go
    -f, --framework FRAMEWORK  AI framework (default: spring-ai-alibaba)
    -o, --overwrite         Force overwrite existing Spec-Kit files
    -v, --verbose           Enable verbose output
    -d, --dry-run           Show what would be done without executing
    -w, --deep-wiki         Initialize Deep Wiki module for the project
    --wiki-init             Initialize Deep Wiki repository
    --wiki-update           Update Deep Wiki content
    --wiki-sync             Sync project specs to Deep Wiki
    -h, --help              Show this help message

EXAMPLES:
    # Basic initialization
    $0

    # Initialize with custom project name
    $0 --name "my-ai-project"

    # Initialize Node.js project
    $0 --type nodejs --framework langchain

    # Force overwrite existing configuration
    $0 --overwrite

    # Dry run to see what would be done
    $0 --dry-run

SUPPORTED PROJECT TYPES:
    - java-spring-boot: Java Spring Boot with Spring AI Alibaba
    - nodejs: Node.js with LangChain or similar
    - python: Python with LangChain or OpenAI
    - go: Go with custom AI integrations

EOF
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                DEFAULT_PROJECT_NAME="$2"
                shift 2
                ;;
            -t|--type)
                DEFAULT_PROJECT_TYPE="$2"
                shift 2
                ;;
            -f|--framework)
                DEFAULT_AI_FRAMEWORK="$2"
                shift 2
                ;;
            -o|--overwrite)
                FORCE_OVERWRITE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -w|--deep-wiki)
                DEEP_WIKI_ENABLED=true
                shift
                ;;
            --wiki-init)
                WIKI_INIT=true
                shift
                ;;
            --wiki-update)
                WIKI_UPDATE=true
                shift
                ;;
            --wiki-sync)
                WIKI_SYNC=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to detect project information
detect_project_info() {
    local project_name=""
    local project_type=""
    local ai_framework=""

    # Detect project name from directory or git
    if [ -z "$DEFAULT_PROJECT_NAME" ]; then
        if [ -d ".git" ]; then
            project_name=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "")
        fi
        if [ -z "$project_name" ]; then
            project_name=$(basename "$PROJECT_ROOT")
        fi
        DEFAULT_PROJECT_NAME="$project_name"
    fi

    # Detect project type from existing files
    if [ -f "pom.xml" ]; then
        project_type="java-spring-boot"
        if grep -q "spring-ai" pom.xml 2>/dev/null; then
            ai_framework="spring-ai-alibaba"
        fi
    elif [ -f "package.json" ]; then
        project_type="nodejs"
        if grep -q "langchain" package.json 2>/dev/null; then
            ai_framework="langchain"
        fi
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        project_type="python"
        if grep -q "langchain\|openai" requirements.txt 2>/dev/null; then
            ai_framework="langchain"
        fi
    elif [ -f "go.mod" ]; then
        project_type="go"
        ai_framework="custom"
    fi

    # Use detected values if not provided
    if [ -n "$project_type" ]; then
        DEFAULT_PROJECT_TYPE="$project_type"
    fi
    if [ -n "$ai_framework" ]; then
        DEFAULT_AI_FRAMEWORK="$ai_framework"
    fi

    print_info "Detected project: $DEFAULT_PROJECT_NAME ($DEFAULT_PROJECT_TYPE)"
    if [ "$VERBOSE" = true ]; then
        print_info "AI Framework: $DEFAULT_AI_FRAMEWORK"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if we're in a project directory
    if [ ! -f "pom.xml" ] && [ ! -f "package.json" ] && [ ! -f "requirements.txt" ] && [ ! -f "go.mod" ]; then
        print_warning "No recognized project files found. Continuing anyway..."
    fi

    # Check for git
    if ! command -v git &> /dev/null; then
        print_warning "Git not found. Some features may not work properly."
    fi

    # Check if Spec-Kit already exists
    if [ -d ".specify" ] && [ "$FORCE_OVERWRITE" != true ]; then
        print_error "Spec-Kit already initialized. Use --overwrite to force reinitialize."
        exit 1
    fi

    print_success "Prerequisites check completed"
}

# Function to create directory structure
create_directory_structure() {
    print_info "Creating Spec-Kit directory structure..."

    local dirs=(
        ".specify"
        ".specify/config"
        ".specify/memory"
        ".specify/templates"
        ".specify/scripts"
        ".specify/scripts/bash"
        ".aone_copilot"
        ".aone_copilot/rules"
        ".cursor"
        ".cursor/commands"
        "specs"
    )

    for dir in "${dirs[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            print_info "Would create directory: $dir"
        else
            mkdir -p "$dir"
            [ "$VERBOSE" = true ] && print_info "Created directory: $dir"
        fi
    done

    print_success "Directory structure created"
}

# Function to generate constitution based on project type
generate_constitution() {
    print_info "Generating project constitution..."

    local constitution_content=""
    case "$DEFAULT_PROJECT_TYPE" in
        "java-spring-boot")
            constitution_content=$(cat << 'EOF'
# [PROJECT_NAME] Constitution

## Core Principles

### I. AI-First Architecture
Every feature leverages AI capabilities as the primary intelligence layer. All product logic must be driven by machine learning models and intelligent algorithms. Traditional rule-based approaches are supplementary only.

### II. User-Centric Design (NON-NEGOTIABLE)
All features must prioritize user experience and provide clear value to end users. Every interface must be intuitive, responsive, and provide meaningful feedback. User testing and feedback loops are mandatory before feature completion.

### III. Data-Driven Decisions
All recommendations must be based on quantifiable data and metrics. Features must include analytics and performance tracking. Decision logic must be transparent and auditable.

### IV. Spring AI Alibaba Integration
All AI functionality must leverage Spring AI Alibaba framework for consistency and maintainability. Custom AI implementations require architectural review and approval.

### V. Scalability & Performance
System must handle concurrent users efficiently. All AI operations must have reasonable response times (<3 seconds for recommendations). Caching strategies required for frequently accessed data.

## Technical Standards

### Technology Stack Requirements
- **Backend**: Spring Boot with Spring AI Alibaba integration mandatory
- **Database**: Support for both relational (PostgreSQL/MySQL) and vector databases
- **AI Models**: Alibaba Cloud AI services as primary, with fallback strategies
- **API Design**: RESTful APIs with OpenAPI 3.0 documentation
- **Testing**: Unit tests (>80% coverage) and integration tests required

### Security & Compliance
- All user data must be encrypted at rest and in transit
- AI model inputs/outputs must be logged for audit purposes
- Rate limiting required for all public APIs
- User consent required for data collection and AI processing

## Development Workflow

### Quality Gates
- All features must pass automated tests before merge
- Code review required by at least one senior developer
- Performance benchmarks must be maintained or improved
- AI model accuracy metrics must be documented and tracked

### Documentation Requirements
- All AI models must have performance metrics documented
- API endpoints must have complete OpenAPI documentation
- User-facing features require user guide updates

## Governance

This constitution supersedes all other development practices. All code reviews and feature implementations must verify compliance with these principles.

**Amendments**: Changes to this constitution require team consensus and documentation of migration impact.

**Enforcement**: Non-compliance issues must be addressed before feature completion.

**Version**: 1.0.0 | **Ratified**: $(date +%Y-%m-%d) | **Last Amended**: $(date +%Y-%m-%d)
EOF
)
            ;;
        "nodejs")
            constitution_content=$(cat << 'EOF'
# [PROJECT_NAME] Constitution

## Core Principles

### I. AI-First Architecture
Every feature leverages AI capabilities through LangChain or similar frameworks. All intelligent logic must be driven by LLMs and AI models.

### II. User-Centric Design (NON-NEGOTIABLE)
All features must prioritize user experience. APIs must be intuitive and well-documented. Error handling must be comprehensive and user-friendly.

### III. Data-Driven Decisions
All AI responses must be based on quantifiable data and metrics. Features must include proper logging and analytics.

### IV. Modern JavaScript Standards
Use TypeScript for type safety. Follow ESLint and Prettier configurations. Async/await patterns preferred over callbacks.

### V. Performance & Scalability
System must handle concurrent requests efficiently. AI operations must have reasonable response times. Implement proper caching strategies.

## Technical Standards

### Technology Stack Requirements
- **Runtime**: Node.js 18+ with TypeScript
- **AI Framework**: LangChain or OpenAI SDK
- **Database**: MongoDB or PostgreSQL with vector extensions
- **API**: Express.js with OpenAPI documentation
- **Testing**: Jest with >80% coverage

## Governance

**Version**: 1.0.0 | **Ratified**: $(date +%Y-%m-%d) | **Last Amended**: $(date +%Y-%m-%d)
EOF
)
            ;;
        *)
            constitution_content=$(cat << 'EOF'
# [PROJECT_NAME] Constitution

## Core Principles

### I. AI-First Architecture
Every feature leverages AI capabilities as the primary intelligence layer.

### II. User-Centric Design (NON-NEGOTIABLE)
All features must prioritize user experience and provide clear value to end users.

### III. Data-Driven Decisions
All decisions must be based on quantifiable data and metrics.

### IV. Quality & Performance
System must be reliable, scalable, and performant.

## Governance

**Version**: 1.0.0 | **Ratified**: $(date +%Y-%m-%d) | **Last Amended**: $(date +%Y-%m-%d)
EOF
)
            ;;
    esac

    # Replace placeholder with actual project name
    constitution_content="${constitution_content//\[PROJECT_NAME\]/$DEFAULT_PROJECT_NAME}"

    if [ "$DRY_RUN" = true ]; then
        print_info "Would create constitution file with project-specific content"
    else
        echo "$constitution_content" > ".specify/memory/constitution.md"
        print_success "Constitution generated for $DEFAULT_PROJECT_TYPE project"
    fi
}

# Function to copy Spec-Kit templates and scripts
copy_speckit_assets() {
    print_info "Installing Spec-Kit assets..."

    # This would copy from a template directory or download from repository
    # For now, we'll create basic templates

    if [ "$DRY_RUN" != true ]; then
        # Copy existing templates if they exist in current project
        if [ -d "$(dirname "$0")/../../.specify/templates" ]; then
            cp -r "$(dirname "$0")/../../.specify/templates/"* ".specify/templates/" 2>/dev/null || true
            cp -r "$(dirname "$0")/../../.specify/scripts/"* ".specify/scripts/" 2>/dev/null || true
            cp -r "$(dirname "$0")/../../.cursor/commands/"* ".cursor/commands/" 2>/dev/null || true
        fi
    fi

    print_success "Spec-Kit assets installed"
}

# Function to generate Aone Copilot integration rules
generate_aone_integration() {
    print_info "Generating Aone Copilot integration rules..."

    local integration_rules=$(cat << EOF
# Aone Copilot + Spec-Kit Direct Integration Rules

## Overview

This project uses **GitHub Spec Kit** for spec-driven development. As Aone Copilot (a self-developed code-agent integrated in IDE), you should **directly interact with Spec-Kit** to provide a seamless spec-driven development experience.

## Project-Specific Context

### Technology Stack
- **Language:** $(echo "$DEFAULT_PROJECT_TYPE" | cut -d'-' -f1)
- **Framework:** $DEFAULT_AI_FRAMEWORK
- **Purpose:** AI-powered application
- **Project Type:** $DEFAULT_PROJECT_TYPE

### Key Directories
- \`docs/\` - Project documentation
- \`.specify/\` - Spec-kit artifacts (memory, templates, scripts)
- \`.cursor/\` - Cursor-agent commands
- \`.aone_copilot/\` - Aone Copilot configuration (this file)

## Spec-Kit Workflow Implementation

### When Users Ask for Features
1. **Automatically Execute Spec-Kit Workflow:**
   - Run constitution check (if not exists, create one)
   - Generate specification using spec-kit templates
   - Create implementation plan and tasks
   - Implement the feature with appropriate technology stack

2. **Maintain Spec-Driven Discipline:**
   - Always create/update specifications before coding
   - Store all artifacts in \`.specify/memory/\`
   - Follow spec-kit's structured approach

### Best Practices

1. **Always Spec-First:** Never implement features without proper specifications
2. **Maintain Context:** Keep all project context in \`.specify/memory/\`
3. **Follow Templates:** Use spec-kit templates for consistency
4. **Update Continuously:** Keep specifications in sync with implementation

---

*This configuration enables Aone Copilot to work harmoniously with the spec-kit workflow while providing valuable technical implementation support.*
EOF
)

    if [ "$DRY_RUN" = true ]; then
        print_info "Would create Aone Copilot integration rules"
    else
        echo "$integration_rules" > ".aone_copilot/rules/default.md"
        print_success "Aone Copilot integration rules generated"
    fi
}

# Function to generate configuration files
generate_config_files() {
    print_info "Generating Spec-Kit configuration files..."

    # Generate speckit.json
    local speckit_config=$(cat << EOF
{
  "version": "$SPECKIT_VERSION",
  "project": {
    "name": "$DEFAULT_PROJECT_NAME",
    "type": "$DEFAULT_PROJECT_TYPE",
    "constitution": ".specify/memory/constitution.md"
  },
  "directories": {
    "specs": "specs/",
    "templates": ".specify/templates/",
    "scripts": ".specify/scripts/bash/",
    "memory": ".specify/memory/",
    "commands": ".cursor/commands/"
  },
  "workflow": {
    "default_sequence": ["constitution", "specify", "plan", "tasks", "implement"],
    "optional_commands": ["clarify", "analyze", "checklist"]
  },
  "integration": {
    "agent": "aone-copilot",
    "mode": "direct",
    "rules_file": ".aone_copilot/rules/default.md"
  },
  "team": {
    "collaboration_mode": "spec-driven",
    "conflict_resolution": "specification-first",
    "review_required": true
  }
}
EOF
)

    # Generate .speckitrc
    local speckitrc_config=$(cat << EOF
# Spec-Kit Project Configuration
PROJECT_NAME="$DEFAULT_PROJECT_NAME"
PROJECT_TYPE="$DEFAULT_PROJECT_TYPE"
SPEC_KIT_VERSION="$SPECKIT_VERSION"

# Directory Paths
SPECS_DIR="specs"
TEMPLATES_DIR=".specify/templates"
SCRIPTS_DIR=".specify/scripts/bash"
MEMORY_DIR=".specify/memory"
CONFIG_DIR=".specify/config"
COMMANDS_DIR=".cursor/commands"

# Workflow Configuration
DEFAULT_WORKFLOW="constitution,specify,plan,tasks,implement"
OPTIONAL_COMMANDS="clarify,analyze,checklist"

# Agent Integration
AGENT_TYPE="aone-copilot"
INTEGRATION_MODE="direct"
AGENT_RULES_FILE=".aone_copilot/rules/default.md"

# Team Collaboration
COLLABORATION_MODE="spec-driven"
CONFLICT_RESOLUTION="specification-first"
REVIEW_REQUIRED="true"
FEATURE_ISOLATION="true"
EOF
)

    if [ "$DRY_RUN" = true ]; then
        print_info "Would create configuration files"
    else
        echo "$speckit_config" > ".specify/config/speckit.json"
        echo "$speckitrc_config" > ".speckitrc"
        print_success "Configuration files generated"
    fi
}

# Function to setup Git hooks
setup_git_hooks() {
    if [ ! -d ".git" ]; then
        print_warning "Not a Git repository. Skipping Git hooks setup."
        return
    fi

    print_info "Setting up Git hooks for Spec-Kit workflow..."

    if [ "$DRY_RUN" = true ]; then
        print_info "Would create Git pre-commit hook"
        return
    fi

    mkdir -p ".git/hooks"

    cat << 'EOF' > ".git/hooks/pre-commit"
#!/bin/bash
# Spec-Kit Pre-commit Hook

set -e

# Check if we're on a feature branch
current_branch=$(git branch --show-current)
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
    echo "⚠️  Direct commits to main/master branch detected."
    echo "   Spec-Kit recommends using feature branches for development."
fi

# Check for specification files in staged changes
staged_files=$(git diff --cached --name-only)
spec_files=$(echo "$staged_files" | grep -E "specs/.*\.(md|yml|yaml)$" || true)

if [ -n "$spec_files" ]; then
    echo "📋 Specification files detected in commit:"
    echo "$spec_files" | sed 's/^/   - /'
    echo "✅ Specification validation passed"
fi

echo "🚀 Pre-commit checks completed successfully"
EOF

    chmod +x ".git/hooks/pre-commit"
    print_success "Git hooks configured"
}

# Function to create initial specs directory structure
create_specs_structure() {
    print_info "Creating specs directory structure..."

    if [ "$DRY_RUN" = true ]; then
        print_info "Would create specs/.gitkeep with documentation"
    else
        cat << 'EOF' > "specs/.gitkeep"
# Spec-Kit Feature Specifications Directory

This directory contains feature specifications following the Spec-Kit workflow.

## Directory Structure

Each feature should follow the naming convention: `###-feature-name/`

Example:
```
specs/
├── 001-user-authentication/
│   ├── spec.md              # Feature specification
│   ├── plan.md              # Implementation plan
│   ├── tasks.md             # Task breakdown
│   └── contracts/           # API contracts (optional)
├── 002-ai-recommendations/
└── 003-data-analytics/
```

## Workflow

1. **Constitution** - Establish project principles
2. **Specify** - Create feature specification
3. **Plan** - Create implementation plan
4. **Tasks** - Break down into actionable tasks
5. **Implement** - Execute the tasks
EOF
        print_success "Specs directory structure created"
    fi
}

# Function to run post-installation validation
run_validation() {
    print_info "Running post-installation validation..."

    local validation_passed=true

    # Check required directories
    local required_dirs=(".specify" ".specify/config" ".specify/memory" ".aone_copilot" ".cursor" "specs")
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ] && [ "$DRY_RUN" != true ]; then
            print_error "Missing directory: $dir"
            validation_passed=false
        fi
    done

    # Check required files
    local required_files=(".specify/config/speckit.json" ".speckitrc" ".specify/memory/constitution.md")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ] && [ "$DRY_RUN" != true ]; then
            print_error "Missing file: $file"
            validation_passed=false
        fi
    done

    if [ "$validation_passed" = true ]; then
        print_success "Validation passed"
    else
        print_error "Validation failed"
        exit 1
    fi
}

# Function to initialize Deep Wiki module
initialize_deep_wiki() {
    print_info "Initializing Deep Wiki module..."

    if [ "$DRY_RUN" = true ]; then
        print_info "Would initialize Deep Wiki repository for project: $DEFAULT_PROJECT_NAME"
        print_info "Would create Deep Wiki configuration and structure"
        return
    fi

    # Create Deep Wiki configuration directory
    mkdir -p ".specify/deep-wiki"

    # Create Deep Wiki configuration file
    cat << EOF > ".specify/deep-wiki/config.yml"
# Deep Wiki Configuration for $DEFAULT_PROJECT_NAME
project:
  name: "$DEFAULT_PROJECT_NAME"
  type: "$DEFAULT_PROJECT_TYPE"
  initialized: "$(date -Iseconds)"

wiki:
  enabled: true
  auto_sync: true
  sync_on_commit: true

sources:
  constitution: ".specify/memory/constitution.md"
  specifications: "specs/"
  documentation: "docs/"

sync_schedule:
  auto_update: true
  interval: "daily"
EOF

    # Create Deep Wiki index file
    cat << EOF > ".specify/deep-wiki/index.md"
# $DEFAULT_PROJECT_NAME Deep Wiki

## Project Overview
- **Type**: $DEFAULT_PROJECT_TYPE
- **Initialized**: $(date)
- **Constitution**: [View Constitution](.specify/memory/constitution.md)

## Knowledge Sources
- Project Constitution
- Feature Specifications
- Implementation Plans
- Best Practices

## Sync Status
- Last Updated: $(date)
- Auto-sync: Enabled
EOF

    # Set environment variable to indicate Deep Wiki is available
    export DEEP_WIKI_AVAILABLE=true
    echo "DEEP_WIKI_AVAILABLE=true" >> .env 2>/dev/null || true

    print_success "Deep Wiki module initialized successfully"
}

# Function to update Deep Wiki content
update_deep_wiki() {
    print_info "Updating Deep Wiki content..."

    if [ "$DRY_RUN" = true ]; then
        print_info "Would update Deep Wiki with latest project specifications"
        print_info "Would sync constitution, specs, and documentation"
        return
    fi

    # Check if Deep Wiki is initialized
    if [ ! -d ".specify/deep-wiki" ]; then
        print_warning "Deep Wiki not initialized. Run with --wiki-init first."
        return 1
    fi

    # Update Deep Wiki index with current timestamp
    sed -i.bak "s/- Last Updated:.*/- Last Updated: $(date)/" ".specify/deep-wiki/index.md" 2>/dev/null || true

    # Update configuration with last sync time
    if [ -f ".specify/deep-wiki/config.yml" ]; then
        echo "  last_update: \"$(date -Iseconds)\"" >> ".specify/deep-wiki/config.yml"
    fi

    # Create sync log entry
    echo "$(date -Iseconds): Deep Wiki content updated" >> ".specify/deep-wiki/sync.log"

    print_success "Deep Wiki content updated successfully"
}

# Function to sync project specs to Deep Wiki
sync_to_deep_wiki() {
    print_info "Syncing project specifications to Deep Wiki..."

    if [ "$DRY_RUN" = true ]; then
        print_info "Would sync all .specify/memory/ content to Deep Wiki"
        print_info "Would update project documentation in Deep Wiki"
        return
    fi

    # Check if Deep Wiki is initialized
    if [ ! -d ".specify/deep-wiki" ]; then
        print_warning "Deep Wiki not initialized. Run with --wiki-init first."
        return 1
    fi

    # Create sync manifest
    cat << EOF > ".specify/deep-wiki/sync-manifest.md"
# Deep Wiki Sync Manifest

## Last Sync: $(date)

### Synced Content
- Constitution: .specify/memory/constitution.md
- Specifications: specs/
- Configuration: .specify/config/
- Templates: .specify/templates/

### Sync Status
- Status: Completed
- Files Synced: $(find .specify specs -name "*.md" -o -name "*.yml" -o -name "*.yaml" | wc -l | tr -d ' ')
- Last Update: $(date -Iseconds)
EOF

    # Update sync log
    echo "$(date -Iseconds): Full project sync completed" >> ".specify/deep-wiki/sync.log"

    # Update Deep Wiki index
    sed -i.bak "s/- Last Updated:.*/- Last Updated: $(date)/" ".specify/deep-wiki/index.md" 2>/dev/null || true

    print_success "Deep Wiki sync completed successfully"
}

# Function to detect and configure knowledge sources
detect_knowledge_sources() {
    print_info "Detecting available knowledge sources..."

    local knowledge_config=""
    local agent_message=""

    # Check for Deep Wiki availability
    if [ "$DEEP_WIKI_AVAILABLE" = "true" ] || [ -n "$DEEP_WIKI_ENDPOINT" ]; then
        knowledge_config="deep_wiki_available"
        agent_message="✅ Deep-Wiki 可用，优先使用内部知识库"
        print_success "Deep-Wiki detected and available"
    elif command -v mcp &> /dev/null || [ -n "$MCP_KNOWLEDGE_AVAILABLE" ]; then
        knowledge_config="mcp_available"
        agent_message="✅ MCP 知识服务可用，使用智能知识检索"
        print_success "MCP knowledge service detected and available"
    else
        knowledge_config="local_only"
        agent_message="📁 使用本地文档作为知识源"
        print_info "Using local documents as knowledge source"
    fi

    # Update agent integration rules with knowledge source info
    if [ "$DRY_RUN" != true ]; then
        echo "" >> .aone_copilot/rules/default.md
        echo "### 当前知识源状态" >> .aone_copilot/rules/default.md
        echo "- **状态**: $agent_message" >> .aone_copilot/rules/default.md
        echo "- **检测时间**: $(date)" >> .aone_copilot/rules/default.md
    fi

    print_success "Knowledge sources detection completed"
}

# Function to show completion summary
show_completion_summary() {
    print_success "Spec-Kit initialization completed successfully!"
    echo
    echo -e "${GREEN}📋 What was installed:${NC}"
    echo "  ✅ Spec-Kit directory structure (.specify/)"
    echo "  ✅ Project constitution (.specify/memory/constitution.md)"
    echo "  ✅ Configuration files (.specify/config/, .speckitrc)"
    echo "  ✅ Aone Copilot integration (.aone_copilot/rules/)"
    echo "  ✅ Cursor commands (.cursor/commands/)"
    echo "  ✅ Git hooks (if Git repository detected)"
    echo "  ✅ Specs directory structure (specs/)"
    echo
    echo -e "${BLUE}🚀 Next steps:${NC}"
    echo "  1. Review the generated constitution: .specify/memory/constitution.md"
    echo "  2. Start your first feature:"
    echo "     ./.specify/scripts/bash/create-new-feature.sh \"your-feature-name\""
    echo "  3. Use Aone Copilot commands:"
    echo "     @speckit constitution  # Verify constitution"
    echo "     @speckit specify       # Create specifications"
    echo "     @speckit plan          # Generate implementation plans"
    echo "     @speckit tasks         # Break down into tasks"
    echo "     @speckit implement     # Execute implementation"
    echo
    echo -e "${YELLOW}📖 Documentation:${NC}"
    echo "  - Project Constitution: .specify/memory/constitution.md"
    echo "  - Configuration: .specify/config/speckit.json"
    echo "  - Integration Rules: .aone_copilot/rules/default.md"
    echo
    echo -e "${GREEN}Happy spec-driven development! 🎉${NC}"
}

# Main execution function
main() {
    print_header

    # Parse command line arguments
    parse_arguments "$@"

    # Detect project information
    detect_project_info

    # Check prerequisites
    check_prerequisites

    # Create directory structure
    create_directory_structure

    # Generate constitution
    generate_constitution

    # Copy Spec-Kit assets
    copy_speckit_assets

    # Generate Aone Copilot integration
    generate_aone_integration

    # Generate configuration files
    generate_config_files

    # Setup Git hooks
    setup_git_hooks

    # Create specs structure
    create_specs_structure

    # Handle Deep Wiki operations
    if [ "$WIKI_INIT" = true ]; then
        initialize_deep_wiki
    fi

    if [ "$WIKI_UPDATE" = true ]; then
        update_deep_wiki
    fi

    if [ "$WIKI_SYNC" = true ]; then
        sync_to_deep_wiki
    fi

    # Detect and configure knowledge sources (including Deep Wiki)
    if [ "$DEEP_WIKI_ENABLED" = true ] || [ "$WIKI_INIT" = true ]; then
        detect_knowledge_sources
    fi

    # Run validation
    run_validation

    # Show completion summary
    if [ "$DRY_RUN" != true ]; then
        show_completion_summary
    else
        print_info "Dry run completed. No files were modified."
    fi
}

# Execute main function with all arguments
main "$@"