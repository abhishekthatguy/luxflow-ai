import { describe, expect, it } from "vitest";
import { isApiHealthy } from "@lexflow/shared";

describe("isApiHealthy", () => {
  it("returns true for ok api response", () => {
    expect(isApiHealthy({ status: "ok", service: "api" })).toBe(true);
  });

  it("returns false for other responses", () => {
    expect(isApiHealthy({ status: "degraded", service: "api" })).toBe(false);
  });
});
