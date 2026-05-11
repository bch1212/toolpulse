import { describe, it, expect } from "vitest";
import { fingerprint, extractShape } from "./schemaHash.js";

describe("fingerprint", () => {
  it("matches when shape is identical", () => {
    const a = { name: "Alice", age: 30, tags: ["admin"] };
    const b = { name: "Bob", age: 99, tags: ["user", "beta"] };
    expect(fingerprint(a)).toBe(fingerprint(b));
  });

  it("differs when keys differ", () => {
    expect(fingerprint({ a: 1 })).not.toBe(fingerprint({ b: 1 }));
  });

  it("differs when value types differ", () => {
    expect(fingerprint({ id: 1 })).not.toBe(fingerprint({ id: "x" }));
  });

  it("ignores key order", () => {
    expect(fingerprint({ a: 1, b: 2 })).toBe(fingerprint({ b: 2, a: 1 }));
  });

  it("treats empty list as distinct from populated", () => {
    expect(fingerprint({ x: [] })).not.toBe(fingerprint({ x: [{ id: 1 }] }));
  });

  it("merges heterogeneous list element shapes", () => {
    const a = [{ id: 1 }, { id: 2, extra: "x" }];
    const b = [{ id: 5, extra: "y" }, { id: 6 }];
    expect(fingerprint(a)).toBe(fingerprint(b));
  });
});

describe("extractShape", () => {
  it("normalizes primitives", () => {
    expect(extractShape("hi")).toBe("str");
    expect(extractShape(42)).toBe("int");
    expect(extractShape(3.14)).toBe("float");
    expect(extractShape(true)).toBe("bool");
    expect(extractShape(null)).toBe("null");
  });
});
