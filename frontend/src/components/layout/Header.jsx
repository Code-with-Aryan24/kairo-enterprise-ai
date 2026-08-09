import { Bell, Search, CircleUserRound } from "lucide-react";

function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      {/* Search */}
      <div className="flex items-center gap-3 text-slate-400">
        <Search size={19} />
        <span className="text-sm">Search KAIRO...</span>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-5">
        <button className="text-slate-500 transition hover:text-slate-900">
          <Bell size={19} />
        </button>

        <div className="flex items-center gap-2">
          <CircleUserRound size={24} className="text-slate-600" />

          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium text-slate-900">
              KAIRO User
            </p>
            <p className="text-xs text-slate-500">
              Enterprise Workspace
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;