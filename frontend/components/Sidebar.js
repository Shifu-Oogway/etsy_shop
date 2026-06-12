"use client";
export default function Sidebar({ active, onChange }) {
  const items = [
    { id: "overview",  icon: "▣", label: "Overview" },
    { id: "products",  icon: "◧", label: "Products" },
    { id: "listings",  icon: "≡", label: "Listings" },
    { id: "trends",    icon: "⟋", label: "Trends" },
    { id: "agents",    icon: "◈", label: "Agents" },
    { id: "schedules", icon: "◷", label: "Schedules" },
    { id: "tests",     icon: "⬡", label: "Test Runner" },
  ];
  return (
    <nav className="sidebar">
      {items.map((item, i) => (
        <div key={item.id}>
          {i === 2 && <div className="sidebar-divider" />}
          {i === 6 && <div className="sidebar-divider" />}
          <button
            className={`sidebar-icon${active === item.id ? " active" : ""}`}
            onClick={() => onChange(item.id)}
            title={item.label}
          >
            {item.icon}
          </button>
        </div>
      ))}
    </nav>
  );
}
