"use client"
import { Brain, Zap } from "lucide-react"
import DocumentUploader from "@/components/ui/DocumentUploader"
import ServiceTabs from "@/components/ui/ServiceTabs"
import ResultViewer from "@/components/ui/ResultViewer"
import HistoryPanel from "@/components/ui/HistoryPanel"

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">NLP Platform</h1>
                <p className="text-sm text-gray-500">Procesamiento de Lenguaje Natural</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <DocumentUploader />
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <ServiceTabs />
            </div>

            {/* History Panel - Mobile */}
            <div className="lg:hidden">
              <HistoryPanel />
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-8">
            <ResultViewer />

            {/* History Panel - Desktop */}
            <div className="hidden lg:block">
              <HistoryPanel />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-gray-500">
            <p>© 2025 NLP Platform. Desarrollado con React 18 + Next.js + Tailwind CSS</p>
            <p className="mt-2">Servicios disponibles: Generación de Preguntas • Resumen de Texto • Traducción EN→ES</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
