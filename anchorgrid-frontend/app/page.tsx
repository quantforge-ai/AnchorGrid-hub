import { AgentCard } from "@/components/AgentCard"
import mockData from "@/lib/mock_data.json"
import { Input } from "@/components/ui/input"
import { Search, ShieldCheck } from "lucide-react"

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      {/* Navbar */}
      <div className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="AnchorGrid Hub" className="h-10 w-auto" />
          </div>
          <div className="flex items-center gap-4 text-sm font-medium">
            <span className="text-slate-500 hidden md:inline">Network Status:</span>
            <span className="flex items-center text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full border border-emerald-100 text-xs font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
              Mainnet Active
            </span>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-12 text-center max-w-2xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 mb-4">
            The Secure Agent Economy
          </h1>
          <p className="text-lg text-slate-500 mb-8 leading-relaxed">
            Discover, verify, and deploy autonomous agents. <br className="hidden md:block" />
            Protected by the <span className="text-indigo-600 font-semibold">Proof-of-Integrity Protocol</span>.
          </p>

          {/* Search Bar */}
          <div className="relative max-w-md mx-auto shadow-sm">
            <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
            <Input
              placeholder="Search for verified capabilities (e.g., finance, medical)..."
              className="pl-10 h-12 bg-white border-slate-200 text-base"
            />
          </div>
        </div>

        {/* The Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockData.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </div>
    </main>
  )
}
