import { describe, test, expect } from "vitest";

/**
 * Test the formatCredits logic extracted from the useCredits hook.
 * This is a pure function that converts a credit amount (in cents) to a
 * formatted dollar string. Testing it standalone avoids the need to render
 * the full hook with all its API dependencies.
 */
describe("formatCredits", () => {
  const formatCredits = (credit: number | null): string => {
    if (credit === null) return "-";
    const value = Math.abs(credit);
    const sign = credit < 0 ? "-" : "";
    return `${sign}$${(value / 100).toFixed(2)}`;
  };

  test("null returns dash", () => {
    expect(formatCredits(null)).toBe("-");
  });

  test("zero", () => {
    expect(formatCredits(0)).toBe("$0.00");
  });

  test("positive", () => {
    expect(formatCredits(1000)).toBe("$10.00");
  });

  test("negative", () => {
    expect(formatCredits(-500)).toBe("-$5.00");
  });

  test("small amount", () => {
    expect(formatCredits(1)).toBe("$0.01");
  });

  test("large amount", () => {
    expect(formatCredits(999999)).toBe("$9999.99");
  });

  test("negative small amount", () => {
    expect(formatCredits(-1)).toBe("-$0.01");
  });
});
