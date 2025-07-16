"use client"
import { Clock, FileText, MessageSquare, Languages, Download } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"

const serviceIcons = {
  questions: MessageSquare,
  summary: FileText,
  translation: Languages,
}

const serviceNames = {
  questions: "Preguntas",
  summary: "Resumen",
  translation: "Traducción",
}

export default function HistoryPanel() {
  const { state } = useNLP()

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("es-ES", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)
  }

  const downloadHistoryItem = (result: any) => {
    const content = JSON.stringify(result.result, null, 2)
    const blob = new Blob([content], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `nlp-${result.service}-${result.id}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (state.history.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center">
          <Clock className="mx-auto h-8 w-8 text-gray-400 mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-1">Sin historial</h3>
          <p className="text-sm text-gray-500">Las operaciones aparecerán aquí una vez procesadas.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Historial de Operaciones</h3>
        <p className="text-sm text-gray-500 mt-1">
          {state.history.length} operación{state.history.length !== 1 ? "es" : ""} realizadas
        </p>
      </div>

      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {state.history
          .slice()
          .reverse()
          .map((item) => {
            const Icon = serviceIcons[item.service as keyof typeof serviceIcons]
            const document = state.documents.find((doc) => doc.id === item.documentId)

            return (
              <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="flex-shrink-0">
                      <Icon className="h-5 w-5 text-primary-500 mt-0.5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-900">
                          {serviceNames[item.service as keyof typeof serviceNames]}
                        </span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800">
                          {item.service}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 truncate mb-1">{document?.name || "Documento eliminado"}</p>
                      <p className="text-xs text-gray-500">{formatDate(item.createdAt)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => downloadHistoryItem(item)}
                    className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                    title="Descargar resultado"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>

                {/* Preview del resultado */}
                <div className="mt-3 pl-8">
                  <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
                    {item.service === "questions" && (
                      <span>{item.result.questions?.length || 0} preguntas generadas</span>
                    )}
                    {item.service === "summary" && <span>Resumen de {item.result.wordCount || 0} palabras</span>}
                    {item.service === "translation" && (
                      <span>Traducción con {((item.result.confidence || 0) * 100).toFixed(1)}% confianza</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}
