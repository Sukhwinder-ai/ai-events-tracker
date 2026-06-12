import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Dropdown from "./Dropdown";

const options = [
  { value: "all", label: "All cities" },
  { value: "brisbane", label: "Brisbane" },
  { value: "ipswich", label: "Ipswich" },
];

describe("Dropdown", () => {
  it("shows the selected option's label on the trigger", () => {
    render(<Dropdown value="ipswich" options={options} onChange={vi.fn()} ariaLabel="City" />);
    expect(screen.getByRole("button", { name: "City" }).textContent).toContain("Ipswich");
  });

  it("reveals the options only after the trigger is clicked", () => {
    render(<Dropdown value="all" options={options} onChange={vi.fn()} ariaLabel="City" />);
    expect(screen.queryByRole("option", { name: "Brisbane" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "City" }));
    expect(screen.getByRole("option", { name: "Brisbane" })).toBeDefined();
  });

  it("calls onChange with the chosen value and closes the list", () => {
    const onChange = vi.fn();
    render(<Dropdown value="all" options={options} onChange={onChange} ariaLabel="City" />);
    fireEvent.click(screen.getByRole("button", { name: "City" }));
    fireEvent.click(screen.getByText("Brisbane"));
    expect(onChange).toHaveBeenCalledWith("brisbane");
    expect(screen.queryByRole("listbox")).toBeNull();
  });
});
