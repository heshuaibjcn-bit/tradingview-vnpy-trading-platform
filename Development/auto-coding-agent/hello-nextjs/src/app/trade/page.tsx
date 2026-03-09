import { Header } from "@/components/layout/Header";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { TradeClient } from "@/components/trade/TradeClient";

export default async function TradePage() {
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
          <TradeClient userId={user.id} />
        </div>
      </main>
    </div>
  );
}
