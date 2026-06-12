import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import FilterMenu from "./FilterMenu";

const items = [
  { key: "newOnly", label: "New only", active: false },
  { key: "freeOnly", label: "Free only", active: false },
];

describe("FilterMenu", () => {
  it("reveals its items only after the trigger is clicked", () => {
    render(<FilterMenu ariaLabel="Filters" items={items} onToggle={vi.fn()} />);
    expect(screen.queryByText("New only")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Filters/ }));
    expect(screen.getByText("New only")).toBeDefined();
    expect(screen.getByText("Free only")).toBeDefined();
  });

  it("calls onToggle with the item key and keeps the list open", () => {
    const onToggle = vi.fn();
    render(<FilterMenu ariaLabel="Filters" items={items} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("button", { name: /Filters/ }));
    fireEvent.click(screen.getByText("New only"));
    expect(onToggle).toHaveBeenCalledWith("newOnly");
    expect(screen.getByText("Free only")).toBeDefined();
  });

  it("shows the active count on the trigger", () => {
    const active = [
      { key: "newOnly", label: "New only", active: true },
      { key: "freeOnly", label: "Free only", active: false },
    ];
    render(<FilterMenu ariaLabel="Filters" items={active} onToggle={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Filters/ }).textContent).toContain("1");
  });
});
