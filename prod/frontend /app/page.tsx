import { YoloDetectionDashboard } from "@/components/yolo-detection-dashboard"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 p-4 md:p-8">
      <div className="mx-auto max-w-7xl">
        <YoloDetectionDashboard />
      </div>
    </main>
  )
}
