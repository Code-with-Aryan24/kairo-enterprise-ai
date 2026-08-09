function Dashboard() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <p className="text-sm font-medium text-blue-600">
          KAIRO ENTERPRISE AI
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          Welcome to KAIRO
        </h1>

        <p className="mt-2 text-slate-600">
          Enterprise intelligence, knowledge and automation in one workspace.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">System Status</h2>
          <p className="mt-2 text-sm text-emerald-600">
            ● All systems operational
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">Knowledge</h2>
          <p className="mt-2 text-sm text-slate-600">
            Knowledge sources will appear here.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">AI Activity</h2>
          <p className="mt-2 text-sm text-slate-600">
            AI activity will appear here.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;