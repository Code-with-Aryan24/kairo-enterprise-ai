import {
  LayoutDashboard,
  MessageSquare,
  Brain,
  FileText,
  BarChart3,
  Settings,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigationItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Chat", icon: MessageSquare, path: "/chat" },
  { label: "Knowledge", icon: Brain, path: "/knowledge" },
  { label: "Documents", icon: FileText, path: "/documents" },
  { label: "Analytics", icon: BarChart3, path: "/analytics" },
];

function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed inset-y-0 left-0 z-50 flex w-64 flex-col
          border-r border-slate-200 bg-white
          transition-transform duration-200
          md:static md:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Brand */}
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-6">
          <div className="flex items-center">
            <span className="text-2xl">🚀</span>
            <span className="ml-2 text-xl font-bold tracking-tight text-slate-900">
              KAIRO
            </span>
          </div>

          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-500 hover:bg-slate-100 md:hidden"
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navigationItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.label}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`
                }
              >
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Settings */}
        <div className="border-t border-slate-200 p-3">
          <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
            <Settings size={18} />
            Settings
          </button>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;