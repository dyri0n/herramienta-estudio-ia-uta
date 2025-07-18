"use client"

import { useState, useEffect } from "react"
import { Download, Copy, Eye, Check, ChevronDown, ChevronUp } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"

export default function ResultViewer() {
  const { state } = useNLP()
  const [activeTab, setActiveTab] = useState<"preview" | "json" | "txt">("preview")
  const [copied, setCopied] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())

  const latestResult = state.results[state.results.length - 1]

  const toggleExpand = (index: number) => {
    const newSet = new Set(expandedItems)
    if (newSet.has(index)) {
      newSet.delete(index)
    } else {
      newSet.add(index)
    }
    setExpandedItems(newSet)
  }

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
        return `PREGUNTAS Y RESPUESTAS:\n\n${result.qas.map((qa: any, i: number) => 
          `${i + 1}. ${qa.question}\n   Respuesta: ${qa.answer}\n   Contexto: ${qa.context}\n`
        ).join("\n")}`
        
      case "summary":
        return `RESUMEN:\n\n${result.summary}\n\nPALABRAS CLAVE:\n${result.keywords.join(", ")}\n\nCONTEO DE PALABRAS: ${result.wordCount}`
        
      case "translation":
        return `TEXTO ORIGINAL:\n${result.originalText}\n\nTRADUCCIÓN:\n${result.translatedText}\n\nCONFIANZA: ${(result.confidence * 100).toFixed(1)}%`
        
      case "paraphrase":
        return `TEXTO ORIGINAL:\n${result.originalText}\n\nTEXTO PARAFRASEADO:\n${result.paraphrasedText}`
        
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
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-lg text-gray-900 mb-4">Preguntas y Respuestas Generadas</h3>
              <div className="space-y-4">
                {result.qas.map((qa: any, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      className="w-full p-4 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
                      onClick={() => toggleExpand(index)}
                    >
                      <div className="flex items-start space-x-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </span>
                        <span className="text-left text-gray-800 font-medium">{qa.question}</span>
                      </div>
                      {expandedItems.has(index) ? <ChevronUp className="h-5 w-5 text-gray-500" /> : <ChevronDown className="h-5 w-5 text-gray-500" />}
                    </button>
                    
                    {expandedItems.has(index) && (
                      <div className="p-4 space-y-3">
                        <div className="bg-blue-50 p-3 rounded-md">
                          <h4 className="text-sm font-medium text-blue-800 mb-1">Respuesta</h4>
                          <p className="text-gray-700">{qa.answer}</p>
                        </div>
                        
                        <div className="border-t border-gray-100 pt-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-1">Contexto</h4>
                          <p className="text-gray-600 text-sm">{qa.context}</p>
                        </div>
                        
                        {qa.quality && (
                          <div className="flex items-center justify-between pt-2">
                            <span className="text-sm font-medium text-gray-700">Calidad:</span>
                            <span className="text-sm font-medium text-gray-900">{qa.quality.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
        
      case "summary":
        return (
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-lg text-gray-900 mb-2">Resumen</h3>
              <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg">{result.summary}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Palabras Clave</h4>
                <div className="flex flex-wrap gap-2">
                  {result.keywords.map((keyword: string, index: number) => (
                    <span 
                      key={index} 
                      className="px-3 py-1 bg-accent-100 text-accent-800 rounded-full text-sm"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Estadísticas</h4>
                <div className="space-y-1">
                  <p className="text-sm text-gray-600 flex justify-between">
                    <span>Palabras en resumen:</span>
                    <span className="font-medium">{result.wordCount}</span>
                  </p>
                  {result.quality && (
                    <p className="text-sm text-gray-600 flex justify-between">
                      <span>Calidad:</span>
                      <span className="font-medium">{result.quality.toFixed(2)}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )
        
      case "translation":
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Texto Original</h4>
                <p className="text-gray-700">{result.originalText}</p>
              </div>
              
              <div className="bg-primary-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Traducción</h4>
                <p className="text-gray-700">{result.translatedText}</p>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">Confianza</h4>
                <span className="text-sm font-medium text-gray-700">{(result.confidence * 100).toFixed(1)}%</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-green-600 h-2.5 rounded-full" 
                  style={{ width: `${result.confidence * 100}%` }}
                ></div>
              </div>
              
              {result.quality && (
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Calidad:</span>
                  <span className="text-sm font-medium text-gray-900">{result.quality.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        )
        
      case "paraphrase":
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Texto Original</h4>
                <p className="text-gray-700">{result.originalText}</p>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Texto Parafraseado</h4>
                <p className="text-gray-700">{result.paraphrasedText}</p>
              </div>
            </div>
            
            {result.quality && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Calidad:</span>
                  <span className="text-sm font-medium text-gray-900">{result.quality.toFixed(2)}</span>
                </div>
              </div>
            )}
          </div>
        )
        
      default:
        return (
          <div className="bg-gray-50 p-4 rounded-lg">
            <pre className="text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )
    }
  }

  if (!latestResult) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
        <div className="text-center">
          <Eye className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Sin resultados</h3>
          <p className="text-gray-500">
            Sube un documento y selecciona un servicio para ver los resultados aquí.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between p-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Resultados</h3>
            <p className="text-xs text-gray-500 mt-1 capitalize">
              Servicio: {latestResult.service}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => copyToClipboard(
                activeTab === "preview" 
                  ? formatAsText(latestResult.result, latestResult.service)
                  : JSON.stringify(latestResult.result, null, 2)
              )}
              className="p-2 text-gray-500 hover:text-gray-700 focus:outline-none rounded-lg hover:bg-gray-100"
              title="Copiar resultado"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
            
            <button
              onClick={() => downloadResult("txt")}
              className="p-2 text-gray-500 hover:text-gray-700 focus:outline-none rounded-lg hover:bg-gray-100"
              title="Descargar TXT"
            >
              <Download className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex border-t border-gray-200 bg-white">
          {[
            { id: "preview", label: "Vista Previa", icon: Eye },
            { id: "json", label: "JSON", icon: null },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                px-4 py-2.5 text-sm font-medium border-b-2 focus:outline-none
                ${
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600 bg-white"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
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

      <div className="p-6 max-h-[calc(100vh-220px)] overflow-y-auto bg-white">
        {activeTab === "preview" && renderPreview()}
        
        {activeTab === "json" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => downloadResult("json")}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <Download className="h-4 w-4 mr-1.5" />
                Descargar JSON
              </button>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm text-gray-800 overflow-x-auto">
                {JSON.stringify(latestResult.result, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      {copied && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg animate-fadeInOut">
          ¡Copiado al portapapeles!
        </div>
      )}
    </div>
  )
}