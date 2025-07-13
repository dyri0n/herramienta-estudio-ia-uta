"use client"

import { useState } from "react"
import { Download, Copy, Eye } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"

export default function ResultViewer() {
  const { state } = useNLP()
  const [activeTab, setActiveTab] = useState<"preview" | "json" | "txt">("preview")
  const [copied, setCopied] = useState(false)

  const latestResult = state.results[state.results.length - 1]

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Error copying to clipboard:", err)
    }
  }

  const downloadResult = (format: "json" | "txt") => {
    if (!latestResult) return

    const content =
      format === "json"
        ? JSON.stringify(latestResult.result, null, 2)
        : formatAsText(latestResult.result, latestResult.service)

    const blob = new Blob([content], {
      type: format === "json" ? "application/json" : "text/plain",
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `nlp-result-${latestResult.id}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatAsText = (result: any, service: string) => {
    switch (service) {
      case "questions":
        return `PREGUNTAS GENERADAS:\n\n${result.questions.map((q: string, i: number) => `${i + 1}. ${q}`).join("\n")}\n\nPALABRAS CLAVE:\n${result.keywords.join(", ")}`
      case "summary":
        return `RESUMEN:\n\n${result.summary}\n\nPALABRAS CLAVE:\n${result.keywords.join(", ")}\n\nCONTEO DE PALABRAS: ${result.wordCount}`
      case "translation":
        return `TEXTO ORIGINAL:\n${result.originalText}\n\nTRADUCCIÓN:\n${result.translatedText}\n\nCONFIANZA: ${(result.confidence * 100).toFixed(1)}%`
      default:
        return JSON.stringify(result, null, 2)
    }
  }

  const renderPreview = () => {
    if (!latestResult) return null

    const { result, service } = latestResult

    switch (service) {
      case "questions":
        return (
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Preguntas Generadas</h4>
              <ul className="space-y-2">
                {result.questions.map((question: string, index: number) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{question}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Palabras Clave</h4>
              <div className="flex flex-wrap gap-2">
                {result.keywords.map((keyword: string, index: number) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-accent-100 text-accent-800 rounded-full text-sm font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )
      case "summary":
        return (
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Resumen</h4>
              <p className="text-gray-700 leading-relaxed">{result.summary}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Palabras Clave</h4>
                <div className="flex flex-wrap gap-2">
                  {result.keywords.map((keyword: string, index: number) => (
                    <span key={index} className="px-2 py-1 bg-accent-100 text-accent-800 rounded text-sm">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Estadísticas</h4>
                <p className="text-sm text-gray-600">
                  Palabras en resumen: <span className="font-medium">{result.wordCount}</span>
                </p>
              </div>
            </div>
          </div>
        )
      case "translation":
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Texto Original</h4>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-gray-700 text-sm">{result.originalText}</p>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Traducción</h4>
                <div className="p-3 bg-primary-50 rounded-lg">
                  <p className="text-gray-700 text-sm">{result.translatedText}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900 mb-1">Confianza</h4>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${result.confidence * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-700">{(result.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        )
      default:
        return <pre className="text-sm text-gray-600">{JSON.stringify(result, null, 2)}</pre>
    }
  }

  if (!latestResult) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center">
          <Eye className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Sin resultados</h3>
          <p className="text-gray-500">Sube un documento y selecciona un servicio para ver los resultados aquí.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="border-b border-gray-200">
        <div className="flex items-center justify-between p-4">
          <h3 className="text-lg font-medium text-gray-900">Resultados</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => copyToClipboard(JSON.stringify(latestResult.result, null, 2))}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
              title="Copiar resultado"
            >
              <Copy className="h-4 w-4" />
            </button>
            <button
              onClick={() => downloadResult("json")}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
              title="Descargar JSON"
            >
              <Download className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex border-b border-gray-200">
          {[
            { id: "preview", label: "Vista Previa", icon: Eye },
            { id: "json", label: "JSON", icon: null },
            { id: "txt", label: "TXT", icon: null },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                px-4 py-2 text-sm font-medium border-b-2 focus:outline-none
                ${
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }
              `}
            >
              <div className="flex items-center space-x-1">
                {tab.icon && <tab.icon className="h-4 w-4" />}
                <span>{tab.label}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {activeTab === "preview" && renderPreview()}
        {activeTab === "json" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => downloadResult("json")}
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <Download className="h-4 w-4 mr-1" />
                Descargar JSON
              </button>
            </div>
            <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-800 overflow-x-auto">
              {JSON.stringify(latestResult.result, null, 2)}
            </pre>
          </div>
        )}
        {activeTab === "txt" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => downloadResult("txt")}
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <Download className="h-4 w-4 mr-1" />
                Descargar TXT
              </button>
            </div>
            <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-800 whitespace-pre-wrap">
              {formatAsText(latestResult.result, latestResult.service)}
            </pre>
          </div>
        )}
      </div>

      {copied && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
          ¡Copiado al portapapeles!
        </div>
      )}
    </div>
  )
}
