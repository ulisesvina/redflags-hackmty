import { describe, expect, it } from "vitest";
import { buildBookList, groupReadiness, readinessProgress } from "./investigation";

const requiredFiles = [
  "company.json", "suppliers.csv", "customers.csv", "employees.csv", "invoices.csv",
  "goods_receipts.csv", "bank_transactions.csv", "counterparty_bank.csv", "ledger.csv", "efos_69b.csv",
];

describe("investigation readiness", () => {
  it("keeps analysis gated until every required file is present", () => {
    const partial = { ready: false, requiredFiles, presentFiles: ["company.json", "suppliers.csv"], missingFiles: requiredFiles.slice(2) };
    expect(readinessProgress(partial)).toBe(20);
    expect(groupReadiness(partial).every((group) => group.complete)).toBe(false);
  });

  it("marks all comparison groups complete for the minimum estate", () => {
    const ready = { ready: true, requiredFiles, presentFiles: requiredFiles, missingFiles: [] };
    expect(readinessProgress(ready)).toBe(100);
    expect(groupReadiness(ready).every((group) => group.complete)).toBe(true);
  });

  it("accepts supported accounting formats and ignores unrelated files", () => {
    const zip = new File(["books"], "estate.zip", { type: "application/zip", lastModified: 1 });
    const image = new File(["image"], "receipt.png", { type: "image/png", lastModified: 2 });
    expect(buildBookList([], [zip, image]).map((book) => book.name)).toEqual(["estate.zip"]);
  });
});
