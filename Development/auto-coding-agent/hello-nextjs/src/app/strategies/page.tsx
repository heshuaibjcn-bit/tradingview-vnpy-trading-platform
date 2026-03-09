import { Header } from "@/components/layout/Header";
import { createClient } from "@/lib/supabase/server";
import { getStrategiesWithSignals } from "@/lib/db/strategies";
import { redirect } from "next/navigation";
import { StrategiesClient } from "@/components/strategies/StrategiesClient";

export default async function StrategiesPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const strategies = await getStrategiesWithSignals(user.id);

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <Header user={user} />
      <main className="flex flex-1 flex-col px-4 py-8">
        <div className="mx-auto w-full max-w-7xl">
          {/* Strategies Content */}
          <StrategiesClient userId={user.id} initialStrategies={strategies} />
        </div>
      </main>
    </div>
  );
}
