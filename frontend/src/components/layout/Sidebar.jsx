import {
  LayoutDashboard,
  MessageSquare,
  Brain,
  FileText,
  BarChart3,
  Settings,
} from "lucide-react";

const navigationItems = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Chat",
    icon: MessageSquare,
  },
  {
    label: "Knowledge",
    icon: Brain,
  },
  {
    label: "Documents",
    icon: FileText,
  },
  {
    label: "Analytics",
    icon: BarChart3,
  },
];

function Sidebar() {
  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-200 bg-white">
      {/* Brand */}
      <div className="flex h-16 items-center border-b border-slate-200 px-6">
        <span className="text-2xl">🚀</span>
        <span className="ml-2 text-xl font-bold tracking-tight text-slate-900">
          KAIRO
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.label}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-slate-200 p-3">
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
          <Settings size={18} />
          Settings
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;