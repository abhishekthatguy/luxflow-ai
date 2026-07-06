import http from "k6/http";
import { check, sleep } from "k6";

/**
 * k6 load baseline — case list/read (LEX-507).
 * Run: k6 run tests/load/cases-read.js
 * Requires: API on API_URL, valid credentials.
 */
const API = __ENV.API_URL || "http://localhost:8000";
const EMAIL = __ENV.LOAD_TEST_EMAIL || "jane@example.com";
const PASSWORD = __ENV.LOAD_TEST_PASSWORD || "password123";

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "1m", target: 100 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export function setup() {
  const res = http.post(
    `${API}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(res, { "login ok": (r) => r.status === 200 });
  return { token: res.json("data.accessToken") };
}

export default function (data) {
  const headers = { Authorization: `Bearer ${data.token}` };
  const list = http.get(`${API}/api/v1/cases?pageSize=25`, { headers });
  check(list, {
    "cases list 200": (r) => r.status === 200,
    "cases list fast": (r) => r.timings.duration < 500,
  });
  const cases = list.json("data");
  if (cases && cases.length > 0) {
    const id = cases[0].id;
    const detail = http.get(`${API}/api/v1/cases/${id}`, { headers });
    check(detail, { "case detail 200": (r) => r.status === 200 });
  }
  sleep(0.5);
}
