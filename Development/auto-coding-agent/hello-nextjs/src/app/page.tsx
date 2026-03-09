import { Header } from "@/components/layout/Header";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <Header user={user} />
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-16">
        <div className="max-w-3xl text-center">
          <h1 className="mb-4 text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            StockAutoTrader
          </h1>
          <p className="mb-6 text-xl text-zinc-600 dark:text-zinc-400">
            股票全自动交易软件
          </p>
          <p className="mb-8 text-lg text-zinc-500 dark:text-zinc-500">
            基于混合架构的智能交易系统，支持策略自动交易、手动辅助交易、行情监控和提醒、回测系统
          </p>

          <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-3 text-3xl">🤖</div>
              <h3 className="mb-2 font-semibold text-zinc-900 dark:text-zinc-100">策略自动交易</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">自定义策略，AI智能决策</p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-3 text-3xl">📊</div>
              <h3 className="mb-2 font-semibold text-zinc-900 dark:text-zinc-100">行情监控</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">实时行情，及时提醒</p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-3 text-3xl">📈</div>
              <h3 className="mb-2 font-semibold text-zinc-900 dark:text-zinc-100">策略回测</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">历史数据，验证策略</p>
            </div>
          </div>

          {user ? (
            <div className="flex flex-col items-center gap-4">
              <p className="text-zinc-600 dark:text-zinc-400">
                欢迎回来，{user.email}
              </p>
              <div className="flex gap-4">
                <Link
                  href="/dashboard"
                  className="flex h-12 items-center justify-center rounded-lg bg-zinc-900 px-6 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  进入仪表盘
                </Link>
                <Link
                  href="/strategies"
                  className="flex h-12 items-center justify-center rounded-lg border border-zinc-300 bg-white px-6 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:bg-zinc-800"
                >
                  策略管理
                </Link>
              </div>
            </div>
          ) : (
            <div className="flex justify-center gap-4">
              <Link
                href="/login"
                className="flex h-12 items-center justify-center rounded-lg bg-zinc-900 px-6 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="flex h-12 items-center justify-center rounded-lg border border-zinc-300 bg-white px-6 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:bg-zinc-800"
              >
                注册
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
