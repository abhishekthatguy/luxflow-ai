"""Enterprise n8n node builders — branching, auth, internal API calls."""

from __future__ import annotations

from typing import Any

# Matches docker-compose N8N_WEBHOOK_SECRET default for local dev.
INTERNAL_TOKEN = "dev-n8n-webhook-secret"
API_BASE = "http://api:8000"
N8N_BASE = "http://n8n:5678"
SESSION_INIT_SLUG = "workflow-session-init-v1"


def _pos(x: int, y: int = 300) -> list[int]:
    return [x, y]


def code_node(node_id: str, name: str, code: str, x: int, y: int = 300) -> dict[str, Any]:
    return {
        "parameters": {"jsCode": code},
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": _pos(x, y),
    }


def if_node(
    node_id: str,
    name: str,
    left_expression: str,
    *,
    x: int,
    y: int = 300,
    operation: str = "true",
) -> dict[str, Any]:
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": node_id,
                        "leftValue": left_expression,
                        "rightValue": "",
                        "operator": {"type": "boolean", "operation": operation},
                    }
                ],
                "combinator": "and",
            }
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": _pos(x, y),
    }


def wait_node(node_id: str, name: str, seconds: int, x: int, y: int = 420) -> dict[str, Any]:
    return {
        "parameters": {"amount": seconds, "unit": "seconds"},
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": _pos(x, y),
    }


def http_get_internal(
    node_id: str,
    name: str,
    url: str,
    x: int,
    y: int = 300,
    *,
    with_session_token: bool = False,
) -> dict[str, Any]:
    headers = [{"name": "X-Internal-Token", "value": INTERNAL_TOKEN}]
    if with_session_token:
        headers.append(
            {
                "name": "X-Session-Token",
                "value": "={{ $getWorkflowStaticData('global').sessionToken || '' }}",
            }
        )
    return {
        "parameters": {
            "method": "GET",
            "url": url,
            "sendHeaders": True,
            "headerParameters": {"parameters": headers},
            "options": {"response": {"response": {"fullResponse": False}}},
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": _pos(x, y),
    }


def http_post_internal(
    node_id: str,
    name: str,
    url: str,
    json_body: str,
    x: int,
    y: int = 300,
    *,
    signed: bool = False,
    raw_body: bool = False,
) -> dict[str, Any]:
    headers = [{"name": "X-Internal-Token", "value": INTERNAL_TOKEN}]
    if signed:
        headers = [
            {"name": "Content-Type", "value": "application/json"},
            {"name": "X-LexFlow-Signature", "value": "={{ $json.callbackSignature }}"},
        ]
    params: dict[str, Any] = {
        "method": "POST",
        "url": url,
        "sendHeaders": True,
        "headerParameters": {"parameters": headers},
        "sendBody": True,
    }
    if raw_body:
        params["specifyBody"] = "string"
        params["body"] = "={{ $json.callbackRaw }}"
    else:
        params["specifyBody"] = "json"
        params["jsonBody"] = json_body
    return {
        "parameters": params,
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": _pos(x, y),
    }


NORMALIZE_WEBHOOK_CODE = """
const inbound = $json.body ?? $json;
const executionId = inbound.executionId || inbound.execution_id;
const caseId = inbound.caseId || inbound.case_id || null;
const payload = inbound.payload || {};
const documentId = payload.documentId || inbound.documentId || null;
return [{
  json: {
    executionId,
    caseId,
    documentId,
    payload,
    inboundSignature: $json.headers?.['x-lexflow-signature'] || null,
    ok: Boolean(executionId),
  }
}];
""".strip()


VALIDATE_SIGNATURE_CODE = """
const ctx = $json;
if (!ctx.ok) {
  throw new Error('Missing executionId on webhook payload');
}
if (!ctx.inboundSignature) {
  throw new Error('Missing X-LexFlow-Signature — reject unsigned webhook');
}
return [{ json: { ...ctx, signatureValid: true, step: 'Validate Signature' } }];
""".strip()


MERGE_VERIFY_SESSION_CODE = """
const ctx = $('Normalize Context').first().json;
const verify = $json.data ?? $json;
if (verify.sessionValid === false || verify.authorized === false) {
  throw new Error(verify.message || 'Orchestrator session invalid — run WF-11 Initialize');
}
return [{ json: { ...ctx, sessionValid: true, ocrAttempt: 1, step: 'Verify Session Token' } }];
""".strip()


STORE_SESSION_TOKEN_CODE = """
const data = $json.data ?? $json;
const staticData = $getWorkflowStaticData('global');
staticData.sessionToken = data.sessionToken || data.session_token || '';
staticData.expiresAt = data.expiresAt || data.expires_at || '';
$setWorkflowStaticData('global', staticData);
return [{ json: { ...data, stored: true, step: 'Store Session Token' } }];
""".strip()


LOAD_SESSION_TOKEN_CODE = """
const staticData = $getWorkflowStaticData('global');
return [{ json: { sessionToken: staticData.sessionToken || '', expiresAt: staticData.expiresAt || '' } }];
""".strip()


MERGE_HEARTBEAT_CODE = """
const root = $json.body?.data ?? $json.body ?? $json.data ?? $json;
const validRaw = root.sessionValid ?? root.session_valid ?? root.authorized ?? false;
const valid = validRaw === true || validRaw === 'true';
const requiresInit = root.requiresInitialize ?? root.requires_initialize ?? false;
return [{
  json: {
    sessionValid: valid,
    sessionIsValid: valid ? 'yes' : 'no',
    requiresInitialize: requiresInit === true || requiresInit === 'true',
    sessionToken: root.sessionToken || root.session_token || $('Load Session Token').first().json.sessionToken || '',
    message: root.message || '',
  }
}];
""".strip()


MERGE_CASE_CODE = """
const ctx = $('Merge Execution Context').first().json;
const caseData = $json.data ?? $json;
return [{ json: { ...ctx, caseContext: caseData, step: 'Get Case Details' } }];
""".strip()


MERGE_OCR_CODE = """
const ctx = $('Merge Execution Context').first().json;
const ocr = $json.data ?? $json;
const attempt = Number(ocr.attempt || ctx.ocrAttempt || 0) + 1;
return [{
  json: {
    ...ctx,
    ocrStatus: ocr.ocrStatus || ocr.ocr_status,
    ocrComplete: Boolean(ocr.ocrComplete ?? ocr.ocr_complete),
    ocrAttempt: attempt,
    step: 'Poll OCR Status',
  }
}];
""".strip()


MERGE_INIT_EXECUTION_CODE = """
const ctx = $('Merge Session Context').first().json;
const init = $json.data ?? $json;
const flags = init.flags || {};
return [{
  json: {
    ...ctx,
    slug: init.slug || ctx.slug,
    executionId: init.executionId || ctx.executionId,
    caseId: init.caseId || ctx.caseId,
    documentId: init.documentId || ctx.documentId,
    flags,
    ocrComplete: Boolean(flags.ocrComplete),
    aiEnabled: Boolean(flags.aiEnabled),
    ocrAttempt: ctx.ocrAttempt || 1,
    step: 'Initialize Execution',
  }
}];
""".strip()


MERGE_STEP_RESULT_CODE = """
const ctx = $('Merge Execution Context').first().json;
const res = $json.data ?? $json;
return [{ json: { ...ctx, lastStepResult: res, ok: res.success !== false } }];
""".strip()


def prepare_callback_code(slug: str) -> str:
    return f"""
const crypto = require('crypto');
const ctx = $json;
const secret = '{INTERNAL_TOKEN}';
const status = ctx.workflowStatus || (ctx.aiSuccess === false || ctx.ocrComplete === false ? 'failed' : 'completed');
const body = {{
  executionId: ctx.executionId,
  status,
  n8nExecutionId: String($execution.id),
  output: {{
    slug: ctx.slug || '{slug}',
    ocrComplete: ctx.ocrComplete,
    aiSuccess: ctx.aiSuccess,
    steps: ['validate','verify-session','initialize','steps','callback'],
  }},
  errorMessage: ctx.errorMessage || null,
}};
const raw = JSON.stringify(body);
const sig = crypto.createHmac('sha256', secret).update(raw).digest('hex');
return [{{ json: {{ ...ctx, callbackBody: body, callbackRaw: raw, callbackSignature: sig, workflowStatus: status }} }}];
""".strip()


def admin_notify_node(step_id: str, label: str, workflow_name: str, x: int) -> dict[str, Any]:
    import json as _json

    subject = f"[LexFlow] {workflow_name} — {label}"
    return {
        "parameters": {
            "method": "POST",
            "url": f"{API_BASE}/internal/notifications/admin",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": (
                '={"subject": '
                + _json.dumps(subject)
                + ', "body": '
                + _json.dumps(f"Workflow step completed: {label}")
                + ', "source": "n8n", "metadata": {"workflow": '
                + _json.dumps(workflow_name)
                + ', "step": '
                + _json.dumps(label)
                + ', "executionId": "{{ $execution.id }}"}}'
            ),
        },
        "id": step_id,
        "name": label,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": _pos(x),
    }


def _init_execution_nodes(slug: str, x: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, int]:
    init_body = (
        "={{ JSON.stringify({ executionId: $('Merge Session Context').first().json.executionId, "
        "caseId: $('Merge Session Context').first().json.caseId, "
        "payload: $('Merge Session Context').first().json.payload || {} }) }}"
    )
    nodes = [
        http_post_internal(
            "init-execution",
            "Initialize Execution",
            f"{API_BASE}/internal/workflows/{slug}/initialize",
            init_body,
            x,
        ),
        code_node("merge-init", "Merge Execution Context", MERGE_INIT_EXECUTION_CODE, x + 220),
    ]
    connections = {
        "Initialize Execution": {
            "main": [[{"node": "Merge Execution Context", "type": "main", "index": 0}]]
        },
    }
    return nodes, connections, "Merge Execution Context", x + 440


PREPARE_CALLBACK_CODE = prepare_callback_code("document-upload-v1")


INCREMENT_RETRY_CODE = """
const ctx = $json;
return [{ json: { ...ctx, ocrAttempt: Number(ctx.ocrAttempt || 0) + 1 } }];
""".strip()


MERGE_AI_CODE = """
const ctx = $('Merge OCR').first().json;
const ai = $json.data ?? $json;
return [{
  json: {
    ...ctx,
    aiSuccess: Boolean(ai.success),
    aiMessage: ai.message || '',
    step: 'Trigger AI Summary',
  }
}];
""".strip()


PREPARE_CALLBACK_CODE = prepare_callback_code("document-upload-v1")


def build_standard_webhook_workflow(
    slug: str,
    webhook_node: dict,
    steps: list[tuple[str, str]],
    *,
    workflow_name: str = "",
    admin_notify_steps: set[str] | None = None,
    with_callback: bool = True,
) -> dict[str, Any]:
    """Business webhook — verify session, initialize execution, run API steps, callback."""
    prefix = build_token_verify_prefix(webhook_node)
    nodes = prefix["nodes"]
    connections = dict(prefix["connections"])
    x = prefix["next_x"]
    last = prefix["last_node"]

    init_nodes, init_conn, exec_last, x = _init_execution_nodes(slug, x)
    nodes.extend(init_nodes)
    connections.update(init_conn)
    connections["Merge Session Context"] = {
        "main": [[{"node": "Initialize Execution", "type": "main", "index": 0}]]
    }
    last = exec_last

    notify_steps = admin_notify_steps or set()
    display = workflow_name or slug
    step_order = 10

    for step_id, label in steps:
        x += 220
        if label in notify_steps:
            nodes.append(admin_notify_node(step_id, label, display, x))
            connections[last] = {"main": [[{"node": label, "type": "main", "index": 0}]]}
            last = label
            continue

        if label == "Get Case Details":
            nodes.append(
                http_get_internal(
                    f"step-{step_id}",
                    label,
                    f"={{{{ '{API_BASE}/internal/workflows/executions/' + $('Merge Execution Context').first().json.executionId + '/case-context' }}}}",
                    x,
                )
            )
            merge_name = f"Merge {label}"
            nodes.append(code_node(f"merge-{step_id}", merge_name, MERGE_CASE_CODE, x + 220))
            connections[last] = {"main": [[{"node": label, "type": "main", "index": 0}]]}
            connections[label] = {"main": [[{"node": merge_name, "type": "main", "index": 0}]]}
            last = merge_name
            x += 220
            step_order += 10
            continue

        step_url = (
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/step?"
            f"execution_id=' + $('Merge Execution Context').first().json.executionId + "
            f"'&step_name=' + encodeURIComponent('{label}') + "
            f"'&step_order={step_order}' }}}}"
        )
        nodes.append(http_post_internal(f"step-{step_id}", label, step_url, "{}", x))
        nodes.append(code_node(f"merge-{step_id}", f"Merge {label}", MERGE_STEP_RESULT_CODE, x + 220))
        connections[last] = {"main": [[{"node": label, "type": "main", "index": 0}]]}
        connections[label] = {"main": [[{"node": f"Merge {label}", "type": "main", "index": 0}]]}
        last = f"Merge {label}"
        x += 220
        step_order += 10

    if with_callback:
        prep = code_node("prepare-callback", "Prepare Callback", prepare_callback_code(slug), x + 220)
        cb = http_post_internal(
            "callback",
            "Callback API",
            f"{API_BASE}/internal/webhooks/n8n/{slug}",
            "",
            x + 440,
            signed=True,
            raw_body=True,
        )
        nodes.extend([prep, cb])
        connections[last] = {"main": [[{"node": "Prepare Callback", "type": "main", "index": 0}]]}
        connections["Prepare Callback"] = {"main": [[{"node": "Callback API", "type": "main", "index": 0}]]}

    return {"nodes": nodes, "connections": connections}


def build_scheduled_runner_workflow(
    slug: str,
    schedule_node: dict,
    *,
    notify_on_failure: bool = False,
) -> dict[str, Any]:
    """Scheduled workflow — single FastAPI runner; optional admin alert on failure."""
    nodes: list[dict[str, Any]] = [
        schedule_node,
        http_post_internal(
            "run-job",
            "Run Scheduled Job",
            f"{API_BASE}/internal/workflows/scheduled/{slug}/run",
            "{}",
            460,
        ),
    ]
    connections: dict[str, Any] = {
        "Schedule": {"main": [[{"node": "Run Scheduled Job", "type": "main", "index": 0}]]},
    }
    if notify_on_failure:
        nodes.append(
            if_node(
                "if-healthy",
                "Decision: Healthy?",
                "={{ ($json.data?.healthy ?? $json.healthy) !== false }}",
                x=680,
            )
        )
        nodes.append(admin_notify_node("notify-fail", "Notify Ops", slug, 900))
        connections["Run Scheduled Job"] = {
            "main": [[{"node": "Decision: Healthy?", "type": "main", "index": 0}]]
        }
        connections["Decision: Healthy?"] = {
            "main": [
                [],
                [{"node": "Notify Ops", "type": "main", "index": 0}],
            ]
        }
    return {"nodes": nodes, "connections": connections}


def build_notification_teams_workflow(webhook_node: dict) -> dict[str, Any]:
    """Teams delivery sub-workflow — posts Adaptive Card to configured webhook."""
    webhook = dict(webhook_node)
    webhook["parameters"] = {
        **webhook_node.get("parameters", {}),
        "responseMode": "responseNode",
    }
    resolve_code = """
const body = $json.body ?? $json;
const url = body.teamsWebhookUrl;
return [{
  json: {
    ...body,
    hasUrl: url ? 'yes' : 'no',
    postUrl: url || '',
    correlationId: body.correlationId,
    message: url ? '' : 'TEAMS_WEBHOOK_URL not configured',
  }
}];
""".strip()
    respond_stub = {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ { status: 'stub', correlationId: $json.correlationId, message: $json.message } }}",
        },
        "id": "respond-stub",
        "name": "Respond Stub",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": _pos(900, 480),
    }
    nodes = [
        webhook,
        code_node("resolve", "Resolve Webhook URL", resolve_code, 460),
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": "if-url",
                            "leftValue": "={{ $json.hasUrl }}",
                            "rightValue": "yes",
                            "operator": {"type": "string", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                }
            },
            "id": "if-url",
            "name": "Decision: Has URL?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": _pos(680),
        },
        {
            "parameters": {
                "method": "POST",
                "url": "={{ $json.postUrl }}",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ $json.card }}",
            },
            "id": "teams",
            "name": "Post to Teams",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": _pos(900),
        },
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ { status: 'accepted', correlationId: $('Resolve Webhook URL').item.json.correlationId } }}",
            },
            "id": "respond",
            "name": "Respond",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1.1,
            "position": _pos(1120),
        },
        respond_stub,
    ]
    connections = {
        "Webhook": {"main": [[{"node": "Resolve Webhook URL", "type": "main", "index": 0}]]},
        "Resolve Webhook URL": {"main": [[{"node": "Decision: Has URL?", "type": "main", "index": 0}]]},
        "Decision: Has URL?": {
            "main": [
                [{"node": "Post to Teams", "type": "main", "index": 0}],
                [{"node": "Respond Stub", "type": "main", "index": 0}],
            ]
        },
        "Post to Teams": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections}


def build_notification_slack_workflow(webhook_node: dict) -> dict[str, Any]:
    """Slack delivery sub-workflow — posts Block Kit payload via Bot API or Incoming Webhook."""
    webhook = dict(webhook_node)
    webhook["parameters"] = {
        **webhook_node.get("parameters", {}),
        "responseMode": "responseNode",
    }
    resolve_code = """
const body = $json.body ?? $json;
const token = body.slackBotToken;
const channel = body.slackChannelId;
const webhookUrl = body.slackWebhookUrl;
const msg = body.message || {};
const hasBot = token && channel ? 'yes' : 'no';
const hasWebhook = webhookUrl ? 'yes' : 'no';
const canSend = hasBot === 'yes' || hasWebhook === 'yes' ? 'yes' : 'no';
const useBot = hasBot === 'yes';
return [{
  json: {
    ...body,
    hasBot,
    hasWebhook,
    canSend,
    slackAuth: useBot ? `Bearer ${token}` : '',
    postUrl: useBot ? 'https://slack.com/api/chat.postMessage' : (webhookUrl || ''),
    slackBody: useBot ? { ...msg, channel } : msg,
    correlationId: body.correlationId,
    message: canSend === 'yes' ? '' : 'Slack bot token+channel or webhook URL not configured',
  }
}];
""".strip()
    respond_stub = {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ { status: 'stub', correlationId: $json.correlationId, message: $json.message } }}",
        },
        "id": "respond-stub",
        "name": "Respond Stub",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": _pos(900, 480),
    }
    nodes = [
        webhook,
        code_node("resolve-slack", "Resolve Slack Target", resolve_code, 460),
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": "if-can-send",
                            "leftValue": "={{ $json.canSend }}",
                            "rightValue": "yes",
                            "operator": {"type": "string", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                }
            },
            "id": "if-can-send",
            "name": "Decision: Can Send?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": _pos(680),
        },
        {
            "parameters": {
                "method": "POST",
                "url": "={{ $json.postUrl }}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "={{ $json.slackAuth }}",
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json",
                        },
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ $json.slackBody }}",
                "options": {
                    "response": {
                        "response": {
                            "fullResponse": True,
                            "neverError": True,
                        }
                    },
                    "timeout": 30000,
                },
            },
            "id": "slack-post",
            "name": "Post to Slack",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": _pos(900),
        },
        code_node(
            "verify-slack",
            "Verify Slack Response",
            """
const req = $('Resolve Slack Target').first().json;
const resp = $json.body ?? $json;
const useBot = req.hasBot === 'yes';
let ok = true;
let error = '';
if (useBot) {
  ok = resp.ok === true;
  error = resp.error || '';
} else {
  ok = (resp.statusCode ?? 200) < 400;
}
return [{
  json: {
    correlationId: req.correlationId,
    deliveryOk: ok ? 'yes' : 'no',
    error: error || (ok ? '' : 'Slack delivery failed'),
  }
}];
""".strip(),
            1120,
        ),
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": "if-slack-ok",
                            "leftValue": "={{ $json.deliveryOk }}",
                            "rightValue": "yes",
                            "operator": {"type": "string", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                }
            },
            "id": "if-slack-ok",
            "name": "Decision: Slack OK?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": _pos(1340),
        },
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ { status: 'accepted', correlationId: $json.correlationId } }}",
            },
            "id": "respond",
            "name": "Respond",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1.1,
            "position": _pos(1560),
        },
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ { status: 'failed', correlationId: $json.correlationId, error: $json.error } }}",
            },
            "id": "respond-failed",
            "name": "Respond Failed",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1.1,
            "position": _pos(1560, 480),
        },
        respond_stub,
    ]
    connections = {
        "Webhook": {"main": [[{"node": "Resolve Slack Target", "type": "main", "index": 0}]]},
        "Resolve Slack Target": {"main": [[{"node": "Decision: Can Send?", "type": "main", "index": 0}]]},
        "Decision: Can Send?": {
            "main": [
                [{"node": "Post to Slack", "type": "main", "index": 0}],
                [{"node": "Respond Stub", "type": "main", "index": 0}],
            ]
        },
        "Post to Slack": {"main": [[{"node": "Verify Slack Response", "type": "main", "index": 0}]]},
        "Verify Slack Response": {"main": [[{"node": "Decision: Slack OK?", "type": "main", "index": 0}]]},
        "Decision: Slack OK?": {
            "main": [
                [{"node": "Respond", "type": "main", "index": 0}],
                [{"node": "Respond Failed", "type": "main", "index": 0}],
            ]
        },
    }
    return {"nodes": nodes, "connections": connections}


def build_test_slack_notification_workflow(manual_node: dict) -> dict[str, Any]:
    """Manual-only Slack smoke — exercises notification-slack-v1 from the n8n editor."""
    pick_case_code = """
// Edit test_mode before Run (see n8n/workflows/test/slack-notification.test-cases.md)
const test_mode = 'client_created';
const correlationId = 'slack-test-' + ($execution.id || Date.now());

function blockKit(title, description, fields) {
  return {
    text: title + ' — ' + description,
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: title, emoji: true } },
      { type: 'section', text: { type: 'mrkdwn', text: description } },
      { type: 'section', fields: fields },
      {
        type: 'context',
        elements: [{ type: 'mrkdwn', text: 'LexFlow test · correlation `' + correlationId + '`' }],
      },
    ],
  };
}

const token = $env.SLACK_BOT_TOKEN || '';
const channel = $env.SLACK_TEAM_CHANNEL_ID || 'C0BF67RKS3Z';
const webhook = $env.SLACK_WEBHOOK_URL || '';

const cases = {
  basic_text: {
    route: 'n8n',
    expectStatus: 'accepted',
    body: {
      correlationId,
      slackBotToken: token || null,
      slackChannelId: channel || null,
      slackWebhookUrl: webhook || null,
      message: { text: 'LexFlow Slack smoke — basic text from n8n editor' },
      eventType: 'SYSTEM_ALERT',
      workflowSlug: 'test-slack-notification-v1',
    },
  },
  client_created: {
    route: 'n8n',
    expectStatus: 'accepted',
    body: {
      correlationId,
      slackBotToken: token || null,
      slackChannelId: channel || null,
      slackWebhookUrl: webhook || null,
      message: blockKit(
        'New client onboarded',
        'Gitlime was added to LexFlow (dummy WF-04 follow-up).',
        [
          { type: 'mrkdwn', text: '*Event*\\nCLIENT_CREATED' },
          { type: 'mrkdwn', text: '*Client*\\nGitlime' },
          { type: 'mrkdwn', text: '*Email*\\nkashyapabhi688@gmail.com' },
          { type: 'mrkdwn', text: '*Workflow*\\nclient-created-v1' },
        ],
      ),
      eventType: 'CLIENT_CREATED',
      workflowSlug: 'client-created-v1',
    },
  },
  case_created: {
    route: 'n8n',
    expectStatus: 'accepted',
    body: {
      correlationId,
      slackBotToken: token || null,
      slackChannelId: channel || null,
      slackWebhookUrl: webhook || null,
      message: blockKit(
        'New case opened',
        'Smith v. Jones — intake workflow started (dummy).',
        [
          { type: 'mrkdwn', text: '*Event*\\nCASE_CREATED' },
          { type: 'mrkdwn', text: '*Case*\\nSmith v. Jones' },
          { type: 'mrkdwn', text: '*Workflow*\\ncase-intake-v1' },
        ],
      ),
      eventType: 'CASE_CREATED',
      workflowSlug: 'case-intake-v1',
    },
  },
  workflow_failed: {
    route: 'n8n',
    expectStatus: 'accepted',
    body: {
      correlationId,
      slackBotToken: token || null,
      slackChannelId: channel || null,
      slackWebhookUrl: webhook || null,
      message: blockKit(
        'Workflow failed',
        'document-upload-v1 step OCR callback timed out (dummy).',
        [
          { type: 'mrkdwn', text: '*Event*\\nWORKFLOW_FAILED' },
          { type: 'mrkdwn', text: '*Status*\\nFailed' },
          { type: 'mrkdwn', text: '*Workflow*\\ndocument-upload-v1' },
        ],
      ),
      eventType: 'WORKFLOW_FAILED',
      workflowSlug: 'document-upload-v1',
    },
  },
  stub_no_credentials: {
    route: 'n8n',
    expectStatus: 'stub',
    body: {
      correlationId,
      slackBotToken: null,
      slackChannelId: null,
      slackWebhookUrl: null,
      message: { text: 'LexFlow stub test — no Slack credentials supplied' },
      eventType: 'SYSTEM_ALERT',
      workflowSlug: 'test-slack-notification-v1',
    },
  },
  via_fastapi: {
    route: 'fastapi',
    expectStatus: 'sent',
    url: 'http://api:8000/internal/notifications/slack/test',
    body: {},
  },
};

const picked = cases[test_mode];
if (!picked) {
  throw new Error('Unknown test_mode: ' + test_mode + '. See slack-notification.test-cases.md');
}

const postUrl = picked.route === 'fastapi'
  ? picked.url
  : 'http://n8n:5678/webhook/notification-slack-v1';

return [{
  json: {
    test_mode,
    route: picked.route,
    expectStatus: picked.expectStatus,
    correlationId,
    postUrl,
    body: picked.body || {},
    hasCredentials: Boolean(token && channel) || Boolean(webhook),
  },
}];
""".strip()

    report_code = """
const req = $('Pick Test Case').first().json;
const http = $('POST Slack Test').first().json;
const statusCode = http.statusCode ?? http.status ?? 200;
let actual = http.status ?? http.body?.status;
if (!actual) {
  actual = statusCode >= 400 ? 'failed' : (req.expectStatus === 'stub' ? 'stub' : 'accepted');
}
if (typeof actual === 'object') {
  actual = actual.status || JSON.stringify(actual);
}
const pass = String(actual) === String(req.expectStatus)
  || (req.expectStatus === 'accepted' && String(actual) === 'accepted')
  || (req.route === 'fastapi' && String(actual) === 'sent');
return [{
  json: {
    pass,
    test_mode: req.test_mode,
    route: req.route,
    expected: req.expectStatus,
    actual: String(actual),
    correlationId: req.correlationId,
    postUrl: req.postUrl,
    hasCredentials: req.hasCredentials,
    hint: pass ? 'PASS — check Slack channel C0BF67RKS3Z for the message' : 'FAIL — inspect POST Slack Test node output',
    response: http,
  },
}];
""".strip()

    nodes = [
        manual_node,
        code_node("pick-case", "Pick Test Case", pick_case_code, 460),
        {
            "parameters": {
                "method": "POST",
                "url": "={{ $json.postUrl }}",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ $json.body }}",
                "options": {
                    "response": {
                        "response": {
                            "fullResponse": True,
                            "neverError": True,
                        }
                    },
                    "timeout": 30000,
                },
            },
            "id": "post-slack",
            "name": "POST Slack Test",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": _pos(680),
            "notes": "Routes to notification-slack-v1 (n8n) or FastAPI /internal/notifications/slack/test",
        },
        code_node("report", "Report Result", report_code, 900),
    ]
    connections = {
        "Manual Trigger": {"main": [[{"node": "Pick Test Case", "type": "main", "index": 0}]]},
        "Pick Test Case": {"main": [[{"node": "POST Slack Test", "type": "main", "index": 0}]]},
        "POST Slack Test": {"main": [[{"node": "Report Result", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections}


def build_token_verify_prefix(webhook_node: dict) -> dict[str, Any]:
    """Every business workflow: validate inbound signature then verify orchestrator session."""
    nodes = [
        webhook_node,
        code_node("normalize-ctx", "Normalize Context", NORMALIZE_WEBHOOK_CODE, 460),
        code_node("validate-signature", "Validate Signature", VALIDATE_SIGNATURE_CODE, 680),
        http_get_internal(
            "verify-session",
            "Verify Session Token",
            f"{API_BASE}/internal/workflows/session/verify",
            900,
        ),
        code_node("merge-session", "Merge Session Context", MERGE_VERIFY_SESSION_CODE, 1120),
    ]
    connections: dict[str, Any] = {
        "Webhook": {"main": [[{"node": "Normalize Context", "type": "main", "index": 0}]]},
        "Normalize Context": {"main": [[{"node": "Validate Signature", "type": "main", "index": 0}]]},
        "Validate Signature": {"main": [[{"node": "Verify Session Token", "type": "main", "index": 0}]]},
        "Verify Session Token": {"main": [[{"node": "Merge Session Context", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections, "last_node": "Merge Session Context", "next_x": 1340}


def build_session_init_workflow(webhook_node: dict, manual_node: dict) -> dict[str, Any]:
    """WF-11 — run once on deploy; also triggered by heartbeat when session expires."""
    nodes = [
        webhook_node,
        manual_node,
        http_post_internal(
            "init-session",
            "Initialize Session",
            f"{API_BASE}/internal/workflows/session/initialize",
            "{}",
            480,
        ),
        code_node("store-token", "Store Session Token", STORE_SESSION_TOKEN_CODE, 700),
    ]
    connections: dict[str, Any] = {
        "Webhook": {"main": [[{"node": "Initialize Session", "type": "main", "index": 0}]]},
        "Manual Trigger": {"main": [[{"node": "Initialize Session", "type": "main", "index": 0}]]},
        "Initialize Session": {"main": [[{"node": "Store Session Token", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections}


def build_session_heartbeat_workflow(schedule_node: dict) -> dict[str, Any]:
    """WF-12 — every 5 min refresh session; re-run WF-11 if expired."""
    nodes = [
        schedule_node,
        code_node("load-token", "Load Session Token", LOAD_SESSION_TOKEN_CODE, 460),
        http_get_internal(
            "heartbeat",
            "Session Heartbeat API",
            f"{API_BASE}/internal/workflows/session/heartbeat",
            680,
            with_session_token=True,
        ),
        code_node("merge-hb", "Merge Heartbeat Result", MERGE_HEARTBEAT_CODE, 900),
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "loose",
                    },
                    "conditions": [
                        {
                            "id": "if-valid",
                            "leftValue": "={{ $json.sessionIsValid }}",
                            "rightValue": "yes",
                            "operator": {"type": "string", "operation": "equals"},
                        }
                    ],
                    "combinator": "and",
                }
            },
            "id": "if-valid",
            "name": "Decision: Session Valid?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": _pos(1120),
        },
        http_post_internal(
            "reinit",
            "Trigger Initialize Workflow",
            f"{N8N_BASE}/webhook/{SESSION_INIT_SLUG}",
            "{}",
            1340,
            y=480,
        ),
        code_node("store-token", "Store Session Token", STORE_SESSION_TOKEN_CODE, 1560, y=480),
    ]
    connections: dict[str, Any] = {
        "Schedule": {"main": [[{"node": "Load Session Token", "type": "main", "index": 0}]]},
        "Load Session Token": {"main": [[{"node": "Session Heartbeat API", "type": "main", "index": 0}]]},
        "Session Heartbeat API": {"main": [[{"node": "Merge Heartbeat Result", "type": "main", "index": 0}]]},
        "Merge Heartbeat Result": {"main": [[{"node": "Decision: Session Valid?", "type": "main", "index": 0}]]},
        "Decision: Session Valid?": {
            "main": [
                [],
                [{"node": "Trigger Initialize Workflow", "type": "main", "index": 0}],
            ]
        },
        "Trigger Initialize Workflow": {"main": [[{"node": "Store Session Token", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections}


def build_document_upload_enterprise(slug: str, webhook_node: dict) -> dict[str, Any]:
    """Enterprise document-upload — token gate then OCR/AI decision graph."""
    prefix = build_token_verify_prefix(webhook_node)
    nodes = prefix["nodes"]
    connections = dict(prefix["connections"])
    x = prefix["next_x"]

    init_nodes, init_conn, _, x = _init_execution_nodes(slug, x)
    nodes.extend(init_nodes)
    connections.update(init_conn)
    connections["Merge Session Context"] = {
        "main": [[{"node": "Initialize Execution", "type": "main", "index": 0}]]
    }

    extra_nodes = [
        http_get_internal(
            "case-context",
            "Get Case Details",
            f"={{{{ '{API_BASE}/internal/workflows/executions/' + $('Merge Execution Context').first().json.executionId + '/case-context' }}}}",
            x,
        ),
        code_node("merge-case", "Merge Case Context", MERGE_CASE_CODE, x + 220),
        http_get_internal(
            "poll-ocr",
            "Poll OCR Status",
            f"={{{{ '{API_BASE}/internal/workflows/documents/' + $('Merge Execution Context').first().json.documentId + '/ocr-status?attempt=' + ($('Merge Execution Context').first().json.ocrAttempt || 1) }}}}",
            x + 440,
        ),
        code_node("merge-ocr", "Merge OCR", MERGE_OCR_CODE, x + 660),
        if_node("if-ocr", "Decision: OCR Complete?", "={{ $json.ocrComplete }}", x=x + 880),
        if_node(
            "if-retry",
            "Decision: Retry OCR?",
            "={{ $json.ocrAttempt < 12 }}",
            x=x + 880,
            y=480,
        ),
        wait_node("wait-ocr", "Wait & Retry", 5, x + 1100, y=480),
        code_node("retry-bump", "Increment Attempt", INCREMENT_RETRY_CODE, x + 1320, y=480),
        http_post_internal(
            "ai-summary",
            "Trigger AI Summary",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/ai-summary?execution_id=' + $json.executionId }}}}",
            "{}",
            x + 1100,
        ),
        code_node("merge-ai", "Merge AI Result", MERGE_AI_CODE, x + 1320),
        if_node("if-ai", "Decision: AI Success?", "={{ $json.aiSuccess !== false }}", x=x + 1540),
        http_post_internal(
            "notify",
            "Execute Workflow: Notifications",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/notify?execution_id=' + $json.executionId }}}}",
            "{}",
            x + 1760,
        ),
        http_post_internal(
            "audit",
            "Execute Workflow: Audit",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/audit?execution_id=' + $json.executionId }}}}",
            "{}",
            x + 1980,
        ),
        http_post_internal(
            "alert",
            "Retry / Alert",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/alert?execution_id=' + $('Merge Execution Context').first().json.executionId + '&reason=' + encodeURIComponent('OCR or AI step failed') }}}}",
            "{}",
            x + 1760,
            y=480,
        ),
        code_node("prepare-callback", "Prepare Callback", prepare_callback_code(slug), x + 2200),
        http_post_internal(
            "callback",
            "Callback API",
            f"{API_BASE}/internal/webhooks/n8n/{slug}",
            "",
            x + 2420,
            signed=True,
            raw_body=True,
        ),
    ]
    nodes.extend(extra_nodes)

    connections["Merge Execution Context"] = {"main": [[{"node": "Get Case Details", "type": "main", "index": 0}]]}
    connections["Get Case Details"] = {"main": [[{"node": "Merge Case Context", "type": "main", "index": 0}]]}
    connections["Merge Case Context"] = {"main": [[{"node": "Poll OCR Status", "type": "main", "index": 0}]]}
    connections["Poll OCR Status"] = {"main": [[{"node": "Merge OCR", "type": "main", "index": 0}]]}
    connections["Merge OCR"] = {"main": [[{"node": "Decision: OCR Complete?", "type": "main", "index": 0}]]}
    connections["Decision: OCR Complete?"] = {
        "main": [
            [{"node": "Trigger AI Summary", "type": "main", "index": 0}],
            [{"node": "Decision: Retry OCR?", "type": "main", "index": 0}],
        ]
    }
    connections["Decision: Retry OCR?"] = {
        "main": [
            [{"node": "Wait & Retry", "type": "main", "index": 0}],
            [{"node": "Retry / Alert", "type": "main", "index": 0}],
        ]
    }
    connections["Wait & Retry"] = {"main": [[{"node": "Increment Attempt", "type": "main", "index": 0}]]}
    connections["Increment Attempt"] = {"main": [[{"node": "Poll OCR Status", "type": "main", "index": 0}]]}
    connections["Trigger AI Summary"] = {"main": [[{"node": "Merge AI Result", "type": "main", "index": 0}]]}
    connections["Merge AI Result"] = {"main": [[{"node": "Decision: AI Success?", "type": "main", "index": 0}]]}
    connections["Decision: AI Success?"] = {
        "main": [
            [{"node": "Execute Workflow: Notifications", "type": "main", "index": 0}],
            [{"node": "Retry / Alert", "type": "main", "index": 0}],
        ]
    }
    connections["Execute Workflow: Notifications"] = {
        "main": [[{"node": "Execute Workflow: Audit", "type": "main", "index": 0}]]
    }
    connections["Execute Workflow: Audit"] = {
        "main": [[{"node": "Prepare Callback", "type": "main", "index": 0}]]
    }
    connections["Retry / Alert"] = {"main": [[{"node": "Prepare Callback", "type": "main", "index": 0}]]}
    connections["Prepare Callback"] = {"main": [[{"node": "Callback API", "type": "main", "index": 0}]]}

    return {"nodes": nodes, "connections": connections}


def signed_callback_nodes(slug: str, x_start: int) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    prep = code_node("prepare-callback", "Prepare Callback", prepare_callback_code(slug), x_start)
    cb = http_post_internal(
        "callback",
        "Callback API",
        f"{API_BASE}/internal/webhooks/n8n/{slug}",
        "",
        x_start + 220,
        signed=True,
        raw_body=True,
    )
    connections = {
        "Prepare Callback": {"main": [[{"node": "Callback API", "type": "main", "index": 0}]]},
    }
    return [prep, cb], connections, "Prepare Callback"
