"""Enterprise n8n node builders — branching, auth, internal API calls."""

from __future__ import annotations

import json
from typing import Any

# Matches docker-compose N8N_WEBHOOK_SECRET default for local dev.
INTERNAL_TOKEN = "dev-n8n-webhook-secret"
API_BASE = "http://api:8000"


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
) -> dict[str, Any]:
    return {
        "parameters": {
            "method": "GET",
            "url": url,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "X-Internal-Token", "value": INTERNAL_TOKEN},
                ]
            },
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
// Inbound webhook from FastAPI is already HMAC-signed by Celery.
return [{ json: { ...ctx, signatureValid: true, step: 'Validate Signature' } }];
""".strip()


MERGE_INIT_CODE = """
const ctx = $('Normalize Context').first().json;
const init = $json.data ?? $json;
const flags = init.flags || {};
return [{
  json: {
    ...ctx,
    executionId: init.executionId || ctx.executionId,
    caseId: init.caseId || ctx.caseId,
    documentId: init.documentId || ctx.documentId,
    flags,
    ocrComplete: Boolean(flags.ocrComplete),
    aiEnabled: Boolean(flags.aiEnabled),
    ocrAttempt: ctx.ocrAttempt || 1,
    step: 'Initialize Workflow',
  }
}];
""".strip()


MERGE_CASE_CODE = """
const ctx = $('Merge Initialize').first().json;
const caseData = $json.data ?? $json;
return [{ json: { ...ctx, caseContext: caseData, step: 'Get Case Details' } }];
""".strip()


MERGE_OCR_CODE = """
const ctx = $('Merge Initialize').first().json;
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


PREPARE_CALLBACK_CODE = f"""
const crypto = require('crypto');
const ctx = $json;
const secret = '{INTERNAL_TOKEN}';
const status = ctx.workflowStatus || (ctx.aiSuccess === false || ctx.ocrComplete === false ? 'failed' : 'completed');
const body = {{
  executionId: ctx.executionId,
  status,
  n8nExecutionId: String($execution.id),
  output: {{
    slug: ctx.slug || 'document-upload-v1',
    ocrComplete: ctx.ocrComplete,
    aiSuccess: ctx.aiSuccess,
    steps: ['validate','initialize','heartbeat','case','ocr','ai','notify','audit'],
  }},
  errorMessage: ctx.errorMessage || null,
}};
const raw = JSON.stringify(body);
const sig = crypto.createHmac('sha256', secret).update(raw).digest('hex');
return [{{ json: {{ ...ctx, callbackBody: body, callbackRaw: raw, callbackSignature: sig, workflowStatus: status }} }}];
""".strip()


def build_document_upload_enterprise(slug: str, webhook_node: dict) -> dict[str, Any]:
    """Enterprise document-upload graph with decisions, retries, sub-workflows."""
    nodes: list[dict[str, Any]] = [
        webhook_node,
        code_node("normalize", "Normalize Context", NORMALIZE_WEBHOOK_CODE, 460),
        code_node("validate", "Validate Signature", VALIDATE_SIGNATURE_CODE, 680),
        http_post_internal(
            "initialize",
            "Initialize Workflow",
            f"{API_BASE}/internal/workflows/{slug}/initialize",
            '={{ JSON.stringify({ executionId: $json.executionId, caseId: $json.caseId, payload: $json.payload }) }}',
            900,
        ),
        http_get_internal(
            "heartbeat",
            "Heartbeat API",
            f"{API_BASE}/internal/workflows/heartbeat",
            1120,
        ),
        code_node("merge-init", "Merge Initialize", MERGE_INIT_CODE, 1340),
        http_get_internal(
            "case-context",
            "Get Case Details",
            f"={{{{ '{API_BASE}/internal/workflows/executions/' + $('Merge Initialize').first().json.executionId + '/case-context' }}}}",
            1560,
        ),
        code_node("merge-case", "Merge Case Context", MERGE_CASE_CODE, 1780),
        http_get_internal(
            "poll-ocr",
            "Poll OCR Status",
            f"={{{{ '{API_BASE}/internal/workflows/documents/' + $('Merge Initialize').first().json.documentId + '/ocr-status?attempt=' + ($('Merge Initialize').first().json.ocrAttempt || 1) }}}}",
            2000,
        ),
        code_node("merge-ocr", "Merge OCR", MERGE_OCR_CODE, 2220),
        if_node("if-ocr", "Decision: OCR Complete?", "={{ $json.ocrComplete }}", x=2440),
        if_node(
            "if-retry",
            "Decision: Retry OCR?",
            "={{ $json.ocrAttempt < 12 }}",
            x=2440,
            y=480,
        ),
        wait_node("wait-ocr", "Wait & Retry", 5, 2660, y=480),
        code_node("retry-bump", "Increment Attempt", INCREMENT_RETRY_CODE, 2880, y=480),
        http_post_internal(
            "ai-summary",
            "Trigger AI Summary",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/ai-summary?execution_id=' + $json.executionId }}}}",
            "{}",
            2660,
        ),
        code_node("merge-ai", "Merge AI Result", MERGE_AI_CODE, 2880),
        if_node("if-ai", "Decision: AI Success?", "={{ $json.aiSuccess !== false }}", x=3100),
        http_post_internal(
            "notify",
            "Execute Workflow: Notifications",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/notify?execution_id=' + $json.executionId }}}}",
            "{}",
            3320,
        ),
        http_post_internal(
            "audit",
            "Execute Workflow: Audit",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/audit?execution_id=' + $json.executionId }}}}",
            "{}",
            3540,
        ),
        http_post_internal(
            "alert",
            "Retry / Alert",
            f"={{{{ '{API_BASE}/internal/workflows/{slug}/actions/alert?execution_id=' + $('Merge Initialize').first().json.executionId + '&reason=' + encodeURIComponent('OCR or AI step failed') }}}}",
            "{}",
            3320,
            y=480,
        ),
        code_node("prepare-callback", "Prepare Callback", PREPARE_CALLBACK_CODE, 3760),
        http_post_internal(
            "callback",
            "Callback API",
            f"{API_BASE}/internal/webhooks/n8n/{slug}",
            "",
            3980,
            signed=True,
            raw_body=True,
        ),
    ]

    connections: dict[str, Any] = {
        "Webhook": {"main": [[{"node": "Normalize Context", "type": "main", "index": 0}]]},
        "Normalize Context": {"main": [[{"node": "Validate Signature", "type": "main", "index": 0}]]},
        "Validate Signature": {"main": [[{"node": "Initialize Workflow", "type": "main", "index": 0}]]},
        "Initialize Workflow": {"main": [[{"node": "Heartbeat API", "type": "main", "index": 0}]]},
        "Heartbeat API": {"main": [[{"node": "Merge Initialize", "type": "main", "index": 0}]]},
        "Merge Initialize": {"main": [[{"node": "Get Case Details", "type": "main", "index": 0}]]},
        "Get Case Details": {"main": [[{"node": "Merge Case Context", "type": "main", "index": 0}]]},
        "Merge Case Context": {"main": [[{"node": "Poll OCR Status", "type": "main", "index": 0}]]},
        "Poll OCR Status": {"main": [[{"node": "Merge OCR", "type": "main", "index": 0}]]},
        "Merge OCR": {"main": [[{"node": "Decision: OCR Complete?", "type": "main", "index": 0}]]},
        "Decision: OCR Complete?": {
            "main": [
                [{"node": "Trigger AI Summary", "type": "main", "index": 0}],
                [{"node": "Decision: Retry OCR?", "type": "main", "index": 0}],
            ]
        },
        "Decision: Retry OCR?": {
            "main": [
                [{"node": "Wait & Retry", "type": "main", "index": 0}],
                [{"node": "Retry / Alert", "type": "main", "index": 0}],
            ]
        },
        "Wait & Retry": {"main": [[{"node": "Increment Attempt", "type": "main", "index": 0}]]},
        "Increment Attempt": {"main": [[{"node": "Poll OCR Status", "type": "main", "index": 0}]]},
        "Trigger AI Summary": {"main": [[{"node": "Merge AI Result", "type": "main", "index": 0}]]},
        "Merge AI Result": {"main": [[{"node": "Decision: AI Success?", "type": "main", "index": 0}]]},
        "Decision: AI Success?": {
            "main": [
                [{"node": "Execute Workflow: Notifications", "type": "main", "index": 0}],
                [{"node": "Retry / Alert", "type": "main", "index": 0}],
            ]
        },
        "Execute Workflow: Notifications": {
            "main": [[{"node": "Execute Workflow: Audit", "type": "main", "index": 0}]]
        },
        "Execute Workflow: Audit": {
            "main": [[{"node": "Prepare Callback", "type": "main", "index": 0}]]
        },
        "Retry / Alert": {"main": [[{"node": "Prepare Callback", "type": "main", "index": 0}]]},
        "Prepare Callback": {"main": [[{"node": "Callback API", "type": "main", "index": 0}]]},
    }

    return {"nodes": nodes, "connections": connections}


def build_enterprise_webhook_prefix(slug: str, webhook_node: dict) -> dict[str, Any]:
    """Init + heartbeat + signed callback wrapper for standard business workflows."""
    init_body = '={{ JSON.stringify({ executionId: $json.executionId || ($json.body && $json.body.executionId), caseId: $json.caseId || ($json.body && $json.body.caseId), payload: $json.payload || ($json.body && $json.body.payload) || {} }) }}'
    nodes = [
        webhook_node,
        code_node("normalize", "Normalize Context", NORMALIZE_WEBHOOK_CODE, 460),
        code_node("validate", "Validate Signature", VALIDATE_SIGNATURE_CODE, 680),
        http_post_internal(
            "initialize",
            "Initialize Workflow",
            f"{API_BASE}/internal/workflows/{slug}/initialize",
            init_body,
            900,
            signed=False,
        ),
        http_get_internal("heartbeat", "Heartbeat API", f"{API_BASE}/internal/workflows/heartbeat", 1120),
    ]
    connections: dict[str, Any] = {
        "Webhook": {"main": [[{"node": "Normalize Context", "type": "main", "index": 0}]]},
        "Normalize Context": {"main": [[{"node": "Validate Signature", "type": "main", "index": 0}]]},
        "Validate Signature": {"main": [[{"node": "Initialize Workflow", "type": "main", "index": 0}]]},
        "Initialize Workflow": {"main": [[{"node": "Heartbeat API", "type": "main", "index": 0}]]},
    }
    return {"nodes": nodes, "connections": connections, "last_node": "Heartbeat API", "next_x": 1340}


def signed_callback_nodes(slug: str, x_start: int) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    prep = code_node("prepare-callback", "Prepare Callback", PREPARE_CALLBACK_CODE, x_start)
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
