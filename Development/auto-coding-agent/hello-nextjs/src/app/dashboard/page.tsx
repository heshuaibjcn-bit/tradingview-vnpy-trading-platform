import { Header } from "@/components/layout/Header";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { DashboardClient } from "@/components/dashboard/DashboardClient";

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface DashboardPageProps {}

export default async function DashboardPage({}: DashboardPageProps) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <Header user={user} />
      <main className="flex flex-1 flex-col px-4 py-8">
        <div className="mx-auto w-full max-w-7xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
              交易仪表盘
            </h1>
            <p className="mt-1 text-zinc-600 dark:text-zinc-400">
              实时监控您的交易账户
            </p>
          </div>

          {/* Dashboard Content */}
          <DashboardClient userId={user.id} />
        </div>
      </main>
    </div>
  );
}
