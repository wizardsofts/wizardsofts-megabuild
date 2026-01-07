# Claude-Slack Custom Bot Implementation Guide

**Status:** Phase 2 - Ready for Development
**Created:** 2026-01-01
**Target Deployment:** Server 84 (10.0.0.84)
**Repository:** wizardsofts-megabuild

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Implementation Steps](#implementation-steps)
5. [Docker Deployment](#docker-deployment)
6. [GitLab Integration](#gitlab-integration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Testing](#testing)

---

## Overview

This custom Slack bot provides deep integration between Claude AI, Slack, and the WizardSofts GitLab instance. Unlike the official Claude Slack app (Phase 1), this custom implementation gives full control over:

- ✅ **GitLab Integration:** Direct interaction with internal GitLab (10.0.0.84:8090)
- ✅ **Custom Workflows:** Task assignment, approvals, automated MR creation
- ✅ **Security:** Runs within internal network, follows WizardSofts security guidelines
- ✅ **Monitoring:** Prometheus metrics, Grafana dashboards
- ✅ **Cost Control:** Rate limiting, usage tracking, budget management

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Slack Workspace                         │
│                      (wizardsofts.slack.com)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS (Webhooks)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Server 84 (10.0.0.84)                        │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │           Claude Slack Bot Container                       ││
│  │           Port: 3000 (internal)                            ││
│  │                                                             ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │  Slack Event Listener (Bolt.js/FastAPI)              │ ││
│  │  │  • @mention events → Task extraction                 │ ││
│  │  │  • Emoji reactions → Quick actions                   │ ││
│  │  │  • Button clicks → Approval workflows                │ ││
│  │  └──────────────┬───────────────────────────────────────┘ ││
│  │                 │                                          ││
│  │  ┌──────────────▼───────────────────────────────────────┐ ││
│  │  │  Claude API Service                                  │ ││
│  │  │  • Anthropic API client                              │ ││
│  │  │  • Context management (thread history)               │ ││
│  │  │  • Streaming responses                               │ ││
│  │  │  • Tool use orchestration                            │ ││
│  │  └──────────────┬───────────────────────────────────────┘ ││
│  │                 │                                          ││
│  │  ┌──────────────▼───────────────────────────────────────┐ ││
│  │  │  GitLab Integration Service                          │ ││
│  │  │  • API client (python-gitlab)                        │ ││
│  │  │  • Repository cloning                                │ ││
│  │  │  • Branch management                                 │ ││
│  │  │  • MR creation & updates                             │ ││
│  │  │  • CI/CD status monitoring                           │ ││
│  │  └──────────────┬───────────────────────────────────────┘ ││
│  │                 │                                          ││
│  │  ┌──────────────▼───────────────────────────────────────┐ ││
│  │  │  Workflow Engine                                     │ ││
│  │  │  • State machine for approvals                       │ ││
│  │  │  • Task queueing (Celery/Redis)                      │ ││
│  │  │  • Retry logic & error handling                      │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  │                                                             ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │  Observability Layer                                 │ ││
│  │  │  • Prometheus metrics exporter                       │ ││
│  │  │  • Structured logging (JSON)                         │ ││
│  │  │  • OpenTelemetry traces                              │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Supporting Services                                       ││
│  │  • Redis (task queue, caching)                            ││
│  │  • PostgreSQL (state persistence)                         ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  GitLab Instance (Port 8090)                              ││
│  │  • wizardsofts-megabuild repository                       ││
│  │  • CI/CD pipelines                                        ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Monitoring Stack                                          ││
│  │  • Prometheus (Port 9090)                                  ││
│  │  • Grafana (Port 3002)                                     ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Task Assignment → MR Creation

```
1. Slack User posts message
   ↓
2. Slack sends webhook to bot
   ↓
3. Bot extracts task + thread context
   ↓
4. Bot calls Claude API with context
   ↓
5. Claude generates code changes
   ↓
6. Bot creates feature branch in GitLab
   ↓
7. Bot commits changes to branch
   ↓
8. Bot creates merge request
   ↓
9. Bot posts MR link to Slack with approval buttons
   ↓
10. User clicks [✅ Approve]
    ↓
11. Bot merges MR (if CI passes)
    ↓
12. GitLab CI/CD deploys to production
```

---

## Prerequisites

### 1. Slack App Setup

1. **Create Slack App**
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - App Name: `Claude Bot`
   - Workspace: `WizardSofts`

2. **Configure OAuth & Permissions**
   - Navigate to "OAuth & Permissions"
   - Add Bot Token Scopes:
     ```
     chat:write
     chat:write.public
     channels:history
     channels:read
     groups:history
     groups:read
     im:history
     im:read
     reactions:read
     users:read
     files:read
     ```

3. **Enable Event Subscriptions**
   - Navigate to "Event Subscriptions"
   - Enable Events: `On`
   - Request URL: `https://bot.wizardsofts.com/slack/events`
     - (This will be set up via Traefik reverse proxy)
   - Subscribe to Bot Events:
     ```
     app_mention
     message.channels
     message.groups
     reaction_added
     ```

4. **Enable Interactivity**
   - Navigate to "Interactivity & Shortcuts"
   - Interactivity: `On`
   - Request URL: `https://bot.wizardsofts.com/slack/interactions`

5. **Install App to Workspace**
   - Navigate to "Install App"
   - Click "Install to Workspace"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 2. Anthropic API Key

1. **Get API Key**
   - Go to https://console.anthropic.com/
   - Navigate to "API Keys"
   - Create new key: `wizardsofts-slack-bot`
   - Copy the key (starts with `sk-ant-`)

2. **Set Usage Limits** (Optional but recommended)
   - Set monthly budget: $100
   - Enable email alerts at 80% usage

### 3. GitLab Access Token

1. **Create Personal Access Token**
   - Login to GitLab: http://10.0.0.84:8090
   - User Settings → Access Tokens
   - Name: `claude-slack-bot`
   - Scopes:
     ```
     api
     read_repository
     write_repository
     read_api
     ```
   - Expiration: 1 year
   - Create token and copy (starts with `glpat-`)

### 4. Server 84 Access

- SSH access to 10.0.0.84
- Docker and Docker Compose installed
- Access to wizardsofts-network

---

## Implementation Steps

### Step 1: Project Structure

```bash
# On Server 84
cd /opt/wizardsofts-megabuild
mkdir -p infrastructure/claude-slack-bot

# Project structure
infrastructure/claude-slack-bot/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── slack_handlers.py       # Slack event handlers
│   ├── claude_client.py        # Claude API client
│   ├── gitlab_client.py        # GitLab API client
│   ├── workflows.py            # Approval workflows
│   └── models.py               # Data models
├── config/
│   ├── settings.py             # Configuration
│   └── prompts/                # Claude prompts
│       ├── code_generation.txt
│       ├── code_review.txt
│       └── bug_analysis.txt
├── tests/
│   ├── test_slack_handlers.py
│   ├── test_claude_client.py
│   └── test_workflows.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── .env.example
```

### Step 2: Core Implementation

#### 2.1 Main Application (`app/main.py`)

```python
from fastapi import FastAPI, Request, BackgroundTasks
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
import os
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.slack_handlers import register_handlers
from app.config.settings import settings

# Initialize Slack app
slack_app = AsyncApp(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET
)

# Register event handlers
register_handlers(slack_app)

# Initialize FastAPI
api = FastAPI(title="Claude Slack Bot")

# Slack request handler
slack_handler = AsyncSlackRequestHandler(slack_app)

# Prometheus metrics
slack_events_total = Counter(
    'slack_events_total',
    'Total Slack events received',
    ['event_type']
)

claude_requests_total = Counter(
    'claude_requests_total',
    'Total Claude API requests',
    ['status']
)

task_duration = Histogram(
    'task_completion_duration_seconds',
    'Time to complete tasks',
    ['task_type']
)

@api.post("/slack/events")
async def slack_events_endpoint(request: Request):
    """Handle Slack events"""
    return await slack_handler.handle(request)

@api.post("/slack/interactions")
async def slack_interactions_endpoint(request: Request):
    """Handle Slack interactive components"""
    return await slack_handler.handle(request)

@api.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "slack_connected": True,
        "gitlab_connected": True
    }

@api.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=3000)
```

#### 2.2 Slack Event Handlers (`app/slack_handlers.py`)

```python
from slack_bolt.async_app import AsyncApp
from app.claude_client import ClaudeClient
from app.gitlab_client import GitLabClient
from app.workflows import ApprovalWorkflow
import logging

logger = logging.getLogger(__name__)

claude_client = ClaudeClient()
gitlab_client = GitLabClient()

def register_handlers(app: AsyncApp):

    @app.event("app_mention")
    async def handle_app_mention(event, say, client):
        """Handle @ClaudeBot mentions"""
        try:
            # Extract task from message
            text = event['text']
            user_id = event['user']
            channel_id = event['channel']
            thread_ts = event.get('thread_ts', event['ts'])

            # Get thread context
            thread_context = await get_thread_context(
                client, channel_id, thread_ts
            )

            # Show typing indicator
            await say(
                text="🔍 Analyzing your request...",
                thread_ts=thread_ts
            )

            # Call Claude API
            response = await claude_client.generate_code(
                task=text,
                context=thread_context
            )

            # Present response with approval buttons
            await say(
                text=response['summary'],
                thread_ts=thread_ts,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": response['summary']
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```\n{response['code_preview']}\n```"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "✅ Approve & Create MR"},
                                "style": "primary",
                                "action_id": "approve_create_mr",
                                "value": response['task_id']
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "🔍 Review Details"},
                                "action_id": "review_details",
                                "value": response['task_id']
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "❌ Cancel"},
                                "style": "danger",
                                "action_id": "cancel_task",
                                "value": response['task_id']
                            }
                        ]
                    }
                ]
            )

        except Exception as e:
            logger.error(f"Error handling mention: {e}")
            await say(
                text=f"❌ Error: {str(e)}",
                thread_ts=thread_ts
            )

    @app.action("approve_create_mr")
    async def handle_approve_create_mr(ack, body, say):
        """Handle approval and create MR in GitLab"""
        await ack()

        try:
            task_id = body['actions'][0]['value']
            user_id = body['user']['id']

            # Update message to show processing
            await say(
                text="🚀 Creating merge request...",
                thread_ts=body['message']['thread_ts']
            )

            # Get task details
            task = await get_task_details(task_id)

            # Create branch and MR in GitLab
            mr = await gitlab_client.create_merge_request(
                project_id=settings.GITLAB_PROJECT_ID,
                task=task,
                author=user_id
            )

            # Post success message
            await say(
                text=f"✅ Merge request created: {mr['web_url']}",
                thread_ts=body['message']['thread_ts'],
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Merge Request Created*\n\n"
                                    f"<{mr['web_url']}|!{mr['iid']}: {mr['title']}>\n"
                                    f"Branch: `{mr['source_branch']}`\n"
                                    f"Status: {mr['detailed_merge_status']}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View MR"},
                                "url": mr['web_url']
                            }
                        ]
                    }
                ]
            )

        except Exception as e:
            logger.error(f"Error creating MR: {e}")
            await say(
                text=f"❌ Failed to create MR: {str(e)}",
                thread_ts=body['message']['thread_ts']
            )

    @app.action("review_details")
    async def handle_review_details(ack, body, say):
        """Show detailed code review"""
        await ack()

        task_id = body['actions'][0]['value']
        task = await get_task_details(task_id)

        await say(
            text="📋 Detailed Code Review",
            thread_ts=body['message']['thread_ts'],
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Files Changed:*\n{format_files_changed(task['changes'])}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Full Diff:*\n```\n{task['full_diff']}\n```"
                    }
                }
            ]
        )

async def get_thread_context(client, channel_id, thread_ts):
    """Fetch thread messages for context"""
    result = await client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        limit=20
    )

    messages = []
    for msg in result['messages']:
        messages.append({
            'user': msg.get('user', 'bot'),
            'text': msg['text'],
            'timestamp': msg['ts']
        })

    return messages

async def get_task_details(task_id):
    """Retrieve task details from cache/database"""
    # Implementation depends on your storage choice
    pass

def format_files_changed(changes):
    """Format file changes for display"""
    lines = []
    for change in changes:
        lines.append(f"• {change['path']} (+{change['additions']} -{change['deletions']})")
    return "\n".join(lines)
```

#### 2.3 Claude API Client (`app/claude_client.py`)

```python
from anthropic import AsyncAnthropic
from app.config.settings import settings
import logging
import json

logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20251101"  # Latest model

    async def generate_code(self, task: str, context: list):
        """Generate code based on task and context"""
        try:
            # Build context string
            context_str = self._format_context(context)

            # Load code generation prompt
            system_prompt = self._load_prompt('code_generation')

            # Call Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"{context_str}\n\nTask: {task}"
                    }
                ]
            )

            # Parse response
            content = response.content[0].text

            return {
                'task_id': str(response.id),
                'summary': self._extract_summary(content),
                'code_preview': self._extract_code_preview(content),
                'full_changes': self._extract_changes(content),
                'files_changed': self._extract_files(content)
            }

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    def _format_context(self, context: list) -> str:
        """Format thread context for Claude"""
        lines = ["Thread Context:"]
        for msg in context:
            lines.append(f"[{msg['user']}]: {msg['text']}")
        return "\n".join(lines)

    def _load_prompt(self, prompt_name: str) -> str:
        """Load system prompt from file"""
        prompt_path = f"config/prompts/{prompt_name}.txt"
        with open(prompt_path, 'r') as f:
            return f.read()

    def _extract_summary(self, content: str) -> str:
        """Extract summary from Claude's response"""
        # Implementation depends on response format
        pass

    def _extract_code_preview(self, content: str) -> str:
        """Extract code preview (first 20 lines)"""
        pass

    def _extract_changes(self, content: str) -> dict:
        """Extract full code changes"""
        pass

    def _extract_files(self, content: str) -> list:
        """Extract list of files changed"""
        pass
```

#### 2.4 GitLab Client (`app/gitlab_client.py`)

```python
import gitlab
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class GitLabClient:
    def __init__(self):
        self.gl = gitlab.Gitlab(
            url=settings.GITLAB_URL,
            private_token=settings.GITLAB_TOKEN
        )
        self.project = self.gl.projects.get(settings.GITLAB_PROJECT_ID)

    async def create_merge_request(self, project_id: int, task: dict, author: str):
        """Create a merge request with Claude's changes"""
        try:
            # Generate branch name
            branch_name = f"feature/claude-{task['task_id'][:8]}"

            # Create branch
            self.project.branches.create({
                'branch': branch_name,
                'ref': 'master'
            })

            # Commit changes
            commit_actions = []
            for file_change in task['full_changes']:
                commit_actions.append({
                    'action': 'update',
                    'file_path': file_change['path'],
                    'content': file_change['content']
                })

            commit = self.project.commits.create({
                'branch': branch_name,
                'commit_message': self._generate_commit_message(task),
                'actions': commit_actions
            })

            # Create MR
            mr = self.project.mergerequests.create({
                'source_branch': branch_name,
                'target_branch': 'master',
                'title': task['summary'],
                'description': self._generate_mr_description(task),
                'remove_source_branch': True
            })

            return {
                'iid': mr.iid,
                'title': mr.title,
                'web_url': mr.web_url,
                'source_branch': branch_name,
                'detailed_merge_status': mr.detailed_merge_status
            }

        except Exception as e:
            logger.error(f"GitLab API error: {e}")
            raise

    def _generate_commit_message(self, task: dict) -> str:
        """Generate commit message"""
        return f"""feat: {task['summary']}

{task.get('description', '')}

🤖 Generated with Claude Code via Slack

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
"""

    def _generate_mr_description(self, task: dict) -> str:
        """Generate MR description"""
        return f"""## Summary
{task['summary']}

## Changes
{self._format_changes(task['files_changed'])}

## Testing Checklist
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Security scan passed (gitleaks)

## Related Discussion
Slack Thread: [Link to thread]

---
🤖 This MR was generated automatically by Claude Bot
"""

    def _format_changes(self, files_changed: list) -> str:
        """Format file changes for MR description"""
        lines = []
        for file in files_changed:
            lines.append(f"- `{file['path']}`")
        return "\n".join(lines)
```

### Step 3: Configuration (`config/settings.py`)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Slack
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    SLACK_APP_TOKEN: Optional[str] = None

    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-opus-4-5-20251101"
    ANTHROPIC_MAX_TOKENS: int = 8192

    # GitLab
    GITLAB_URL: str = "http://10.0.0.84:8090"
    GITLAB_TOKEN: str
    GITLAB_PROJECT_ID: int = 1  # wizardsofts-megabuild

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Database
    DATABASE_URL: str = "postgresql://user:pass@postgres:5432/claude_bot"

    # Monitoring
    PROMETHEUS_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Security
    MAX_REQUESTS_PER_MINUTE: int = 10
    ALLOWED_CHANNELS: list = ["development", "bugs", "feature-requests"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Step 4: Docker Deployment

#### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["python", "-m", "app.main"]
```

#### `docker-compose.yml`

```yaml
version: '3.8'

services:
  claude-slack-bot:
    build: .
    container_name: claude-slack-bot
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "3000:3000"  # Internal only
    networks:
      - wizardsofts-network
    depends_on:
      - redis
      - postgres
    volumes:
      - ./app:/app/app
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.claude-bot.rule=Host(`bot.wizardsofts.com`)"
      - "traefik.http.routers.claude-bot.entrypoints=websecure"
      - "traefik.http.routers.claude-bot.tls.certresolver=letsencrypt"
      - "traefik.http.services.claude-bot.loadbalancer.server.port=3000"
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    container_name: claude-bot-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    networks:
      - wizardsofts-network
    volumes:
      - redis-data:/data
    deploy:
      resources:
        limits:
          memory: 256M

  postgres:
    image: postgres:15-alpine
    container_name: claude-bot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: claude_bot
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - wizardsofts-network
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 512M

networks:
  wizardsofts-network:
    external: true

volumes:
  redis-data:
  postgres-data:
```

#### `.env.example`

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-api-key

# GitLab
GITLAB_URL=http://10.0.0.84:8090
GITLAB_TOKEN=glpat-your-gitlab-token
GITLAB_PROJECT_ID=1

# Redis
REDIS_PASSWORD=your-redis-password

# PostgreSQL
POSTGRES_USER=claude_bot
POSTGRES_PASSWORD=your-postgres-password

# Monitoring
LOG_LEVEL=INFO
```

### Step 5: Deployment

```bash
# On Server 84
cd /opt/wizardsofts-megabuild/infrastructure/claude-slack-bot

# Create .env from example
cp .env.example .env
nano .env  # Fill in actual credentials

# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f claude-slack-bot

# Verify health
curl http://localhost:3000/health
```

---

## Monitoring & Observability

### Prometheus Metrics

Add to `/opt/wizardsofts-megabuild/infrastructure/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'claude-slack-bot'
    static_configs:
      - targets: ['claude-slack-bot:3000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Create dashboard at http://10.0.0.84:3002:

```json
{
  "title": "Claude Slack Bot",
  "panels": [
    {
      "title": "Slack Events Received",
      "targets": [
        {"expr": "rate(slack_events_total[5m])"}
      ]
    },
    {
      "title": "Claude API Requests",
      "targets": [
        {"expr": "rate(claude_requests_total[5m])"}
      ]
    },
    {
      "title": "Task Completion Time",
      "targets": [
        {"expr": "histogram_quantile(0.95, task_completion_duration_seconds)"}
      ]
    }
  ]
}
```

---

## Testing

### Unit Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=app

# Expected output:
# test_slack_handlers.py::test_handle_mention PASSED
# test_claude_client.py::test_generate_code PASSED
# test_gitlab_client.py::test_create_mr PASSED
```

### Integration Test

```bash
# Test Slack webhook
curl -X POST http://localhost:3000/slack/events \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/slack_mention_event.json

# Test health endpoint
curl http://localhost:3000/health

# Test metrics endpoint
curl http://localhost:3000/metrics
```

---

## Next Steps

1. **Deploy to Production**
   - [ ] Set up Traefik routing for bot.wizardsofts.com
   - [ ] Configure SSL certificates
   - [ ] Test end-to-end workflow

2. **Add Advanced Features**
   - [ ] Code review automation
   - [ ] CI/CD status monitoring
   - [ ] Deployment approvals via Slack

3. **Security Hardening**
   - [ ] Implement request signing verification
   - [ ] Add rate limiting per user
   - [ ] Set up audit logging

4. **Documentation**
   - [ ] User guide for team
   - [ ] API documentation
   - [ ] Runbook for incidents

---

**Document Version:** 1.0
**Last Updated:** 2026-01-01
**Maintainer:** DevOps Team
