import { describe, test, expect } from "vitest";
import {
  cn,
  hashString,
  deepEquals,
  beautifyString,
  setNestedProperty,
  removeEmptyStringsAndNulls,
  getTypeTextColor,
  getTypeBgColor,
  getTypeColor,
} from "./utils";

// ── cn() ────────────────────────────────────────────────────────────────────

describe("cn", () => {
  test("test_cn_merges_classes", () => {
    const result = cn("px-2", "py-1");
    expect(result).toContain("px-2");
    expect(result).toContain("py-1");
  });

  test("test_cn_handles_conflicts", () => {
    // tailwind-merge should resolve conflicting classes
    const result = cn("px-2", "px-4");
    expect(result).toBe("px-4");
  });

  test("test_cn_empty_inputs", () => {
    expect(cn()).toBe("");
    expect(cn("")).toBe("");
    expect(cn(undefined)).toBe("");
    expect(cn(null)).toBe("");
  });
});

// ── hashString() ────────────────────────────────────────────────────────────

describe("hashString", () => {
  test("test_hashString_deterministic", () => {
    const hash1 = hashString("hello");
    const hash2 = hashString("hello");
    expect(hash1).toBe(hash2);
  });

  test("test_hashString_different_inputs", () => {
    const hash1 = hashString("hello");
    const hash2 = hashString("world");
    expect(hash1).not.toBe(hash2);
  });

  test("test_hashString_empty_string", () => {
    expect(hashString("")).toBe(0);
  });
});

// ── deepEquals() ────────────────────────────────────────────────────────────

describe("deepEquals", () => {
  test("test_deepEquals_primitives", () => {
    expect(deepEquals(1, 1)).toBe(true);
    expect(deepEquals(1, 2)).toBe(false);
    expect(deepEquals("a", "a")).toBe(true);
    expect(deepEquals("a", "b")).toBe(false);
    expect(deepEquals(true, true)).toBe(true);
    expect(deepEquals(true, false)).toBe(false);
  });

  test("test_deepEquals_objects", () => {
    expect(deepEquals({ a: 1, b: { c: 2 } }, { a: 1, b: { c: 2 } })).toBe(
      true,
    );
    expect(deepEquals({ a: 1 }, { a: 2 })).toBe(false);
    expect(deepEquals({ a: 1 }, { a: 1, b: 2 })).toBe(false);
  });

  test("test_deepEquals_arrays", () => {
    expect(deepEquals([1, 2, 3], [1, 2, 3])).toBe(true);
    expect(deepEquals([1, 2], [1, 3])).toBe(false);
  });

  test("test_deepEquals_null_handling", () => {
    // The implementation filters out null keys via Object.keys().filter(key => obj[key] !== null)
    // So {a: 1, b: null} should equal {a: 1} because null keys are ignored
    expect(deepEquals({ a: 1, b: null }, { a: 1 })).toBe(true);
  });

  test("test_deepEquals_different_types", () => {
    expect(deepEquals(1, "1")).toBe(false);
    expect(deepEquals({}, [])).toBe(true); // both are objects with 0 non-null keys
    expect(deepEquals(null, undefined)).toBe(false);
  });
});

// ── beautifyString() ────────────────────────────────────────────────────────

describe("beautifyString", () => {
  test("test_beautifyString_camelCase", () => {
    expect(beautifyString("camelCase")).toBe("Camel Case");
  });

  test("test_beautifyString_snake_case", () => {
    expect(beautifyString("snake_case")).toBe("Snake Case");
  });

  test("test_beautifyString_exceptions", () => {
    // Exception map is applied in order: "Auto GPT" key is checked before "Gpt"
    // "auto_gpt" -> "Auto Gpt" (after underscore + capitalize transforms)
    // Then exceptions iterate in order:
    //   "Auto GPT" key doesn't match "Auto Gpt" (case-sensitive word boundary)
    //   "Gpt" -> "GPT" produces "Auto GPT"
    // The "Auto GPT" key was already processed, so the result stays "Auto GPT"
    expect(beautifyString("auto_gpt")).toBe("Auto GPT");
    // "openai" -> "Openai" -> exception "Openai" -> "OpenAI"
    expect(beautifyString("openai")).toBe("OpenAI");
    // "api" -> "Api" -> exception "API"
    expect(beautifyString("api")).toBe("API");
    // "url" -> "Url" -> exception "URL"
    expect(beautifyString("url")).toBe("URL");
  });
});

// ── setNestedProperty() ─────────────────────────────────────────────────────

describe("setNestedProperty", () => {
  test("test_setNestedProperty_simple", () => {
    const obj: Record<string, unknown> = {};
    setNestedProperty(obj, "key", "value");
    expect(obj.key).toBe("value");
  });

  test("test_setNestedProperty_nested", () => {
    const obj: Record<string, unknown> = {};
    setNestedProperty(obj, "a.b.c", 42);
    expect((obj as any).a.b.c).toBe(42);
  });

  test("test_setNestedProperty_creates_intermediate", () => {
    const obj: Record<string, unknown> = {};
    setNestedProperty(obj, "x.y.z", "deep");
    expect((obj as any).x).toBeDefined();
    expect((obj as any).x.y).toBeDefined();
    expect((obj as any).x.y.z).toBe("deep");
  });

  test("test_setNestedProperty_rejects_proto", () => {
    const obj = {};
    expect(() => setNestedProperty(obj, "__proto__.polluted", true)).toThrow(
      "Invalid property name",
    );
  });

  test("test_setNestedProperty_invalid_target", () => {
    expect(() => setNestedProperty(null, "key", "value")).toThrow(
      "Target must be a non-null object",
    );
    expect(() => setNestedProperty("string", "key", "value")).toThrow(
      "Target must be a non-null object",
    );
  });
});

// ── removeEmptyStringsAndNulls() ────────────────────────────────────────────

describe("removeEmptyStringsAndNulls", () => {
  test("test_removeEmptyStringsAndNulls_removes_nulls", () => {
    const obj = { a: 1, b: null, c: "hello" };
    const result = removeEmptyStringsAndNulls(obj);
    expect(result).toEqual({ a: 1, c: "hello" });
    expect(result.b).toBeUndefined();
  });

  test("test_removeEmptyStringsAndNulls_removes_empty_strings", () => {
    const obj = { a: 1, b: "", c: "hello" };
    const result = removeEmptyStringsAndNulls(obj);
    expect(result).toEqual({ a: 1, c: "hello" });
    expect(result.b).toBeUndefined();
  });

  test("test_removeEmptyStringsAndNulls_keeps_values", () => {
    const obj = { a: 1, b: "text", c: true, d: 0 };
    const result = removeEmptyStringsAndNulls(obj);
    expect(result).toEqual({ a: 1, b: "text", c: true, d: 0 });
  });

  test("test_removeEmptyStringsAndNulls_handles_arrays", () => {
    const obj = { a: [1, null, 3] };
    const result = removeEmptyStringsAndNulls(obj);
    // Arrays: null/undefined elements become ""
    expect(result.a).toEqual([1, "", 3]);
  });
});

// ── getTypeTextColor() ──────────────────────────────────────────────────────

describe("getTypeTextColor", () => {
  test("test_getTypeTextColor_known_types", () => {
    expect(getTypeTextColor("string")).toBe("text-green-500");
    expect(getTypeTextColor("number")).toBe("text-blue-500");
    expect(getTypeTextColor("integer")).toBe("text-blue-500");
    expect(getTypeTextColor("boolean")).toBe("text-yellow-500");
    expect(getTypeTextColor("object")).toBe("text-purple-500");
    expect(getTypeTextColor("array")).toBe("text-indigo-500");
  });

  test("test_getTypeTextColor_null", () => {
    expect(getTypeTextColor(null)).toBe("text-gray-500");
  });

  test("test_getTypeTextColor_unknown", () => {
    expect(getTypeTextColor("unknown_type")).toBe("text-gray-500");
  });
});

// ── getTypeBgColor() ────────────────────────────────────────────────────────

describe("getTypeBgColor", () => {
  test("returns correct border colors for known types", () => {
    expect(getTypeBgColor("string")).toBe("border-green-500");
    expect(getTypeBgColor("number")).toBe("border-blue-500");
    expect(getTypeBgColor("boolean")).toBe("border-yellow-500");
    expect(getTypeBgColor("object")).toBe("border-purple-500");
    expect(getTypeBgColor("array")).toBe("border-indigo-500");
  });

  test("returns gray for null", () => {
    expect(getTypeBgColor(null)).toBe("border-gray-500");
  });

  test("returns gray for unknown type", () => {
    expect(getTypeBgColor("unknown_type")).toBe("border-gray-500");
  });
});

// ── getTypeColor() ──────────────────────────────────────────────────────────

describe("getTypeColor", () => {
  test("returns correct hex colors for known types", () => {
    expect(getTypeColor("string")).toBe("#22c55e");
    expect(getTypeColor("number")).toBe("#3b82f6");
    expect(getTypeColor("boolean")).toBe("#eab308");
    expect(getTypeColor("object")).toBe("#a855f7");
    expect(getTypeColor("array")).toBe("#6366f1");
  });

  test("returns gray hex for null", () => {
    expect(getTypeColor(null)).toBe("#6b7280");
  });

  test("returns gray hex for unknown type", () => {
    expect(getTypeColor("unknown_type")).toBe("#6b7280");
  });
});
