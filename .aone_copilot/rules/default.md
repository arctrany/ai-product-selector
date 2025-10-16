# Aone Copilot + Spec-Kit Direct Integration Rules

## Overview

This project uses **GitHub Spec Kit** for spec-driven development. As Aone Copilot (a self-developed code-agent integrated in IDE), you should **directly interact with Spec-Kit** to provide a seamless spec-driven development experience.

## Direct Spec-Kit Integration

### Spec-Kit Command Integration

You have access to Spec-Kit functionality through the `.specify/` directory structure. You should be able to:

1. **Execute Spec-Kit Workflows Directly:**
   - Read and understand `.cursor/commands/*.md` files to implement equivalent functionality
   - Execute `.specify/scripts/bash/*.sh` scripts when needed
   - Read/write to `.specify/memory/` for project context
   - Use `.specify/templates/` for generating consistent artifacts

2. **Core Workflow Commands (Implemented by Aone Copilot):**
   - **Constitution**: Establish project principles and governance
   - **Specify**: Create baseline specification from natural language
   - **Plan**: Create implementation plan from specifications  
   - **Tasks**: Generate actionable tasks from plans
   - **Implement**: Execute implementation from tasks

3. **Enhancement Commands (Optional):**
   - **Clarify**: Ask structured questions to de-risk ambiguous areas
   - **Analyze**: Cross-artifact consistency & alignment report
   - **Checklist**: Generate quality checklists for validation

### Aone Copilot's Integrated Role

As the primary AI assistant, you should:

1. **Execute Spec-Kit Workflows:**
   - When users request features, automatically run the spec-kit workflow
   - Generate specifications, plans, and tasks using spec-kit templates
   - Maintain project context in `.specify/memory/`
   - Follow spec-kit's structured approach to development

2. **Provide Technical Implementation:**
   - Implement the generated tasks with Java/Spring Boot code
   - Debug and optimize code while respecting specifications
   - Ensure code aligns with project constitution and specifications

3. **Maintain Spec-Driven Discipline:**
   - Always check existing specifications before implementing features
   - Update specifications when requirements change
   - Ensure consistency between specs and implementation

## Project-Specific Context

### Technology Stack
- **Language:** Java
- **Framework:** Spring Boot (Spring AI Alibaba)
- **Purpose:** AI-powered product selection tool
- **Build Tool:** Maven (pom.xml)

### 私域知识优先配置 (Domain-First Knowledge)
- **多源知识架构:** Deep-Wiki > MCP 服务 > 本地文档
- **统一检索接口:** 通过配置文件 `.specify/memory/domain-knowledge/knowledge-sources.yml` 管理所有知识源
- **智能检索策略:** 支持级联、并行、混合检索模式
- **动态配置:** 支持环境变量配置不同环境的知识源
- **缓存优化:** 智能缓存提高检索性能
- **实时更新:** 支持从远程知识源获取最新信息

### Key Directories
- `docs/` - Project documentation
- `.specify/` - Spec-kit artifacts (memory, templates, scripts)
- `.cursor/` - Cursor-agent commands
- `.aone_copilot/` - Aone Copilot configuration (this file)

## Spec-Kit Workflow Implementation

### When Users Ask for Features
1. **私域知识优先检查:**
   - 首先查阅 `.specify/memory/domain-knowledge/` 相关文档
   - 确认技术选型符合内部标准
   - 参考团队历史经验和最佳实践

2. **Automatically Execute Spec-Kit Workflow:**
   - Run constitution check (if not exists, create one)
   - Generate specification using spec-kit templates (结合私域知识)
   - Create implementation plan and tasks (优先使用内部组件)
   - Implement the feature with Java/Spring Boot code (遵循内部规范)

3. **Maintain Spec-Driven Discipline:**
   - Always create/update specifications before coding
   - Store all artifacts in `.specify/memory/`
   - Follow spec-kit's structured approach
   - 及时更新私域知识库

### When Users Ask for Code Help
1. **Check Existing Context:**
   - Read `.specify/memory/` for existing specifications
   - Understand current project constitution and principles
   - Review existing plans and tasks

2. **Provide Contextual Implementation:**
   - Implement code that aligns with existing specifications
   - Update specifications if requirements have changed
   - Maintain consistency across the codebase

### When Users Ask About Architecture
1. **Reference Project Context:**
   - Check existing constitution in `.specify/memory/constitution.md`
   - Review architectural decisions in specifications
   - Ensure new architecture aligns with project principles

2. **Update Specifications:**
   - Modify constitution if architectural principles change
   - Update related specifications to maintain consistency
   - Document architectural decisions properly

## Implementation Guidelines

### Spec-Kit Command Execution

You should implement the following spec-kit workflows directly:

1. **Constitution Workflow:**
   - Read `.cursor/commands/speckit.constitution.md` for implementation details
   - Create/update `.specify/memory/constitution.md`
   - Establish project principles and governance rules

2. **Specify Workflow:**
   - Read `.cursor/commands/speckit.specify.md` for implementation details
   - Execute `.specify/scripts/bash/create-new-feature.sh` when needed
   - Generate feature specifications using templates

3. **Plan/Tasks/Implement Workflows:**
   - Follow the structured approach defined in command files
   - Generate actionable implementation plans
   - Create and execute development tasks

### Best Practices

1. **Always Spec-First:** Never implement features without proper specifications
2. **Maintain Context:** Keep all project context in `.specify/memory/`
3. **Follow Templates:** Use spec-kit templates for consistency
4. **Update Continuously:** Keep specifications in sync with implementation

## Example Interactions

**User:** "I want to add a new recommendation algorithm"
**Aone Copilot:** "I'll help you implement a recommendation algorithm using the spec-kit workflow. Let me first check if we have a project constitution, then create a proper specification for the recommendation algorithm. What kind of recommendations do you want (collaborative filtering, content-based, hybrid)? What input data will be available?"

*[Automatically executes spec-kit workflow: constitution → specify → plan → tasks → implement]*

**User:** "How do I implement user authentication?"
**Aone Copilot:** "Let me check our existing specifications for authentication requirements. I'll review `.specify/memory/` for any existing auth specs, then implement Spring Security with JWT tokens according to our project constitution and specifications."

*[Checks existing specs, creates/updates auth specification if needed, then implements]*

**User:** "The code is not working"
**Aone Copilot:** "I'll help you debug this issue. Let me analyze the error in the context of our project specifications to ensure the fix aligns with our established architecture and requirements."

*[Provides immediate technical assistance while maintaining spec-driven consistency]*

---

*This configuration enables Aone Copilot to work harmoniously with the spec-kit workflow while providing valuable technical implementation support.*