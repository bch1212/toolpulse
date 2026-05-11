import { describe, it, expect } from "vitest";
import { monitor } from "./monitor.js";

describe("monitor", () => {
  it("returns sync function results unchanged", () => {
    const add = monitor((a: number, b: number) => a + b);
    expect(add(2, 3)).toBe(5);
  });

  it("propagates sync exceptions", () => {
    const boom = monitor(() => { throw new Error("expected"); });
    expect(() => boom()).toThrow("expected");
  });

  it("returns async function results unchanged", async () => {
    const addAsync = monitor(async (a: number, b: number) => a + b);
    await expect(addAsync(2, 3)).resolves.toBe(5);
  });

  it("propagates async rejections", async () => {
    const boomAsync = monitor(async () => { throw new Error("expected"); });
    await expect(boomAsync()).rejects.toThrow("expected");
  });
});
